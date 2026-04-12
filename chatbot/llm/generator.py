"""
llm/generator.py

Text generation using Qwen/Qwen2.5-1.5B-Instruct via HuggingFace Transformers.

GPU acceleration stack (applied automatically when CUDA is present):
  1. 4-bit NF4 quantisation via bitsandbytes  → model fits in ~1 GB VRAM
  2. bfloat16 compute dtype                   → fast tensor cores
  3. Flash Attention 2 (if installed)         → faster attention kernel
  4. torch.compile (PyTorch ≥ 2.0)           → fused CUDA kernels on first run
  5. use_cache=True (KV-cache, default on)    → no redundant recomputation

Expected generation time on a mid-range NVIDIA GPU (RTX 3060/4060):
  CPU only   : ~60-90 s for 512 tokens
  4-bit GPU  : ~3-6 s  for 512 tokens
"""

import sys
import logging
from pathlib import Path
from typing import Iterator

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TextIteratorStreamer,
    BitsAndBytesConfig,
)
from threading import Thread

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    LLM_MODEL_ID, LLM_MAX_NEW_TOKENS,
    LLM_TEMPERATURE, LLM_TOP_P, LLM_DEVICE,
    RAG_SYSTEM_PROMPT, RAG_USER_TEMPLATE,
    TOP_K_FINAL, CUDA_AVAILABLE,
)
from retrieval.hybrid_ranker import RankedResult

log = logging.getLogger(__name__)


def _build_quantisation_config() -> "BitsAndBytesConfig | None":
    """
    4-bit NF4 quantisation — cuts VRAM use ~75% with minimal quality loss.
    Only activates when bitsandbytes is installed AND CUDA is present.
    """
    if not CUDA_AVAILABLE:
        return None
    try:
        import bitsandbytes  # noqa: F401
        log.info("bitsandbytes found — enabling 4-bit NF4 quantisation")
        return BitsAndBytesConfig(
            load_in_4bit              = True,
            bnb_4bit_quant_type       = "nf4",
            bnb_4bit_use_double_quant = True,        # nested quantisation saves ~0.4 bits/param
            bnb_4bit_compute_dtype    = torch.bfloat16,  # fastest on Ampere+ GPUs
        )
    except ImportError:
        log.warning(
            "bitsandbytes not installed — falling back to bfloat16 (full precision). "
            "Install it with: pip install bitsandbytes"
        )
        return None


def _supports_flash_attention() -> bool:
    """Check whether flash-attn ≥ 2 is available."""
    try:
        import flash_attn  # noqa: F401
        return True
    except ImportError:
        return False


class F1Generator:
    """
    Wraps Qwen2.5-1.5B-Instruct for RAG-based question answering.

    Usage
    -----
    gen = F1Generator()
    answer = gen.answer("Who won the 2023 F1 championship?", context_docs)
    # or stream:
    for token in gen.stream("...", context_docs):
        print(token, end="", flush=True)
    """

    def __init__(self, model_id: str = LLM_MODEL_ID) -> None:
        self.model_id  = model_id
        self._loaded   = False
        self.tokenizer = None
        self.model     = None

    def _load(self) -> None:
        if self._loaded:
            return

        log.info(f"Loading LLM: {self.model_id}  (CUDA available: {CUDA_AVAILABLE})")

        # ── Tokenizer ───────────────────────────────────────────────────────────
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_id,
            trust_remote_code=True,
        )

        # ── Model loading strategy ──────────────────────────────────────────────
        quant_cfg = _build_quantisation_config()

        if quant_cfg:
            # Path 1: 4-bit quantised on GPU — fastest & smallest VRAM footprint
            log.info("Loading model with 4-bit NF4 quantisation on GPU …")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                quantization_config = quant_cfg,
                device_map          = LLM_DEVICE,
                trust_remote_code   = True,
                # Flash Attention 2 reduces memory bandwidth & speeds up attention
                attn_implementation = "flash_attention_2" if _supports_flash_attention() else "eager",
            )

        elif CUDA_AVAILABLE:
            # Path 2: GPU available but bitsandbytes missing → bfloat16
            log.info("Loading model in bfloat16 on GPU (no quantisation) …")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                torch_dtype         = torch.bfloat16,
                device_map          = LLM_DEVICE,
                trust_remote_code   = True,
                attn_implementation = "flash_attention_2" if _supports_flash_attention() else "eager",
            )

        else:
            # Path 3: CPU-only fallback
            log.warning("No CUDA GPU found — running on CPU. Generation will be slow.")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                torch_dtype       = torch.float32,
                device_map        = "cpu",
                trust_remote_code = True,
            )

        self.model.eval()

        # ── torch.compile (PyTorch ≥ 2.0, CUDA only) ───────────────────────────
        # Fuses CUDA kernels — adds ~30 s on first call but speeds up all later ones.
        # Skip on CPU or older PyTorch where compile is unsupported.
        if CUDA_AVAILABLE and hasattr(torch, "compile"):
            try:
                log.info("Applying torch.compile to model (first inference will be slower) …")
                self.model = torch.compile(self.model, mode="reduce-overhead")
            except Exception as e:
                log.warning(f"torch.compile failed (non-fatal): {e}")

        self._loaded = True

        # Log which device(s) the model ended up on
        if hasattr(self.model, "hf_device_map"):
            unique_devices = set(self.model.hf_device_map.values())
            log.info(f"Model loaded ✓  —  device map: {unique_devices}")
        else:
            log.info("Model loaded ✓")

    # ── Prompt construction ─────────────────────────────────────────────────────

    @staticmethod
    def _build_context(docs: list[RankedResult]) -> str:
        parts = []
        for i, doc in enumerate(docs, 1):
            src   = doc.metadata.get("source", "unknown")
            title = doc.metadata.get("title",  "unknown")
            parts.append(
                f"[Document {i}] (Source: {title} — {src})\n{doc.text}"
            )
        return "\n\n---\n\n".join(parts)

    def _build_messages(self, question: str, docs: list[RankedResult]) -> list[dict]:
        context = self._build_context(docs)
        user_msg = RAG_USER_TEMPLATE.format(context=context, question=question)
        return [
            {"role": "system", "content": RAG_SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ]

    def _tokenise_messages(self, messages: list[dict]) -> dict:
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize              = False,
            add_generation_prompt = True,
        )
        return self.tokenizer(text, return_tensors="pt").to(self.model.device)

    # ── Generation ──────────────────────────────────────────────────────────────

    def answer(
        self,
        question:       str,
        docs:           list[RankedResult],
        max_new_tokens: int   = LLM_MAX_NEW_TOKENS,
        temperature:    float = LLM_TEMPERATURE,
        top_p:          float = LLM_TOP_P,
    ) -> str:
        """Generate a complete answer (blocking)."""
        self._load()

        messages = self._build_messages(question, docs)
        inputs   = self._tokenise_messages(messages)

        with torch.inference_mode():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens = max_new_tokens,
                temperature    = temperature,
                top_p          = top_p,
                do_sample      = temperature > 0,
                pad_token_id   = self.tokenizer.eos_token_id,
                use_cache      = True,   # KV-cache — critical for GPU speed
            )

        # Decode only the newly generated tokens
        new_tokens = output_ids[0][inputs["input_ids"].shape[-1]:]
        return self.tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

    def stream(
        self,
        question:       str,
        docs:           list[RankedResult],
        max_new_tokens: int   = LLM_MAX_NEW_TOKENS,
        temperature:    float = LLM_TEMPERATURE,
        top_p:          float = LLM_TOP_P,
    ) -> Iterator[str]:
        """Stream the answer token by token."""
        self._load()

        messages = self._build_messages(question, docs)
        inputs   = self._tokenise_messages(messages)
        streamer = TextIteratorStreamer(
            self.tokenizer, skip_prompt=True, skip_special_tokens=True
        )

        gen_kwargs = dict(
            **inputs,
            max_new_tokens = max_new_tokens,
            temperature    = temperature,
            top_p          = top_p,
            do_sample      = temperature > 0,
            pad_token_id   = self.tokenizer.eos_token_id,
            use_cache      = True,   # KV-cache
            streamer       = streamer,
        )

        thread = Thread(target=self.model.generate, kwargs=gen_kwargs)
        thread.start()

        for token in streamer:
            yield token

        thread.join()
