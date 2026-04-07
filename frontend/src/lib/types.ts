export interface Trip {
  id: string;
  title: string;
  subtitle: string;
  created_at: string;
  updated_at: string;
  style: string;
  print_width: number;
  print_height: number;
  dpi: number;
  show_title: boolean;
  loop_route: boolean;
  api_key_ref: string | null;
}

export interface TripSummary {
  id: string;
  title: string;
  subtitle: string;
  updated_at: string;
  stop_count: number;
  has_output: boolean;
}

export interface Stop {
  id: string;
  trip_id: string;
  sort_order: number;
  city: string;
  label: string | null;
  lat: number;
  lon: number;
  dates: string;
  nights: number;
  highlight: boolean;
  photo_path: string | null;
  created_at: string;
}

export interface TripDetail extends Trip {
  stops: Stop[];
}

export interface RenderStatus {
  status: "pending" | "rendering" | "done" | "error";
  progress?: number;
  styles_complete?: string[];
  error?: string;
}

export interface GeocodeSuggestion {
  display_name: string;
  lat: number;
  lon: number;
}

export interface Settings {
  stadia_api_key_set: boolean;
  default_style: string;
  default_print_width: number;
  default_print_height: number;
  default_dpi: number;
}

export interface StyleConfig {
  name: string;
  label: string;
  requiresApiKey: boolean;
}

export interface PrintPreset {
  label: string;
  width: number;
  height: number;
}
