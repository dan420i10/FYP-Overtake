import { useNavigate } from "react-router";
import { Trophy, TrendingUp, Globe, Users } from "lucide-react";

export default function Dashboard() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background">
      <div className="relative h-[600px] overflow-hidden">
        <img
          src="https://images.unsplash.com/photo-1540747913346-19e32dc3e97e?q=80&w=2000"
          alt="F1 Racing Track"
          className="absolute inset-0 h-full w-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-black/70 via-black/50 to-background"></div>

        <div className="relative flex h-full flex-col items-center justify-center px-6 text-center">
          <img
            src="https://upload.wikimedia.org/wikipedia/commons/3/33/F1.svg"
            alt="F1 Logo"
            className="mb-8 h-20 w-auto opacity-90"
          />
          <h1 className="mb-4 text-6xl font-bold tracking-tight text-white md:text-7xl lg:text-8xl">
            FORMULA 1
          </h1>
          <p className="max-w-3xl text-lg text-gray-200 md:text-xl">
            The pinnacle of motorsport. Experience the thrill, understand the sport,
            <br />
            and see AI-powered predictions based on real-time race analysis.
          </p>
          <button
            onClick={() => navigate("/predictions")}
            className="mt-8 rounded-lg bg-[#e10600] px-8 py-4 text-lg font-semibold text-white shadow-2xl shadow-[#e10600]/30 transition-all hover:bg-[#c00500] hover:shadow-[#e10600]/50"
          >
            View AI Predictions
          </button>
        </div>
      </div>

      <div className="container mx-auto px-6 py-16">
        <div className="mb-16 overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-[#e10600]/10 to-card backdrop-blur-xl">
          <div className="grid gap-8 p-8 md:grid-cols-2 md:p-12">
            <div>
              <h3 className="mb-4 text-3xl font-bold text-foreground">
                See AI Predictions
              </h3>
              <p className="mb-6 text-lg leading-relaxed text-muted-foreground">
                Our AI model analyzes race data, driver performance, team strategies, and track conditions.
                Adjust the prediction factors to see how different variables affect the race outcome predictions.
              </p>
              <button
                onClick={() => navigate("/predictions")}
                className="rounded-lg bg-gradient-to-r from-[#e10600] to-[#c00500] px-6 py-3 font-semibold text-white shadow-xl shadow-[#e10600]/30 transition-all hover:shadow-2xl hover:shadow-[#e10600]/40"
              >
                Generate Predictions
              </button>
            </div>
            <div className="flex items-center justify-center">
              <img
                src="https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?q=80&w=600"
                alt="F1 Car"
                className="h-64 w-full rounded-xl object-cover shadow-2xl"
              />
            </div>
          </div>
        </div>

        <div className="mb-12 text-center">
          <div className="mb-4 flex items-center justify-center gap-2">
            <Trophy className="h-8 w-8 text-[#ffd700]" />
            <h2 className="text-3xl font-bold text-foreground md:text-4xl">
              What is Formula 1?
            </h2>
          </div>
        </div>

        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
          <div className="group overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-card to-secondary/40 p-6 backdrop-blur-xl transition-all hover:shadow-2xl hover:shadow-[#e10600]/10">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br from-[#e10600] to-[#a00500]">
              <Trophy className="h-6 w-6 text-white" />
            </div>
            <h3 className="mb-3 text-xl font-bold text-[#e10600]">The Beginning</h3>
            <p className="leading-relaxed text-muted-foreground">
              Formula 1 was founded in <span className="font-semibold text-foreground">1950</span> as the world's
              premier motorsport championship. Starting with just 7 races, it has
              evolved into a global phenomenon showcasing cutting-edge technology and
              exceptional driver talent.
            </p>
          </div>

          <div className="group overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-card to-secondary/40 p-6 backdrop-blur-xl transition-all hover:shadow-2xl hover:shadow-[#00d4ff]/10">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br from-[#00d4ff] to-[#0099cc]">
              <Globe className="h-6 w-6 text-white" />
            </div>
            <h3 className="mb-3 text-xl font-bold text-[#00d4ff]">Today's F1</h3>
            <p className="leading-relaxed text-muted-foreground">
              Modern F1 features <span className="font-semibold text-foreground">20 drivers</span> competing across{" "}
              <span className="font-semibold text-foreground">24+ races</span> on 5 continents. From the streets of
              Monaco to the high-speed circuits of Monza, each race delivers unmatched
              excitement and drama.
            </p>
          </div>

          <div className="group overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-card to-secondary/40 p-6 backdrop-blur-xl transition-all hover:shadow-2xl hover:shadow-[#00ff88]/10">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br from-[#00ff88] to-[#00cc66]">
              <TrendingUp className="h-6 w-6 text-white" />
            </div>
            <h3 className="mb-3 text-xl font-bold text-[#00ff88]">Technology</h3>
            <p className="leading-relaxed text-muted-foreground">
              F1 cars are engineering marvels, featuring hybrid power units producing over{" "}
              <span className="font-semibold text-foreground">1,000 horsepower</span>, advanced aerodynamics, and
              telemetry systems that transmit real-time data to teams for split-second
              strategy decisions.
            </p>
          </div>

          <div className="group overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-card to-secondary/40 p-6 backdrop-blur-xl transition-all hover:shadow-2xl hover:shadow-[#ffd700]/10">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-gradient-to-br from-[#ffd700] to-[#ffed4e]">
              <Users className="h-6 w-6 text-black" />
            </div>
            <h3 className="mb-3 text-xl font-bold text-[#ffd700]">The Teams</h3>
            <p className="leading-relaxed text-muted-foreground">
              Ten teams battle for supremacy, from legendary names like{" "}
              <span className="font-semibold text-foreground">Ferrari</span> and{" "}
              <span className="font-semibold text-foreground">Mercedes</span> to rising challengers. Each team
              employs hundreds of engineers and mechanics working tirelessly to gain
              every competitive advantage.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
