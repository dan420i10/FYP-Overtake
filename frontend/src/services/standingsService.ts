/** Jolpica Ergast-compatible API (current season standings). */

export const ERGAST_DRIVER_STANDINGS_URL =
  "https://api.jolpi.ca/ergast/f1/current/driverStandings.json";
export const ERGAST_CONSTRUCTOR_STANDINGS_URL =
  "https://api.jolpi.ca/ergast/f1/current/constructorStandings.json";

export interface StandingsMeta {
  season: string;
  round: string;
}

export interface DriverStandingRow {
  position: number;
  driver: string;
  team: string;
  points: number;
  driverId: string;
}

export interface ConstructorStandingRow {
  position: number;
  team: string;
  points: number;
  constructorId: string;
}

function parseListMeta(lists: unknown): StandingsMeta {
  const l0 = Array.isArray(lists) ? (lists[0] as Record<string, unknown> | undefined) : undefined;
  return {
    season: String(l0?.season ?? ""),
    round: String(l0?.round ?? ""),
  };
}

export async function fetchDriverStandings(): Promise<{
  meta: StandingsMeta;
  rows: DriverStandingRow[];
}> {
  const res = await fetch(ERGAST_DRIVER_STANDINGS_URL);
  if (!res.ok) {
    throw new Error(`Driver standings request failed (${res.status})`);
  }
  const data = (await res.json()) as {
    MRData?: { StandingsTable?: { StandingsLists?: unknown[] } };
  };
  const lists = data?.MRData?.StandingsTable?.StandingsLists;
  const meta = parseListMeta(lists);
  const raw = (lists?.[0] as { DriverStandings?: unknown[] } | undefined)?.DriverStandings ?? [];

  const rows: DriverStandingRow[] = raw.map((entry) => {
    const ds = entry as {
      position?: string;
      points?: string;
      Driver?: { givenName?: string; familyName?: string; driverId?: string };
      Constructors?: { name?: string }[];
    };
    const driver = [ds.Driver?.givenName, ds.Driver?.familyName].filter(Boolean).join(" ").trim();
    return {
      position: Number(ds.position),
      driver: driver || "Unknown",
      team: ds.Constructors?.[0]?.name ?? "",
      points: Number(ds.points),
      driverId: String(ds.Driver?.driverId ?? ds.position ?? ""),
    };
  });

  return { meta, rows };
}

export async function fetchConstructorStandings(): Promise<{
  meta: StandingsMeta;
  rows: ConstructorStandingRow[];
}> {
  const res = await fetch(ERGAST_CONSTRUCTOR_STANDINGS_URL);
  if (!res.ok) {
    throw new Error(`Constructor standings request failed (${res.status})`);
  }
  const data = (await res.json()) as {
    MRData?: { StandingsTable?: { StandingsLists?: unknown[] } };
  };
  const lists = data?.MRData?.StandingsTable?.StandingsLists;
  const meta = parseListMeta(lists);
  const raw =
    (lists?.[0] as { ConstructorStandings?: unknown[] } | undefined)?.ConstructorStandings ?? [];

  const rows: ConstructorStandingRow[] = raw.map((entry) => {
    const cs = entry as {
      position?: string;
      points?: string;
      Constructor?: { name?: string; constructorId?: string };
    };
    return {
      position: Number(cs.position),
      team: cs.Constructor?.name ?? "Unknown",
      points: Number(cs.points),
      constructorId: String(cs.Constructor?.constructorId ?? cs.position ?? ""),
    };
  });

  return { meta, rows };
}

/** Bar accent colours keyed by Ergast constructorId */
export function constructorAccentColor(constructorId: string): string {
  const id = constructorId.toLowerCase();
  const map: Record<string, string> = {
    mercedes: "#00d4cc",
    ferrari: "#dc2626",
    mclaren: "#f97316",
    red_bull: "#1e3a8a",
    aston_martin: "#15803d",
    alpine: "#3b82f6",
    rb: "#4338ca",
    williams: "#1e40af",
    haas: "#6b7280",
    sauber: "#22c55e",
    cadillac: "#a855f7",
    audi: "#94a3b8",
    kick_sauber: "#22c55e",
    racing_bulls: "#4338ca",
  };
  return map[id] ?? "#e10600";
}
