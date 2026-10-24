/**
 * Browser read-aloud. Speech synthesis availability varies by device and may
 * require network or installed voices; callers must always show the text too.
 */

export function speechSupported(): boolean {
  return typeof window !== "undefined" && "speechSynthesis" in window && "SpeechSynthesisUtterance" in window;
}

let current: SpeechSynthesisUtterance | null = null;
let speaking = false;

export interface SpeakOptions {
  lang?: string;
  rate?: number;
  onEnd?: () => void;
  onError?: (message: string) => void;
}

export function speak(text: string, options: SpeakOptions = {}): boolean {
  if (!speechSupported()) {
    options.onError?.("unavailable");
    return false;
  }
  try {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = options.lang ?? "en-IN";
    utterance.rate = options.rate ?? 0.95;
    utterance.onend = () => {
      speaking = false;
      current = null;
      options.onEnd?.();
    };
    utterance.onerror = () => {
      speaking = false;
      current = null;
      options.onError?.("error");
    };
    current = utterance;
    speaking = true;
    window.speechSynthesis.speak(utterance);
    return true;
  } catch {
    speaking = false;
    options.onError?.("error");
    return false;
  }
}

export function pauseSpeech(): void {
  if (speechSupported()) window.speechSynthesis.pause();
}

export function resumeSpeech(): void {
  if (speechSupported()) window.speechSynthesis.resume();
}

export function stopSpeech(): void {
  if (speechSupported()) window.speechSynthesis.cancel();
  speaking = false;
  current = null;
}

export function isSpeaking(): boolean {
  return speaking;
}

export function speakLabel(): string {
  return current?.text ?? "";
}
