import { useState } from "react";
import { RotateCcw, Zap, TrendingUp, Cloud, Trophy, Target, Settings } from "lucide-react";
import * as Slider from "@radix-ui/react-slider";

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

const predictionResults = [
  {
    position: 1,
    driver: "Max Verstappen",
    team: "Red Bull Racing",
    probability: 68,
    confidence: 92,
  },
  {
    position: 2,
    driver: "Charles Leclerc",
    team: "Ferrari",
    probability: 52,
    confidence: 85,
  },
  {
    position: 3,
    driver: "Lando Norris",
    team: "McLaren",
    probability: 45,
    confidence: 78,
  },
  {
    position: 4,
    driver: "Lewis Hamilton",
    team: "Mercedes",
    probability: 38,
    confidence: 74,
  },
  {
    position: 5,
    driver: "George Russell",
    team: "Mercedes",
    probability: 35,
    confidence: 71,
  },
  {
    position: 6,
    driver: "Carlos Sainz",
    team: "Ferrari",
    probability: 32,
    confidence: 68,
  },
  {
    position: 7,
    driver: "Sergio Perez",
    team: "Red Bull Racing",
    probability: 28,
    confidence: 65,
  },
  {
    position: 8,
    driver: "Fernando Alonso",
    team: "Aston Martin",
    probability: 24,
    confidence: 62,
  },
  {
    position: 9,
    driver: "Oscar Piastri",
    team: "McLaren",
    probability: 21,
    confidence: 58,
  },
  {
    position: 10,
    driver: "Lance Stroll",
    team: "Aston Martin",
    probability: 18,
    confidence: 55,
  },
];

export default function Predictions() {
  const [factors, setFactors] = useState<Factor[]>(initialFactors);
  const [isPredicting, setIsPredicting] = useState(false);
  const [showResults, setShowResults] = useState(false);

  const handleWeightChange = (id: string, value: number[]) => {
    setFactors((prev) =>
      prev.map((f) => (f.id === id ? { ...f, weight: value[0] } : f))
    );
  };

  const resetFactors = () => {
    setFactors(initialFactors);
  };

  const runPrediction = () => {
    setIsPredicting(true);
    setTimeout(() => {
      setIsPredicting(false);
      setShowResults(true);
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-background py-8">
      <div className="container mx-auto px-6">
        <div className="mb-8">
          <h1 className="mb-2 text-4xl font-bold tracking-tight text-foreground">
            AI Race Predictor
          </h1>
          <p className="text-muted-foreground">
            Adjust the prediction factors below and let our AI model generate race outcome predictions for you
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <div className="space-y-6">
            <div className="overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-card/80 to-secondary/40 p-6 backdrop-blur-xl">
              <div className="mb-6 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Settings className="h-6 w-6 text-[#e10600]" />
                  <h3 className="text-lg text-foreground">Prediction Factors</h3>
                </div>
                <button
                  onClick={resetFactors}
                  className="flex items-center gap-2 rounded-lg border border-border bg-secondary/30 px-4 py-2 text-sm text-foreground transition-all hover:bg-secondary/50"
                >
                  <RotateCcw className="h-4 w-4" />
                  Reset
                </button>
              </div>

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
                      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#e10600]/10 border border-[#e10600]/20">
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

              <button
                onClick={runPrediction}
                disabled={isPredicting}
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
                <div className="text-sm text-muted-foreground">Miami GP</div>
              </div>

              {!showResults ? (
                <div className="flex h-96 items-center justify-center">
                  <div className="text-center">
                    <div className="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-secondary/30">
                      <Zap className="h-10 w-10 text-muted-foreground" />
                    </div>
                    <p className="text-muted-foreground">
                      Adjust factors and generate AI prediction to see results
                    </p>
                  </div>
                </div>
              ) : (
                <div className="space-y-3 max-h-[800px] overflow-y-auto pr-2">
                  {predictionResults.map((result) => (
                    <div
                      key={result.position}
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
                        <div className="flex-1">
                          <div className="font-semibold text-foreground">{result.driver}</div>
                          <div className="text-sm text-muted-foreground">{result.team}</div>
                        </div>
                        <div className="text-right">
                          <div className="text-xl font-bold text-foreground">
                            {result.probability}%
                          </div>
                          <div className="text-xs text-muted-foreground">Probability</div>
                        </div>
                      </div>

                      <div className="space-y-1.5">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-muted-foreground">Confidence</span>
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
                <p className="text-sm leading-relaxed text-muted-foreground">
                  Based on your configured factors, the AI model predicts <span className="font-semibold text-foreground">Max Verstappen</span> has the highest probability of winning the Miami GP. His strong recent form combined with Red Bull's superior team performance gives him a significant advantage. Weather conditions are expected to be favorable, which further supports this prediction.
                </p>
                <div className="mt-4 flex items-center gap-2 text-xs text-muted-foreground">
                  <div className="h-2 w-2 rounded-full bg-[#00ff88]"></div>
                  <span>Model confidence: 89%</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
