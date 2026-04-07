import type {
  TripSummary,
  TripDetail,
  Trip,
  Stop,
  GeocodeSuggestion,
  Settings,
} from "../lib/types";

const BASE = import.meta.env.VITE_API_URL || "/api/v1";

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const resp = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new ApiError(resp.status, body.detail || resp.statusText);
  }
  if (resp.status === 204) return undefined as T;
  return resp.json();
}

// Trips
export const getTrips = () => request<TripSummary[]>("/trips");

export const createTrip = (title: string, subtitle = "") =>
  request<TripDetail>("/trips", {
    method: "POST",
    body: JSON.stringify({ title, subtitle }),
  });

export const getTrip = (id: string) => request<TripDetail>(`/trips/${id}`);

export const updateTrip = (id: string, data: Partial<Trip>) =>
  request<Trip>(`/trips/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });

export const deleteTrip = (id: string) =>
  request<void>(`/trips/${id}`, { method: "DELETE" });

export const duplicateTrip = (id: string) =>
  request<TripDetail>(`/trips/${id}/duplicate`, { method: "POST" });

export const importTrip = async (file: File) => {
  const form = new FormData();
  form.append("file", file);
  const resp = await fetch(`${BASE}/trips/import`, {
    method: "POST",
    body: form,
  });
  if (!resp.ok) throw new ApiError(resp.status, "Import failed");
  return resp.json() as Promise<TripDetail>;
};

export const exportTrip = (id: string) =>
  `${BASE}/trips/${id}/export`;

// Stops
export const addStop = (
  tripId: string,
  data: { city: string; dates: string; lat?: number; lon?: number; nights?: number; highlight?: boolean },
) =>
  request<Stop>(`/trips/${tripId}/stops`, {
    method: "POST",
    body: JSON.stringify(data),
  });

export const updateStop = (tripId: string, stopId: string, data: Partial<Stop>) =>
  request<Stop>(`/trips/${tripId}/stops/${stopId}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });

export const deleteStop = (tripId: string, stopId: string) =>
  request<void>(`/trips/${tripId}/stops/${stopId}`, { method: "DELETE" });

export const reorderStops = (tripId: string, stopIds: string[]) =>
  request<Stop[]>(`/trips/${tripId}/stops/reorder`, {
    method: "PUT",
    body: JSON.stringify({ stop_ids: stopIds }),
  });

export const uploadPhoto = async (tripId: string, stopId: string, file: File) => {
  const form = new FormData();
  form.append("file", file);
  const resp = await fetch(`${BASE}/trips/${tripId}/stops/${stopId}/photo`, {
    method: "POST",
    body: form,
  });
  if (!resp.ok) throw new ApiError(resp.status, "Upload failed");
  return resp.json() as Promise<Stop>;
};

export const deletePhoto = (tripId: string, stopId: string) =>
  request<void>(`/trips/${tripId}/stops/${stopId}/photo`, { method: "DELETE" });

export const getPhotoThumbUrl = (tripId: string, stopId: string) =>
  `${BASE}/trips/${tripId}/stops/${stopId}/photo/thumb`;

export const getRoadRoute = (tripId: string) =>
  request<{ coordinates: [number, number][] }>(`/trips/${tripId}/road-route`);

// Render
export const startRender = (
  tripId: string,
  options: { style?: string; all_styles?: boolean } = {},
) =>
  request<{ job_id: string }>(`/trips/${tripId}/render`, {
    method: "POST",
    body: JSON.stringify(options),
  });

export const getRenderStatus = (tripId: string) =>
  request<{ status: string; progress?: number; styles_complete?: string[]; error?: string }>(
    `/trips/${tripId}/render/status`,
  );

export const getRenderUrl = (tripId: string, style: string) =>
  `${BASE}/trips/${tripId}/render/${style}.png`;

export const getPreviewUrl = (tripId: string) =>
  `${BASE}/trips/${tripId}/render/preview`;

// Geocode
export const geocode = (q: string) =>
  request<GeocodeSuggestion[]>(`/geocode?q=${encodeURIComponent(q)}`);

// Settings
export const getSettings = () => request<Settings>("/settings");

export const updateSettings = (data: Partial<Settings & { stadia_api_key?: string }>) =>
  request<Settings>("/settings", {
    method: "PUT",
    body: JSON.stringify(data),
  });
