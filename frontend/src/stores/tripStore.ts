import { create } from "zustand";
import type { TripDetail, Stop } from "../lib/types";
import * as api from "../api/client";

interface TripState {
  trip: TripDetail | null;
  loading: boolean;
  error: string | null;

  fetchTrip: (id: string) => Promise<void>;
  updateTrip: (data: Partial<TripDetail>) => Promise<void>;
  addStop: (data: Parameters<typeof api.addStop>[1]) => Promise<void>;
  updateStop: (stopId: string, data: Partial<Stop>) => Promise<void>;
  removeStop: (stopId: string) => Promise<void>;
  reorderStops: (stopIds: string[]) => void;
  uploadPhoto: (stopId: string, file: File) => Promise<void>;
  deletePhoto: (stopId: string) => Promise<void>;
  reset: () => void;
}

export const useTripStore = create<TripState>((set, get) => ({
  trip: null,
  loading: false,
  error: null,

  fetchTrip: async (id) => {
    set({ loading: true, error: null });
    try {
      const trip = await api.getTrip(id);
      set({ trip, loading: false });
    } catch (e) {
      set({ error: (e as Error).message, loading: false });
    }
  },

  updateTrip: async (data) => {
    const { trip } = get();
    if (!trip) return;
    try {
      const updated = await api.updateTrip(trip.id, data);
      set({ trip: { ...trip, ...updated } });
    } catch (e) {
      set({ error: (e as Error).message });
    }
  },

  addStop: async (data) => {
    const { trip } = get();
    if (!trip) return;
    try {
      const stop = await api.addStop(trip.id, data);
      set({ trip: { ...trip, stops: [...trip.stops, stop] } });
    } catch (e) {
      set({ error: (e as Error).message });
    }
  },

  updateStop: async (stopId, data) => {
    const { trip } = get();
    if (!trip) return;
    try {
      const updated = await api.updateStop(trip.id, stopId, data);
      set({
        trip: {
          ...trip,
          stops: trip.stops.map((s) => (s.id === stopId ? updated : s)),
        },
      });
    } catch (e) {
      set({ error: (e as Error).message });
    }
  },

  removeStop: async (stopId) => {
    const { trip } = get();
    if (!trip) return;
    try {
      await api.deleteStop(trip.id, stopId);
      set({
        trip: { ...trip, stops: trip.stops.filter((s) => s.id !== stopId) },
      });
    } catch (e) {
      set({ error: (e as Error).message });
    }
  },

  reorderStops: (stopIds) => {
    const { trip } = get();
    if (!trip) return;
    // Optimistic update
    const sorted = stopIds
      .map((id, i) => {
        const stop = trip.stops.find((s) => s.id === id);
        return stop ? { ...stop, sort_order: i } : null;
      })
      .filter(Boolean) as Stop[];
    set({ trip: { ...trip, stops: sorted } });
    // Fire and forget the API call
    api.reorderStops(trip.id, stopIds).catch((e) => {
      set({ error: (e as Error).message });
    });
  },

  uploadPhoto: async (stopId, file) => {
    const { trip } = get();
    if (!trip) return;
    try {
      const updated = await api.uploadPhoto(trip.id, stopId, file);
      set({
        trip: {
          ...trip,
          stops: trip.stops.map((s) => (s.id === stopId ? updated : s)),
        },
      });
    } catch (e) {
      set({ error: (e as Error).message });
    }
  },

  deletePhoto: async (stopId) => {
    const { trip } = get();
    if (!trip) return;
    try {
      await api.deletePhoto(trip.id, stopId);
      set({
        trip: {
          ...trip,
          stops: trip.stops.map((s) =>
            s.id === stopId ? { ...s, photo_path: null } : s,
          ),
        },
      });
    } catch (e) {
      set({ error: (e as Error).message });
    }
  },

  reset: () => set({ trip: null, loading: false, error: null }),
}));
