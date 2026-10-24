import { AlertTriangle, CheckCircle2, Info, Loader2, X, XCircle } from "lucide-react";
import {
  useEffect,
  useRef,
  type ButtonHTMLAttributes,
  type HTMLAttributes,
  type ReactNode,
} from "react";
import clsx from "clsx";

export function cn(...values: (string | false | null | undefined)[]): string {
  return clsx(values);
}

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";

export function Button({
  variant = "primary",
  className,
  children,
  type = "button",
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant }) {
  return (
    <button
      type={type}
      className={cn(
        variant === "primary" && "btn-primary",
        variant === "secondary" && "btn-secondary",
        variant === "ghost" && "btn-ghost",
        variant === "danger" && "btn-danger",
        className,
      )}
      {...rest}
    >
      {children}
    </button>
  );
}

export function Card({ className, children, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("card", className)} {...rest}>
      {children}
    </div>
  );
}

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
  icon,
}: {
  eyebrow?: string;
  title: string;
  description?: ReactNode;
  actions?: ReactNode;
  icon?: ReactNode;
}) {
  return (
    <header className="mb-6 flex flex-col gap-4 sm:mb-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex min-w-0 items-start gap-3">
          {icon ? <div className="mt-1 rounded-xl bg-brand-50 p-2 text-brand-800">{icon}</div> : null}
          <div className="min-w-0">
            {eyebrow ? (
              <p className="mb-1 text-xs font-bold uppercase tracking-[0.14em] text-brand-700">{eyebrow}</p>
            ) : null}
            <h1 className="text-2xl leading-tight sm:text-3xl">{title}</h1>
            {description ? <div className="mt-2 max-w-3xl text-[15px] leading-relaxed text-muted">{description}</div> : null}
          </div>
        </div>
        {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
      </div>
    </header>
  );
}

type Tone = "success" | "warning" | "danger" | "info" | "neutral";

const TONE_STYLES: Record<Tone, { box: string; icon: ReactNode }> = {
  success: { box: "border-brand-300 bg-brand-50 text-brand-950", icon: <CheckCircle2 aria-hidden="true" className="mt-0.5 size-5 shrink-0" /> },
  warning: { box: "border-amber-300 bg-warningBg text-amber-950", icon: <AlertTriangle aria-hidden="true" className="mt-0.5 size-5 shrink-0" /> },
  danger: { box: "border-red-300 bg-dangerBg text-red-950", icon: <XCircle aria-hidden="true" className="mt-0.5 size-5 shrink-0" /> },
  info: { box: "border-slate-300 bg-infoBg text-slate-900", icon: <Info aria-hidden="true" className="mt-0.5 size-5 shrink-0" /> },
  neutral: { box: "border-line bg-white text-ink", icon: <Info aria-hidden="true" className="mt-0.5 size-5 shrink-0" /> },
};

export function Notice({
  tone = "info",
  title,
  children,
  className,
  ariaLive,
}: {
  tone?: Tone;
  title?: string;
  children: ReactNode;
  className?: string;
  ariaLive?: "polite" | "assertive";
}) {
  const style = TONE_STYLES[tone];
  return (
    <div
      role={tone === "danger" ? "alert" : undefined}
      aria-live={ariaLive}
      className={cn("flex gap-3 rounded-xl border p-4 text-sm leading-relaxed", style.box, className)}
    >
      {style.icon}
      <div className="min-w-0">
        {title ? <p className="mb-1 font-bold">{title}</p> : null}
        <div className="space-y-1">{children}</div>
      </div>
    </div>
  );
}

export function LoadingState({ label = "Loading…" }: { label?: string }) {
  return (
    <div role="status" aria-live="polite" className="flex items-center gap-3 rounded-xl border border-line bg-white p-5 text-muted">
      <Loader2 aria-hidden="true" className="size-5 animate-spin text-brand-700" />
      <span>{label}</span>
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="rounded-xl border border-red-300 bg-dangerBg p-5">
      <p className="font-semibold text-red-950">Something needs attention</p>
      <p className="mt-1 text-sm text-red-900">{message}</p>
      {onRetry ? (
        <Button variant="secondary" className="mt-3" onClick={onRetry}>
          Try again
        </Button>
      ) : null}
    </div>
  );
}

export function EmptyState({ title, children, action }: { title: string; children?: ReactNode; action?: ReactNode }) {
  return (
    <div className="rounded-2xl border border-dashed border-line bg-white/60 p-6 text-center">
      <p className="font-semibold text-ink">{title}</p>
      {children ? <div className="mx-auto mt-2 max-w-xl text-sm text-muted">{children}</div> : null}
      {action ? <div className="mt-4 flex justify-center">{action}</div> : null}
    </div>
  );
}

export function Field({
  label,
  htmlFor,
  hint,
  error,
  children,
  optional,
}: {
  label: string;
  htmlFor: string;
  hint?: string;
  error?: string;
  children: ReactNode;
  optional?: boolean;
}) {
  return (
    <div>
      <label className="label" htmlFor={htmlFor}>
        {label}
        {optional ? <span className="ml-1 font-normal text-muted">({optional ? "optional" : ""})</span> : null}
      </label>
      {children}
      {hint ? <p className="mt-1.5 text-xs leading-relaxed text-muted">{hint}</p> : null}
      {error ? (
        <p role="alert" className="mt-1.5 text-xs font-semibold text-danger">
          {error}
        </p>
      ) : null}
    </div>
  );
}

export function Modal({
  open,
  title,
  description,
  onClose,
  children,
  footer,
}: {
  open: boolean;
  title: string;
  description?: string;
  onClose: () => void;
  children?: ReactNode;
  footer?: ReactNode;
}) {
  const panelRef = useRef<HTMLDivElement>(null);
  const titleId = useRef(`modal-${Math.random().toString(36).slice(2)}`);

  useEffect(() => {
    if (!open) return;
    const previouslyFocused = document.activeElement as HTMLElement | null;
    const panel = panelRef.current;
    const first = panel?.querySelector<HTMLElement>("button, [href], input, select, textarea");
    first?.focus();
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
      if (event.key !== "Tab" || !panel) return;
      const focusable = Array.from(
        panel.querySelectorAll<HTMLElement>(
          'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
        ),
      );
      if (focusable.length === 0) return;
      const firstEl = focusable[0];
      const lastEl = focusable[focusable.length - 1];
      if (!event.shiftKey && document.activeElement === lastEl) {
        event.preventDefault();
        firstEl.focus();
      } else if (event.shiftKey && document.activeElement === firstEl) {
        event.preventDefault();
        lastEl.focus();
      }
    };
    document.addEventListener("keydown", handleKey);
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", handleKey);
      document.body.style.overflow = originalOverflow;
      previouslyFocused?.focus();
    };
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-ink/50 p-0 sm:items-center sm:p-4">
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId.current}
        className="max-h-[92vh] w-full max-w-lg overflow-y-auto rounded-t-2xl bg-white p-5 shadow-xl sm:rounded-2xl sm:p-6"
      >
        <div className="mb-3 flex items-start justify-between gap-4">
          <div>
            <h2 id={titleId.current} className="text-xl">
              {title}
            </h2>
            {description ? <p className="mt-1 text-sm text-muted">{description}</p> : null}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close dialog"
            className="rounded-lg p-2 text-muted hover:bg-canvas"
          >
            <X aria-hidden="true" className="size-5" />
          </button>
        </div>
        {children}
        {footer ? <div className="mt-5 flex flex-wrap justify-end gap-2">{footer}</div> : null}
      </div>
    </div>
  );
}

export function DataRow({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="grid gap-1 border-b border-line/70 py-2.5 text-sm last:border-0 sm:grid-cols-[minmax(9rem,14rem)_1fr] sm:gap-4">
      <dt className="text-muted">{label}</dt>
      <dd className="font-medium text-ink">{children}</dd>
    </div>
  );
}

export function ActionRow({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn("flex flex-wrap items-center gap-2", className)}>{children}</div>;
}
