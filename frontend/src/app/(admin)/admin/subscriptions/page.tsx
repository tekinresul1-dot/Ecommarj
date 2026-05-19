"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { Filter, ExternalLink, XCircle } from "lucide-react";
import { api } from "@/lib/api";
import { fmtDate, subBadge, Paginated } from "@/lib/admin";

interface Sub {
  id: number; user_id: number; user_email: string | null;
  plan_id: number | null; plan_name: string | null; status: string;
  start_date: string | null; end_date: string | null;
}

const STATUS_OPTIONS = [
  { value: "", label: "Tümü" },
  { value: "active", label: "Aktif" },
  { value: "passive", label: "Pasif" },
  { value: "trial", label: "Trial" },
  { value: "trialing", label: "Trial (eski)" },
  { value: "expired", label: "Süresi Dolmuş" },
  { value: "cancelled", label: "İptal" },
  { value: "suspended", label: "Askıda" },
  { value: "past_due", label: "Gecikmiş" },
];

export default function AdminSubscriptionsPage() {
  const [list, setList] = useState<Sub[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState("");
  const [expiringSoon, setExpiringSoon] = useState(false);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.set("status", statusFilter);
      if (expiringSoon) params.set("expiring_soon", "1");
      params.set("page", String(page));
      const data = (await api.get(`/admin/subscriptions/?${params.toString()}`)) as Paginated<Sub>;
      setList(data.results || []);
      setCount(data.count || 0);
      setSelected(new Set());
    } catch (e) {
      alert(e instanceof Error ? e.message : "Yüklenemedi");
    } finally {
      setLoading(false);
    }
  }, [statusFilter, expiringSoon, page]);

  useEffect(() => { void load(); }, [load]);

  const toggle = (id: number) => {
    setSelected((s) => {
      const n = new Set(s);
      if (n.has(id)) n.delete(id); else n.add(id);
      return n;
    });
  };
  const toggleAll = () => {
    setSelected((s) => s.size === list.length ? new Set() : new Set(list.map((x) => x.id)));
  };

  const cancelSelected = async () => {
    if (selected.size === 0) return;
    if (!confirm(`${selected.size} aboneliği iptal etmek istiyor musunuz?`)) return;
    setBusy(true);
    try {
      for (const id of selected) {
        await api.post(`/admin/subscriptions/${id}/cancel/`, {});
      }
      await load();
    } catch (e) { alert(e instanceof Error ? e.message : "Hata"); }
    finally { setBusy(false); }
  };

  const totalPages = Math.max(1, Math.ceil(count / 25));

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white">Abonelikler</h1>
          <p className="text-sm text-white/60 mt-1">{count} kayıt</p>
        </div>
        {selected.size > 0 && (
          <button onClick={cancelSelected} disabled={busy}
                  className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-md border border-rose-500/30 bg-rose-500/10 text-rose-300 hover:bg-rose-500/20">
            <XCircle className="h-4 w-4" /> Seçilenleri İptal Et ({selected.size})
          </button>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <select value={statusFilter}
                onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
                className="rounded-lg bg-navy-900/60 border border-white/10 text-white text-sm px-3 py-2">
          {STATUS_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <label className="inline-flex items-center gap-2 text-sm text-white/80">
          <input type="checkbox" checked={expiringSoon}
                 onChange={(e) => { setExpiringSoon(e.target.checked); setPage(1); }}
                 className="rounded border-white/20 bg-navy-900 text-blue-500" />
          <Filter className="h-4 w-4 text-amber-400" /> 7 günde sona erecek
        </label>
      </div>

      <div className="rounded-xl border border-white/10 bg-navy-900/40 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wider text-white/40 bg-navy-950/50">
                <th className="px-4 py-3 w-10">
                  <input type="checkbox" checked={selected.size === list.length && list.length > 0}
                         onChange={toggleAll} className="rounded border-white/20 bg-navy-900 text-blue-500" />
                </th>
                <th className="px-4 py-3 font-medium">Kullanıcı</th>
                <th className="px-4 py-3 font-medium">Plan</th>
                <th className="px-4 py-3 font-medium">Başlangıç</th>
                <th className="px-4 py-3 font-medium">Bitiş</th>
                <th className="px-4 py-3 font-medium">Durum</th>
                <th className="px-4 py-3 font-medium text-right">İşlemler</th>
              </tr>
            </thead>
            <tbody>
              {loading && <tr><td colSpan={7} className="px-4 py-6 text-center text-white/40">Yükleniyor…</td></tr>}
              {!loading && list.length === 0 && <tr><td colSpan={7} className="px-4 py-6 text-center text-white/40">Kayıt yok.</td></tr>}
              {list.map((s) => (
                <tr key={s.id} className="border-t border-white/5 hover:bg-white/5">
                  <td className="px-4 py-3">
                    <input type="checkbox" checked={selected.has(s.id)} onChange={() => toggle(s.id)}
                           className="rounded border-white/20 bg-navy-900 text-blue-500" />
                  </td>
                  <td className="px-4 py-3 text-white">{s.user_email}</td>
                  <td className="px-4 py-3 text-white/70">{s.plan_name || "—"}</td>
                  <td className="px-4 py-3 text-white/60 text-xs whitespace-nowrap">{fmtDate(s.start_date)}</td>
                  <td className="px-4 py-3 text-white/60 text-xs whitespace-nowrap">{fmtDate(s.end_date)}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border ${subBadge(s.status)}`}>{s.status}</span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Link href={`/admin/users/${s.user_id}`} className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-md border border-blue-500/30 bg-blue-500/10 text-blue-300 hover:bg-blue-500/20">
                      <ExternalLink className="h-3.5 w-3.5" /> Detay
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="flex items-center justify-between px-4 py-3 border-t border-white/10">
          <div className="text-xs text-white/40">Sayfa {page} / {totalPages}</div>
          <div className="flex gap-2">
            <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)} className="px-3 py-1 text-sm rounded-md border border-white/10 text-white/70 disabled:opacity-40">←</button>
            <button disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)} className="px-3 py-1 text-sm rounded-md border border-white/10 text-white/70 disabled:opacity-40">→</button>
          </div>
        </div>
      </div>
    </div>
  );
}
