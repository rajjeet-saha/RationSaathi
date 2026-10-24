import { FlaskConical, Info } from "lucide-react";
import { useI18n } from "../lib/i18n";

export function DemoBanner() {
  const { t } = useI18n();
  return (
    <div className="border-b border-amber-300 bg-warningBg px-4 py-2.5 text-amber-950">
      <div className="mx-auto flex max-w-7xl items-start gap-2.5">
        <FlaskConical aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
        <p className="text-xs leading-relaxed sm:text-[13px]">
          <span className="mr-2 inline-flex items-center gap-1 rounded bg-amber-900 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-widest text-white">
            {t("demoMode")}
          </span>
          {t("demoNotice")}
        </p>
        <Info aria-hidden="true" className="ml-auto mt-0.5 hidden size-4 shrink-0 sm:block" />
      </div>
    </div>
  );
}
