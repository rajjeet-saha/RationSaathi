import { Pause, Play, RotateCcw, Square, Volume2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useI18n } from "../lib/i18n";
import { pauseSpeech, resumeSpeech, speak, speechSupported, stopSpeech } from "../lib/speech";
import { Button } from "./ui";

/**
 * Spoken alternative for critical instructions. Always paired with the visible
 * text; speech availability varies by device and may need network access.
 */
export function ReadAloud({
  text,
  label,
  compact = false,
  rate = 0.95,
}: {
  text: string;
  label?: string;
  compact?: boolean;
  rate?: number;
}) {
  const { t, speechLang } = useI18n();
  const [status, setStatus] = useState<"idle" | "speaking" | "paused" | "error">("idle");
  const [message, setMessage] = useState("");

  useEffect(() => {
    return () => stopSpeech();
  }, []);

  const start = (speed = rate) => {
    setMessage("");
    const ok = speak(text, {
      lang: speechLang,
      rate: speed,
      onEnd: () => setStatus("idle"),
      onError: () => {
        setStatus("error");
        setMessage(t("a11y.voiceUnavailable"));
      },
    });
    if (ok) setStatus("speaking");
  };

  if (!speechSupported() && status !== "error") {
    return (
      <p className="text-xs leading-relaxed text-muted" role="note">
        <Volume2 aria-hidden="true" className="mr-1 inline size-3.5" />
        {t("a11y.voiceUnavailable")}
      </p>
    );
  }

  return (
    <div className={compact ? "flex flex-wrap items-center gap-2" : "rounded-xl border border-line bg-canvas/70 p-3"}>
      {!compact ? (
        <p className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-muted">
          <Volume2 aria-hidden="true" className="size-4" />
          {label ?? t("common.readAloud")}
        </p>
      ) : null}
      <div className="flex flex-wrap items-center gap-2">
        <Button
          variant="secondary"
          className="min-h-9 px-3 py-1.5 text-xs"
          onClick={() => (status === "paused" ? (resumeSpeech(), setStatus("speaking")) : start())}
          aria-label={status === "paused" ? t("common.resumeReading") : t("common.readAloud")}
        >
          {status === "speaking" ? <Pause aria-hidden="true" className="size-4" /> : <Play aria-hidden="true" className="size-4" />}
          {status === "speaking" ? t("common.pauseReading") : status === "paused" ? t("common.resumeReading") : t("common.readAloud")}
        </Button>
        {status === "speaking" ? (
          <Button
            variant="ghost"
            className="min-h-9 px-3 py-1.5 text-xs"
            onClick={() => {
              pauseSpeech();
              setStatus("paused");
            }}
            aria-label={t("common.pauseReading")}
          >
            <Pause aria-hidden="true" className="size-4" />
            {t("common.pauseReading")}
          </Button>
        ) : null}
        <Button
          variant="ghost"
          className="min-h-9 px-3 py-1.5 text-xs"
          onClick={() => {
            stopSpeech();
            setStatus("idle");
          }}
          aria-label={t("common.stopReading")}
        >
          <Square aria-hidden="true" className="size-4" />
          {t("common.stopReading")}
        </Button>
        <Button
          variant="ghost"
          className="min-h-9 px-3 py-1.5 text-xs"
          onClick={() => start(0.7)}
          aria-label={t("common.slower")}
        >
          <RotateCcw aria-hidden="true" className="size-4" />
          {t("common.slower")}
        </Button>
        <Button
          variant="ghost"
          className="min-h-9 px-3 py-1.5 text-xs"
          onClick={() => start()}
          aria-label={t("common.repeat")}
        >
          {t("common.repeat")}
        </Button>
      </div>
      <p aria-live="polite" className="mt-1 text-xs text-muted">
        {message}
      </p>
    </div>
  );
}
