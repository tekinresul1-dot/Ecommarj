"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import type { LucideIcon } from "lucide-react";
import { Plus, Wallet, AlertTriangle, ExternalLink } from "lucide-react";
import { api } from "@/lib/api";
import { fmtDate, fmtTL, payBadge, Paginated } from "@/lib/admin";

interface Payment {
  id: number; user_id: number; user_email: string | null; plan_name: string | null;
  amount: string; status: string; payment_date: string | null; due_date: string | null;
  invoice_note: string; added_by_admin: boolean; created_at: string;
}
interface Stats { total_revenue: string; month_revenue: string; overdue_count: number; }

const STATUS_OPTIONS = [
  { value: "", label: "Tümü" },
  { value: "paid", label: "Ödendi" },
  { value: "success", label: "Başarılı (PayTR)" },
  { value: "pending", label: "Bekliyor" },
  { value: "failed", label: "Başarısız" },
  { value: "refunded", label: "İade" },
  { value: "overdue", label: "Gecikmiş" },
];

export default function AdminPaymentsPage() {
  const [list, setList] = useState<Payment[]>([]);
  const [count, setCount] = useState(0);
  const [stats, setStats] = useState<Stats | null>(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState({ user_id: "", amount: "", status: "paid", invoice_note: "" });

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.set("status", statusFilter);
      if (dateFrom) params.set("date_from", dateFrom);
      if (dateTo) params.set("date_to", dateTo);
      params.set("page", String(page));
      const [data, st] = await Promise.all([
        api.get(`/admin/payments/?${params.toString()}`) as Promise<Paginated<Payment>>,
        api.get(`/admin/payments/stats/`) as Promise<Stats>,
      ]);
      setList(data.results || []);
      setCount(data.count || 0);
      setStats(st);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Yüklenemedi");
    } finally {
      setLoading(false);
    }
  }, [statusFilter, dateFrom, dateTo, page]);

  useEffect(() => { void load(); }, [load]);

  const addPayment = async () => {
    if (!form.user_id || !form.amount) return alert("user_id ve amount zorunlu.");
    setBusy(true);
    try {
      await api.post(`/admin/payments/`, {
        user_id: Number(form.user_id), amount: form.amount,
        status: form.status, invoice_note: form.invoice_note,
      });
      setModalOpen(false);
      setForm({ user_id: "", amount: "", status: "paid", invoice_note: "" });
      await load();
    } catch (e) { alert(e instanceof Error ? e.message : "Hata"); }
    finally { setBusy(false); }
  };

  const totalPages = Math.max(1, Math.ceil(count / 25));

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white">Ödemeler</h1>
          <p className="text-sm text-white/60 mt-1">{count} kayıt</p>
        </div>
        <button onClick={() => setModalOpen(true)}
                className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-md border border-blue-500/30 bg-blue-500/10 text-blue-300 hover:bg-blue-500/20">
          <Plus className="h-4 w-4" /> Manuel Ödeme Ekle
        </button>
      </div>

      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StatCard icon={Wallet}        label="Toplam Gelir"   value={fmtTL(stats.total_revenue)}  accent="bg-emerald-500/15 text-emerald-300" />
          <StatCard icon={Wallet}        label="Bu Ay Gelir"    value={fmtTL(stats.month_revenue)}  accent="bg-violet-500/15 text-violet-300" />
          <StatCard icon={AlertTriangle} label="Gecikmiş Ödeme" value={stats.overdue_count}         accent="bg-rose-500/15 text-rose-300" />
        </div>
      )}

      <div className="flex flex-wrap items-center gap-3">
        <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
                className="rounded-lg bg-navy-900/60 border border-white/10 text-white text-sm px-3 py-2">
          {STATUS_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <input type="date" value={dateFrom} onChange={(e) => { setDateFrom(e.target.value); setPage(1); }}
               className="rounded-lg bg-navy-900/60 border border-white/10 text-white text-sm px-3 py-2" />
        <span className="text-white/40 text-sm">→</span>
        <input type="date" value={dateTo} onChange={(e) => { setDateTo(e.target.value); setPage(1); }}
               className="rounded-lg bg-navy-900/60 border border-white/10 text-white text-sm px-3 py-2" />
      </div>

      <div className="rounded-xl border border-white/10 bg-navy-900/40 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wider text-white/40 bg-navy-950/50">
                <th className="px-4 py-3 font-medium">Kullanıcı</th>
                <th className="px-4 py-3 font-medium">Tutar</th>
                <th className="px-4 py-3 font-medium">Plan</th>
                <th className="px-4 py-3 font-medium">Tarih</th>
                <th className="px-4 py-3 font-medium">Durum</th>
                <th className="px-4 py-3 font-medium">Not</th>
                <th className="px-4 py-3 font-medium text-right">İşlemler</th>
              </tr>
            </thead>
            <tbody>
              {loading && <tr><td colSpan={7} className="px-4 py-6 text-center text-white/40">Yükleniyor…</td></tr>}
              {!loading && list.length === 0 && <tr><td colSpan={7} className="px-4 py-6 text-center text-white/40">Kayıt yok.</td></tr>}
              {list.map((pm) => (
                <tr key={pm.id} className="border-t border-white/5 hover:bg-white/5">
                  <td className="px-4 py-3 text-white">{pm.user_email}</td>
                  <td className="px-4 py-3 text-white font-medium">{fmtTL(pm.amount)}</td>
                  <td className="px-4 py-3 text-white/70">{pm.plan_name || "—"}</td>
                  <td className="px-4 py-3 text-white/60 text-xs whitespace-nowrap">{fmtDate(pm.payment_date || pm.created_at)}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border ${payBadge(pm.status)}`}>{pm.status}</span>
                    {pm.added_by_admin && <span className="ml-1 text-xs text-violet-300">[manuel]</span>}
                  </td>
                  <td className="px-4 py-3 text-white/60 text-sm">{pm.invoice_note || "—"}</td>
                  <td className="px-4 py-3 text-right">
                    <Link href={`/admin/users/${pm.user_id}`} className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-md border border-blue-500/30 bg-blue-500/10 text-blue-300 hover:bg-blue-500/20">
                      <ExternalLink className="h-3.5 w-3.5" /> Kullanıcı
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

      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-navy-950/80 backdrop-blur-sm p-4" onClick={() => setModalOpen(false)}>
          <div onClick={(e) => e.stopPropagation()} className="w-full max-w-md rounded-xl border border-white/10 bg-navy-900 p-5 space-y-3">
            <div className="text-lg font-semibold text-white">Manuel Ödeme Ekle</div>
            <input type="number" value={form.user_id} onChange={(e) => setForm((o) => ({ ...o, user_id: e.target.value }))}
                   placeholder="Kullanıcı ID"
                   className="w-full text-sm rounded-md border border-white/10 bg-navy-950 px-2 py-1.5 text-white placeholder:text-white/30" />
            <input type="number" step="0.01" value={form.amount} onChange={(e) => setForm((o) => ({ ...o, amount: e.target.value }))}
                   placeholder="Tutar (₺)"
                   className="w-full text-sm rounded-md border border-white/10 bg-navy-950 px-2 py-1.5 text-white placeholder:text-white/30" />
            <select value={form.status} onChange={(e) => setForm((o) => ({ ...o, status: e.target.value }))}
                    className="w-full text-sm rounded-md border border-white/10 bg-navy-950 px-2 py-1.5 text-white">
              <option value="paid">Ödendi</option>
              <option value="pending">Bekliyor</option>
              <option value="failed">Başarısız</option>
              <option value="refunded">İade</option>
              <option value="overdue">Gecikmiş</option>
            </select>
            <input value={form.invoice_note} onChange={(e) => setForm((o) => ({ ...o, invoice_note: e.target.value }))}
                   placeholder="Fatura notu (opsiyonel)"
                   className="w-full text-sm rounded-md border border-white/10 bg-navy-950 px-2 py-1.5 text-white placeholder:text-white/30" />
            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setModalOpen(false)} className="text-sm px-3 py-1.5 rounded-md border border-white/10 text-white/70 hover:bg-white/5">Vazgeç</button>
              <button onClick={addPayment} disabled={busy} className="text-sm px-3 py-1.5 rounded-md border border-blue-500/30 bg-blue-500/10 text-blue-300 hover:bg-blue-500/20 disabled:opacity-40">Ekle</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ icon: Icon, label, value, accent }: { icon: LucideIcon; label: string; value: string | number; accent: string }) {
  return (
    <div className="rounded-xl border border-white/10 bg-navy-900/60 p-5">
      <div className="flex items-center gap-3">
        <div className={`h-10 w-10 rounded-lg flex items-center justify-center ${accent}`}><Icon className="h-5 w-5" /></div>
        <div>
          <div className="text-xs uppercase tracking-wider text-white/40">{label}</div>
          <div className="text-xl font-semibold text-white mt-0.5">{value}</div>
        </div>
      </div>
    </div>
  );
}
