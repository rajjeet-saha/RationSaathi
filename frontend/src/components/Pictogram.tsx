import {
  ArrowLeftRight,
  BadgeCheck,
  Ban,
  Bus,
  CheckCircle2,
  ClipboardCheck,
  ClipboardList,
  FileWarning,
  HandCoins,
  HelpCircle,
  LogOut,
  PackageCheck,
  PackageX,
  Receipt,
  Scale,
  ShieldAlert,
  ShoppingBasket,
  Timer,
  UserRoundCheck,
} from "lucide-react";
import type { ReactNode } from "react";

export type PictogramKey =
  | "collect"
  | "travel"
  | "available"
  | "outOfStock"
  | "missingDocument"
  | "mismatch"
  | "risk"
  | "draft"
  | "submitted"
  | "receipt"
  | "grievance"
  | "escalation"
  | "privacy"
  | "logout"
  | "verified"
  | "blocked";

const PICTURES: Record<PictogramKey, { icon: ReactNode; label: string }> = {
  collect: { icon: <ShoppingBasket aria-hidden="true" className="size-5" />, label: "Collect ration" },
  travel: { icon: <Bus aria-hidden="true" className="size-5" />, label: "Travel / migration" },
  available: { icon: <PackageCheck aria-hidden="true" className="size-5" />, label: "Stock available" },
  outOfStock: { icon: <PackageX aria-hidden="true" className="size-5" />, label: "Out of stock" },
  missingDocument: { icon: <FileWarning aria-hidden="true" className="size-5" />, label: "Missing document" },
  mismatch: { icon: <ArrowLeftRight aria-hidden="true" className="size-5" />, label: "Record mismatch" },
  risk: { icon: <ShieldAlert aria-hidden="true" className="size-5" />, label: "Entitlement risk" },
  draft: { icon: <ClipboardList aria-hidden="true" className="size-5" />, label: "Saved draft" },
  submitted: { icon: <CheckCircle2 aria-hidden="true" className="size-5" />, label: "Official submission confirmed" },
  receipt: { icon: <Receipt aria-hidden="true" className="size-5" />, label: "Receipt verification" },
  grievance: { icon: <Timer aria-hidden="true" className="size-5" />, label: "Pending grievance" },
  escalation: { icon: <Scale aria-hidden="true" className="size-5" />, label: "Escalation" },
  privacy: { icon: <UserRoundCheck aria-hidden="true" className="size-5" />, label: "Privacy" },
  logout: { icon: <LogOut aria-hidden="true" className="size-5" />, label: "End session" },
  verified: { icon: <BadgeCheck aria-hidden="true" className="size-5" />, label: "Verified" },
  blocked: { icon: <Ban aria-hidden="true" className="size-5" />, label: "Blocked" }
};

export function Pictogram({ name, label }: { name: PictogramKey; label?: string }) {
  const picture = PICTURES[name];
  return (
    <span className="inline-flex items-center gap-2 text-sm font-medium text-ink">
      <span className="rounded-lg bg-brand-50 p-1.5 text-brand-800">{picture.icon}</span>
      <span>{label ?? picture.label}</span>
    </span>
  );
}

export function PictogramLegend() {
  const keys: PictogramKey[] = [
    "collect",
    "travel",
    "available",
    "outOfStock",
    "missingDocument",
    "mismatch",
    "risk",
    "draft",
    "submitted",
    "receipt",
    "grievance",
    "escalation",
    "privacy",
    "logout"
  ];
  return (
    <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
      {keys.map((key) => (
        <li key={key}>
          <Pictogram name={key} />
        </li>
      ))}
    </ul>
  );
}

/** Useful when a workflow needs a short "what this means" panel. */
export function HelpfulPictograms({
  items,
}: {
  items: { name: PictogramKey; label?: string; text: string }[];
}) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {items.map((item) => (
        <div key={`${item.name}-${item.text}`} className="rounded-xl border border-line bg-white p-3">
          <Pictogram name={item.name} label={item.label} />
          <p className="mt-2 text-sm text-muted">{item.text}</p>
        </div>
      ))}
    </div>
  );
}

export const PictogramIcon = {
  help: <HelpCircle aria-hidden="true" className="size-5" />,
  clipboard: <ClipboardCheck aria-hidden="true" className="size-5" />,
  handCoins: <HandCoins aria-hidden="true" className="size-5" />
};
