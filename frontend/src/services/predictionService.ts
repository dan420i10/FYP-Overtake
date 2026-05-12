import { authService } from "./authService";

const API_BASE_URL = "http://localhost:8080/api";

export interface PredictionRow {
  position: number;
  driver: string;
  team: string;
  probability: number;
  confidence: number;
}

export interface PredictMeta {
  defaultSeason: number;
  defaultRound: number;
  defaultEventName: string;
  races: { season: number; round: number; event: string }[];
}

export interface PredictResponse {
  season: number;
  round: number;
  eventName: string;
  userBlend: number | null;
  top10: PredictionRow[];
  topPickDriver: string;
  topPickTeam: string;
  modelConfidence: number;
  analysis: string;
}

async function authHeaders(): Promise<HeadersInit> {
  const token = authService.getToken();
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

export const predictionService = {
  async getMeta(): Promise<PredictMeta> {
    const res = await fetch(`${API_BASE_URL}/predict/meta`, {
      headers: await authHeaders(),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error((data as { message?: string }).message || "Failed to load prediction metadata");
    }
    return data as PredictMeta;
  },

  async predict(body: {
    season?: number;
    round?: number;
    user_weights?: Record<string, number>;
  }): Promise<PredictResponse> {
    const res = await fetch(`${API_BASE_URL}/predict`, {
      method: "POST",
      headers: await authHeaders(),
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error((data as { message?: string }).message || "Prediction request failed");
    }
    return data as PredictResponse;
  },
};
