import { useState, useCallback, useRef } from "react";
import * as api from "../api/client";
import type { RenderStatus } from "../lib/types";

export function useRender(tripId: string | undefined) {
  const [status, setStatus] = useState<RenderStatus>({ status: "pending" });
  const [isRendering, setIsRendering] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval>>();

  const startRender = useCallback(
    async (options: { style?: string; all_styles?: boolean } = {}) => {
      if (!tripId) return;
      setIsRendering(true);
      setStatus({ status: "pending" });

      try {
        await api.startRender(tripId, options);

        // Poll for status
        intervalRef.current = setInterval(async () => {
          try {
            const s = await api.getRenderStatus(tripId);
            setStatus(s as RenderStatus);
            if (s.status === "done" || s.status === "error") {
              clearInterval(intervalRef.current);
              setIsRendering(false);
            }
          } catch {
            clearInterval(intervalRef.current);
            setIsRendering(false);
          }
        }, 1000);
      } catch (e) {
        setStatus({ status: "error", error: (e as Error).message });
        setIsRendering(false);
      }
    },
    [tripId],
  );

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
    setIsRendering(false);
  }, []);

  return { status, isRendering, startRender, stopPolling };
}
