import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useTripStore } from "../stores/tripStore";
import { useRender } from "../hooks/useRender";
import { useToast } from "../components/ui/Toast";
import { Button } from "../components/ui/Button";
import { Spinner } from "../components/ui/Spinner";
import { MapPanel } from "../components/MapPanel";
import { StopList } from "../components/StopList";
import { AddStop } from "../components/AddStop";
import { SettingsDrawer } from "../components/SettingsDrawer";
import { RenderModal } from "../components/RenderModal";

export function TripEditor() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const { trip, loading, error, fetchTrip, updateTrip } = useTripStore();
  const { status, isRendering, startRender, stopPolling } = useRender(id);

  const [settingsOpen, setSettingsOpen] = useState(false);
  const [renderModalOpen, setRenderModalOpen] = useState(false);
  const [editingTitle, setEditingTitle] = useState(false);
  const [titleValue, setTitleValue] = useState("");
  const [editingSubtitle, setEditingSubtitle] = useState(false);
  const [subtitleValue, setSubtitleValue] = useState("");

  useEffect(() => {
    if (id) fetchTrip(id);
  }, [id, fetchTrip]);

  useEffect(() => {
    if (trip) {
      setTitleValue(trip.title);
      setSubtitleValue(trip.subtitle);
    }
  }, [trip]);

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        handleGenerate();
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [trip]);

  const handleGenerate = useCallback(() => {
    if (!trip || trip.stops.length === 0) {
      toast("Add at least one stop before generating", "error");
      return;
    }
    setRenderModalOpen(true);
    startRender({ style: trip.style });
  }, [trip, startRender, toast]);

  const handleTitleSave = () => {
    if (titleValue.trim() && titleValue !== trip?.title) {
      updateTrip({ title: titleValue.trim() });
    }
    setEditingTitle(false);
  };

  const handleSubtitleSave = () => {
    if (subtitleValue !== trip?.subtitle) {
      updateTrip({ subtitle: subtitleValue });
    }
    setEditingSubtitle(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Spinner className="h-8 w-8" />
      </div>
    );
  }

  if (error || !trip) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4">
        <p className="text-red-500">{error || "Trip not found"}</p>
        <Button variant="secondary" onClick={() => navigate("/")}>
          Back to trips
        </Button>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-50 dark:bg-gray-950">
      {/* Top bar */}
      <header className="border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 px-6 py-3">
        <div className="flex items-center gap-4">
          <Link
            to="/"
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            &larr;
          </Link>
          <div className="flex-1">
            {editingTitle ? (
              <input
                className="text-lg font-bold bg-transparent border-b border-blue-500 outline-none w-full"
                value={titleValue}
                onChange={(e) => setTitleValue(e.target.value)}
                onBlur={handleTitleSave}
                onKeyDown={(e) => e.key === "Enter" && handleTitleSave()}
                autoFocus
              />
            ) : (
              <h1
                className="text-lg font-bold cursor-pointer hover:text-blue-600"
                onClick={() => setEditingTitle(true)}
              >
                {trip.title}
              </h1>
            )}
            {editingSubtitle ? (
              <input
                className="text-sm text-gray-500 bg-transparent border-b border-blue-500 outline-none w-full"
                value={subtitleValue}
                onChange={(e) => setSubtitleValue(e.target.value)}
                onBlur={handleSubtitleSave}
                onKeyDown={(e) => e.key === "Enter" && handleSubtitleSave()}
                autoFocus
              />
            ) : (
              <p
                className="text-sm text-gray-500 cursor-pointer hover:text-blue-500"
                onClick={() => setEditingSubtitle(true)}
              >
                {trip.subtitle || "Click to add subtitle"}
              </p>
            )}
          </div>
          <Button
            variant="ghost"
            onClick={() => setSettingsOpen(true)}
          >
            Settings
          </Button>
          <Button
            onClick={handleGenerate}
            disabled={trip.stops.length === 0 || isRendering}
          >
            {isRendering ? <Spinner className="mr-2" /> : null}
            Generate Map
          </Button>
        </div>
      </header>

      {/* Two-panel layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Map — isolate stacking context so Leaflet z-indices stay contained */}
        <div className="flex-1 relative z-0 isolate">
          <MapPanel
            stops={trip.stops}
            style={trip.style}
            loopRoute={trip.loop_route}
            routeType={trip.route_type}
            tripId={trip.id}
          />
        </div>

        {/* Right: Stop list */}
        <div className="w-96 border-l border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 overflow-y-auto flex flex-col">
          <div className="flex-1">
            <StopList />
          </div>
          <div className="border-t border-gray-200 dark:border-gray-800 p-4">
            <AddStop tripId={trip.id} />
          </div>
        </div>
      </div>

      <SettingsDrawer open={settingsOpen} onClose={() => setSettingsOpen(false)} />
      <RenderModal
        open={renderModalOpen}
        onClose={() => {
          setRenderModalOpen(false);
          stopPolling();
        }}
        tripId={trip.id}
        style={trip.style}
        status={status}
        isRendering={isRendering}
        onRegenerate={handleGenerate}
      />
    </div>
  );
}
