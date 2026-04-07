import type { StyleConfig, PrintPreset } from "./types";

export const STYLES: StyleConfig[] = [
  { name: "watercolor", label: "Stamen Watercolor", requiresApiKey: true },
  { name: "toner", label: "Stamen Toner Lite", requiresApiKey: true },
  { name: "terrain", label: "Stamen Terrain", requiresApiKey: true },
  { name: "positron", label: "CartoDB Positron", requiresApiKey: false },
  { name: "dark", label: "CartoDB Dark Matter", requiresApiKey: false },
  { name: "osm", label: "OpenStreetMap", requiresApiKey: false },
];

export const PRINT_PRESETS: PrintPreset[] = [
  { label: '18" × 12"', width: 18, height: 12 },
  { label: '24" × 18"', width: 24, height: 18 },
  { label: '36" × 24"', width: 36, height: 24 },
];

export const DPI_PRESETS = [
  { label: "Draft (150)", value: 150 },
  { label: "Print (300)", value: 300 },
];

export const ROUTE_STYLES = ["solid", "dashed", "dotted"] as const;

export const TILE_URLS: Record<string, string> = {
  watercolor:
    "https://tiles.stadiamaps.com/tiles/stamen_watercolor/{z}/{x}/{y}.jpg",
  toner:
    "https://tiles.stadiamaps.com/tiles/stamen_toner_lite/{z}/{x}/{y}.png",
  terrain:
    "https://tiles.stadiamaps.com/tiles/stamen_terrain/{z}/{x}/{y}.png",
  positron: "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png",
  dark: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png",
  osm: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
};
