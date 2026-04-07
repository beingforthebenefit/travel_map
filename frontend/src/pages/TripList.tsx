import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import * as api from "../api/client";
import type { TripSummary } from "../lib/types";
import { Button } from "../components/ui/Button";
import { TripCard } from "../components/TripCard";
import { useToast } from "../components/ui/Toast";

export function TripList() {
  const [trips, setTrips] = useState<TripSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { toast } = useToast();

  const fetchTrips = async () => {
    try {
      const data = await api.getTrips();
      setTrips(data);
    } catch {
      toast("Failed to load trips", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrips();
  }, []);

  const handleCreate = async () => {
    try {
      const trip = await api.createTrip("New Trip");
      navigate(`/trips/${trip.id}`);
    } catch {
      toast("Failed to create trip", "error");
    }
  };

  const handleImport = async () => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".yaml,.yml";
    input.onchange = async () => {
      const file = input.files?.[0];
      if (!file) return;
      try {
        const trip = await api.importTrip(file);
        navigate(`/trips/${trip.id}`);
        toast("Trip imported", "success");
      } catch {
        toast("Failed to import trip", "error");
      }
    };
    input.click();
  };

  const handleDelete = async (id: string) => {
    try {
      await api.deleteTrip(id);
      setTrips((prev) => prev.filter((t) => t.id !== id));
      toast("Trip deleted", "success");
    } catch {
      toast("Failed to delete trip", "error");
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <header className="border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold">Travel Map</h1>
          <div className="flex gap-2">
            <Button variant="secondary" onClick={handleImport}>
              Import YAML
            </Button>
            <Button onClick={handleCreate}>New Trip</Button>
          </div>
        </div>
      </header>
      <main className="max-w-6xl mx-auto px-6 py-8">
        {loading ? (
          <p className="text-gray-500">Loading...</p>
        ) : trips.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-gray-500 dark:text-gray-400 mb-4">
              No trips yet. Create one to get started.
            </p>
            <Button onClick={handleCreate}>Create Your First Trip</Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {trips.map((trip) => (
              <TripCard
                key={trip.id}
                trip={trip}
                onClick={() => navigate(`/trips/${trip.id}`)}
                onDelete={() => handleDelete(trip.id)}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
