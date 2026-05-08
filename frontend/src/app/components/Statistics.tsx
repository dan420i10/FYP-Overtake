import { CheckCircle, XCircle, AlertCircle, Calendar, Trophy, Target, Users, Award } from "lucide-react";
import { useState } from "react";

const previousPredictions = [
  {
    id: 1,
    race: "China Grand Prix",
    date: "April 20, 2026",
    circuit: "Shanghai International Circuit",
    predicted: [
      "Max Verstappen",
      "Charles Leclerc",
      "Lando Norris",
      "Lewis Hamilton",
      "George Russell",
      "Carlos Sainz",
      "Sergio Perez",
      "Fernando Alonso",
      "Oscar Piastri",
      "Lance Stroll",
    ],
    actual: [
      "Max Verstappen",
      "Charles Leclerc",
      "Lando Norris",
      "Carlos Sainz",
      "Lewis Hamilton",
      "George Russell",
      "Sergio Perez",
      "Fernando Alonso",
      "Oscar Piastri",
      "Lance Stroll",
    ],
    status: "correct",
    points: 68,
    accuracy: 90,
  },
  {
    id: 2,
    race: "Japan Grand Prix",
    date: "April 13, 2026",
    circuit: "Suzuka Circuit",
    predicted: [
      "Max Verstappen",
      "Lando Norris",
      "Charles Leclerc",
      "Lewis Hamilton",
      "Carlos Sainz",
      "George Russell",
      "Sergio Perez",
      "Fernando Alonso",
      "Oscar Piastri",
      "Yuki Tsunoda",
    ],
    actual: [
      "Max Verstappen",
      "Charles Leclerc",
      "Lando Norris",
      "Carlos Sainz",
      "Lewis Hamilton",
      "George Russell",
      "Fernando Alonso",
      "Sergio Perez",
      "Oscar Piastri",
      "Yuki Tsunoda",
    ],
    status: "partial",
    points: 52,
    accuracy: 75,
  },
];

const driverStandings = [
  { pos: 1, driver: "Max Verstappen", team: "Red Bull Racing", points: 186, color: "#1e3a8a" },
  { pos: 2, driver: "Charles Leclerc", team: "Ferrari", points: 154, color: "#dc2626" },
  { pos: 3, driver: "Lando Norris", team: "McLaren", points: 142, color: "#f97316" },
  { pos: 4, driver: "Carlos Sainz", team: "Ferrari", points: 128, color: "#dc2626" },
  { pos: 5, driver: "Lewis Hamilton", team: "Mercedes", points: 118, color: "#00d4cc" },
  { pos: 6, driver: "George Russell", team: "Mercedes", points: 106, color: "#00d4cc" },
  { pos: 7, driver: "Sergio Perez", team: "Red Bull Racing", points: 98, color: "#1e3a8a" },
  { pos: 8, driver: "Fernando Alonso", team: "Aston Martin", points: 82, color: "#15803d" },
  { pos: 9, driver: "Oscar Piastri", team: "McLaren", points: 74, color: "#f97316" },
  { pos: 10, driver: "Lance Stroll", team: "Aston Martin", points: 56, color: "#15803d" },
  { pos: 11, driver: "Pierre Gasly", team: "Alpine", points: 48, color: "#3b82f6" },
  { pos: 12, driver: "Esteban Ocon", team: "Alpine", points: 42, color: "#3b82f6" },
  { pos: 13, driver: "Alex Albon", team: "Williams", points: 38, color: "#1e40af" },
  { pos: 14, driver: "Yuki Tsunoda", team: "RB", points: 32, color: "#4338ca" },
  { pos: 15, driver: "Daniel Ricciardo", team: "RB", points: 28, color: "#4338ca" },
  { pos: 16, driver: "Nico Hulkenberg", team: "Haas", points: 24, color: "#6b7280" },
  { pos: 17, driver: "Kevin Magnussen", team: "Haas", points: 18, color: "#6b7280" },
  { pos: 18, driver: "Valtteri Bottas", team: "Sauber", points: 14, color: "#22c55e" },
  { pos: 19, driver: "Zhou Guanyu", team: "Sauber", points: 10, color: "#22c55e" },
  { pos: 20, driver: "Logan Sargeant", team: "Williams", points: 8, color: "#1e40af" },
  { pos: 21, driver: "Liam Lawson", team: "Cadillac", points: 6, color: "#a855f7" },
  { pos: 22, driver: "Oliver Bearman", team: "Cadillac", points: 4, color: "#a855f7" },
];

const constructorStandings = [
  { pos: 1, team: "Red Bull Racing", points: 284, color: "#1e3a8a" },
  { pos: 2, team: "Ferrari", points: 282, color: "#dc2626" },
  { pos: 3, team: "Mercedes", points: 224, color: "#00d4cc" },
  { pos: 4, team: "McLaren", points: 216, color: "#f97316" },
  { pos: 5, team: "Aston Martin", points: 138, color: "#15803d" },
  { pos: 6, team: "Alpine", points: 90, color: "#3b82f6" },
  { pos: 7, team: "RB", points: 60, color: "#4338ca" },
  { pos: 8, team: "Williams", points: 46, color: "#1e40af" },
  { pos: 9, team: "Haas", points: 42, color: "#6b7280" },
  { pos: 10, team: "Sauber", points: 24, color: "#22c55e" },
  { pos: 11, team: "Cadillac", points: 10, color: "#a855f7" },
];

export default function Statistics() {
  const [activeTab, setActiveTab] = useState<"predictions" | "drivers" | "constructors">("predictions");

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "correct":
        return <CheckCircle className="h-5 w-5 text-[#00ff88]" />;
      case "partial":
        return <AlertCircle className="h-5 w-5 text-[#ffd700]" />;
      case "incorrect":
        return <XCircle className="h-5 w-5 text-[#ef4444]" />;
      default:
        return null;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "correct":
        return "border-[#00ff88]/30 bg-[#00ff88]/5";
      case "partial":
        return "border-[#ffd700]/30 bg-[#ffd700]/5";
      case "incorrect":
        return "border-[#ef4444]/30 bg-[#ef4444]/5";
      default:
        return "border-border";
    }
  };

  const totalPoints = previousPredictions.reduce((sum, pred) => sum + pred.points, 0);
  const avgAccuracy = Math.round(
    previousPredictions.reduce((sum, pred) => sum + pred.accuracy, 0) / previousPredictions.length
  );
  const correctPredictions = previousPredictions.filter((p) => p.status === "correct").length;

  return (
    <div className="min-h-screen bg-background py-8">
      <div className="container mx-auto px-6">
        <div className="mb-8">
          <h1 className="mb-2 text-4xl font-bold tracking-tight text-foreground">
            Statistics & Standings
          </h1>
          <p className="text-muted-foreground">
            Review AI predictions, driver standings, and constructor championship
          </p>
        </div>

        <div className="mb-8 flex gap-2 overflow-x-auto rounded-xl bg-secondary/50 p-1">
          <button
            onClick={() => setActiveTab("predictions")}
            className={`flex-1 whitespace-nowrap rounded-lg px-6 py-3 transition-all ${
              activeTab === "predictions"
                ? "bg-[#e10600] text-white shadow-lg shadow-[#e10600]/20"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <div className="flex items-center justify-center gap-2">
              <Target className="h-5 w-5" />
              <span>Prediction History</span>
            </div>
          </button>
          <button
            onClick={() => setActiveTab("drivers")}
            className={`flex-1 whitespace-nowrap rounded-lg px-6 py-3 transition-all ${
              activeTab === "drivers"
                ? "bg-[#e10600] text-white shadow-lg shadow-[#e10600]/20"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <div className="flex items-center justify-center gap-2">
              <Trophy className="h-5 w-5" />
              <span>Driver Standings</span>
            </div>
          </button>
          <button
            onClick={() => setActiveTab("constructors")}
            className={`flex-1 whitespace-nowrap rounded-lg px-6 py-3 transition-all ${
              activeTab === "constructors"
                ? "bg-[#e10600] text-white shadow-lg shadow-[#e10600]/20"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <div className="flex items-center justify-center gap-2">
              <Users className="h-5 w-5" />
              <span>Constructor Standings</span>
            </div>
          </button>
        </div>

        {activeTab === "predictions" && (
          <>
            <div className="mb-8 grid gap-6 md:grid-cols-3">
              <div className="overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-card/80 to-secondary/40 p-6 backdrop-blur-xl">
                <div className="mb-2 flex items-center gap-2 text-muted-foreground">
                  <Trophy className="h-5 w-5 text-[#ffd700]" />
                  <span className="text-sm">Total Points Earned</span>
                </div>
                <div className="text-3xl font-bold text-foreground">{totalPoints}</div>
                <div className="mt-2 text-sm text-muted-foreground">
                  From {previousPredictions.length} races
                </div>
              </div>

              <div className="overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-card/80 to-secondary/40 p-6 backdrop-blur-xl">
                <div className="mb-2 flex items-center gap-2 text-muted-foreground">
                  <Target className="h-5 w-5 text-[#00d4ff]" />
                  <span className="text-sm">Average Accuracy</span>
                </div>
                <div className="text-3xl font-bold text-foreground">{avgAccuracy}%</div>
                <div className="mt-2 text-sm text-muted-foreground">
                  Across all predictions
                </div>
              </div>

              <div className="overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-card/80 to-secondary/40 p-6 backdrop-blur-xl">
                <div className="mb-2 flex items-center gap-2 text-muted-foreground">
                  <CheckCircle className="h-5 w-5 text-[#00ff88]" />
                  <span className="text-sm">Perfect Predictions</span>
                </div>
                <div className="text-3xl font-bold text-foreground">{correctPredictions}</div>
                <div className="mt-2 text-sm text-muted-foreground">
                  AI model 100% accuracy
                </div>
              </div>
            </div>

            <div className="space-y-6">
              {previousPredictions.map((prediction) => (
                <div
                  key={prediction.id}
                  className={`overflow-hidden rounded-2xl border backdrop-blur-xl ${getStatusColor(
                    prediction.status
                  )}`}
                >
                  <div className="p-6">
                    <div className="mb-4 flex items-start justify-between">
                      <div>
                        <div className="mb-2 flex items-center gap-3">
                          <h3 className="text-2xl font-bold text-foreground">
                            {prediction.race}
                          </h3>
                          {getStatusIcon(prediction.status)}
                        </div>
                        <div className="flex items-center gap-4 text-sm text-muted-foreground">
                          <div className="flex items-center gap-1">
                            <Calendar className="h-4 w-4" />
                            <span>{prediction.date}</span>
                          </div>
                          <span>•</span>
                          <span>{prediction.circuit}</span>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="mb-1 text-3xl font-bold text-foreground">
                          +{prediction.points}
                        </div>
                        <div className="text-sm text-muted-foreground">points</div>
                      </div>
                    </div>

                    <div className="grid gap-6 md:grid-cols-2">
                      <div className="rounded-lg border border-border bg-secondary/30 p-4">
                        <h4 className="mb-3 text-sm font-semibold text-muted-foreground">
                          AI MODEL PREDICTION (TOP 10)
                        </h4>
                        <div className="space-y-2">
                          {prediction.predicted.map((driver, index) => (
                            <div key={index} className="flex items-center gap-3">
                              <div
                                className={`flex h-7 w-7 items-center justify-center rounded-lg text-xs font-bold ${
                                  index === 0
                                    ? "bg-gradient-to-br from-[#ffd700] to-[#ffed4e] text-black"
                                    : index === 1
                                    ? "bg-gradient-to-br from-[#c0c0c0] to-[#e8e8e8] text-black"
                                    : index === 2
                                    ? "bg-gradient-to-br from-[#cd7f32] to-[#e8a87c] text-white"
                                    : "bg-secondary/50 text-foreground"
                                }`}
                              >
                                {index + 1}
                              </div>
                              <span className="flex-1 text-sm text-foreground">{driver}</span>
                              {prediction.predicted[index] === prediction.actual[index] && (
                                <CheckCircle className="h-4 w-4 text-[#00ff88]" />
                              )}
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="rounded-lg border border-border bg-secondary/30 p-4">
                        <h4 className="mb-3 text-sm font-semibold text-muted-foreground">
                          ACTUAL RESULT (TOP 10)
                        </h4>
                        <div className="space-y-2">
                          {prediction.actual.map((driver, index) => (
                            <div key={index} className="flex items-center gap-3">
                              <div
                                className={`flex h-7 w-7 items-center justify-center rounded-lg text-xs font-bold ${
                                  index === 0
                                    ? "bg-gradient-to-br from-[#ffd700] to-[#ffed4e] text-black"
                                    : index === 1
                                    ? "bg-gradient-to-br from-[#c0c0c0] to-[#e8e8e8] text-black"
                                    : index === 2
                                    ? "bg-gradient-to-br from-[#cd7f32] to-[#e8a87c] text-white"
                                    : "bg-secondary/50 text-foreground"
                                }`}
                              >
                                {index + 1}
                              </div>
                              <span className="flex-1 text-sm text-foreground">{driver}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div className="mt-4 flex items-center justify-between rounded-lg bg-secondary/30 p-3">
                      <span className="text-sm text-muted-foreground">Model Accuracy</span>
                      <div className="flex items-center gap-3">
                        <div className="h-2 w-32 overflow-hidden rounded-full bg-secondary/50">
                          <div
                            className="h-full rounded-full bg-gradient-to-r from-[#00ff88] to-[#00d4ff]"
                            style={{ width: `${prediction.accuracy}%` }}
                          ></div>
                        </div>
                        <span className="font-semibold text-foreground">
                          {prediction.accuracy}%
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}

        {activeTab === "drivers" && (
          <div className="overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-card/80 to-secondary/40 backdrop-blur-xl">
            <div className="border-b border-border bg-gradient-to-r from-[#e10600]/10 to-transparent p-6">
              <div className="flex items-center gap-3">
                <Trophy className="h-8 w-8 text-[#ffd700]" />
                <div>
                  <h2 className="text-2xl font-bold text-foreground">2026 Driver Standings</h2>
                  <p className="text-sm text-muted-foreground">Current championship positions</p>
                </div>
              </div>
            </div>
            <div className="p-6">
              <div className="space-y-3">
                {driverStandings.map((driver) => (
                  <div
                    key={driver.pos}
                    className="flex items-center gap-4 rounded-lg border border-border bg-secondary/30 p-4 transition-all hover:bg-secondary/50"
                  >
                    <div
                      className={`flex h-12 w-12 items-center justify-center rounded-lg font-bold text-white ${
                        driver.pos === 1
                          ? "bg-gradient-to-br from-[#ffd700] to-[#ffed4e] text-black"
                          : driver.pos === 2
                          ? "bg-gradient-to-br from-[#c0c0c0] to-[#e8e8e8] text-black"
                          : driver.pos === 3
                          ? "bg-gradient-to-br from-[#cd7f32] to-[#e8a87c]"
                          : "bg-gradient-to-br from-[#2a2a35] to-[#1f1f28]"
                      }`}
                    >
                      {driver.pos}
                    </div>
                    <div className="flex-1">
                      <div className="font-semibold text-foreground">{driver.driver}</div>
                      <div className="text-sm text-muted-foreground">{driver.team}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-foreground">{driver.points}</div>
                      <div className="text-xs text-muted-foreground">points</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === "constructors" && (
          <div className="overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-card/80 to-secondary/40 backdrop-blur-xl">
            <div className="border-b border-border bg-gradient-to-r from-[#e10600]/10 to-transparent p-6">
              <div className="flex items-center gap-3">
                <Award className="h-8 w-8 text-[#00d4ff]" />
                <div>
                  <h2 className="text-2xl font-bold text-foreground">2026 Constructor Standings</h2>
                  <p className="text-sm text-muted-foreground">Team championship positions</p>
                </div>
              </div>
            </div>
            <div className="p-6">
              <div className="space-y-3">
                {constructorStandings.map((team) => (
                  <div
                    key={team.pos}
                    className="flex items-center gap-4 rounded-lg border border-border bg-secondary/30 p-4 transition-all hover:bg-secondary/50"
                  >
                    <div
                      className={`flex h-12 w-12 items-center justify-center rounded-lg font-bold text-white ${
                        team.pos === 1
                          ? "bg-gradient-to-br from-[#ffd700] to-[#ffed4e] text-black"
                          : team.pos === 2
                          ? "bg-gradient-to-br from-[#c0c0c0] to-[#e8e8e8] text-black"
                          : team.pos === 3
                          ? "bg-gradient-to-br from-[#cd7f32] to-[#e8a87c]"
                          : "bg-gradient-to-br from-[#2a2a35] to-[#1f1f28]"
                      }`}
                    >
                      {team.pos}
                    </div>
                    <div className="flex-1">
                      <div className="font-semibold text-foreground">{team.team}</div>
                      <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-secondary/50">
                        <div
                          className="h-full rounded-full transition-all"
                          style={{
                            backgroundColor: team.color,
                            width: `${(team.points / constructorStandings[0].points) * 100}%`,
                          }}
                        ></div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-foreground">{team.points}</div>
                      <div className="text-xs text-muted-foreground">points</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
