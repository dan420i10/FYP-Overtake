from flask import Blueprint, jsonify, request

from prediction_service import (
    PICKER_SEASON,
    get_default_race,
    get_default_race_for_season,
    get_prediction_engine,
    list_races,
    run_race_prediction,
)
from routes import token_required

predict_bp = Blueprint("predict", __name__)


def _parse_user_weights(body: dict) -> dict | None:
    raw = body.get("user_weights")
    if not raw or not isinstance(raw, dict):
        return None
    key_map = {
        "driver_skill": "driver_skill",
        "driver-skill": "driver_skill",
        "team_performance": "team_performance",
        "team-performance": "team_performance",
        "track_history": "track_history",
        "track-history": "track_history",
        "weather": "weather",
        "recent_form": "recent_form",
        "recent-form": "recent_form",
    }
    out: dict = {}
    for k, v in raw.items():
        nk = key_map.get(str(k).strip())
        if nk is None:
            continue
        try:
            out[nk] = float(v)
        except (TypeError, ValueError):
            continue
    return out or None


@predict_bp.route("/predict/meta", methods=["GET"])
@token_required
def predict_meta(_current_user):
    """Default race and full list for PICKER_SEASON (requires models and features to load)."""
    try:
        get_prediction_engine()
        races = list_races(season=PICKER_SEASON)
        if races:
            season, rnd, name = get_default_race_for_season(PICKER_SEASON)
        else:
            season, rnd, name = get_default_race()
        return jsonify(
            {
                "defaultSeason": season,
                "defaultRound": rnd,
                "defaultEventName": name,
                "races": races,
                "pickerSeason": PICKER_SEASON,
            }
        ), 200
    except FileNotFoundError as e:
        return jsonify({"message": str(e)}), 503
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@predict_bp.route("/predict", methods=["POST"])
@token_required
def predict(_current_user):
    """
    JSON body (all optional except auth):
      season, round — default to latest race in features file
      user_weights — { driver_skill, team_performance, track_history, weather, recent_form } in [0,10]
    """
    try:
        body = request.get_json(silent=True) or {}
        season = body.get("season")
        rnd = body.get("round")

        if season is None or rnd is None:
            season, rnd, _ = get_default_race()
        else:
            season, rnd = int(season), int(rnd)

        uw = _parse_user_weights(body)
        result = run_race_prediction(season, rnd, user_weights=uw)
        return jsonify(result), 200
    except FileNotFoundError as e:
        return jsonify({"message": str(e)}), 503
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": str(e)}), 500
