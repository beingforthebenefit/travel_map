import { useState } from "react";
import { useGeocode } from "../hooks/useGeocode";
import { useTripStore } from "../stores/tripStore";
import { Input } from "./ui/Input";
import { Spinner } from "./ui/Spinner";

interface Props {
  tripId: string;
}

export function AddStop(_props: Props) {
  const [query, setQuery] = useState("");
  const [dates, setDates] = useState("");
  const { suggestions, loading, search, clear } = useGeocode();
  const { addStop } = useTripStore();

  const handleInput = (value: string) => {
    setQuery(value);
    search(value);
  };

  const handleSelect = async (suggestion: (typeof suggestions)[0]) => {
    await addStop({
      city: suggestion.display_name.split(",")[0] ?? suggestion.display_name,
      dates: dates || "",
      lat: suggestion.lat,
      lon: suggestion.lon,
    });
    setQuery("");
    setDates("");
    clear();
  };

  return (
    <div className="space-y-2">
      <div className="relative">
        <Input
          placeholder="Search city to add..."
          value={query}
          onChange={(e) => handleInput(e.target.value)}
        />
        {loading && (
          <div className="absolute right-3 top-2.5">
            <Spinner className="h-4 w-4" />
          </div>
        )}
        {suggestions.length > 0 && (
          <div className="absolute z-10 mt-1 w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-lg max-h-48 overflow-auto">
            {suggestions.map((s, i) => (
              <button
                key={i}
                className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 dark:hover:bg-gray-700 truncate"
                onClick={() => handleSelect(s)}
              >
                {s.display_name}
              </button>
            ))}
          </div>
        )}
      </div>
      <Input
        placeholder="Dates (e.g. Mar 22-24)"
        value={dates}
        onChange={(e) => setDates(e.target.value)}
      />
    </div>
  );
}
