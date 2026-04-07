import { Modal } from "./ui/Modal";
import { Button } from "./ui/Button";
import { Spinner } from "./ui/Spinner";
import type { RenderStatus } from "../lib/types";
import { getRenderUrl } from "../api/client";

interface Props {
  open: boolean;
  onClose: () => void;
  tripId: string;
  style: string;
  status: RenderStatus;
  isRendering: boolean;
  onRegenerate: () => void;
}

export function RenderModal({
  open,
  onClose,
  tripId,
  style,
  status,
  isRendering: _isRendering,
  onRegenerate,
}: Props) {
  const progress = status.progress ?? 0;

  return (
    <Modal open={open} onClose={onClose} title="Generate Map">
      <div className="space-y-6">
        {/* Progress */}
        {(status.status === "pending" || status.status === "rendering") && (
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Spinner />
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {progress < 0.5
                  ? "Fetching map tiles..."
                  : "Compositing map..."}
              </span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${Math.round(progress * 100)}%` }}
              />
            </div>
            <p className="text-xs text-gray-400 mt-1 text-right">
              {Math.round(progress * 100)}%
            </p>
          </div>
        )}

        {/* Error */}
        {status.status === "error" && (
          <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
            <p className="text-red-600 dark:text-red-400 text-sm">
              Render failed: {status.error || "Unknown error"}
            </p>
          </div>
        )}

        {/* Done */}
        {status.status === "done" && (
          <div>
            <div className="mb-4 rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700">
              <img
                src={getRenderUrl(tripId, style)}
                alt="Rendered map"
                className="w-full"
              />
            </div>
            {status.styles_complete && (
              <div className="flex flex-wrap gap-2">
                {status.styles_complete.map((s) => (
                  <a
                    key={s}
                    href={getRenderUrl(tripId, s)}
                    download={`travel_map_${s}.png`}
                    className="inline-flex"
                  >
                    <Button variant="secondary" size="sm">
                      Download {s}
                    </Button>
                  </a>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-2">
          {status.status === "done" && (
            <Button variant="secondary" onClick={onRegenerate}>
              Regenerate
            </Button>
          )}
          {status.status === "error" && (
            <Button onClick={onRegenerate}>Retry</Button>
          )}
          <Button variant="ghost" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </Modal>
  );
}
