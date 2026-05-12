import { useEffect, useState } from "react";
import {
  RotateCcw,
  Zap,
  TrendingUp,
  Cloud,
  Trophy,
  Target,
  Settings,
  SlidersHorizontal,
  Calendar,
} from "lucide-react";
import * as Slider from "@radix-ui/react-slider";
import { Switch } from "./ui/switch";
import { Label } from "./ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import {
  predictionService,
  type PredictionRow,
} from "../../services/predictionService";

function raceOptionKey(season: number, round: number) {
  return `${season}-${round}`;
}

interface Factor {
  id: string;
  name: string;
  icon: React.ReactNode;
  weight: number;
  description: string;
}

const initialFactors: Factor[] = [
  {
    id: "driver-skill",
    name: "Driver Skill",
    icon: <Trophy className="h-5 w-5" />,
    weight: 1,
    description: "Overall driver ability and experience",
  },
  {
    id: "team-performance",
    name: "Team Performance",
    icon: <TrendingUp className="h-5 w-5" />,
    weight: 1,
    description: "Team strategy and pit crew efficiency",
  },
  {
    id: "track-history",
    name: "Track History",
    icon: <Target className="h-5 w-5" />,
    weight: 1,
    description: "Past performance on this circuit",
  },
  {
    id: "weather",
    name: "Weather Conditions",
    icon: <Cloud className="h-5 w-5" />,
    weight: 1,
    description: "Impact of current weather forecast",
  },
  {
    id: "recent-form",
    name: "Recent Form",
    icon: <Zap className="h-5 w-5" />,
    weight: 1,
    description: "Performance in last 3 races",
  },
];

function buildUserWeights(factors: Factor[]): Record<string, number> {
  const idToKey: Record<string, string> = {
    "driver-skill": "driver_skill",
    "team-performance": "team_performance",
    "track-history": "track_history",
    weather: "weather",
    "recent-form": "recent_form",
  };
  const out: Record<string, number> = {};
  for (const f of factors) {
    const k = idToKey[f.id];
    if (k) out[k] = f.weight;
  }
  return out;
}

export default function Predictions() {
  const [factors, setFactors] = useState<Factor[]>(initialFactors);
  const [isPredicting, setIsPredicting] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [customWeightsEnabled, setCustomWeightsEnabled] = useState(false);
  const [eventLabel, setEventLabel] = useState("");
  const [pickerSeason, setPickerSeason] = useState(2025);
  const [seasonRaces, setSeasonRaces] = useState<
    { season: number; round: number; event: string }[]
  >([]);
  const [raceKey, setRaceKey] = useState("");
  const [metaLoading, setMetaLoading] = useState(true);
  const [metaError, setMetaError] = useState<string | null>(null);
  const [predictionRows, setPredictionRows] = useState<PredictionRow[]>([]);
  const [analysisText, setAnalysisText] = useState("");
  const [modelConfidence, setModelConfidence] = useState(0);
  const [predictionError, setPredictionError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    predictionService
      .getMeta()
      .then((m) => {
        if (cancelled) return;
        setMetaError(null);
        setMetaLoading(false);
        setPickerSeason(m.pickerSeason ?? 2025);
        setSeasonRaces(m.races);
        if (m.races.length > 0) {
          const hasDefault = m.races.some(
            (r) => r.season === m.defaultSeason && r.round === m.defaultRound
          );
          const pick = hasDefault
            ? raceOptionKey(m.defaultSeason, m.defaultRound)
            : raceOptionKey(
                m.races[m.races.length - 1].season,
                m.races[m.races.length - 1].round
              );
          setRaceKey(pick);
          const sel =
            m.races.find((r) => raceOptionKey(r.season, r.round) === pick) ??
            m.races[m.races.length - 1];
          setEventLabel(sel.event);
        } else {
          setRaceKey("");
          setEventLabel(m.defaultEventName);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setMetaLoading(false);
          setSeasonRaces([]);
          setRaceKey("");
          setEventLabel("");
          setMetaError(
            "Could not load races. Check that the backend is running and you are signed in."
          );
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleWeightChange = (id: string, value: number[]) => {
    setFactors((prev) =>
      prev.map((f) => (f.id === id ? { ...f, weight: value[0] } : f))
    );
  };

  const resetFactors = () => {
    setFactors(initialFactors);
  };

  const runPrediction = async () => {
    setPredictionError(null);
    if (!raceKey) {
      setPredictionError(
        seasonRaces.length === 0
          ? `No ${pickerSeason} races found in the model dataset.`
          : "Choose a race first."
      );
      return;
    }
    const parts = raceKey.split("-");
    const season = Number(parts[0]);
    const round = Number(parts[1]);
    if (!Number.isFinite(season) || !Number.isFinite(round)) {
      setPredictionError("Invalid race selection.");
      return;
    }
    setIsPredicting(true);
    try {
      const payload: {
        season: number;
        round: number;
        user_weights?: Record<string, number>;
      } = { season, round };
      if (customWeightsEnabled) {
        payload.user_weights = buildUserWeights(factors);
      }
      const data = await predictionService.predict(payload);
      setPredictionRows(data.top10);
      setEventLabel(data.eventName);
      setAnalysisText(data.analysis);
      setModelConfidence(data.modelConfidence);
      setShowResults(true);
    } catch (e) {
      setPredictionError(e instanceof Error ? e.message : "Prediction failed");
      setShowResults(false);
    } finally {
      setIsPredicting(false);
    }
  };

  return (
    <div className="min-h-screen bg-background py-8">
      <div className="container mx-auto px-6">
        <div className="mb-8">
          <h1 className="mb-2 text-4xl font-bold tracking-tight text-foreground">
            AI Race Predictor
          </h1>
          <p className="text-muted-foreground">
            {customWeightsEnabled
              ? `Pick a ${pickerSeason} race, tune factor weights below, then generate a prediction tailored to your preferences.`
              : `Pick a ${pickerSeason} race, then run a prediction with the model’s default balanced weights, or turn on custom weights to fine-tune each factor.`}
          </p>
        </div>

        {metaError && (
          <p className="mb-6 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-600 dark:text-red-400">
            {metaError}
          </p>
        )}

        <div className="grid gap-6 lg:grid-cols-2">
          <div className="space-y-6">
            <div className="overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-card/80 to-secondary/40 p-6 backdrop-blur-xl">
              <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <Calendar className="h-6 w-6 text-[#e10600]" />
                  <h3 className="text-lg text-foreground">{pickerSeason} season — race</h3>
                </div>
              </div>
              {metaLoading ? (
                <p className="text-sm text-muted-foreground">Loading races…</p>
              ) : seasonRaces.length > 0 ? (
                <div className="space-y-2">
                  <Label htmlFor="race-select" className="text-sm text-muted-foreground">
                    Grand Prix
                  </Label>
                  <Select
                    value={raceKey}
                    onValueChange={(v) => {
                      setRaceKey(v);
                      const hit = seasonRaces.find(
                        (r) => raceOptionKey(r.season, r.round) === v
                      );
                      if (hit) setEventLabel(hit.event);
                    }}
                  >
                    <SelectTrigger id="race-select" className="w-full bg-input-background">
                      <SelectValue placeholder="Select a race" />
                    </SelectTrigger>
                    <SelectContent>
                      {seasonRaces.map((r) => (
                        <SelectItem
                          key={raceOptionKey(r.season, r.round)}
                          value={raceOptionKey(r.season, r.round)}
                        >
                          R{r.round} — {r.event}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              ) : !metaError ? (
                <p className="text-sm text-muted-foreground">
                  No {pickerSeason} races in the features file yet. Add that season to the dataset or check{" "}
                  <code className="rounded bg-secondary px-1 py-0.5 text-xs">F1_FEATURES_PARQUET</code>.
                </p>
              ) : null}
            </div>

            <div className="overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-card/80 to-secondary/40 p-6 backdrop-blur-xl">
              <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <Settings className="h-6 w-6 text-[#e10600]" />
                  <h3 className="text-lg text-foreground">Prediction Factors</h3>
                </div>
                {customWeightsEnabled && (
                  <button
                    type="button"
                    onClick={resetFactors}
                    className="flex items-center gap-2 rounded-lg border border-border bg-secondary/30 px-4 py-2 text-sm text-foreground transition-all hover:bg-secondary/50"
                  >
                    <RotateCcw className="h-4 w-4" />
                    Reset
                  </button>
                )}
              </div>

              <div className="mb-6 flex flex-col gap-3 rounded-xl border border-border bg-secondary/20 p-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[#e10600]/15 text-[#e10600]">
                    <SlidersHorizontal className="h-4 w-4" />
                  </div>
                  <div className="min-w-0 space-y-1">
                    <Label htmlFor="custom-weights" className="text-sm font-semibold text-foreground">
                      Custom factor weights
                    </Label>
                    <p className="text-xs leading-relaxed text-muted-foreground">
                      Off: default balanced weights — go straight to Predict. On: show sliders and tune each factor.
                    </p>
                  </div>
                </div>
                <div className="flex shrink-0 items-center gap-3 self-end sm:self-center">
                  <span className="text-xs font-medium text-muted-foreground sm:hidden">
                    {customWeightsEnabled ? "On" : "Off"}
                  </span>
                  <Switch
                    id="custom-weights"
                    checked={customWeightsEnabled}
                    onCheckedChange={setCustomWeightsEnabled}
                    aria-label="Toggle custom factor weights"
                  />
                </div>
              </div>

              {customWeightsEnabled ? (
                <div className="space-y-4">
                  {factors.map((factor) => (
                    <div
                      key={factor.id}
                      className="rounded-lg border border-border bg-secondary/30 p-4"
                    >
                      <div className="mb-4 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-[#e10600] to-[#a00500] text-white">
                            {factor.icon}
                          </div>
                          <div>
                            <div className="font-semibold text-foreground">{factor.name}</div>
                            <div className="text-xs text-muted-foreground">
                              {factor.description}
                            </div>
                          </div>
                        </div>
                        <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-[#e10600]/20 bg-[#e10600]/10">
                          <span className="font-bold text-foreground">{factor.weight}</span>
                        </div>
                      </div>

                      <div className="space-y-2">
                        <Slider.Root
                          className="relative flex h-5 w-full touch-none select-none items-center"
                          value={[factor.weight]}
                          onValueChange={(value) => handleWeightChange(factor.id, value)}
                          max={10}
                          step={1}
                        >
                          <Slider.Track className="relative h-2 grow rounded-full bg-secondary/50">
                            <Slider.Range className="absolute h-full rounded-full bg-gradient-to-r from-[#e10600] to-[#c00500]" />
                          </Slider.Track>
                          <Slider.Thumb className="block h-5 w-5 rounded-full border-2 border-[#e10600] bg-white shadow-lg shadow-[#e10600]/30 transition-all hover:scale-110 focus:outline-none" />
                        </Slider.Root>

                        <div className="flex justify-between text-xs text-muted-foreground">
                          <span>0</span>
                          <span>5</span>
                          <span>10</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="rounded-xl border border-dashed border-border bg-secondary/10 px-4 py-10 text-center">
                  <p className="text-sm text-muted-foreground">
                    Default model weights are in use. Tap{" "}
                    <span className="font-semibold text-foreground">Generate AI Prediction</span> when you are ready,
                    or enable custom weights above to adjust factors first.
                  </p>
                </div>
              )}

              {predictionError && (
                <p className="mb-3 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-600 dark:text-red-400">
                  {predictionError}
                </p>
              )}

              <button
                type="button"
                onClick={() => void runPrediction()}
                disabled={isPredicting || !raceKey}
                className="mt-6 flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-[#e10600] to-[#c00500] px-6 py-4 font-semibold text-white shadow-xl shadow-[#e10600]/30 transition-all hover:shadow-2xl hover:shadow-[#e10600]/40 disabled:opacity-50"
              >
                {isPredicting ? (
                  <>
                    <div className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
                    <span>AI Model Processing...</span>
                  </>
                ) : (
                  <>
                    <Zap className="h-5 w-5" />
                    <span>Generate AI Prediction</span>
                  </>
                )}
              </button>
            </div>
          </div>

          <div className="space-y-6">
            <div className="overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-card/80 to-secondary/40 p-6 backdrop-blur-xl">
              <div className="mb-6 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Trophy className="h-6 w-6 text-[#ffd700]" />
                  <h3 className="text-lg text-foreground">AI Predicted Top 10</h3>
                </div>
                <div className="text-sm text-muted-foreground">{eventLabel || "Race"}</div>
              </div>

              {!showResults ? (
                <div className="flex h-96 items-center justify-center">
                  <div className="text-center">
                    <div className="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-secondary/30">
                      <Zap className="h-10 w-10 text-muted-foreground" />
                    </div>
                    <p className="text-muted-foreground">
                      {customWeightsEnabled
                        ? "Adjust factor weights and generate a prediction to see results"
                        : "Click Generate AI Prediction to see results using default model weights"}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="space-y-3 max-h-[800px] overflow-y-auto pr-2">
                  {predictionRows.map((result) => (
                    <div
                      key={`${result.position}-${result.driver}`}
                      className="overflow-hidden rounded-xl border border-border bg-gradient-to-r from-secondary/50 to-secondary/30 p-4 transition-all hover:border-[#e10600]/50"
                    >
                      <div className="mb-3 flex items-center gap-3">
                        <div
                          className={`flex h-10 w-10 items-center justify-center rounded-lg font-bold ${
                            result.position === 1
                              ? "bg-gradient-to-br from-[#ffd700] to-[#ffed4e] text-black"
                              : result.position === 2
                              ? "bg-gradient-to-br from-[#c0c0c0] to-[#e8e8e8] text-black"
                              : result.position === 3
                              ? "bg-gradient-to-br from-[#cd7f32] to-[#e8a87c] text-white"
                              : "bg-gradient-to-br from-[#2a2a35] to-[#1f1f28] text-white border border-border"
                          }`}
                        >
                          {result.position}
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="font-semibold text-foreground">{result.driver}</div>
                          <div className="text-sm text-muted-foreground">{result.team}</div>
                        </div>
                      </div>

                      <div className="space-y-1.5">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-muted-foreground">Completion Probability</span>
                          <span className="font-semibold text-[#00ff88]">
                            {result.confidence}%
                          </span>
                        </div>
                        <div className="h-1.5 overflow-hidden rounded-full bg-secondary/50">
                          <div
                            className="h-full rounded-full bg-gradient-to-r from-[#00ff88] to-[#00d4ff]"
                            style={{ width: `${result.confidence}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {showResults && (
              <div className="overflow-hidden rounded-2xl border border-[#00d4ff]/20 bg-gradient-to-br from-[#00d4ff]/10 to-transparent p-6 backdrop-blur-xl">
                <h3 className="mb-4 flex items-center gap-2 text-foreground">
                  <Target className="h-5 w-5 text-[#00d4ff]" />
                  Model Analysis
                </h3>
                <p className="text-sm leading-relaxed text-muted-foreground">{analysisText}</p>
                <div className="mt-4 flex items-center gap-2 text-xs text-muted-foreground">
                  <div className="h-2 w-2 rounded-full bg-[#00ff88]"></div>
                  <span>Model confidence: {modelConfidence}%</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
