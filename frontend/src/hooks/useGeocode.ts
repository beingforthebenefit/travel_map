import { useState, useCallback, useRef } from "react";
import * as api from "../api/client";
import type { GeocodeSuggestion } from "../lib/types";

export function useGeocode() {
  const [suggestions, setSuggestions] = useState<GeocodeSuggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  const search = useCallback((query: string) => {
    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (query.length < 2) {
      setSuggestions([]);
      return;
    }

    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const results = await api.geocode(query);
        setSuggestions(results);
      } catch {
        setSuggestions([]);
      } finally {
        setLoading(false);
      }
    }, 500);
  }, []);

  const clear = useCallback(() => {
    setSuggestions([]);
    if (debounceRef.current) clearTimeout(debounceRef.current);
  }, []);

  return { suggestions, loading, search, clear };
}
