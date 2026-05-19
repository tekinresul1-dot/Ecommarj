"use client";

import { useEffect, useState, useCallback } from "react";
import { Download } from "lucide-react";
import { api } from "@/lib/api";
import { fmtDate, Paginated } from "@/lib/admin";

interface Log {
  id: number; admin_email: string | null; target_user_email: string | null;
  action_type: string; description: string; created_at: string; ip_address: string | null;
}

const ACTIONS = [
  "", "user_activate", "user_deactivate", "user_suspend", "user_unsuspend", "user_update",
  "plan_change", "subscription_create", "subscription_extend", "subscription_cancel",
  "subscription_trial", "code_create", "code_delete", "code_regenerate",
  "payment_add", "payment_edit", "override_set", "note_add",
];

export default function AdminLogsPage() {
  const [list, setList] = useState<Log[]>([]);
  const [count, setCount] = useState(0);
  const [adminFilter, setAdminFilter] = useState("");
  const [actionFilter, setActionFilter] = useState("");
  const [userFilter, setUserFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const buildParams = useCallback(() => {
    const p = new URLSearchParams();
    if (adminFilter) p.set("admin", adminFilter);
    if (actionFilter) p.set("action_type", actionFilter);
    if (userFilter) p.set("user", userFilter);
    if (dateFrom) p.set("date_from", dateFrom);
    return p;
  }, [adminFilter, actionFilter, userFilter, dateFrom]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const p = buildParams();
      p.set("page", String(page));
      const data = (await api.get(`/admin/logs/?${p.toString()}`)) as Paginated<Log>;
      setList(data.results || []);
      setCount(data.count || 0);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Yüklenemedi");
    } finally {
      setLoading(false);
    }
  }, [buildParams, page]);

  useEffect(() => { void load(); }, [load]);

  const exportCsv = () => {
    const header = ["Tarih", "Admin", "Hedef", "İşlem", "Açıklama", "IP"].join(",");
    const rows = list.map((l) => [
      fmtDate(l.created_at), l.admin_email || "", l.target_user_email || "",
      l.action_type, (l.description || "").replace(/"/g, '""'), l.ip_address || "",
    ].map((v) => `"${String(v)}"`).join(","));
    const blob = new Blob([header + "\n" + rows.join("\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `admin-logs-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const totalPages = Math.max(1, Math.ceil(count / 25));

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white">Yönetici Logları</h1>
          <p className="text-sm text-white/60 mt-1">{count} kayıt</p>
        </div>
        <button onClick={exportCsv}
                className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-md border border-white/10 bg-white/5 text-white hover:bg-white/10">
          <Download className="h-4 w-4" /> CSV (bu sayfa)
        </button>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <input value={adminFilter} onChange={(e) => { setAdminFilter(e.target.value); setPage(1); }}
               placeholder="Admin ID"
               className="rounded-lg bg-navy-900/60 border border-white/10 text-white text-sm px-3 py-2 w-32" />
        <input value={userFilter} onChange={(e) => { setUserFilter(e.target.value); setPage(1); }}
               placeholder="Hedef Kullanıcı ID"
               className="rounded-lg bg-navy-900/60 border border-white/10 text-white text-sm px-3 py-2 w-40" />
        <select value={actionFilter} onChange={(e) => { setActionFilter(e.target.value); setPage(1); }}
                className="rounded-lg bg-navy-900/60 border border-white/10 text-white text-sm px-3 py-2">
          {ACTIONS.map((a) => <option key={a} value={a}>{a || "Tüm işlemler"}</option>)}
        </select>
        <input type="date" value={dateFrom} onChange={(e) => { setDateFrom(e.target.value); setPage(1); }}
               className="rounded-lg bg-navy-900/60 border border-white/10 text-white text-sm px-3 py-2" />
      </div>

      <div className="rounded-xl border border-white/10 bg-navy-900/40 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wider text-white/40 bg-navy-950/50">
                <th className="px-4 py-3 font-medium">Tarih</th>
                <th className="px-4 py-3 font-medium">Admin</th>
                <th className="px-4 py-3 font-medium">Hedef</th>
                <th className="px-4 py-3 font-medium">İşlem</th>
                <th className="px-4 py-3 font-medium">Açıklama</th>
                <th className="px-4 py-3 font-medium">IP</th>
              </tr>
            </thead>
            <tbody>
              {loading && <tr><td colSpan={6} className="px-4 py-6 text-center text-white/40">Yükleniyor…</td></tr>}
              {!loading && list.length === 0 && <tr><td colSpan={6} className="px-4 py-6 text-center text-white/40">Kayıt yok.</td></tr>}
              {list.map((l) => (
                <tr key={l.id} className="border-t border-white/5">
                  <td className="px-4 py-2.5 text-white/60 text-xs whitespace-nowrap">{fmtDate(l.created_at)}</td>
                  <td className="px-4 py-2.5 text-white/80">{l.admin_email || "—"}</td>
                  <td className="px-4 py-2.5 text-white/80">{l.target_user_email || "—"}</td>
                  <td className="px-4 py-2.5">
                    <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border bg-white/10 text-white/70 border-white/20">{l.action_type}</span>
                  </td>
                  <td className="px-4 py-2.5 text-white/70 text-sm">{l.description}</td>
                  <td className="px-4 py-2.5 text-white/40 font-mono text-xs">{l.ip_address || "—"}</td>
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
