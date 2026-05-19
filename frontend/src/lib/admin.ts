/**
 * Yönetici paneli yardımcıları — durum renkleri ve formatlama.
 */

export type SubStatus =
  | "active" | "passive" | "trial" | "trialing" | "cancelled" | "expired" | "suspended" | "past_due" | "admin_override";

export type PayStatus = "paid" | "success" | "pending" | "failed" | "refunded" | "overdue";

const SUB_BADGE: Record<string, string> = {
  active: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  trial: "bg-amber-400/15 text-amber-300 border-amber-400/30",
  trialing: "bg-amber-400/15 text-amber-300 border-amber-400/30",
  passive: "bg-slate-500/15 text-slate-300 border-slate-500/30",
  cancelled: "bg-rose-500/15 text-rose-300 border-rose-500/30",
  expired: "bg-rose-500/15 text-rose-300 border-rose-500/30",
  suspended: "bg-rose-500/15 text-rose-300 border-rose-500/30",
  past_due: "bg-rose-500/15 text-rose-300 border-rose-500/30",
  admin_override: "bg-violet-500/15 text-violet-300 border-violet-500/30",
};

const PAY_BADGE: Record<string, string> = {
  paid: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  success: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  pending: "bg-amber-400/15 text-amber-300 border-amber-400/30",
  failed: "bg-rose-500/15 text-rose-300 border-rose-500/30",
  refunded: "bg-slate-500/15 text-slate-300 border-slate-500/30",
  overdue: "bg-rose-500/15 text-rose-300 border-rose-500/30",
};

export function subBadge(status: string): string {
  return SUB_BADGE[status] || "bg-white/10 text-white/70 border-white/20";
}
export function payBadge(status: string): string {
  return PAY_BADGE[status] || "bg-white/10 text-white/70 border-white/20";
}

export function fmtDate(s?: string | null): string {
  if (!s) return "—";
  try {
    return new Date(s).toLocaleString("tr-TR", {
      year: "numeric", month: "2-digit", day: "2-digit",
      hour: "2-digit", minute: "2-digit",
    });
  } catch {
    return s;
  }
}

export function fmtDay(s?: string | null): string {
  if (!s) return "—";
  try {
    return new Date(s).toLocaleDateString("tr-TR");
  } catch {
    return s;
  }
}

export function fmtTL(v: string | number | null | undefined): string {
  if (v === null || v === undefined || v === "") return "—";
  const n = typeof v === "string" ? Number(v) : v;
  if (!isFinite(n as number)) return String(v);
  return new Intl.NumberFormat("tr-TR", { style: "currency", currency: "TRY", minimumFractionDigits: 2 }).format(n as number);
}

/** Çağrılan endpoint'in DRF paginated yanıtı: {count, next, previous, results}. */
export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
