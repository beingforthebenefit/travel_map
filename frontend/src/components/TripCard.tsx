import { useState } from "react";
import type { TripSummary } from "../lib/types";
import { Button } from "./ui/Button";
import { ConfirmDialog } from "./ui/ConfirmDialog";

interface Props {
  trip: TripSummary;
  onClick: () => void;
  onDelete: () => void;
}

export function TripCard({ trip, onClick, onDelete }: Props) {
  const [confirmOpen, setConfirmOpen] = useState(false);

  return (
    <>
      <div
        className="group rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 hover:shadow-lg transition-shadow cursor-pointer overflow-hidden"
        onClick={onClick}
      >
        <div className="h-32 bg-gradient-to-br from-blue-100 to-blue-200 dark:from-blue-900 dark:to-blue-800 flex items-center justify-center">
          {trip.has_output ? (
            <span className="text-sm text-blue-600 dark:text-blue-300">
              Map generated
            </span>
          ) : (
            <span className="text-sm text-blue-400 dark:text-blue-500">
              No map yet
            </span>
          )}
        </div>
        <div className="p-4">
          <h3 className="font-semibold text-gray-900 dark:text-gray-100 truncate">
            {trip.title}
          </h3>
          {trip.subtitle && (
            <p className="text-sm text-gray-500 dark:text-gray-400 truncate">
              {trip.subtitle}
            </p>
          )}
          <div className="mt-2 flex items-center justify-between text-xs text-gray-400">
            <span>
              {trip.stop_count} stop{trip.stop_count !== 1 ? "s" : ""}
            </span>
            <span>{new Date(trip.updated_at).toLocaleDateString()}</span>
          </div>
          <div className="mt-3 flex justify-end">
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                setConfirmOpen(true);
              }}
            >
              Delete
            </Button>
          </div>
        </div>
      </div>
      <ConfirmDialog
        open={confirmOpen}
        title="Delete Trip"
        message={`Delete "${trip.title}" and all its stops? This cannot be undone.`}
        onConfirm={() => {
          setConfirmOpen(false);
          onDelete();
        }}
        onCancel={() => setConfirmOpen(false)}
      />
    </>
  );
}
