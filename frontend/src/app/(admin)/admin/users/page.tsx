"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { Search, ShieldOff, ShieldCheck, KeyRound, ExternalLink } from "lucide-react";
import { api } from "@/lib/api";
import { fmtDate, subBadge, Paginated } from "@/lib/admin";

interface AdminUser {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  date_joined: string | null;
  last_login: string | null;
  profile: { is_suspended: boolean; company: string } | null;
  subscription: { plan_name: string | null; status: string } | null;
}

const STATUS_OPTIONS = [
  { value: "", label: "Tümü" },
  { value: "active", label: "Aktif" },
  { value: "passive", label: "Pasif" },
  { value: "trial", label: "Trial" },
  { value: "suspended", label: "Askıya Alınmış" },
  { value: "paid", label: "Ücretli" },
];

export default function AdminUsersPage() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setErr(null);
    try {
      const params = new URLSearchParams();
      if (search) params.set("search", search);
      if (statusFilter) params.set("status", statusFilter);
      params.set("page", String(page));
      const data = (await api.get(`/admin/users/?${params.toString()}`)) as Paginated<AdminUser>;
      setUsers(data.results || []);
      setCount(data.count || 0);
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Yüklenemedi");
    } finally {
      setLoading(false);
    }
  }, [search, statusFilter, page]);

  useEffect(() => {
    void load();
  }, [load]);

  const toggleActive = async (u: AdminUser) => {
    try {
      await api.patch(`/admin/users/${u.id}/`, { is_active: !u.is_active });
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Hata");
    }
  };

  const totalPages = Math.max(1, Math.ceil(count / 25));

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white">Kullanıcılar</h1>
          <p className="text-sm text-white/60 mt-1">{count} kayıt</p>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-white/40" />
          <input
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            placeholder="E-posta / ad / şirket ara…"
            className="w-full pl-9 pr-3 py-2 rounded-lg bg-navy-900/60 border border-white/10 text-white text-sm placeholder:text-white/30 focus:border-blue-400/50 focus:outline-none"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="rounded-lg bg-navy-900/60 border border-white/10 text-white text-sm px-3 py-2 focus:outline-none focus:border-blue-400/50"
        >
          {STATUS_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
      </div>

      <div className="rounded-xl border border-white/10 bg-navy-900/40 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wider text-white/40 bg-navy-950/50">
                <th className="px-4 py-3 font-medium">Email</th>
                <th className="px-4 py-3 font-medium">Ad</th>
                <th className="px-4 py-3 font-medium">Plan</th>
                <th className="px-4 py-3 font-medium">Durum</th>
                <th className="px-4 py-3 font-medium">Kayıt</th>
                <th className="px-4 py-3 font-medium">Son Giriş</th>
                <th className="px-4 py-3 font-medium text-right">İşlemler</th>
              </tr>
            </thead>
            <tbody>
              {loading && <tr><td colSpan={7} className="px-4 py-6 text-center text-white/40">Yükleniyor…</td></tr>}
              {!loading && err && <tr><td colSpan={7} className="px-4 py-6 text-center text-rose-300">{err}</td></tr>}
              {!loading && !err && users.length === 0 && <tr><td colSpan={7} className="px-4 py-6 text-center text-white/40">Sonuç yok.</td></tr>}
              {users.map((u) => (
                <tr key={u.id} className="border-t border-white/5 hover:bg-white/5">
                  <td className="px-4 py-3 text-white">
                    <Link href={`/admin/users/${u.id}`} className="hover:text-blue-300 inline-flex items-center gap-1">
                      {u.email} <ExternalLink className="h-3 w-3 opacity-50" />
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-white/70">{u.full_name || "—"}</td>
                  <td className="px-4 py-3 text-white/70">{u.subscription?.plan_name || "—"}</td>
                  <td className="px-4 py-3">
                    {u.profile?.is_suspended ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border bg-rose-500/15 text-rose-300 border-rose-500/30">Askıda</span>
                    ) : u.is_active ? (
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border ${subBadge(u.subscription?.status || "active")}`}>
                        {u.subscription?.status || "aktif"}
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border bg-slate-500/15 text-slate-300 border-slate-500/30">Pasif</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-white/60 text-xs whitespace-nowrap">{fmtDate(u.date_joined)}</td>
                  <td className="px-4 py-3 text-white/60 text-xs whitespace-nowrap">{fmtDate(u.last_login)}</td>
                  <td className="px-4 py-3 text-right whitespace-nowrap">
                    <button onClick={() => toggleActive(u)}
                            className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-md border border-white/10 bg-white/5 text-white/80 hover:bg-white/10 mr-2"
                            title={u.is_active ? "Pasifleştir" : "Aktifleştir"}>
                      {u.is_active ? <ShieldOff className="h-3.5 w-3.5" /> : <ShieldCheck className="h-3.5 w-3.5" />}
                      {u.is_active ? "Pasif" : "Aktif"}
                    </button>
                    <Link href={`/admin/users/${u.id}`} className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-md border border-blue-500/30 bg-blue-500/10 text-blue-300 hover:bg-blue-500/20">
                      <KeyRound className="h-3.5 w-3.5" /> Detay
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
            <button disabled={page <= 1} onClick={() => setPage((p) => Math.max(1, p - 1))}
                    className="px-3 py-1 text-sm rounded-md border border-white/10 text-white/70 disabled:opacity-40 hover:bg-white/5">←</button>
            <button disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}
                    className="px-3 py-1 text-sm rounded-md border border-white/10 text-white/70 disabled:opacity-40 hover:bg-white/5">→</button>
          </div>
        </div>
      </div>
    </div>
  );
}
