import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import type { TranslationKey } from "../locales/en";
import { en } from "../locales/en";
import { hi } from "../locales/hi";
import { bn } from "../locales/bn";
import { te } from "../locales/te";

export type LocaleCode = "en" | "hi" | "bn" | "te";

export const LANGUAGES: { code: LocaleCode; label: string; native: string; speech: string }[] = [
  { code: "en", label: "English", native: "English", speech: "en-IN" },
  { code: "hi", label: "Hindi", native: "हिन्दी", speech: "hi-IN" },
  { code: "bn", label: "Bengali", native: "বাংলা", speech: "bn-IN" },
  { code: "te", label: "Telugu", native: "తెలుగు", speech: "te-IN" },
];

const DICTIONARIES: Record<LocaleCode, Partial<Record<TranslationKey, string>>> = { en, hi, bn, te };
const STORAGE_KEY = "rationsaathi.language";

interface I18nValue {
  locale: LocaleCode;
  setLocale: (locale: LocaleCode) => void;
  t: (key: TranslationKey, vars?: Record<string, string | number>) => string;
  speechLang: string;
  isTranslated: (key: TranslationKey) => boolean;
  languageLabel: string;
}

const I18nContext = createContext<I18nValue | null>(null);

function readStoredLocale(): LocaleCode {
  try {
    const value = localStorage.getItem(STORAGE_KEY);
    if (value && value in DICTIONARIES) return value as LocaleCode;
  } catch {
    // Storage may be disabled; English remains the safe default.
  }
  return "en";
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<LocaleCode>(readStoredLocale);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, locale);
    } catch {
      // Non-sensitive preference only; failure is harmless.
    }
    document.documentElement.lang = locale;
  }, [locale]);

  const t = useCallback(
    (key: TranslationKey, vars?: Record<string, string | number>) => {
      const raw = DICTIONARIES[locale]?.[key] ?? en[key] ?? key;
      if (!vars) return raw;
      return Object.entries(vars).reduce(
        (text, [name, value]) => text.replaceAll(`{${name}}`, String(value)),
        raw,
      );
    },
    [locale],
  );

  const value = useMemo<I18nValue>(
    () => ({
      locale,
      setLocale: setLocaleState,
      t,
      speechLang: LANGUAGES.find((l) => l.code === locale)?.speech ?? "en-IN",
      isTranslated: (key) => Boolean(DICTIONARIES[locale]?.[key]),
      languageLabel: LANGUAGES.find((l) => l.code === locale)?.native ?? "English",
    }),
    [locale, t],
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nValue {
  const value = useContext(I18nContext);
  if (!value) throw new Error("useI18n must be used inside I18nProvider");
  return value;
}
