"""
Load F1 ensemble models and feature parquet from model-training for inference.

Paths default to repo sibling folders; override with env F1_FEATURES_PARQUET and F1_MODEL_DIR.
"""
from __future__ import annotations

import os
import pickle
import sys
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

_repo_root = Path(__file__).resolve().parent.parent
_model_training = _repo_root / "model-training"

_lock = threading.Lock()
_state: Dict[str, Any] = {}

# Calendar year for the predictions UI race list (when present in features).
PICKER_SEASON = 2025


def _features_path() -> str:
    return os.getenv(
        "F1_FEATURES_PARQUET",
        str(_model_training / "f1_features.parquet"),
    )


def _model_dir() -> Path:
    return Path(os.getenv("F1_MODEL_DIR", str(_model_training / "f1_models")))


def _ensure_training_on_path() -> None:
    s = str(_model_training)
    if s not in sys.path:
        sys.path.insert(0, s)


def _load_engine_unlocked() -> Dict[str, Any]:
    parquet = _features_path()
    if not Path(parquet).is_file():
        raise FileNotFoundError(f"Features parquet not found: {parquet}")

    model_dir = _model_dir()
    for name in ("position", "dnf", "ranking"):
        p = model_dir / f"{name}_model.pkl"
        if not p.is_file():
            raise FileNotFoundError(
                f"Missing trained model: {p}. Train with:\n"
                f"  python model-training/f1_model.py --features {parquet} "
                f"--mode train --model_dir {model_dir}"
            )

    _ensure_training_on_path()
    import f1_model  # noqa: PLC0415 — after sys.path

    df, _ = f1_model.load_features(parquet)
    feature_cols = f1_model.get_feature_cols(df)
    models: Dict[str, Any] = {}
    for name in ("position", "dnf", "ranking"):
        with open(model_dir / f"{name}_model.pkl", "rb") as f:
            models[name] = pickle.load(f)

    return {
        "f1_model": f1_model,
        "df": df,
        "feature_cols": feature_cols,
        "models": models,
    }


def get_prediction_engine() -> Dict[str, Any]:
    with _lock:
        if "df" in _state:
            return _state
        _state.clear()
        loaded = _load_engine_unlocked()
        _state.update(loaded)
        return _state


def get_default_race() -> Tuple[int, int, str]:
    st = get_prediction_engine()
    df: pd.DataFrame = st["df"]
    keys = (
        df.groupby(["Season", "RoundNumber"], sort=True)
        .size()
        .reset_index()[["Season", "RoundNumber"]]
    )
    if keys.empty:
        raise ValueError("No races in features dataset")
    last = keys.iloc[-1]
    season = int(last["Season"])
    rnd = int(last["RoundNumber"])
    sub = df[(df["Season"] == season) & (df["RoundNumber"] == rnd)]
    name = str(sub["OfficialEventName"].iloc[0]) if len(sub) else f"Season {season} R{rnd}"
    return season, rnd, name


def list_races(season: Optional[int] = None, limit: int = 40) -> List[Dict[str, Any]]:
    st = get_prediction_engine()
    df: pd.DataFrame = st["df"]
    work = df[df["Season"] == season] if season is not None else df
    if len(work) == 0:
        return []
    g = (
        work.groupby(["Season", "RoundNumber"], as_index=False)
        .agg(event=("OfficialEventName", "first"))
        .sort_values(["Season", "RoundNumber"])
    )
    if season is None:
        g = g.tail(limit)
    return [
        {
            "season": int(r["Season"]),
            "round": int(r["RoundNumber"]),
            "event": str(r["event"]),
        }
        for _, r in g.iterrows()
    ]


def get_default_race_for_season(season: int) -> Tuple[int, int, str]:
    races = list_races(season=season)
    if not races:
        raise ValueError(f"No races in features dataset for season {season}")
    last = races[-1]
    return last["season"], last["round"], last["event"]


def run_race_prediction(
    season: int,
    round_no: int,
    user_weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    st = get_prediction_engine()
    f1_model = st["f1_model"]
    df: pd.DataFrame = st["df"]
    feature_cols: List[str] = st["feature_cols"]
    models = st["models"]

    race_df = df[(df["Season"] == season) & (df["RoundNumber"] == round_no)].copy()
    if len(race_df) == 0:
        raise ValueError(f"No feature rows for season={season} round={round_no}")

    uw = None
    if user_weights:
        uw = {k: float(np.clip(v, 0.0, 10.0)) for k, v in user_weights.items()}
        if not any(v > 0 for v in uw.values()):
            uw = None

    preds = f1_model.predict_race(
        race_df,
        feature_cols,
        models["position"],
        models["dnf"],
        models["ranking"],
        user_weights=uw,
    )

    top = preds.head(10).reset_index(drop=True)

    rows: List[Dict[str, Any]] = []
    for _, r in top.iterrows():
        dnf = float(r["DNF_Prob"])
        conf = int(max(45, min(99, round((1.0 - dnf) * 100))))
        rows.append(
            {
                "position": int(r["PredPosition"]),
                "driver": str(r["Driver"]),
                "team": str(r["TeamName"]),
                "confidence": conf,
            }
        )

    winner = top.iloc[0]
    event_name = str(race_df["OfficialEventName"].iloc[0])
    blend = None
    if "User_Blend" in top.columns and uw:
        try:
            blend = float(top["User_Blend"].iloc[0])
        except (TypeError, ValueError):
            blend = None

    top_driver = str(winner["Driver"])
    top_team = str(winner["TeamName"])
    model_conf = int(max(50, min(95, round(float(np.mean([x["confidence"] for x in rows[:3]]))))))

    if uw and blend and blend > 0.01:
        analysis = (
            f"With your custom factor emphasis (about {int(round(blend * 100))}% blend toward your priorities), "
            f"the ensemble ranks {top_driver} ({top_team}) most likely to win {event_name}. "
            f"Outputs combine position regression, learning-to-rank, and DNF risk with circuit chaos blending."
        )
    else:
        analysis = (
            f"Using the trained ensemble’s default weighting, {top_driver} ({top_team}) is projected to finish "
            f"highest at {event_name}. Rankings merge finishing-position regression, pairwise rank scores, and "
            f"calibrated DNF probabilities, adjusted for grid penalties and historical circuit chaos."
        )

    return {
        "season": season,
        "round": round_no,
        "eventName": event_name,
        "userBlend": blend,
        "top10": rows,
        "topPickDriver": top_driver,
        "topPickTeam": top_team,
        "modelConfidence": model_conf,
        "analysis": analysis,
    }
