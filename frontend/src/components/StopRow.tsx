import { useState, useRef } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import type { Stop } from "../lib/types";
import { useTripStore } from "../stores/tripStore";
import { ConfirmDialog } from "./ui/ConfirmDialog";

interface Props {
  stop: Stop;
  index: number;
}

export function StopRow({ stop, index }: Props) {
  const { updateStop, removeStop, uploadPhoto, deletePhoto } = useTripStore();
  const [editingCity, setEditingCity] = useState(false);
  const [cityValue, setCityValue] = useState(stop.city);
  const [editingDates, setEditingDates] = useState(false);
  const [datesValue, setDatesValue] = useState(stop.dates);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const { attributes, listeners, setNodeRef, transform, transition, isDragging } =
    useSortable({ id: stop.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const handleCitySave = () => {
    if (cityValue.trim() && cityValue !== stop.city) {
      updateStop(stop.id, { city: cityValue.trim() });
    }
    setEditingCity(false);
  };

  const handleDatesSave = () => {
    if (datesValue !== stop.dates) {
      updateStop(stop.id, { dates: datesValue });
    }
    setEditingDates(false);
  };

  const handlePhotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadPhoto(stop.id, file);
  };

  return (
    <>
      <div ref={setNodeRef} style={style} className="flex items-start gap-3 px-4 py-3">
        {/* Drag handle */}
        <button
          className="mt-1 cursor-grab text-gray-300 hover:text-gray-500 dark:text-gray-600 dark:hover:text-gray-400"
          {...attributes}
          {...listeners}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <circle cx="5" cy="3" r="1.5" />
            <circle cx="11" cy="3" r="1.5" />
            <circle cx="5" cy="8" r="1.5" />
            <circle cx="11" cy="8" r="1.5" />
            <circle cx="5" cy="13" r="1.5" />
            <circle cx="11" cy="13" r="1.5" />
          </svg>
        </button>

        {/* Number */}
        <span className="mt-1 text-xs font-bold text-gray-400 w-5 text-center">
          {index + 1}
        </span>

        {/* Photo thumbnail */}
        <button
          className="w-10 h-10 rounded-full bg-gray-100 dark:bg-gray-800 flex-shrink-0 flex items-center justify-center overflow-hidden border-2 border-gray-200 dark:border-gray-700 hover:border-blue-400"
          onClick={() => fileRef.current?.click()}
          title={stop.photo_path ? "Replace photo" : "Add photo"}
        >
          {stop.photo_path ? (
            <span className="text-xs text-green-600">img</span>
          ) : (
            <span className="text-gray-400 text-lg">+</span>
          )}
        </button>
        <input
          ref={fileRef}
          type="file"
          accept="image/jpeg,image/png"
          className="hidden"
          onChange={handlePhotoChange}
        />

        {/* City & dates */}
        <div className="flex-1 min-w-0">
          {editingCity ? (
            <input
              className="font-medium text-sm bg-transparent border-b border-blue-500 outline-none w-full"
              value={cityValue}
              onChange={(e) => setCityValue(e.target.value)}
              onBlur={handleCitySave}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleCitySave();
                if (e.key === "Escape") { setCityValue(stop.city); setEditingCity(false); }
              }}
              autoFocus
            />
          ) : (
            <p
              className="font-medium text-sm cursor-pointer hover:text-blue-600 truncate"
              onClick={() => setEditingCity(true)}
            >
              {stop.label || stop.city}
            </p>
          )}
          {editingDates ? (
            <input
              className="text-xs text-gray-500 bg-transparent border-b border-blue-500 outline-none w-full"
              value={datesValue}
              onChange={(e) => setDatesValue(e.target.value)}
              onBlur={handleDatesSave}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleDatesSave();
                if (e.key === "Escape") { setDatesValue(stop.dates); setEditingDates(false); }
              }}
              autoFocus
            />
          ) : (
            <p
              className="text-xs text-gray-500 cursor-pointer hover:text-blue-500"
              onClick={() => setEditingDates(true)}
            >
              {stop.dates || "Add dates"}
            </p>
          )}
          <p className="text-xs text-gray-300 dark:text-gray-600 mt-0.5">
            {stop.lat.toFixed(4)}, {stop.lon.toFixed(4)}
          </p>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1 mt-1">
          {/* Highlight toggle */}
          <button
            className={`text-sm ${stop.highlight ? "text-yellow-500" : "text-gray-300 dark:text-gray-600"} hover:text-yellow-500`}
            onClick={() => updateStop(stop.id, { highlight: !stop.highlight })}
            title="Toggle highlight"
          >
            &#9733;
          </button>

          {/* Delete photo */}
          {stop.photo_path && (
            <button
              className="text-xs text-gray-300 hover:text-red-500"
              onClick={() => deletePhoto(stop.id)}
              title="Remove photo"
            >
              &times;
            </button>
          )}

          {/* Delete stop */}
          <button
            className="text-xs text-gray-300 hover:text-red-500 ml-1"
            onClick={() => setConfirmDelete(true)}
            title="Delete stop"
          >
            &#128465;
          </button>
        </div>
      </div>
      <ConfirmDialog
        open={confirmDelete}
        title="Delete Stop"
        message={`Delete "${stop.city}"?`}
        onConfirm={() => { setConfirmDelete(false); removeStop(stop.id); }}
        onCancel={() => setConfirmDelete(false)}
      />
    </>
  );
}
