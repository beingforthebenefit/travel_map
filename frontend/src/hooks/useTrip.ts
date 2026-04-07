import { useEffect } from "react";
import { useTripStore } from "../stores/tripStore";

export function useTrip(id: string | undefined) {
  const { trip, loading, error, fetchTrip, reset } = useTripStore();

  useEffect(() => {
    if (id) {
      fetchTrip(id);
    }
    return () => reset();
  }, [id, fetchTrip, reset]);

  return { trip, loading, error };
}
