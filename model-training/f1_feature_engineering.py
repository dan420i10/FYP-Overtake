import duckdb
import pandas as pd
import numpy as np
from typing import Optional
import warnings
warnings.filterwarnings("ignore")

def interval_to_seconds(series: pd.Series) -> pd.Series:
    """Convert pandas Timedelta / string interval column to float seconds."""
    if pd.api.types.is_timedelta64_dtype(series):
        return series.dt.total_seconds()
    return pd.to_timedelta(series, errors="coerce").dt.total_seconds()


def ewm_expanding(series: pd.Series, halflife: int = 3) -> pd.Series:
    """Exponentially weighted mean — shifts by 1 to avoid leakage."""
    return series.shift(1).ewm(halflife=halflife, min_periods=1).mean()


def rolling_mean_no_leak(series: pd.Series, window: int) -> pd.Series:
    """Rolling mean shifted by 1 race to prevent data leakage."""
    return series.shift(1).rolling(window, min_periods=1).mean()


def rolling_std_no_leak(series: pd.Series, window: int) -> pd.Series:
    return series.shift(1).rolling(window, min_periods=1).std()


class F1FeatureBuilder:

    def __init__(self, con: duckdb.DuckDBPyConnection):
        self.con = con

    def _q(self, sql: str) -> pd.DataFrame:
        return self.con.execute(sql).df()

    def build_skeleton(self) -> pd.DataFrame:
        df = self._q("""
            SELECT
                Season,
                RoundNumber,
                OfficialEventName,
                Abbreviation as Driver,
                DriverNumber,
                TeamName,
                GridPosition,
                Position         AS FinalPosition,
                ClassifiedPosition,
                Points,
                Status,
                Laps             AS LapsCompleted
            FROM results
            WHERE SessionName = 'Race'
            ORDER BY Season, RoundNumber, Position
        """)

        df["Finished"] = df["Status"].str.lower().isin(["finished", "+1 lap", "+2 laps",
                                                          "+3 laps", "+4 laps", "+5 laps"])
        df["DNF"] = (~df["Finished"]).astype(int)

        denom = df.groupby(["Season", "RoundNumber"])["FinalPosition"].transform("max") - 1
        df["NormPosition"] = (df["FinalPosition"] - 1) / denom.replace(0, np.nan)

        df["LogPosition"] = np.log1p(df["FinalPosition"])

        df["GridToFinish_delta"] = df["GridPosition"] - df["FinalPosition"]

        return df

    def build_quali_features(self) -> pd.DataFrame:
        df = self._q("""
            SELECT
                Season,
                RoundNumber,
                Abbreviation as Driver,
                GridPosition,
                Q1, Q2, Q3,
                Position AS QualiPosition
            FROM results
            WHERE SessionName = 'Qualifying'
        """)

        for col in ["Q1", "Q2", "Q3"]:
            df[col + "_sec"] = interval_to_seconds(df[col])

        df["QualiStage"] = (
            (~df["Q1_sec"].isna()).astype(int) +
            (~df["Q2_sec"].isna()).astype(int) +
            (~df["Q3_sec"].isna()).astype(int)
        )

        df["BestQualiTime_sec"] = np.where(
            df["Q3_sec"].notna(), df["Q3_sec"],
            np.where(df["Q2_sec"].notna(), df["Q2_sec"], df["Q1_sec"])
        )

        df["GapToPole_sec"] = df.groupby(["Season", "RoundNumber"])["BestQualiTime_sec"].transform(
            lambda x: x - x.min()
        )

        df["GapToPole_pct"] = df.groupby(["Season", "RoundNumber"])["BestQualiTime_sec"].transform(
            lambda x: (x - x.min()) / x.min() * 100
        )

        df["GapToPole_sec"] = df.groupby(["Season", "RoundNumber"])["GapToPole_sec"].transform(
            lambda x: x.fillna(x.max())
        )
        df["GapToPole_pct"] = df.groupby(["Season", "RoundNumber"])["GapToPole_pct"].transform(
            lambda x: x.fillna(x.max())
        )

        for col in ["Q1", "Q2", "Q3"]:
            for s in ["Sector1Time", "Sector2Time", "Sector3Time"]:
                pass

        keep = ["Season", "RoundNumber", "Driver",
                "QualiPosition", "GridPosition", "QualiStage",
                "BestQualiTime_sec", "GapToPole_sec", "GapToPole_pct",
                "Q1_sec", "Q2_sec", "Q3_sec"]
        return df[keep]

    def build_practice_features(self) -> pd.DataFrame:
        laps = self._q("""
            SELECT
                Season,
                RoundNumber,
                OfficialEventName,
                SessionName,
                Driver,
                LapTime,
                LapNumber,
                Compound,
                TyreLife,
                FreshTyre,
                IsAccurate,
                Sector1Time,
                Sector2Time,
                Sector3Time,
                SpeedST,
                SpeedFL
            FROM laps
            WHERE SessionName IN ('Practice 1', 'Practice 2', 'Practice 3')
              AND IsAccurate = TRUE
        """)

        laps["LapTime_sec"] = interval_to_seconds(laps["LapTime"])
        for s in ["Sector1Time", "Sector2Time", "Sector3Time"]:
            laps[s + "_sec"] = interval_to_seconds(laps[s])

        laps = laps[laps["LapTime_sec"].between(60, 200)]

        short_run = (
            laps.groupby(["Season", "RoundNumber", "SessionName", "Driver"])
            ["LapTime_sec"]
            .min()
            .reset_index()
            .rename(columns={"LapTime_sec": "BestLap_sec"})
        )

        short_run_wide = short_run.pivot_table(
            index=["Season", "RoundNumber", "Driver"],
            columns="SessionName",
            values="BestLap_sec"
        ).reset_index()
        short_run_wide.columns.name = None

        short_run_wide = short_run_wide.rename(columns={
            "Practice 1": "P1_BestLap_sec",
            "Practice 2": "P2_BestLap_sec",
            "Practice 3": "P3_BestLap_sec",
        })

        for col in ["P1_BestLap_sec", "P2_BestLap_sec", "P3_BestLap_sec"]:
            if col not in short_run_wide.columns:
                short_run_wide[col] = np.nan

        for col in ["P1_BestLap_sec", "P2_BestLap_sec", "P3_BestLap_sec"]:
            min_col = short_run_wide.groupby(["Season", "RoundNumber"])[col].transform("min")
            gap_col = col.replace("_BestLap_sec", "_GapToFastest_sec")
            short_run_wide[gap_col] = short_run_wide[col] - min_col

        p2 = laps[laps["SessionName"] == "Practice 2"].copy()
        p2 = p2.sort_values(["Season", "RoundNumber", "Driver", "LapNumber"])
        p2["StintLap"] = p2.groupby(["Season", "RoundNumber", "Driver", "TyreLife"]).cumcount() + 1

        long_run = p2[p2["StintLap"] >= 2]

        long_run_agg = (
            long_run.groupby(["Season", "RoundNumber", "Driver"])
            ["LapTime_sec"]
            .agg(
                P2_LongRunMean_sec="mean",
                P2_LongRunMedian_sec="median",
                P2_LongRunLaps="count"
            )
            .reset_index()
        )

        long_run_agg["P2_LongRunGap_sec"] = (
            long_run_agg.groupby(["Season", "RoundNumber"])["P2_LongRunMean_sec"]
            .transform(lambda x: x - x.min())
        )

        p2_median = (
            p2.groupby(["Season", "RoundNumber", "Driver"])["LapTime_sec"]
            .median()
            .reset_index()
            .rename(columns={"LapTime_sec": "P2_MedianFallback_sec"})
        )
        p3 = laps[laps["SessionName"] == "Practice 3"].copy()
        p3_median = (
            p3.groupby(["Season", "RoundNumber", "Driver"])["LapTime_sec"]
            .median()
            .reset_index()
            .rename(columns={"LapTime_sec": "P3_MedianFallback_sec"})
        )
        long_run_agg = long_run_agg.merge(p2_median, on=["Season", "RoundNumber", "Driver"], how="left")
        long_run_agg = long_run_agg.merge(p3_median, on=["Season", "RoundNumber", "Driver"], how="left")

        long_run_agg["P2_LongRunMean_sec"] = (
            long_run_agg["P2_LongRunMean_sec"]
            .fillna(long_run_agg["P2_MedianFallback_sec"])
            .fillna(long_run_agg["P3_MedianFallback_sec"])
        )
        long_run_agg["P2_LongRunMedian_sec"] = (
            long_run_agg["P2_LongRunMedian_sec"]
            .fillna(long_run_agg["P2_MedianFallback_sec"])
            .fillna(long_run_agg["P3_MedianFallback_sec"])
        )

        long_run_agg["P2_LongRunGap_sec"] = (
            long_run_agg.groupby(["Season", "RoundNumber"])["P2_LongRunMean_sec"]
            .transform(lambda x: x - x.min())
        )

        long_run_agg = long_run_agg.drop(columns=["P2_MedianFallback_sec", "P3_MedianFallback_sec"])

        sector_agg = (
            p3.groupby(["Season", "RoundNumber", "Driver"])
            .agg(
                P3_BestS1_sec=("Sector1Time_sec", "min"),
                P3_BestS2_sec=("Sector2Time_sec", "min"),
                P3_BestS3_sec=("Sector3Time_sec", "min"),
                P3_MaxSpeed=("SpeedST", "max"),
                P3_TrapSpeed=("SpeedFL", "max"),
            )
            .reset_index()
        )

        for s_col in ["P3_BestS1_sec", "P3_BestS2_sec", "P3_BestS3_sec"]:
            min_s = sector_agg.groupby(["Season", "RoundNumber"])[s_col].transform("min")
            sector_agg[s_col.replace("Best", "Gap")] = sector_agg[s_col] - min_s

        sector_sum = (
            sector_agg["P3_BestS1_sec"].fillna(0) +
            sector_agg["P3_BestS2_sec"].fillna(0) +
            sector_agg["P3_BestS3_sec"].fillna(0)
        )
        sector_agg["P3_S1_frac"] = sector_agg["P3_BestS1_sec"] / sector_sum.replace(0, np.nan)
        sector_agg["P3_S2_frac"] = sector_agg["P3_BestS2_sec"] / sector_sum.replace(0, np.nan)
        sector_agg["P3_S3_frac"] = sector_agg["P3_BestS3_sec"] / sector_sum.replace(0, np.nan)

        out = short_run_wide.merge(long_run_agg, on=["Season", "RoundNumber", "Driver"], how="left")
        out = out.merge(sector_agg, on=["Season", "RoundNumber", "Driver"], how="left")
        return out

    def build_driver_history_features(self, skeleton: pd.DataFrame) -> pd.DataFrame:
        df = skeleton[["Season", "RoundNumber", "Driver",
                       "FinalPosition", "Points", "GridPosition",
                       "DNF", "Finished"]].copy()
        df = df.sort_values(["Driver", "Season", "RoundNumber"])

        df["GridToFinish_delta"] = df["GridPosition"] - df["FinalPosition"]

        grp = df.groupby("Driver")

        df["Drv_AvgPos_L3"]      = grp["FinalPosition"].transform(lambda x: rolling_mean_no_leak(x, 3))
        df["Drv_AvgPos_L5"]      = grp["FinalPosition"].transform(lambda x: rolling_mean_no_leak(x, 5))
        df["Drv_AvgPos_L10"]     = grp["FinalPosition"].transform(lambda x: rolling_mean_no_leak(x, 10))
        df["Drv_AvgPos_EWM"]     = grp["FinalPosition"].transform(lambda x: ewm_expanding(x, halflife=4))

        df["Drv_AvgPts_L5"]      = grp["Points"].transform(lambda x: rolling_mean_no_leak(x, 5))
        df["Drv_AvgPts_EWM"]     = grp["Points"].transform(lambda x: ewm_expanding(x, halflife=4))

        df["Drv_DNFRate_L10"]    = grp["DNF"].transform(lambda x: rolling_mean_no_leak(x, 10))
        df["Drv_StdPos_L5"]      = grp["FinalPosition"].transform(lambda x: rolling_std_no_leak(x, 5))

        df["Drv_AvgGridDelta_L5"]= grp["GridToFinish_delta"].transform(lambda x: rolling_mean_no_leak(x, 5))

        df["Drv_SeasonPts_cumulative"] = (
            df.groupby(["Driver", "Season"])["Points"]
            .transform(lambda x: x.shift(1).cumsum().fillna(0))
        )

        df["Drv_SeasonRaceCount"] = (
            df.groupby(["Driver", "Season"]).cumcount()
        )

        keep = [c for c in df.columns if c not in ["FinalPosition", "Points",
                                                     "GridPosition", "DNF",
                                                     "Finished", "GridToFinish_delta"]]
        return df[keep]

    def build_team_history_features(self, skeleton: pd.DataFrame) -> pd.DataFrame:
        team_race = (
            skeleton.groupby(["Season", "RoundNumber", "TeamName"])
            .agg(
                Team_AvgPos=("FinalPosition", "mean"),
                Team_TotalPts=("Points", "sum"),
                Team_DNFCount=("DNF", "sum"),
                Team_BestPos=("FinalPosition", "min"),
            )
            .reset_index()
        )
        team_race = team_race.sort_values(["TeamName", "Season", "RoundNumber"])
        grp = team_race.groupby("TeamName")

        team_race["Team_AvgPos_L5"]    = grp["Team_AvgPos"].transform(lambda x: rolling_mean_no_leak(x, 5))
        team_race["Team_AvgPos_EWM"]   = grp["Team_AvgPos"].transform(lambda x: ewm_expanding(x, halflife=4))
        team_race["Team_AvgPts_L5"]    = grp["Team_TotalPts"].transform(lambda x: rolling_mean_no_leak(x, 5))
        team_race["Team_DNFRate_L10"]  = grp["Team_DNFCount"].transform(lambda x: rolling_mean_no_leak(x, 10))

        team_race["Team_SeasonPts_cumulative"] = (
            team_race.groupby(["TeamName", "Season"])["Team_TotalPts"]
            .transform(lambda x: x.shift(1).cumsum().fillna(0))
        )

        keep_cols = ["Season", "RoundNumber", "TeamName",
                     "Team_AvgPos_L5", "Team_AvgPos_EWM",
                     "Team_AvgPts_L5", "Team_DNFRate_L10",
                     "Team_SeasonPts_cumulative"]
        return team_race[keep_cols]

    def build_circuit_history_features(self, skeleton: pd.DataFrame) -> pd.DataFrame:
        events = self._q("SELECT Season, RoundNumber, Location FROM season_events")
        df = skeleton.merge(events, on=["Season", "RoundNumber"], how="left")
        df["CircuitKey"] = df["Location"].str.strip().str.lower().str.replace(" ", "_")

        df = df[["Season", "RoundNumber", "CircuitKey",
                 "Driver", "FinalPosition", "Points", "DNF", "GridPosition"]].copy()
        df = df.sort_values(["Driver", "CircuitKey", "Season", "RoundNumber"])
        grp = df.groupby(["Driver", "CircuitKey"])
        

        df["Drv_CircuitAvgPos"]    = grp["FinalPosition"].transform(lambda x: x.shift(1).expanding().mean())
        df["Drv_CircuitAvgPts"]    = grp["Points"].transform(lambda x: x.shift(1).expanding().mean())
        df["Drv_CircuitDNFRate"]   = grp["DNF"].transform(lambda x: x.shift(1).expanding().mean())
        df["Drv_CircuitRaceCount"] = grp.cumcount()

        df["GridDelta"] = df["GridPosition"] - df["FinalPosition"]
        df["Drv_CircuitGridDelta"] = grp["GridDelta"].transform(lambda x: x.shift(1).expanding().mean())

        global_avg = (
            df.groupby("Driver")
            .apply(lambda d: d.sort_values(["Season", "RoundNumber"])
                .assign(
                    _GlobalAvgPos=lambda x: x["FinalPosition"].shift(1).expanding().mean(),
                    _GlobalAvgPts=lambda x: x["Points"].shift(1).expanding().mean(),
                    _GlobalDNFRate=lambda x: x["DNF"].shift(1).expanding().mean(),
                    _GlobalGridDelta=lambda x: x["GridDelta"].shift(1).expanding().mean(),
                ))
            .reset_index()  
        )

        df = df.merge(
            global_avg[["Season", "RoundNumber", "Driver",
                         "_GlobalAvgPos", "_GlobalAvgPts",
                         "_GlobalDNFRate", "_GlobalGridDelta"]],
            on=["Season", "RoundNumber", "Driver"], how="left"
        )

        df["Drv_CircuitAvgPos"]    = df["Drv_CircuitAvgPos"].fillna(df["_GlobalAvgPos"])
        df["Drv_CircuitAvgPts"]    = df["Drv_CircuitAvgPts"].fillna(df["_GlobalAvgPts"])
        df["Drv_CircuitDNFRate"]   = df["Drv_CircuitDNFRate"].fillna(df["_GlobalDNFRate"])
        df["Drv_CircuitGridDelta"] = df["Drv_CircuitGridDelta"].fillna(df["_GlobalGridDelta"])

        keep = ["Season", "RoundNumber", "Driver",
                "Drv_CircuitAvgPos", "Drv_CircuitAvgPts",
                "Drv_CircuitDNFRate", "Drv_CircuitRaceCount",
                "Drv_CircuitGridDelta"]
        return df[keep]

    def build_elo_features(self, skeleton: pd.DataFrame,
                           k: float = 32.0,
                           initial_elo: float = 1500.0) -> pd.DataFrame:
        """
        FIX: DNFs excluded from pairwise Elo updates.
        Only update ratings for pairs where BOTH drivers finished (DNF == 0).
        This prevents a P19 retirement from counting as a genuine loss to 18 drivers.
        """
        from itertools import combinations

        elo_ratings = {}
        records = []

        races = (skeleton.sort_values(["Season", "RoundNumber"])
                 .groupby(["Season", "RoundNumber"]))

        for (season, rnd), race_df in races:
            drivers = race_df["Driver"].tolist()
            positions = dict(zip(race_df["Driver"], race_df["FinalPosition"]))
            dnfs = dict(zip(race_df["Driver"], race_df["DNF"]))

            for drv in drivers:
                if drv not in elo_ratings:
                    elo_ratings[drv] = initial_elo
                records.append({
                    "Season": season,
                    "RoundNumber": rnd,
                    "Driver": drv,
                    "Elo_before": elo_ratings[drv]
                })

            classified_drivers = [d for d in drivers if dnfs.get(d, 1) == 0]

            for d1, d2 in combinations(classified_drivers, 2):
                r1, r2 = elo_ratings.get(d1, initial_elo), elo_ratings.get(d2, initial_elo)
                p1, p2 = positions.get(d1, 20), positions.get(d2, 20)

                e1 = 1 / (1 + 10 ** ((r2 - r1) / 400))
                e2 = 1 - e1

                if p1 < p2:
                    s1, s2 = 1.0, 0.0
                elif p2 < p1:
                    s1, s2 = 0.0, 1.0
                else:
                    s1, s2 = 0.5, 0.5

                elo_ratings[d1] = r1 + k * (s1 - e1)
                elo_ratings[d2] = r2 + k * (s2 - e2)

        elo_df = pd.DataFrame(records)
        elo_df["Elo_rank"] = elo_df.groupby(["Season", "RoundNumber"])["Elo_before"].rank(ascending=False)

        return elo_df

    def build_car_performance_features(self) -> pd.DataFrame:
        tables = self._q("SHOW TABLES").iloc[:, 0].tolist()
        car_tables = [t for t in tables if t.startswith("car_data")]

        if not car_tables:
            print("[WARNING] No car_data tables found")
            return pd.DataFrame()

        union_sql = "\nUNION ALL\n".join([
            f"""SELECT Season, RoundNumber, Driver,
                       Speed, Throttle, Brake, DRS, RPM
                FROM {t}
                WHERE SessionName = 'Race'"""
            for t in car_tables
        ])

        df = self._q(union_sql)

        df = df[
            (df["Speed"] > 100) &
            (df["Throttle"] > 95) &
            (~df["Brake"])
        ]

        if df.empty:
            print("[WARNING] No telemetry rows survived filtering")
            return pd.DataFrame()

        df["DRS_Open"] = df["DRS"].isin([10, 12, 14]).astype(float)

        agg = (
            df.groupby(["Season", "RoundNumber", "Driver"])
            .agg(
                Car_MaxSpeed          = ("Speed",    "max"),
                Car_P95Speed          = ("Speed",    lambda x: x.quantile(0.95)),
                Car_AvgFullThrotSpeed = ("Speed",    "mean"),
                Car_DRS_UsageFrac     = ("DRS_Open", "mean"),
                Car_AvgRPM            = ("RPM",      "mean"),
                Car_MaxRPM            = ("RPM",      "max"),
            )
            .reset_index()
        )

        events = self._q("SELECT Season, RoundNumber, Location FROM season_events")
        agg = agg.merge(events, on=["Season", "RoundNumber"], how="left")
        agg["CircuitKey"] = agg["Location"].str.strip().str.lower().str.replace(" ", "_")
        agg = agg.sort_values(["Driver", "CircuitKey", "Season", "RoundNumber"])

        grp = agg.groupby(["Driver", "CircuitKey"])
        agg["Car_CircuitAvgMaxSpeed"] = grp["Car_MaxSpeed"].transform(
            lambda x: x.shift(1).expanding().mean()
        )
        agg["Car_CircuitAvgRPM"] = grp["Car_AvgRPM"].transform(
            lambda x: x.shift(1).expanding().mean()
        )

        agg["Car_CircuitAvgMaxSpeed"] = agg["Car_CircuitAvgMaxSpeed"].fillna(agg["Car_MaxSpeed"])
        agg["Car_CircuitAvgRPM"]      = agg["Car_CircuitAvgRPM"].fillna(agg["Car_AvgRPM"])

        keep = ["Season", "RoundNumber", "Driver",
                "Car_MaxSpeed", "Car_P95Speed",
                "Car_AvgFullThrotSpeed", "Car_DRS_UsageFrac",
                "Car_AvgRPM", "Car_MaxRPM",
                "Car_CircuitAvgMaxSpeed", "Car_CircuitAvgRPM"]
        return agg[keep]

    def build_weather_features(self) -> pd.DataFrame:
        df = self._q("""
            SELECT
                Season,
                RoundNumber,
                SessionName,
                AVG(AirTemp)       AS Wx_AvgAirTemp,
                AVG(TrackTemp)     AS Wx_AvgTrackTemp,
                AVG(Humidity)      AS Wx_AvgHumidity,
                AVG(WindSpeed)     AS Wx_AvgWindSpeed,
                AVG(CAST(Rainfall AS INT)) AS Wx_RainfallFrac,
                MAX(CAST(Rainfall AS INT)) AS Wx_AnyRain,
                AVG(Pressure)      AS Wx_AvgPressure
            FROM weather_data
            WHERE SessionName = 'Race'
            GROUP BY Season, RoundNumber, SessionName
        """)

        df_raw = self._q("""
            SELECT Season, RoundNumber, SessionName,
                   MAX(TrackTemp) - MIN(TrackTemp) AS Wx_TrackTempSpread
            FROM weather_data
            WHERE SessionName = 'Race'
            GROUP BY Season, RoundNumber, SessionName
        """)

        df = df.merge(df_raw, on=["Season", "RoundNumber", "SessionName"])
        df = df.drop(columns=["SessionName"])
        return df

    def build_circuit_meta_features(self) -> pd.DataFrame:
        df = self._q("""
            SELECT
                Season,
                RoundNumber,
                OfficialEventName,
                EventName,
                Location,
                Country,
                EventFormat,
                Session5        AS RaceSessionType
            FROM season_events
        """)

        df["IsSprintWeekend"] = df["EventFormat"].str.lower().str.contains("sprint").astype(int)

        street_circuits = ["Monaco", "Singapore", "Baku", "Miami", "Las Vegas",
                           "Jeddah", "Melbourne", "Montréal"]
        df["IsStreetCircuit"] = df["Location"].isin(street_circuits).astype(int)

        df["SeasonProgress"] = df.groupby("Season")["RoundNumber"].transform(
            lambda x: (x - x.min()) / (x.max() - x.min() + 1e-9)
        )

        keep = ["Season", "RoundNumber", "OfficialEventName", "Location", "Country",
                "IsSprintWeekend", "IsStreetCircuit", "SeasonProgress", "EventFormat"]
        return df[keep]

    def build_race_control_features(self) -> pd.DataFrame:
        df = self._q("""
            SELECT
                r.Season,
                r.RoundNumber,
                e.Location,
                SUM(CASE WHEN r.Message ILIKE '%SAFETY CAR DEPLOYED%' THEN 1 ELSE 0 END) AS SC_Count,
                SUM(CASE WHEN r.Flag = 'RED' THEN 1 ELSE 0 END) AS RedFlag_Count,
                SUM(CASE WHEN r.Flag = 'YELLOW' THEN 1 ELSE 0 END) AS YellowFlag_Count
            FROM race_control_messages r
            LEFT JOIN season_events e
                ON r.Season = e.Season AND r.RoundNumber = e.RoundNumber
            WHERE r.SessionName = 'Race'
            GROUP BY r.Season, r.RoundNumber, e.Location
        """)

        df["CircuitKey"] = df["Location"].str.strip().str.lower().str.replace(" ", "_")
        df = df.sort_values(["CircuitKey", "Season", "RoundNumber"])
        grp = df.groupby("CircuitKey")

        df["Circuit_AvgSC_hist"]    = grp["SC_Count"].transform(lambda x: x.shift(1).expanding().mean())
        df["Circuit_AvgFlags_hist"] = grp["YellowFlag_Count"].transform(lambda x: x.shift(1).expanding().mean())

        df["Circuit_SCRate_hist"] = grp["SC_Count"].transform(
            lambda x: x.shift(1).expanding().mean() / x.shift(1).expanding().count().clip(lower=1)
        )

        keep = ["Season", "RoundNumber",
                "SC_Count", "RedFlag_Count", "YellowFlag_Count",
                "Circuit_AvgSC_hist", "Circuit_AvgFlags_hist", "Circuit_SCRate_hist"]
        return df[keep]


    def build_tyre_features(self) -> pd.DataFrame:
        df = self._q("""
            SELECT
                Season,
                RoundNumber,
                Driver,
                Compound,
                Stint,
                LapTime,
                TyreLife,
                LapNumber
            FROM laps
            WHERE SessionName = 'Race'
              AND IsAccurate = TRUE
        """)

        df["LapTime_sec"] = interval_to_seconds(df["LapTime"])
        df = df[df["LapTime_sec"].between(60, 200)]

        def tyre_deg(group):
            if len(group) < 3:
                return np.nan
            x = group["TyreLife"].values.astype(float)
            y = group["LapTime_sec"].values.astype(float)
            mask = np.isfinite(x) & np.isfinite(y)
            x, y = x[mask], y[mask]
            if len(x) < 3:
                return np.nan
            if np.std(x) < 1e-6:
                return np.nan
            return np.polyfit(x, y, 1)[0]

        deg_df = (
            df.groupby(["Season", "RoundNumber", "Driver", "Stint"])
            .apply(tyre_deg, include_groups=False)
            .reset_index()
            .rename(columns={0: "StintDeg"})
        )

        drv_deg = (
            deg_df.groupby(["Season", "RoundNumber", "Driver"])["StintDeg"]
            .mean()
            .reset_index()
            .rename(columns={"StintDeg": "Drv_AvgTyreDeg"})
        )

        stints = (
            df.groupby(["Season", "RoundNumber", "Driver"])["Stint"]
            .max()
            .reset_index()
            .rename(columns={"Stint": "NumStints"})
        )
        stints["NumPitStops"] = stints["NumStints"] - 1

        compound_mode = (
            df.groupby(["Season", "RoundNumber", "Driver"])["Compound"]
            .agg(lambda x: x.mode()[0] if len(x) > 0 else "UNKNOWN")
            .reset_index()
            .rename(columns={"Compound": "PrimaryCompound"})
        )

        out = drv_deg.merge(stints[["Season", "RoundNumber", "Driver", "NumPitStops"]],
                            on=["Season", "RoundNumber", "Driver"], how="left")
        out = out.merge(compound_mode, on=["Season", "RoundNumber", "Driver"], how="left")
        return out

    def build_form_features(self, skeleton: pd.DataFrame) -> pd.DataFrame:
        df = skeleton[["Season", "RoundNumber", "Driver",
                       "FinalPosition", "Points", "DNF"]].copy()
        df = df.sort_values(["Driver", "Season", "RoundNumber"])
        grp = df.groupby("Driver")

        df["Form_Pts_L3"]      = grp["Points"].transform(lambda x: rolling_mean_no_leak(x, 3))

        df["IsPodium"]         = (df["FinalPosition"] <= 3).astype(int)
        df["Form_PodiumRate_L5"] = grp["IsPodium"].transform(lambda x: rolling_mean_no_leak(x, 5))

        df["IsInPoints"]       = (df["FinalPosition"] <= 10).astype(int)
        df["Form_InPointsRate_L5"] = grp["IsInPoints"].transform(lambda x: rolling_mean_no_leak(x, 5))

        df["Form_ConsecDNF"]   = grp["DNF"].transform(
            lambda x: x.shift(1).rolling(3, min_periods=1).sum()
        )

        keep = ["Season", "RoundNumber", "Driver",
                "Form_Pts_L3", "Form_PodiumRate_L5",
                "Form_InPointsRate_L5", "Form_ConsecDNF"]
        return df[keep]

    def build_championship_features(self, skeleton: pd.DataFrame) -> pd.DataFrame:
        df = skeleton[["Season", "RoundNumber", "Driver", "Points"]].copy()
        df = df.sort_values(["Driver", "Season", "RoundNumber"])

        df["SeasonCumPts"] = (
            df.groupby(["Driver", "Season"])["Points"]
            .transform(lambda x: x.shift(1).cumsum().fillna(0))
        )

        df["PtsGapToLeader"] = (
            df.groupby(["Season", "RoundNumber"])["SeasonCumPts"]
            .transform(lambda x: x.max() - x)
        )

        df["ChampionshipRank"] = (
            df.groupby(["Season", "RoundNumber"])["SeasonCumPts"]
            .rank(ascending=False, method="min")
        )

        keep = ["Season", "RoundNumber", "Driver",
                "SeasonCumPts", "PtsGapToLeader", "ChampionshipRank"]
        return df[keep]

    def build_teammate_features(self, skeleton: pd.DataFrame) -> pd.DataFrame:
        df = skeleton[["Season", "RoundNumber", "Driver", "TeamName",
                       "FinalPosition", "Points", "GridPosition"]].copy()

        df_self = df.copy()
        df_mate = df.copy().rename(columns={
            "Driver": "Teammate",
            "FinalPosition": "Mate_FinalPos",
            "Points": "Mate_Points",
            "GridPosition": "Mate_GridPos"
        })

        merged = df_self.merge(df_mate, on=["Season", "RoundNumber", "TeamName"])
        merged = merged[merged["Driver"] != merged["Teammate"]]

        merged["BeatTeammate"]   = (merged["FinalPosition"] < merged["Mate_FinalPos"]).astype(int)
        merged["QualiGapToMate"] = merged["GridPosition"] - merged["Mate_GridPos"]
        merged["PosGapToMate"]   = merged["FinalPosition"] - merged["Mate_FinalPos"]

        merged["_SharedRaces"] = merged.groupby(["Driver", "Teammate"])["Season"].transform("count")
        merged = merged.sort_values(["Season", "RoundNumber", "Driver", "_SharedRaces"],
                                    ascending=[True, True, True, False])
        merged = merged.drop_duplicates(subset=["Season", "RoundNumber", "Driver"])
        merged = merged.drop(columns=["_SharedRaces"])

        merged = merged.sort_values(["Driver", "Season", "RoundNumber"])
        grp = merged.groupby("Driver")

        merged["Tm_BeatRate_L5"]  = grp["BeatTeammate"].transform(lambda x: rolling_mean_no_leak(x, 5))
        merged["Tm_QualiGap_EWM"] = grp["QualiGapToMate"].transform(lambda x: ewm_expanding(x, halflife=4))
        merged["Tm_PosGap_EWM"]   = grp["PosGapToMate"].transform(lambda x: ewm_expanding(x, halflife=4))

        keep = ["Season", "RoundNumber", "Driver",
                "Tm_BeatRate_L5", "Tm_QualiGap_EWM", "Tm_PosGap_EWM"]
        return merged[keep]

    def build_chaos_features(self, skeleton: pd.DataFrame) -> pd.DataFrame:
        """
        NEW: Historical standard deviation of grid-to-finish position changes
        per circuit. High chaos = predictions should blend toward grid order.
        Also computes a circuit-level 'upset rate' (fraction of drivers who
        finish more than 5 places from their grid position).
        """
        events = self._q("SELECT Season, RoundNumber, Location FROM season_events")
        df = skeleton.merge(events, on=["Season", "RoundNumber"], how="left")
        df["CircuitKey"] = df["Location"].str.strip().str.lower().str.replace(" ", "_")
        df["AbsGridDelta"] = (df["GridPosition"] - df["FinalPosition"]).abs()
        df["BigUpset"] = (df["AbsGridDelta"] > 5).astype(int)

        circuit_race = (
            df.groupby(["CircuitKey", "Season", "RoundNumber"])
            .agg(
                Chaos_StdDelta=("AbsGridDelta", "std"),
                Chaos_UpsetRate=("BigUpset", "mean"),
            )
            .reset_index()
        )

        circuit_race = circuit_race.sort_values(["CircuitKey", "Season", "RoundNumber"])
        grp = circuit_race.groupby("CircuitKey")

        circuit_race["Circuit_HistChaos"] = grp["Chaos_StdDelta"].transform(
            lambda x: x.shift(1).expanding().mean()
        )
        circuit_race["Circuit_HistUpsetRate"] = grp["Chaos_UpsetRate"].transform(
            lambda x: x.shift(1).expanding().mean()
        )

        out = df[["Season", "RoundNumber"]].drop_duplicates().merge(
            circuit_race[["Season", "RoundNumber",
                           "Circuit_HistChaos", "Circuit_HistUpsetRate"]],
            on=["Season", "RoundNumber"], how="left"
        )
        return out


    def build_all(self, verbose: bool = True) -> pd.DataFrame:
        def log(msg):
            if verbose:
                print(f"[F1Features] {msg}")

        log("Building skeleton...")
        skeleton = self.build_skeleton()

        log("Building qualifying features...")
        quali = self.build_quali_features()

        log("Building practice features...")
        practice = self.build_practice_features()

        log("Building driver history features...")
        drv_hist = self.build_driver_history_features(skeleton)

        log("Building team history features...")
        team_hist = self.build_team_history_features(skeleton)

        log("Building circuit history features...")
        circuit_hist = self.build_circuit_history_features(skeleton)

        log("Building Elo ratings...")
        elo = self.build_elo_features(skeleton)

        log("Building weather features...")
        weather = self.build_weather_features()

        log("Building circuit meta features...")
        circuit_meta = self.build_circuit_meta_features()

        log("Building race control features...")
        rc = self.build_race_control_features()

        log("Building tyre features...")
        tyres = self.build_tyre_features()

        log("Building car performance features...")
        car_perf = self.build_car_performance_features()

        log("Building form features...")
        form = self.build_form_features(skeleton)

        log("Building championship features...")
        champ = self.build_championship_features(skeleton)

        log("Building teammate features...")
        teammate = self.build_teammate_features(skeleton)

        log("Building chaos index features...")
        chaos = self.build_chaos_features(skeleton)

        log("Merging all features...")
        df = skeleton.copy()

        for feat_df, keys in [
            (quali,        ["Season", "RoundNumber", "Driver"]),
            (practice,     ["Season", "RoundNumber", "Driver"]),
            (drv_hist,     ["Season", "RoundNumber", "Driver"]),
            (team_hist,    ["Season", "RoundNumber", "TeamName"]),
            (circuit_hist, ["Season", "RoundNumber", "Driver"]),
            (elo,          ["Season", "RoundNumber", "Driver"]),
            (weather,      ["Season", "RoundNumber"]),
            (circuit_meta, ["Season", "RoundNumber"]),
            (rc,           ["Season", "RoundNumber"]),
            (tyres,        ["Season", "RoundNumber", "Driver"]),
            (car_perf,     ["Season", "RoundNumber", "Driver"]),
            (form,         ["Season", "RoundNumber", "Driver"]),
            (champ,        ["Season", "RoundNumber", "Driver"]),
            (teammate,     ["Season", "RoundNumber", "Driver"]),
            (chaos,        ["Season", "RoundNumber"]),
        ]:
            df = df.merge(feat_df, on=keys, how="left", suffixes=("", "_dup"))
            dup_cols = [c for c in df.columns if c.endswith("_dup")]
            df = df.drop(columns=dup_cols)

        log(f"Done. Feature table shape: {df.shape}")
        log(f"Columns: {len(df.columns)}")

        return df

class F1PredictionFeatureBuilder:

    def __init__(self, con: duckdb.DuckDBPyConnection,
                 historical_features: pd.DataFrame):
        self.con = con
        self.hist = historical_features
        self.builder = F1FeatureBuilder(con)

    def build_prediction_features(
        self,
        target_season: int,
        target_round: int,
        weather_forecast: Optional[dict] = None
    ) -> pd.DataFrame:
        quali = self.builder.build_quali_features()
        quali_this = quali[
            (quali["Season"] == target_season) &
            (quali["RoundNumber"] == target_round)
        ]

        practice = self.builder.build_practice_features()
        prac_this = practice[
            (practice["Season"] == target_season) &
            (practice["RoundNumber"] == target_round)
        ]

        last_hist = (
            self.hist[self.hist["Season"].lt(target_season) |
                      (self.hist["Season"].eq(target_season) &
                       self.hist["RoundNumber"].lt(target_round))]
            .sort_values(["Season", "RoundNumber"])
            .groupby("Driver")
            .last()
            .reset_index()
        )

        hist_cols = [c for c in last_hist.columns if any(
            c.startswith(p) for p in
            ["Drv_", "Team_", "Elo_", "Form_", "SeasonCumPts",
             "PtsGapToLeader", "ChampionshipRank", "Tm_"]
        )]
        hist_feats = last_hist[["Driver"] + hist_cols]

        circuit_meta = self.builder.build_circuit_meta_features()
        meta_this = circuit_meta[
            (circuit_meta["Season"] == target_season) &
            (circuit_meta["RoundNumber"] == target_round)
        ]

        rc = self.builder.build_race_control_features()
        rc_this = rc[
            (rc["Season"] == target_season) &
            (rc["RoundNumber"] == target_round)
        ]

        df = quali_this.copy()
        df = df.merge(prac_this,     on=["Season", "RoundNumber", "Driver"], how="left")
        df = df.merge(hist_feats,    on=["Driver"],                          how="left")
        df = df.merge(meta_this,     on=["Season", "RoundNumber"],           how="left")
        df = df.merge(rc_this,       on=["Season", "RoundNumber"],           how="left")

        if weather_forecast:
            for k, v in weather_forecast.items():
                df[k] = v

        return df

if __name__ == "__main__":
    import sys

    db_path = sys.argv[1] if len(sys.argv) > 1 else "f1.duckdb"
    print(f"Connecting to {db_path}...")
    con = duckdb.connect(db_path)

    builder = F1FeatureBuilder(con)
    features = builder.build_all(verbose=True)

    print("\n── Feature table sample ──")
    print(features.head(3).T)

    print("\n── Missing value summary ──")
    miss = features.isnull().mean().sort_values(ascending=False)
    print(miss[miss > 0].to_string())

    out_path = "f1_features.parquet"
    features.to_parquet(out_path, index=False)
    print(f"\nSaved to {out_path}")
    con.close()