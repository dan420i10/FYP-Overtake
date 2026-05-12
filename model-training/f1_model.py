import argparse
import pickle
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error
from sklearn.preprocessing import LabelEncoder
from sklearn.calibration import CalibratedClassifierCV
from scipy.stats import spearmanr, kendalltau

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────
# Feature column registry
# ─────────────────────────────────────────────────────────────

PRE_RACE_FEATURES = [
    # Qualifying
    "QualiPosition", "QualiStage",
    "BestQualiTime_sec", "GapToPole_sec", "GapToPole_pct",
    "Q1_sec", "Q2_sec", "Q3_sec",

    "P1_BestLap_sec", "P2_BestLap_sec", "P3_BestLap_sec",
    "P1_GapToFastest_sec", "P2_GapToFastest_sec", "P3_GapToFastest_sec",
    "P2_LongRunMean_sec", "P2_LongRunMedian_sec",
    "P2_LongRunLaps", "P2_LongRunGap_sec",
    "P3_GapS1_sec", "P3_GapS2_sec", "P3_GapS3_sec",
    "P3_MaxSpeed", "P3_TrapSpeed",

    "P3_S1_frac", "P3_S2_frac", "P3_S3_frac",

    "Drv_AvgPos_L3", "Drv_AvgPos_L5", "Drv_AvgPos_L10", "Drv_AvgPos_EWM",
    "Drv_AvgPts_L5", "Drv_AvgPts_EWM",
    "Drv_DNFRate_L10", "Drv_StdPos_L5",
    "Drv_AvgGridDelta_L5",
    "Drv_SeasonPts_cumulative", "Drv_SeasonRaceCount",

    "Team_AvgPos_L5", "Team_AvgPos_EWM",
    "Team_AvgPts_L5", "Team_DNFRate_L10",
    "Team_SeasonPts_cumulative",

    "Drv_CircuitAvgPos", "Drv_CircuitAvgPts",
    "Drv_CircuitDNFRate", "Drv_CircuitRaceCount",
    "Drv_CircuitGridDelta",

    "Elo_before", "Elo_rank",

    "IsSprintWeekend", "IsStreetCircuit", "SeasonProgress",

    "Circuit_AvgSC_hist", "Circuit_AvgFlags_hist",
    "Circuit_HistChaos", "Circuit_HistUpsetRate",

    "Form_Pts_L3", "Form_PodiumRate_L5",
    "Form_InPointsRate_L5", "Form_ConsecDNF",

    "SeasonCumPts", "PtsGapToLeader", "ChampionshipRank",

    "Tm_BeatRate_L5", "Tm_QualiGap_EWM", "Tm_PosGap_EWM",

    "Wx_AvgAirTemp", "Wx_AvgTrackTemp", "Wx_AvgHumidity",
    "Wx_AvgWindSpeed", "Wx_RainfallFrac", "Wx_AnyRain",
    "Wx_TrackTempSpread",
]

DNF_FEATURES = [
    "Drv_DNFRate_L10",
    "Team_DNFRate_L10",
    "Drv_CircuitDNFRate",
    "Form_ConsecDNF",
    "IsStreetCircuit",      
    "SeasonProgress",       
    "Elo_before",           
    "Circuit_AvgSC_hist",  
    "Wx_AnyRain",          
    "Wx_RainfallFrac",
    "IsSprintWeekend",     
    "Drv_SeasonRaceCount", 
]

TARGET_COL    = "LogPosition"
DNF_TARGET    = "DNF"
POSITION_COL  = "FinalPosition"

GROUP_COLS    = ["Season", "RoundNumber"]
ID_COLS       = ["Season", "RoundNumber", "Driver", "TeamName", "OfficialEventName", "GridPosition"]

# ─────────────────────────────────────────────────────────────
# User-weight category helpers
# ─────────────────────────────────────────────────────────────

def _norm_asc(s: pd.Series) -> pd.Series:
    """Normalise to [0, 1] where 0 = best (lower raw values finish better)."""
    s = s.fillna(s.median())
    rng = s.max() - s.min()
    return (s - s.min()) / (rng + 1e-9)


def _norm_desc(s: pd.Series) -> pd.Series:
    """Normalise to [0, 1] where 0 = best (higher raw values finish better)."""
    return 1.0 - _norm_asc(s)


def compute_category_scores(race_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute five normalised per-driver scores (0 = predicted best, 1 = worst)
    for each user-adjustable insight category.

    Categories
    ----------
    driver_skill     : Elo rating + career points momentum
    team_performance : Recent team avg position + recent team points
    track_history    : Driver's historical record at this specific circuit
    weather          : DNF risk / quali pace blended by rain intensity
    recent_form      : Pts in last 3 races + podium & points-finish rates
    """
    idx = race_df.index

    def col(name: str, default: float) -> pd.Series:
        return race_df[name] if name in race_df.columns else pd.Series(default, index=idx)

    # ── 1. Driver Skill ──────────────────────────────────────────────────────
    skill = (
        0.55 * _norm_desc(col("Elo_before",       1500))
        + 0.30 * _norm_desc(col("Drv_AvgPts_EWM",   0))
        + 0.15 * _norm_asc( col("ChampionshipRank", 10))
    )

    # ── 2. Team Performance ──────────────────────────────────────────────────
    team = (
        0.50 * _norm_asc( col("Team_AvgPos_L5", 10))
        + 0.50 * _norm_desc(col("Team_AvgPts_L5",  0))
    )

    # ── 3. Track History ─────────────────────────────────────────────────────
    track = (
        0.60 * _norm_asc( col("Drv_CircuitAvgPos", 10))
        + 0.40 * _norm_desc(col("Drv_CircuitAvgPts",  0))
    )

    # ── 4. Weather ───────────────────────────────────────────────────────────
    # Wet races: low DNF rate + small quali gap = handles conditions well.
    # Dry races: qualifying pace gap is the dominant differentiator.
    wet = float(col("Wx_AnyRain", 0).mean()) + float(col("Wx_RainfallFrac", 0).mean())
    wet_intensity = min(wet, 1.0)

    wet_score = (
        0.50 * _norm_asc(col("Drv_DNFRate_L10", 0.10))
        + 0.50 * _norm_asc(col("GapToPole_pct",   1.50))
    )
    dry_score = _norm_asc(col("GapToPole_pct", 1.50))
    weather = wet_intensity * wet_score + (1.0 - wet_intensity) * dry_score

    # ── 5. Recent Form ───────────────────────────────────────────────────────
    form = (
        0.40 * _norm_desc(col("Form_Pts_L3",           0))
        + 0.35 * _norm_desc(col("Form_PodiumRate_L5",    0))
        + 0.25 * _norm_desc(col("Form_InPointsRate_L5",  0))
    )

    return pd.DataFrame({
        "driver_skill":     skill,
        "team_performance": team,
        "track_history":    track,
        "weather":          weather,
        "recent_form":      form,
    }, index=idx)


def apply_user_weights(
    result: pd.DataFrame,
    race_df: pd.DataFrame,
    user_weights: dict,
) -> pd.DataFrame:
    """
    Blend user insight weights into the final ranking.

    Parameters
    ----------
    result       : output of predict_race() before this call
    race_df      : the same race slice passed to predict_race()
    user_weights : dict with keys driver_skill, team_performance, track_history,
                   weather, recent_form — values in [0, 10].

    Behaviour
    ---------
    The blend strength is driven entirely by the *spread* (std dev) of the
    weights, not their absolute level.  Equal weights — including all-zeros
    or all-tens — produce zero blend and the pure model output is returned
    unchanged.  Only *unequal* weights have any effect: the more spread out
    they are, the more the model bends toward the higher-weighted categories.

      all equal (e.g. 5,5,5,5,5 or 0,0,0,0,0) → blend = 0 % (pure model)
      slight preference (e.g. 7,5,5,5,5)       → blend ≈  9 %
      clear preference (e.g. 9,5,5,5,1)        → blend ≈ 29 %
      extreme (e.g. 10,0,0,0,0)                → blend ≈ 46 %
    """
    user_weights = {k: float(np.clip(v, 0, 10)) for k, v in user_weights.items()}
    values = np.array(list(user_weights.values()), dtype=float)

    # No influence when all weights are equal (std == 0)
    std = float(np.std(values))
    if std < 1e-6:
        return result

    total = float(values.sum())
    if total == 0:
        return result

    cat_scores = compute_category_scores(race_df)

    # Weighted average of category scores — categories with higher weights
    # pull the user signal toward their signal (lower score = predicted better)
    user_score = pd.Series(0.0, index=result.index)
    for cat, w in user_weights.items():
        if cat in cat_scores.columns and w > 0:
            user_score = user_score + (w / total) * cat_scores[cat].values

    # Blend alpha scales with spread, not magnitude.
    # Theoretical max std for 5 values in [0, 10] ≈ 4.9  (e.g. [10,10,0,0,0])
    _MAX_STD = 4.9
    blend_alpha = min(std / _MAX_STD, 1.0) * 0.50   # hard cap at 50 %

    # Normalise model Combined_Score to [0, 1] before blending
    cs = result["Combined_Score"]
    cs_norm = (cs - cs.min()) / (cs.max() - cs.min() + 1e-9)

    result = result.copy()
    result["Combined_Score"] = (1.0 - blend_alpha) * cs_norm + blend_alpha * user_score
    result["PredPosition"]   = result["Combined_Score"].rank(method="first").astype(int)
    result["User_Blend"]     = round(blend_alpha, 3)
    result = result.sort_values("PredPosition")
    return result


def spearman_per_race(df: pd.DataFrame,
                      pred_col: str = "PredPosition",
                      true_col: str = POSITION_COL) -> float:
    scores = []
    for _, race in df.groupby(["Season", "RoundNumber"]):
        if len(race) < 3:
            continue
        r, _ = spearmanr(race[true_col], race[pred_col])
        if not np.isnan(r):
            scores.append(r)
    return float(np.mean(scores))


def top1_accuracy(df: pd.DataFrame,
                  pred_col: str = "PredPosition",
                  true_col: str = POSITION_COL) -> float:
    df = df.dropna(subset=[pred_col, true_col])
    correct = (abs(df[pred_col] - df[true_col]) <= 1).mean()
    return float(correct)


def kendall_per_race(df: pd.DataFrame,
                     pred_col: str = "PredPosition",
                     true_col: str = POSITION_COL) -> float:
    scores = []
    for _, race in df.groupby(["Season", "RoundNumber"]):
        if len(race) < 3:
            continue
        tau, _ = kendalltau(race[true_col], race[pred_col])
        if not np.isnan(tau):
            scores.append(tau)
    return float(np.mean(scores))


def top_n_accuracy(df: pd.DataFrame,
                   pred_col: str = "PredPosition",
                   true_col: str = POSITION_COL,
                   n: int = 3) -> float:
    scores = []
    for _, race in df.groupby(["Season", "RoundNumber"]):
        pred_top = set(race.nsmallest(n, pred_col)["Driver"])
        true_top = set(race.nsmallest(n, true_col)["Driver"])
        overlap = len(pred_top & true_top) / n
        scores.append(overlap)
    return float(np.mean(scores))


def points_finish_accuracy(df: pd.DataFrame,
                           pred_col: str = "PredPosition",
                           true_col: str = POSITION_COL) -> float:
    df = df.copy()
    df["pred_in_pts"] = df[pred_col] <= 10
    df["true_in_pts"] = df[true_col] <= 10
    return float((df["pred_in_pts"] == df["true_in_pts"]).mean())


def evaluate_all(df: pd.DataFrame, pred_col: str = "PredPosition") -> dict:
    df = df.dropna(subset=[POSITION_COL, pred_col])
    spearman_scores = []
    for _, race in df.groupby(["Season", "RoundNumber"]):
        if len(race) >= 3:
            r, _ = spearmanr(race[POSITION_COL], race[pred_col])
            if not np.isnan(r):
                spearman_scores.append(r)
    return {
        "MAE":               mean_absolute_error(df[POSITION_COL], df[pred_col]),
        "Spearman_mean":     float(np.mean(spearman_scores)),
        "Spearman_median":   float(np.median(spearman_scores)), 
        "Kendall_Tau":       kendall_per_race(df, pred_col),
        "Within1_Acc":       top1_accuracy(df, pred_col),
        "Podium_Acc":        top_n_accuracy(df, pred_col, n=3),
        "Top5_Acc":          top_n_accuracy(df, pred_col, n=5),
        "Top10_Acc":          top_n_accuracy(df, pred_col, n=10),
        "Points_Finish_Acc": points_finish_accuracy(df, pred_col),
    }


def load_features(path: str) -> pd.DataFrame:
    df = pd.read_parquet(path)
    
    if "LogPosition" not in df.columns:
        df["LogPosition"] = np.log1p(df["FinalPosition"].fillna(20))

    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    encoders = {}
    for col in cat_cols:
        if col in ID_COLS:
            continue
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        encoders[col] = le

    return df, encoders


def get_feature_cols(df: pd.DataFrame) -> list:
    available = set(df.columns)
    cols = [c for c in PRE_RACE_FEATURES if c in available]
    missing = [c for c in PRE_RACE_FEATURES if c not in available]
    if missing:
        print(f"[WARNING] {len(missing)} features not found in dataframe: {missing[:5]}...")
    return cols


def get_dnf_feature_cols(df: pd.DataFrame) -> list:
    available = set(df.columns)
    cols = [c for c in DNF_FEATURES if c in available]
    return cols

def train_dnf_model(train_df: pd.DataFrame,
                    feature_cols: list,
                    val_df: pd.DataFrame = None):
    import lightgbm as lgb

    dnf_cols = [c for c in DNF_FEATURES if c in train_df.columns]
    if not dnf_cols:
        dnf_cols = feature_cols

    X_train = train_df[dnf_cols].fillna(-999)
    y_train = train_df[DNF_TARGET].astype(int)

    base_model = lgb.LGBMClassifier(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=5,
        num_leaves=31,
        min_child_samples=10,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=(y_train == 0).sum() / max((y_train == 1).sum(), 1),
        random_state=42,
        verbose=-1,
    )
    base_model.fit(X_train, y_train)

    if val_df is not None and len(val_df) > 0:
        X_val = val_df[dnf_cols].fillna(-999)
        y_val = val_df[DNF_TARGET].astype(int)
        calibrated = CalibratedClassifierCV(base_model, method="sigmoid", cv="prefit")
        calibrated.fit(X_val, y_val)
        return calibrated
    else:
        calibrated = CalibratedClassifierCV(base_model, method="sigmoid", cv=3)
        calibrated.fit(X_train, y_train)
        return calibrated


def train_position_model(train_df: pd.DataFrame, feature_cols: list,
                         val_df: pd.DataFrame = None):
    import lightgbm as lgb

    X_train = train_df[feature_cols].fillna(-999)
    # FIX: use LogPosition; DNFs get log1p(20) as worst case
    y_train = train_df[TARGET_COL].fillna(np.log1p(20))

    callbacks = []
    eval_set = None

    if val_df is not None and len(val_df) > 0:
        X_val = val_df[feature_cols].fillna(-999)
        y_val = val_df[TARGET_COL].fillna(np.log1p(20))
        eval_set = [(X_val, y_val)]
        callbacks = [lgb.early_stopping(50, verbose=False),
                     lgb.log_evaluation(-1)]

    model = lgb.LGBMRegressor(
        n_estimators=600,     
        learning_rate=0.02,
        max_depth=6,
        num_leaves=63,
        min_child_samples=10,
        subsample=0.8,
        colsample_bytree=0.7,
        reg_alpha=0.1,
        reg_lambda=0.1,
        random_state=42,
        verbose=-1,
    )

    if eval_set:
        model.fit(X_train, y_train,
                  eval_set=eval_set,
                  callbacks=callbacks)
    else:
        model.fit(X_train, y_train)

    return model

def train_ranking_model(train_df: pd.DataFrame, feature_cols: list):
    import xgboost as xgb

    train_sorted = train_df.sort_values(["Season", "RoundNumber"])
    X = train_sorted[feature_cols].fillna(-999)
    y = train_sorted[POSITION_COL].fillna(20).astype(int)

    max_pos = y.max()
    y_rank  = max_pos + 1 - y

    groups = train_sorted.groupby(["Season", "RoundNumber"]).size().values

    # FIX: assertion to catch group/data alignment issues under rolling validation
    assert groups.sum() == len(train_sorted), (
        f"Ranker group size mismatch: groups sum to {groups.sum()} but data has {len(train_sorted)} rows"
    )

    model = xgb.XGBRanker(
        objective="rank:pairwise",
        learning_rate=0.05,
        n_estimators=400,
        max_depth=5,
        subsample=0.8,
        colsample_bytree=0.7,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=42,
        eval_metric="ndcg@10",
        verbosity=0,
    )
    model.fit(X, y_rank, group=groups)
    return model

def compute_ensemble_weights(season_progress: float,
                              is_street: bool = False) -> dict:
    """
    season_progress: float in [0, 1] where 0 = first race, 1 = last race.
    is_street: True for Monaco, Singapore, Baku, etc.

    Early season: ranking model gets more weight (historical data sparse,
    qualifying order is the strongest signal).
    Late season: position regression gets more weight (rolling history is rich).
    DNF weight is elevated on street circuits where safety car and retirement
    rates are historically higher.
    """
    w_rank = 0.40 + 0.15 * (1.0 - season_progress)
    w_pos  = 0.40 - 0.10 * (1.0 - season_progress)
    w_dnf  = 0.30 if is_street else 0.22   # raised from 0.20; street bump from data

    total  = w_rank + w_pos + w_dnf
    return {
        "position": w_pos  / total,
        "ranking":  w_rank / total,
        "dnf":      w_dnf  / total,
    }

def predict_race(
    race_df: pd.DataFrame,
    feature_cols: list,
    pos_model,
    dnf_model,
    rank_model,
    weights: dict = None,
    user_weights: dict = None,
) -> pd.DataFrame:
    if weights is None:
        season_progress = float(race_df["SeasonProgress"].fillna(0.5).iloc[0])
        is_street = bool(race_df["IsStreetCircuit"].fillna(0).iloc[0])
        weights = compute_ensemble_weights(season_progress, is_street=is_street)

    dnf_cols = [c for c in DNF_FEATURES if c in race_df.columns]
    if not dnf_cols:
        dnf_cols = feature_cols

    X      = race_df[feature_cols].fillna(-999)
    X_dnf  = race_df[dnf_cols].fillna(-999)

    result = race_df[["Driver", "TeamName", "GridPosition"]].copy()

    log_pred = pos_model.predict(X)
    lmin, lmax = log_pred.min(), log_pred.max()
    result["Score_Pos"] = (log_pred - lmin) / (lmax - lmin + 1e-9)

    result["DNF_Prob"] = dnf_model.predict_proba(X_dnf)[:, 1]

    raw_rank_score = rank_model.predict(X)
    rmin, rmax = raw_rank_score.min(), raw_rank_score.max()
    if rmax > rmin:
        result["Score_Rank"] = 1 - (raw_rank_score - rmin) / (rmax - rmin)
    else:
        result["Score_Rank"] = 0.5

    result["Combined_Score"] = (
        weights["position"] * result["Score_Pos"]
        + weights["ranking"] * result["Score_Rank"]
        + weights["dnf"]    * result["DNF_Prob"]
    )

    # Grid penalty: drivers who start further back than they qualified
    # (engine penalties, pit-lane starts) should be pushed down the order.
    # GridPenalty = GridPosition - QualiPosition > 0 means a back-of-grid penalty.
    result["GridPenalty"] = 0.0
    if "QualiPosition" in race_df.columns:
        quali_pos = race_df["QualiPosition"].fillna(
            race_df["QualiPosition"].median()
        ).values
        grid_penalty = pd.Series(
            (result["GridPosition"].fillna(20).values - quali_pos).clip(min=0),
            index=result.index,
        )
        if grid_penalty.max() > 2:
            result["GridPenalty"] = grid_penalty
            result["Combined_Score"] += 0.12 * (grid_penalty / grid_penalty.max())

    chaos = float(race_df["Circuit_HistChaos"].fillna(0).mean())

    chaos_blend = min(chaos / 8.0, 1.0) * 0.35

    if chaos_blend > 0.05 and "GridPosition" in result.columns:
        grid_pos = result["GridPosition"].fillna(result["GridPosition"].median())
        gmin, gmax = grid_pos.min(), grid_pos.max()
        grid_norm = (grid_pos - gmin) / (gmax - gmin + 1e-9)
        result["Combined_Score"] = (
            (1 - chaos_blend) * result["Combined_Score"]
            + chaos_blend     * grid_norm
        )

    # Final ranking from combined score
    result["PredPosition"] = result["Combined_Score"].rank(method="first").astype(int)

    result["Weights_Used"] = str({k: round(v, 3) for k, v in weights.items()})
    result["Chaos_Blend"]  = round(chaos_blend, 3)
    result = result.sort_values("PredPosition")

    # Apply user insight weights if provided (no-op when None or all-zero)
    if user_weights and any(v > 0 for v in user_weights.values()):
        result = apply_user_weights(result, race_df, user_weights)

    return result


def train_all_models(df: pd.DataFrame, feature_cols: list,
                     train_seasons=(2022, 2023, 2024)) -> dict:
    train = df[df["Season"].isin(train_seasons)].copy()

    most_recent = max(train_seasons)
    internal_val = train[train["Season"] == most_recent].copy()
    internal_train = train[train["Season"] != most_recent].copy()

    use_internal_val = len(train_seasons) >= 3

    print(f"Training on {len(train)} rows ({len(train['Season'].unique())} seasons)")
    if use_internal_val:
        print(f"  Internal holdout: season {most_recent} ({len(internal_val)} rows) for early stopping")

    print("  Training DNF model...")
    dnf_model = train_dnf_model(
        internal_train if use_internal_val else train,
        feature_cols,
        val_df=internal_val if use_internal_val else None
    )

    print("  Training position regression model...")
    pos_model = train_position_model(
        internal_train if use_internal_val else train,
        feature_cols,
        val_df=internal_val if use_internal_val else None
    )

    print("  Training ranking model...")
    rank_model = train_ranking_model(train, feature_cols)

    return {
        "position": pos_model,
        "dnf":      dnf_model,
        "ranking":  rank_model,
    }

def rolling_validation(df: pd.DataFrame, feature_cols: list,
                       val_season: int = 2025,
                       user_weights: dict = None) -> pd.DataFrame:
    val_races = sorted(df[df["Season"] == val_season]["RoundNumber"].unique())
    all_preds = []

    has_uw = user_weights and any(v > 0 for v in user_weights.values())
    print(f"\nRolling-forward validation on {len(val_races)} races in {val_season}"
          + (" [user weights active]" if has_uw else "") + "...")

    for rnd in val_races:
        train_mask = (df["Season"] < val_season) | (
            (df["Season"] == val_season) & (df["RoundNumber"] < rnd)
        )
        train = df[train_mask].copy()
        val   = df[(df["Season"] == val_season) & (df["RoundNumber"] == rnd)].copy()

        if len(val) == 0:
            continue
        if len(train) < 40:
            print(f"  Round {rnd:2d} | Skipping — not enough training data ({len(train)} rows)")
            continue

        models = train_all_models(train, feature_cols,
                                  train_seasons=list(df["Season"].unique()))

        preds = predict_race(
            val, feature_cols,
            models["position"], models["dnf"], models["ranking"],
            user_weights=user_weights,
        )

        preds = preds.merge(
            val[["Driver", POSITION_COL, "OfficialEventName"]],
            on="Driver", how="left"
        )
        preds["Season"]      = val_season
        preds["RoundNumber"] = rnd

        all_preds.append(preds)

        metrics = evaluate_all(preds)
        race_name = val["OfficialEventName"].iloc[0]
        chaos_val = float(val["Circuit_HistChaos"].fillna(0).mean())
        print(f"  Round {rnd:2d} | {race_name[:28]:28s} | "
              f"Spearman={metrics['Spearman_mean']:.3f} | "
              f"Within1={metrics['Within1_Acc']:.2f} | "
              f"Podium={metrics['Podium_Acc']:.2f} | "
              f"Top5_Acc={metrics['Top5_Acc']:.2f} | "
              f"Top10_Acc={metrics['Top10_Acc']:.2f} | "
              f"MAE={metrics['MAE']:.2f} | "
              f"Chaos={chaos_val:.1f}")

        comparison = preds[["PredPosition", "Driver", "FinalPosition", "GridPosition"]].dropna()
        comparison = comparison.sort_values("PredPosition").head(10)

        comparison["FinalPosition"] = comparison["FinalPosition"].astype(int)
        comparison["GridPosition"]  = comparison["GridPosition"].astype(int)

        print(f"  {'Pred':>4} {'Driver':>6} {'Quali':>5} {'Actual':>6} {'Res':>5} {'QΔ':>5} {'AΔ':>6}")
        print(f"  {'----':>4} {'------':>6} {'-----':>5} {'------':>6} {'-----':>6} {'------':>6} {'------':>6}")

        for _, row in comparison.iterrows():
            marker = "✓" if row["PredPosition"] == row["FinalPosition"] else "x"
            
            Quali_delta = int(row["PredPosition"]) - int(row["GridPosition"])
            Actual_delta = int(row["PredPosition"]) - int(row["FinalPosition"])
            
            print(f"  {int(row['PredPosition']):>4} {row['Driver']:>6} "
                f"{int(row['GridPosition']):>5} {int(row['FinalPosition']):>6} "
                f"   {marker}     {Quali_delta:+}     {Actual_delta:+}")

        print()

    combined = pd.concat(all_preds, ignore_index=True)

    print("\n── Overall Validation Metrics ──────────────────────")
    overall = evaluate_all(combined)
    for k, v in overall.items():
        print(f"  {k:<24s}: {v:.4f}")

    spearman_per = []
    for _, race in combined.groupby(["Season", "RoundNumber"]):
        if len(race) >= 3:
            r, _ = spearmanr(race[POSITION_COL].dropna(), race["PredPosition"].dropna())
            if not np.isnan(r):
                spearman_per.append(r)
    print(f"\n  Spearman distribution:")
    print(f"    p25={np.percentile(spearman_per,25):.3f}  "
          f"p50={np.percentile(spearman_per,50):.3f}  "
          f"p75={np.percentile(spearman_per,75):.3f}  "
          f"min={min(spearman_per):.3f}  max={max(spearman_per):.3f}")

    return combined


def explain_model(model, X: pd.DataFrame, n_top: int = 20):
    try:
        import shap

        base = model
        if hasattr(model, "calibrated_classifiers_"):
            base = model.calibrated_classifiers_[0].estimator

        explainer = shap.TreeExplainer(base)
        shap_values = explainer.shap_values(X)

        if isinstance(shap_values, list):
            shap_values = shap_values[1]

        importance = pd.DataFrame({
            "feature": X.columns,
            "mean_abs_shap": np.abs(shap_values).mean(axis=0)
        }).sort_values("mean_abs_shap", ascending=False)

        print(f"\n── Top {n_top} Features (SHAP) ──────────────────────")
        print(importance.head(n_top).to_string(index=False))
        return importance
    except ImportError:
        print("Install shap for feature importance: pip install shap")
        return None

def parse_args():
    p = argparse.ArgumentParser(
        description="F1 Position Prediction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
User insight weights (predict mode only)
----------------------------------------
Each flag takes a value from 0 to 10.  Only the *differences* between
the weights matter — equal weights (including all-zeros or all-tens)
leave the model output completely unchanged.  The more unequal the
weights, the more the model bends toward the higher-weighted categories.

Examples
  Pure model — no user input (default):
    --mode predict --round 5

  Same as pure model — all equal, so no effect:
    --mode predict --round 5 --w_driver_skill 7 --w_team_performance 7 \\
      --w_track_history 7 --w_weather 7 --w_recent_form 7

  Track specialists and current form matter more this weekend:
    --mode predict --round 5 --w_track_history 9 --w_recent_form 8 \\
      --w_driver_skill 5 --w_team_performance 4 --w_weather 2

  Wet race — heavily weight weather sensitivity and driver skill:
    --mode predict --round 5 --w_weather 10 --w_driver_skill 8 \\
      --w_team_performance 4 --w_track_history 3 --w_recent_form 3
""",
    )
    p.add_argument("--features",  required=True, help="Path to features parquet")
    p.add_argument("--mode",      required=True,
                   choices=["train", "prediction", "predict", "explain"])
    p.add_argument("--season",    type=int, default=2025)
    p.add_argument("--round",     type=int, default=None)
    p.add_argument("--model_dir", default="./f1_models")

    g = p.add_argument_group("user insight weights  [0–10, predict mode only]")
    g.add_argument("--w_driver_skill",     type=float, default=0, metavar="0-10",
                   help="Elo rating + career points momentum")
    g.add_argument("--w_team_performance", type=float, default=0, metavar="0-10",
                   help="Recent team avg position and points")
    g.add_argument("--w_track_history",    type=float, default=0, metavar="0-10",
                   help="Driver's historical record at this circuit")
    g.add_argument("--w_weather",          type=float, default=0, metavar="0-10",
                   help="Weather sensitivity (DNF risk / quali pace in wet/dry)")
    g.add_argument("--w_recent_form",      type=float, default=0, metavar="0-10",
                   help="Points + podium rate over the last 3–5 races")

    return p.parse_args()


def main():
    args = parse_args()
    model_dir = Path(args.model_dir)
    model_dir.mkdir(exist_ok=True)

    print(f"Loading features from {args.features}...")
    df, encoders = load_features(args.features)
    feature_cols = get_feature_cols(df)
    print(f"Features available: {len(feature_cols)}")

    if args.mode == "train":
        train_seasons = [s for s in df["Season"].unique() if s != args.season]
        models = train_all_models(df, feature_cols, train_seasons)
        for name, model in models.items():
            out = model_dir / f"{name}_model.pkl"
            with open(out, "wb") as f:
                pickle.dump(model, f)
            print(f"Saved {name} model → {out}")

    elif args.mode == "prediction":
        user_weights = {
            "driver_skill":     args.w_driver_skill,
            "team_performance": args.w_team_performance,
            "track_history":    args.w_track_history,
            "weather":          args.w_weather,
            "recent_form":      args.w_recent_form,
        }
        rolling_validation(df, feature_cols, val_season=args.season,
                           user_weights=user_weights)

    elif args.mode == "predict":
        if args.round is None:
            raise ValueError("--round required for predict mode")

        models = {}
        for name in ["position", "dnf", "ranking"]:
            with open(model_dir / f"{name}_model.pkl", "rb") as f:
                models[name] = pickle.load(f)

        race_df = df[
            (df["Season"] == args.season) &
            (df["RoundNumber"] == args.round)
        ].copy()

        if len(race_df) == 0:
            print(f"No data found for Season={args.season} Round={args.round}")
            return

        user_weights = {
            "driver_skill":     args.w_driver_skill,
            "team_performance": args.w_team_performance,
            "track_history":    args.w_track_history,
            "weather":          args.w_weather,
            "recent_form":      args.w_recent_form,
        }

        preds = predict_race(
            race_df, feature_cols,
            models["position"], models["dnf"], models["ranking"],
            user_weights=user_weights,
        )

        event_name = race_df["OfficialEventName"].iloc[0]
        season_prog = float(race_df["SeasonProgress"].fillna(0.5).iloc[0])
        is_street   = bool(race_df["IsStreetCircuit"].fillna(0).iloc[0])
        used_weights = compute_ensemble_weights(season_prog, is_street=is_street)
        chaos_val = float(race_df["Circuit_HistChaos"].fillna(0).mean())

        print(f"\n── Predicted Finishing Order: {event_name} ──")
        print(f"   Ensemble weights : pos={used_weights['position']:.2f}  "
              f"rank={used_weights['ranking']:.2f}  dnf={used_weights['dnf']:.2f}  "
              f"chaos_blend={preds['Chaos_Blend'].iloc[0]:.2f}  "
              f"circuit_chaos={chaos_val:.1f}")

        active_uw = {k: v for k, v in user_weights.items() if v > 0}
        labels = {
            "driver_skill": "Skill", "team_performance": "Team",
            "track_history": "Track", "weather": "Weather",
            "recent_form": "Form",
        }
        if "User_Blend" in preds.columns:
            blend_pct = preds["User_Blend"].iloc[0] * 100
            uw_str = "  ".join(f"{labels[k]}={v:.0f}" for k, v in active_uw.items())
            print(f"   User weights     : {uw_str}  (blend={blend_pct:.0f}% user signal)")
        elif active_uw:
            uw_str = "  ".join(f"{labels[k]}={v:.0f}" for k, v in active_uw.items())
            print(f"   User weights     : {uw_str}  (all equal — no blend, pure model)")
        else:
            print(f"   User weights     : none (pure model)")

        print()
        out_cols = ["PredPosition", "Driver", "TeamName", "GridPosition",
                    "DNF_Prob", "Score_Pos", "Score_Rank"]
        if "User_Blend" in preds.columns and active_uw:
            out_cols.append("User_Blend")
        print(preds[out_cols].to_string(index=False))

    elif args.mode == "explain":
        train = df[df["Season"] != args.season].copy()
        model = train_position_model(train, feature_cols)
        X = train[feature_cols].fillna(-999)
        explain_model(model, X, n_top = 200)


if __name__ == "__main__":
    main()