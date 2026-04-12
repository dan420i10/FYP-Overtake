"""
frontend.py — F1 RAG Web Frontend

Starts a local web server and opens the chat UI in your browser.
The UI talks to main.py via a subprocess with real-time streaming.

Usage
-----
    python frontend.py

Then open http://localhost:7433 in your browser.
The frontend runs main.py --stream --verbose under the hood.
"""

import asyncio
import json
import os
import re
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────────
PORT        = 7433
MAIN_SCRIPT = Path(__file__).parent / "main.py"
PYTHON      = sys.executable   # same interpreter that's running this file

# ── HTML ───────────────────────────────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>F1 RAG — Pit Wall</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Mono:ital,wght@0,300;0,400;0,500;1,300&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">

<style>
  /* ── Reset & tokens ─────────────────────────────────────────────────────── */
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg:        #0a0a0b;
    --surface:   #111114;
    --surface2:  #18181d;
    --border:    #2a2a32;
    --red:       #e8002d;
    --red-dim:   #8c0018;
    --gold:      #f5c842;
    --text:      #e8e8ec;
    --muted:     #6b6b78;
    --mono:      'DM Mono', monospace;
    --sans:      'DM Sans', sans-serif;
    --display:   'Bebas Neue', sans-serif;
  }

  html, body {
    height: 100%;
    background: var(--bg);
    color: var(--text);
    font-family: var(--sans);
    font-size: 15px;
    line-height: 1.6;
    overflow: hidden;
  }

  /* ── Layout ─────────────────────────────────────────────────────────────── */
  .shell {
    display: grid;
    grid-template-rows: auto 1fr auto;
    height: 100vh;
    max-width: 860px;
    margin: 0 auto;
  }

  /* ── Header ─────────────────────────────────────────────────────────────── */
  header {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 22px 28px 18px;
    border-bottom: 1px solid var(--border);
    position: relative;
  }

  .logo-mark {
    width: 38px; height: 38px;
    background: var(--red);
    clip-path: polygon(0 0, 80% 0, 100% 50%, 80% 100%, 0 100%);
    flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    padding-right: 6px;
  }
  .logo-mark svg { width: 18px; height: 18px; fill: white; }

  .title-block h1 {
    font-family: var(--display);
    font-size: 26px;
    letter-spacing: 0.08em;
    color: var(--text);
    line-height: 1;
  }
  .title-block p {
    font-size: 11px;
    color: var(--muted);
    font-family: var(--mono);
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-top: 3px;
  }

  .status-pill {
    margin-left: auto;
    display: flex; align-items: center; gap: 7px;
    font-family: var(--mono);
    font-size: 11px;
    color: var(--muted);
    letter-spacing: 0.08em;
  }
  .status-dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: var(--muted);
    transition: background 0.4s;
  }
  .status-dot.live   { background: #22c55e; box-shadow: 0 0 6px #22c55e88; }
  .status-dot.typing { background: var(--gold); box-shadow: 0 0 6px var(--gold); animation: pulse 0.8s ease infinite; }
  .status-dot.error  { background: var(--red); }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

  /* ── Chat area ───────────────────────────────────────────────────────────── */
  .chat {
    overflow-y: auto;
    padding: 28px 28px 12px;
    display: flex;
    flex-direction: column;
    gap: 24px;
    scroll-behavior: smooth;
  }
  .chat::-webkit-scrollbar { width: 4px; }
  .chat::-webkit-scrollbar-track { background: transparent; }
  .chat::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

  /* ── Messages ────────────────────────────────────────────────────────────── */
  .msg { display: flex; flex-direction: column; gap: 6px; animation: fadeUp 0.25s ease; }
  @keyframes fadeUp { from { opacity:0; transform: translateY(8px); } to { opacity:1; transform: none; } }

  .msg.user { align-items: flex-end; }
  .msg.bot  { align-items: flex-start; }

  .bubble {
    max-width: 78%;
    padding: 12px 16px;
    border-radius: 4px;
    font-size: 14px;
    line-height: 1.65;
  }

  .msg.user .bubble {
    background: var(--red);
    color: #fff;
    border-bottom-right-radius: 1px;
    font-weight: 500;
  }

  .msg.bot .bubble {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-bottom-left-radius: 1px;
    color: var(--text);
    font-family: var(--sans);
    white-space: pre-wrap;
  }

  .msg-label {
    font-family: var(--mono);
    font-size: 10px;
    color: var(--muted);
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 0 4px;
  }

  /* ── Verbose / debug panel ───────────────────────────────────────────────── */
  .debug-panel {
    margin-top: 8px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--gold);
    border-radius: 4px;
    padding: 10px 14px;
    font-family: var(--mono);
    font-size: 11.5px;
    color: var(--muted);
    max-width: 78%;
    white-space: pre-wrap;
    line-height: 1.5;
    animation: fadeUp 0.2s ease;
  }
  .debug-panel .debug-title {
    color: var(--gold);
    font-size: 10px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 6px;
  }

  /* ── Cursor blink ────────────────────────────────────────────────────────── */
  .cursor::after {
    content: '▌';
    color: var(--red);
    animation: blink 0.6s step-end infinite;
  }
  @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }

  /* ── Intro splash ────────────────────────────────────────────────────────── */
  .intro {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 12px;
    flex: 1;
    opacity: 0.55;
    padding: 40px;
    text-align: center;
    pointer-events: none;
  }
  .intro .big { font-family: var(--display); font-size: 52px; letter-spacing: 0.06em; color: var(--muted); }
  .intro p    { font-family: var(--mono); font-size: 12px; color: var(--muted); line-height: 1.8; }

  /* ── Divider ─────────────────────────────────────────────────────────────── */
  .divider {
    display: flex; align-items: center; gap: 10px;
    padding: 0 28px;
    margin: 4px 0;
  }
  .divider-line { flex:1; height:1px; background: var(--border); }
  .divider-text { font-family: var(--mono); font-size: 10px; color: var(--border); letter-spacing:.1em; }

  /* ── Input area ─────────────────────────────────────────────────────────── */
  .input-bar {
    padding: 16px 28px 24px;
    border-top: 1px solid var(--border);
  }

  .input-row {
    display: flex;
    gap: 10px;
    align-items: flex-end;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 10px 10px 10px 16px;
    transition: border-color 0.2s;
  }
  .input-row:focus-within { border-color: var(--red-dim); }

  textarea {
    flex: 1;
    background: transparent;
    border: none;
    outline: none;
    color: var(--text);
    font-family: var(--sans);
    font-size: 14px;
    resize: none;
    min-height: 22px;
    max-height: 120px;
    line-height: 1.5;
    caret-color: var(--red);
  }
  textarea::placeholder { color: var(--muted); }

  button#send {
    width: 36px; height: 36px; flex-shrink: 0;
    background: var(--red);
    border: none; cursor: pointer;
    border-radius: 4px;
    display: flex; align-items: center; justify-content: center;
    transition: background 0.15s, transform 0.1s;
  }
  button#send:hover:not(:disabled)  { background: #ff1a3c; }
  button#send:active:not(:disabled) { transform: scale(0.93); }
  button#send:disabled { background: var(--border); cursor: not-allowed; }
  button#send svg { width:16px; height:16px; fill:white; }

  .input-hint {
    margin-top: 8px;
    font-family: var(--mono);
    font-size: 10px;
    color: var(--border);
    text-align: right;
    letter-spacing: 0.08em;
  }

  /* ── Suggested questions ─────────────────────────────────────────────────── */
  .suggestions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    padding: 0 28px 16px;
  }
  .sug-btn {
    background: transparent;
    border: 1px solid var(--border);
    color: var(--muted);
    font-family: var(--mono);
    font-size: 11px;
    padding: 5px 11px;
    border-radius: 3px;
    cursor: pointer;
    transition: all 0.15s;
    letter-spacing: 0.04em;
  }
  .sug-btn:hover { border-color: var(--red-dim); color: var(--text); }
</style>
</head>

<body>
<div class="shell">

  <!-- Header -->
  <header>
    <div class="logo-mark">
      <svg viewBox="0 0 24 24"><path d="M12 2L2 7v10l10 5 10-5V7L12 2zm0 2.18L20 8.5v7l-8 4-8-4v-7l8-4.32z"/></svg>
    </div>
    <div class="title-block">
      <h1>PIT WALL</h1>
      <p>F1 Intelligence System · RAG</p>
    </div>
    <div class="status-pill">
      <span class="status-dot" id="statusDot"></span>
      <span id="statusText">initialising</span>
    </div>
  </header>

  <!-- Chat -->
  <div class="chat" id="chat">
    <div class="intro" id="intro">
      <div class="big">ASK</div>
      <p>Drivers · Teams · Circuits · History · Rules<br>Powered by Qwen2.5 + Hybrid RAG</p>
    </div>
  </div>

  <!-- Suggestions (hidden after first message) -->
  <div class="suggestions" id="suggestions">
    <button class="sug-btn" onclick="suggest(this)">Who won the 2023 championship?</button>
    <button class="sug-btn" onclick="suggest(this)">Explain DRS and how it works</button>
    <button class="sug-btn" onclick="suggest(this)">What made Senna so special?</button>
    <button class="sug-btn" onclick="suggest(this)">How does KERS work?</button>
  </div>

  <!-- Input -->
  <div class="input-bar">
    <div class="input-row">
      <textarea id="input" rows="1" placeholder="Ask anything about Formula 1…" autocomplete="off"></textarea>
      <button id="send" onclick="sendMessage()" title="Send (Enter)">
        <svg viewBox="0 0 24 24"><path d="M2 21l21-9L2 3v7l15 2-15 2z"/></svg>
      </button>
    </div>
    <div class="input-hint">ENTER to send · SHIFT+ENTER for newline</div>
  </div>

</div>

<script>
const chat        = document.getElementById('chat');
const input       = document.getElementById('input');
const sendBtn     = document.getElementById('send');
const statusDot   = document.getElementById('statusDot');
const statusText  = document.getElementById('statusText');
const suggestions = document.getElementById('suggestions');
const intro       = document.getElementById('intro');

let busy = false;

// ── Status helpers ────────────────────────────────────────────────────────────
function setStatus(state, label) {
  statusDot.className = 'status-dot ' + state;
  statusText.textContent = label;
}

// ── Auto-resize textarea ──────────────────────────────────────────────────────
input.addEventListener('input', () => {
  input.style.height = 'auto';
  input.style.height = Math.min(input.scrollHeight, 120) + 'px';
});

input.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});

// ── Suggestion pills ──────────────────────────────────────────────────────────
function suggest(btn) {
  input.value = btn.textContent;
  input.dispatchEvent(new Event('input'));
  sendMessage();
}

// ── Append a user bubble ──────────────────────────────────────────────────────
function appendUser(text) {
  intro.style.display = 'none';
  suggestions.style.display = 'none';

  const msg = document.createElement('div');
  msg.className = 'msg user';
  msg.innerHTML = `<span class="msg-label">You</span>
    <div class="bubble">${escHtml(text)}</div>`;
  chat.appendChild(msg);
  scrollBottom();
}

// ── Append bot bubble (returns {bubble, debug} for streaming) ────────────────
function appendBot() {
  const wrapper = document.createElement('div');
  wrapper.className = 'msg bot';

  const label = document.createElement('span');
  label.className = 'msg-label';
  label.textContent = 'Pit Wall';
  wrapper.appendChild(label);

  const bubble = document.createElement('div');
  bubble.className = 'bubble cursor';
  wrapper.appendChild(bubble);

  const debugPanel = document.createElement('div');
  debugPanel.className = 'debug-panel';
  debugPanel.style.display = 'none';
  debugPanel.innerHTML = '<div class="debug-title">Retrieval · Verbose</div><span class="debug-body"></span>';
  wrapper.appendChild(debugPanel);

  chat.appendChild(wrapper);
  scrollBottom();
  return { bubble, debugPanel };
}

function scrollBottom() {
  chat.scrollTop = chat.scrollHeight;
}

function escHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// ── Main send ─────────────────────────────────────────────────────────────────
async function sendMessage() {
  const q = input.value.trim();
  if (!q || busy) return;

  busy = true;
  sendBtn.disabled = true;
  input.value = '';
  input.style.height = 'auto';

  appendUser(q);

  const { bubble, debugPanel } = appendBot();
  setStatus('typing', 'generating');

  try {
    const resp = await fetch('/ask', {
      method:  'POST',
      headers: {'Content-Type': 'application/json'},
      body:    JSON.stringify({ question: q }),
    });

    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

    const reader  = resp.body.getReader();
    const decoder = new TextDecoder();
    let   answer  = '';
    let   debug   = '';
    let   inDebug = false;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });

      // Each SSE line is: "data: <json>\n\n"
      const lines = chunk.split('\n');
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        let msg;
        try { msg = JSON.parse(line.slice(6)); } catch { continue; }

        if (msg.type === 'debug') {
          debug += msg.text;
          debugPanel.style.display = 'block';
          debugPanel.querySelector('.debug-body').textContent = debug;
        } else if (msg.type === 'token') {
          answer += msg.text;
          bubble.textContent = answer;
          scrollBottom();
        } else if (msg.type === 'done') {
          bubble.classList.remove('cursor');
          setStatus('live', 'ready');
        } else if (msg.type === 'error') {
          bubble.textContent = '⚠️  ' + msg.text;
          bubble.classList.remove('cursor');
          setStatus('error', 'error');
        }
      }
    }

  } catch (err) {
    bubble.textContent = '⚠️  Connection error: ' + err.message;
    bubble.classList.remove('cursor');
    setStatus('error', 'error');
  }

  busy = false;
  sendBtn.disabled = false;
  input.focus();
}

// ── Ping until ready ──────────────────────────────────────────────────────────
async function waitForReady() {
  setStatus('', 'initialising');
  while (true) {
    try {
      const r = await fetch('/ping');
      if (r.ok) { setStatus('live', 'ready'); input.focus(); return; }
    } catch {}
    await new Promise(r => setTimeout(r, 1200));
  }
}
waitForReady();
</script>
</body>
</html>
"""

# ── Subprocess manager ─────────────────────────────────────────────────────────

class RAGProcess:
    """
    Keeps one long-running `python main.py --stream --verbose` process alive.
    Questions are written to its stdin; tokens are read from stdout.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._proc = None
        self._ready = False
        threading.Thread(target=self._start, daemon=True).start()

    def _start(self):
        cmd = [PYTHON, str(MAIN_SCRIPT), "--stream", "--verbose"]
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        self._proc = subprocess.Popen(
            cmd,
            stdin  = subprocess.PIPE,
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            text   = True,
            encoding = 'utf-8',
            errors = 'replace',
            bufsize= 1,
            cwd    = str(MAIN_SCRIPT.parent),
            env    = env,
        )
        
        # Start a thread to read stderr for debugging
        def read_stderr():
            for line in self._proc.stderr:
                import sys
                print(f"[subprocess error] {line}", file=sys.stderr, flush=True)
        threading.Thread(target=read_stderr, daemon=True).start()
        
        # Drain startup output until we see the "Ready" prompt
        for line in self._proc.stdout:
            if "Ready" in line or "Question:" in line:
                self._ready = True
                break
        self._ready = True

    @property
    def ready(self):
        return self._ready and self._proc and self._proc.poll() is None

    def ask(self, question: str):
        """
        Generator: yields (type, text) tuples.
          type = 'debug'  — verbose retrieval info lines
          type = 'token'  — answer tokens
          type = 'done'   — finished
          type = 'error'  — something went wrong
        """
        with self._lock:
            if not self.ready:
                yield ('error', 'Pipeline not ready yet — please wait a moment.')
                return

            # Send the question
            try:
                self._proc.stdin.write(question + "\n")
                self._proc.stdin.flush()
            except BrokenPipeError:
                yield ('error', 'Pipeline process died. Please restart frontend.py.')
                return

            # ── Parse stdout ──────────────────────────────────────────────────
            # Phases:
            #   1. verbose block: lines between ─────… delimiters
            #   2. "🏎  Answer:" header  → we are now in answer phase
            #   3. answer tokens stream until next "❓ Question:" prompt
            in_verbose = False
            in_answer  = False
            debug_buf  = []

            for raw_line in self._proc.stdout:
                line = raw_line   # keep newlines for debug display

                # Detect verbose block delimiters (─────)
                stripped = raw_line.strip()
                if re.match(r'^─{20,}', stripped):
                    if not in_verbose:
                        in_verbose = True
                    else:
                        # end of verbose block — emit debug
                        in_verbose = False
                        yield ('debug', ''.join(debug_buf))
                    continue

                if in_verbose:
                    debug_buf.append(line)
                    continue

                # Generation time line
                if stripped.startswith('[Generation time:'):
                    yield ('debug', '\n' + stripped)
                    continue

                # Answer header
                if '🏎' in stripped and 'Answer' in stripped:
                    in_answer = True
                    continue

                # Next prompt → done
                if '❓' in stripped and 'Question' in stripped:
                    yield ('done', '')
                    return

                # Answer content
                if in_answer:
                    yield ('token', raw_line)


# ── HTTP handler ───────────────────────────────────────────────────────────────

_rag = RAGProcess()


class Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        pass   # suppress default access log

    def _send(self, code, ctype, body: bytes):
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ('/', '/index.html'):
            self._send(200, 'text/html; charset=utf-8', HTML.encode())
        elif self.path == '/ping':
            if _rag.ready:
                self._send(200, 'text/plain', b'ok')
            else:
                self._send(503, 'text/plain', b'not ready')
        else:
            self._send(404, 'text/plain', b'not found')

    def do_POST(self):
        if self.path != '/ask':
            self._send(404, 'text/plain', b'not found')
            return

        length   = int(self.headers.get('Content-Length', 0))
        body     = self.rfile.read(length)
        question = json.loads(body).get('question', '').strip()

        if not question:
            self._send(400, 'text/plain', b'empty question')
            return

        # Server-Sent Events stream
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('X-Accel-Buffering', 'no')
        self.end_headers()

        def emit(obj):
            data = 'data: ' + json.dumps(obj) + '\n\n'
            self.wfile.write(data.encode())
            self.wfile.flush()

        try:
            for kind, text in _rag.ask(question):
                emit({'type': kind, 'text': text})
                if kind in ('done', 'error'):
                    break
        except (BrokenPipeError, ConnectionResetError):
            pass


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    # Fix Unicode encoding on Windows
    if sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    server = HTTPServer(('127.0.0.1', PORT), Handler)
    url    = f'http://localhost:{PORT}'
    print(f'\n  🏁  F1 Pit Wall starting …')
    print(f'  📡  Initialising RAG pipeline (this takes ~10-30 s first time) …')
    print(f'  🌐  Opening {url}\n')
    threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n  Shutting down. Goodbye! 🏁')
        server.shutdown()


if __name__ == '__main__':
    main()
