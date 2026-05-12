import { Trophy, Users, Award } from "lucide-react";
import { useEffect, useState } from "react";
import {
  constructorAccentColor,
  fetchConstructorStandings,
  fetchDriverStandings,
  type ConstructorStandingRow,
  type DriverStandingRow,
  type StandingsMeta,
} from "../../services/standingsService";

const emptyStandingsMeta: StandingsMeta = { season: "", round: "" };

export default function Statistics() {
  const [activeTab, setActiveTab] = useState<"drivers" | "constructors">("drivers");
  const [driverRows, setDriverRows] = useState<DriverStandingRow[]>([]);
  const [constructorRows, setConstructorRows] = useState<ConstructorStandingRow[]>([]);
  const [driverMeta, setDriverMeta] = useState<StandingsMeta>(emptyStandingsMeta);
  const [constructorMeta, setConstructorMeta] = useState<StandingsMeta>(emptyStandingsMeta);
  const [driversLoading, setDriversLoading] = useState(true);
  const [constructorsLoading, setConstructorsLoading] = useState(true);
  const [driversError, setDriversError] = useState<string | null>(null);
  const [constructorsError, setConstructorsError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      const [dRes, cRes] = await Promise.allSettled([
        fetchDriverStandings(),
        fetchConstructorStandings(),
      ]);

      if (cancelled) return;

      if (dRes.status === "fulfilled") {
        setDriverRows(dRes.value.rows);
        setDriverMeta(dRes.value.meta);
        setDriversError(null);
      } else {
        setDriversError(dRes.reason instanceof Error ? dRes.reason.message : "Could not load driver standings");
      }
      setDriversLoading(false);

      if (cRes.status === "fulfilled") {
        setConstructorRows(cRes.value.rows);
        setConstructorMeta(cRes.value.meta);
        setConstructorsError(null);
      } else {
        setConstructorsError(
          cRes.reason instanceof Error ? cRes.reason.message : "Could not load constructor standings"
        );
      }
      setConstructorsLoading(false);
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  const standingsSubtitle = (meta: StandingsMeta) => {
    if (!meta.season && !meta.round) return "Live championship data (Jolpica / Ergast)";
    const parts = [`Season ${meta.season}`];
    if (meta.round) parts.push(`after round ${meta.round}`);
    // parts.push("Jolpica / Ergast");
    return parts.join(" · ");
  };

  const leaderConstructorPoints =
    constructorRows.length > 0 ? Math.max(constructorRows[0].points, 1) : 1;

  return (
    <div className="min-h-screen bg-background py-8">
      <div className="container mx-auto px-6">
        <div className="mb-8">
          <h1 className="mb-2 text-4xl font-bold tracking-tight text-foreground">
            Statistics & Standings
          </h1>
          <p className="text-muted-foreground">
            Driver and constructor championship standings
          </p>
        </div>

        <div className="mb-8 flex gap-2 overflow-x-auto rounded-xl bg-secondary/50 p-1">
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

        {activeTab === "drivers" && (
          <div className="overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-card/80 to-secondary/40 backdrop-blur-xl">
            <div className="border-b border-border bg-gradient-to-r from-[#e10600]/10 to-transparent p-6">
              <div className="flex items-center gap-3">
                <Trophy className="h-8 w-8 text-[#ffd700]" />
                <div>
                  <h2 className="text-2xl font-bold text-foreground">
                    {driverMeta.season ? `${driverMeta.season} Driver Standings` : "Driver Standings"}
                  </h2>
                  <p className="text-sm text-muted-foreground">{standingsSubtitle(driverMeta)}</p>
                </div>
              </div>
            </div>
            <div className="p-6">
              {driversLoading ? (
                <div className="flex justify-center py-16 text-muted-foreground">Loading driver standings…</div>
              ) : driversError ? (
                <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-600 dark:text-red-400">
                  {driversError}
                </div>
              ) : (
                <div className="space-y-3">
                  {driverRows.map((driver) => (
                    <div
                      key={driver.driverId}
                      className="flex items-center gap-4 rounded-lg border border-border bg-secondary/30 p-4 transition-all hover:bg-secondary/50"
                    >
                      <div
                        className={`flex h-12 w-12 items-center justify-center rounded-lg font-bold text-white ${
                          driver.position === 1
                            ? "bg-gradient-to-br from-[#ffd700] to-[#ffed4e] text-black"
                            : driver.position === 2
                              ? "bg-gradient-to-br from-[#c0c0c0] to-[#e8e8e8] text-black"
                              : driver.position === 3
                                ? "bg-gradient-to-br from-[#cd7f32] to-[#e8a87c]"
                                : "bg-gradient-to-br from-[#2a2a35] to-[#1f1f28]"
                        }`}
                      >
                        {driver.position}
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
              )}
            </div>
          </div>
        )}

        {activeTab === "constructors" && (
          <div className="overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-card/80 to-secondary/40 backdrop-blur-xl">
            <div className="border-b border-border bg-gradient-to-r from-[#e10600]/10 to-transparent p-6">
              <div className="flex items-center gap-3">
                <Award className="h-8 w-8 text-[#00d4ff]" />
                <div>
                  <h2 className="text-2xl font-bold text-foreground">
                    {constructorMeta.season
                      ? `${constructorMeta.season} Constructor Standings`
                      : "Constructor Standings"}
                  </h2>
                  <p className="text-sm text-muted-foreground">{standingsSubtitle(constructorMeta)}</p>
                </div>
              </div>
            </div>
            <div className="p-6">
              {constructorsLoading ? (
                <div className="flex justify-center py-16 text-muted-foreground">
                  Loading constructor standings…
                </div>
              ) : constructorsError ? (
                <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-600 dark:text-red-400">
                  {constructorsError}
                </div>
              ) : (
                <div className="space-y-3">
                  {constructorRows.map((team) => (
                    <div
                      key={team.constructorId}
                      className="flex items-center gap-4 rounded-lg border border-border bg-secondary/30 p-4 transition-all hover:bg-secondary/50"
                    >
                      <div
                        className={`flex h-12 w-12 items-center justify-center rounded-lg font-bold text-white ${
                          team.position === 1
                            ? "bg-gradient-to-br from-[#ffd700] to-[#ffed4e] text-black"
                            : team.position === 2
                              ? "bg-gradient-to-br from-[#c0c0c0] to-[#e8e8e8] text-black"
                              : team.position === 3
                                ? "bg-gradient-to-br from-[#cd7f32] to-[#e8a87c]"
                                : "bg-gradient-to-br from-[#2a2a35] to-[#1f1f28]"
                        }`}
                      >
                        {team.position}
                      </div>
                      <div className="flex-1">
                        <div className="font-semibold text-foreground">{team.team}</div>
                        <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-secondary/50">
                          <div
                            className="h-full rounded-full transition-all"
                            style={{
                              backgroundColor: constructorAccentColor(team.constructorId),
                              width: `${(team.points / leaderConstructorPoints) * 100}%`,
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
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
