import { useEffect } from "react";
import { Drawer } from "./ui/Drawer";
import { Input } from "./ui/Input";
import { Button } from "./ui/Button";
import { StylePicker } from "./StylePicker";
import { useTripStore } from "../stores/tripStore";
import { useSettingsStore } from "../stores/settingsStore";
import { PRINT_PRESETS, DPI_PRESETS } from "../lib/constants";
import { useToast } from "./ui/Toast";

interface Props {
  open: boolean;
  onClose: () => void;
}

export function SettingsDrawer({ open, onClose }: Props) {
  const { trip, updateTrip } = useTripStore();
  const { settings, fetchSettings, updateSettings, theme, setTheme } = useSettingsStore();
  const { toast } = useToast();

  useEffect(() => {
    if (open) fetchSettings();
  }, [open, fetchSettings]);

  if (!trip) return null;

  return (
    <Drawer open={open} onClose={onClose} title="Settings">
      <div className="space-y-8">
        {/* Map Style */}
        <section>
          <h3 className="text-sm font-semibold mb-3">Map Style</h3>
          <StylePicker
            active={trip.style}
            hasApiKey={settings?.stadia_api_key_set ?? false}
            onSelect={(style) => updateTrip({ style })}
          />
        </section>

        {/* Print Size */}
        <section>
          <h3 className="text-sm font-semibold mb-3">Print Size</h3>
          <div className="flex flex-wrap gap-2 mb-3">
            {PRINT_PRESETS.map((p) => (
              <Button
                key={p.label}
                variant={
                  trip.print_width === p.width && trip.print_height === p.height
                    ? "primary"
                    : "secondary"
                }
                size="sm"
                onClick={() =>
                  updateTrip({ print_width: p.width, print_height: p.height })
                }
              >
                {p.label}
              </Button>
            ))}
          </div>
          <div className="grid grid-cols-2 gap-2">
            <Input
              label="Width (in)"
              type="number"
              value={trip.print_width}
              onChange={(e) =>
                updateTrip({ print_width: parseFloat(e.target.value) || 24 })
              }
            />
            <Input
              label="Height (in)"
              type="number"
              value={trip.print_height}
              onChange={(e) =>
                updateTrip({ print_height: parseFloat(e.target.value) || 18 })
              }
            />
          </div>
        </section>

        {/* DPI */}
        <section>
          <h3 className="text-sm font-semibold mb-3">DPI</h3>
          <div className="flex gap-2 mb-2">
            {DPI_PRESETS.map((p) => (
              <Button
                key={p.value}
                variant={trip.dpi === p.value ? "primary" : "secondary"}
                size="sm"
                onClick={() => updateTrip({ dpi: p.value })}
              >
                {p.label}
              </Button>
            ))}
          </div>
          <Input
            type="number"
            value={trip.dpi}
            onChange={(e) =>
              updateTrip({ dpi: parseInt(e.target.value) || 300 })
            }
          />
        </section>

        {/* Title */}
        <section>
          <h3 className="text-sm font-semibold mb-3">Title Banner</h3>
          <label className="flex items-center gap-2 text-sm mb-2">
            <input
              type="checkbox"
              checked={trip.show_title}
              onChange={(e) => updateTrip({ show_title: e.target.checked })}
              className="rounded"
            />
            Show title on map
          </label>
        </section>

        {/* API Key */}
        <section>
          <h3 className="text-sm font-semibold mb-3">Stadia Maps API Key</h3>
          <p className="text-xs text-gray-500 mb-2">
            Required for Watercolor, Toner, and Terrain styles.{" "}
            <a
              href="https://stadiamaps.com/"
              target="_blank"
              rel="noreferrer"
              className="text-blue-500 hover:underline"
            >
              Get a free key
            </a>
          </p>
          <div className="flex gap-2">
            <Input
              type="password"
              placeholder="Enter API key"
              className="flex-1"
              onBlur={(e) => {
                if (e.target.value) {
                  updateSettings({ stadia_api_key: e.target.value });
                  toast("API key saved", "success");
                }
              }}
            />
          </div>
          {settings && (
            <p className="text-xs mt-1">
              Status:{" "}
              <span
                className={
                  settings.stadia_api_key_set
                    ? "text-green-600"
                    : "text-gray-400"
                }
              >
                {settings.stadia_api_key_set ? "Set" : "Not set"}
              </span>
            </p>
          )}
        </section>

        {/* Theme */}
        <section>
          <h3 className="text-sm font-semibold mb-3">Theme</h3>
          <div className="flex gap-2">
            {(["light", "dark", "system"] as const).map((t) => (
              <Button
                key={t}
                variant={theme === t ? "primary" : "secondary"}
                size="sm"
                onClick={() => setTheme(t)}
              >
                {t.charAt(0).toUpperCase() + t.slice(1)}
              </Button>
            ))}
          </div>
        </section>
      </div>
    </Drawer>
  );
}
