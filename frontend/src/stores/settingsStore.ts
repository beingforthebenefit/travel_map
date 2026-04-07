import { create } from "zustand";
import type { Settings } from "../lib/types";
import * as api from "../api/client";

type Theme = "light" | "dark" | "system";

interface SettingsState {
  settings: Settings | null;
  theme: Theme;
  loading: boolean;

  fetchSettings: () => Promise<void>;
  updateSettings: (data: Partial<Settings & { stadia_api_key?: string }>) => Promise<void>;
  setTheme: (theme: Theme) => void;
}

function applyTheme(theme: Theme) {
  const root = document.documentElement;
  if (theme === "dark" || (theme === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches)) {
    root.classList.add("dark");
  } else {
    root.classList.remove("dark");
  }
}

export const useSettingsStore = create<SettingsState>((set) => ({
  settings: null,
  theme: (localStorage.getItem("theme") as Theme) || "system",
  loading: false,

  fetchSettings: async () => {
    set({ loading: true });
    try {
      const settings = await api.getSettings();
      set({ settings, loading: false });
    } catch {
      set({ loading: false });
    }
  },

  updateSettings: async (data) => {
    try {
      const settings = await api.updateSettings(data);
      set({ settings });
    } catch {
      // silently fail
    }
  },

  setTheme: (theme) => {
    localStorage.setItem("theme", theme);
    applyTheme(theme);
    set({ theme });
  },
}));

// Apply theme on load
applyTheme(useSettingsStore.getState().theme);
