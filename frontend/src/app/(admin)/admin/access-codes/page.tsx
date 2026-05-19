"use client";

import { useEffect, useState, useCallback } from "react";
import { Plus, Copy, KeyRound, X } from "lucide-react";
import { api } from "@/lib/api";
import { fmtDate, Paginated } from "@/lib/admin";

interface Code {
  id: number; user_id: number; user_email: string | null;
  code: string; is_active: boolean; is_lifetime: boolean;
  expires_at: string | null; max_uses: number | null; use_count: number;
  last_used_at: string | null; created_at: string;
}

export default function AdminAccessCodesPage() {
  const [list, setList] = useState<Code[]>([]);
  const [count, setCount] = useState(0);
  const [activeFilter, setActiveFilter] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [form, setForm] = useState({ user_id: "", is_lifetime: false, expires_at: "", max_uses: "" });
  const [revealedCode, setRevealedCode] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (activeFilter) params.set("active", activeFilter);
      params.set("page", String(page));
      const data = (await api.get(`/admin/access-codes/?${params.toString()}`)) as Paginated<Code>;
      setList(data.results || []);
      setCount(data.count || 0);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Yüklenemedi");
    } finally {
      setLoading(false);
    }
  }, [activeFilter, page]);

  useEffect(() => { void load(); }, [load]);

  const create = async () => {
    if (!form.user_id) return alert("Kullanıcı ID zorunlu.");
    setBusy(true);
    try {
      const body: Record<string, unknown> = { user_id: Number(form.user_id), is_lifetime: form.is_lifetime };
      if (!form.is_lifetime && form.expires_at) body.expires_at = form.expires_at;
      if (form.max_uses) body.max_uses = Number(form.max_uses);
      const res = (await api.post(`/admin/access-codes/`, body)) as Code;
      setRevealedCode(res.code);
      setModalOpen(false);
      setForm({ user_id: "", is_lifetime: false, expires_at: "", max_uses: "" });
      await load();
    } catch (e) { alert(e instanceof Error ? e.message : "Hata"); }
    finally { setBusy(false); }
  };

  const deactivate = async (id: number) => {
    if (!confirm("Bu kodu pasife almak istiyor musunuz?")) return;
    setBusy(true);
    try {
      await api.delete(`/admin/access-codes/${id}/`);
      await load();
    } catch (e) { alert(e instanceof Error ? e.message : "Hata"); }
    finally { setBusy(false); }
  };

  const regenerate = async (id: number) => {
    setBusy(true);
    try {
      const res = (await api.post(`/admin/access-codes/${id}/regenerate/`, {})) as Code;
      setRevealedCode(res.code);
      await load();
    } catch (e) { alert(e instanceof Error ? e.message : "Hata"); }
    finally { setBusy(false); }
  };

  const totalPages = Math.max(1, Math.ceil(count / 25));

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white">Giriş Kodları</h1>
          <p className="text-sm text-white/60 mt-1">{count} kayıt</p>
        </div>
        <button onClick={() => setModalOpen(true)}
                className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-md border border-blue-500/30 bg-blue-500/10 text-blue-300 hover:bg-blue-500/20">
          <Plus className="h-4 w-4" /> Yeni Kod
        </button>
      </div>

      {revealedCode && (
        <div className="rounded-md border border-emerald-500/30 bg-emerald-500/10 p-3 flex items-center justify-between">
          <div>
            <div className="text-xs text-emerald-300 mb-1">Yeni kod (tek seferlik gösterim):</div>
            <div className="font-mono text-lg text-emerald-200 select-all">{revealedCode}</div>
          </div>
          <div className="flex gap-2">
            <button onClick={() => navigator.clipboard?.writeText(revealedCode)}
                    className="inline-flex items-center gap-1 text-xs px-2.5 py-1.5 rounded-md border border-emerald-500/30 bg-emerald-500/10 text-emerald-200 hover:bg-emerald-500/20">
              <Copy className="h-3.5 w-3.5" /> Kopyala
            </button>
            <button onClick={() => setRevealedCode(null)} className="text-white/60 hover:text-white">
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-3">
        <select value={activeFilter} onChange={(e) => { setActiveFilter(e.target.value); setPage(1); }}
                className="rounded-lg bg-navy-900/60 border border-white/10 text-white text-sm px-3 py-2">
          <option value="">Tümü</option>
          <option value="1">Yalnız Aktif</option>
          <option value="0">Yalnız Pasif</option>
        </select>
      </div>

      <div className="rounded-xl border border-white/10 bg-navy-900/40 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wider text-white/40 bg-navy-950/50">
                <th className="px-4 py-3 font-medium">Kullanıcı</th>
                <th className="px-4 py-3 font-medium">Kod (maskeli)</th>
                <th className="px-4 py-3 font-medium">Oluşturulma</th>
                <th className="px-4 py-3 font-medium">Son Kullanım</th>
                <th className="px-4 py-3 font-medium">Kullanım</th>
                <th className="px-4 py-3 font-medium">Durum</th>
                <th className="px-4 py-3 font-medium text-right">İşlemler</th>
              </tr>
            </thead>
            <tbody>
              {loading && <tr><td colSpan={7} className="px-4 py-6 text-center text-white/40">Yükleniyor…</td></tr>}
              {!loading && list.length === 0 && <tr><td colSpan={7} className="px-4 py-6 text-center text-white/40">Kayıt yok.</td></tr>}
              {list.map((c) => (
                <tr key={c.id} className="border-t border-white/5 hover:bg-white/5">
                  <td className="px-4 py-3 text-white">{c.user_email}</td>
                  <td className="px-4 py-3 font-mono text-white/80 flex items-center gap-2">
                    <KeyRound className="h-3.5 w-3.5 text-white/40" /> {c.code}
                  </td>
                  <td className="px-4 py-3 text-white/60 text-xs whitespace-nowrap">{fmtDate(c.created_at)}</td>
                  <td className="px-4 py-3 text-white/60 text-xs whitespace-nowrap">{fmtDate(c.last_used_at)}</td>
                  <td className="px-4 py-3 text-white/70">{c.use_count}{c.max_uses ? ` / ${c.max_uses}` : ""}</td>
                  <td className="px-4 py-3">
                    {c.is_active ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border bg-emerald-500/15 text-emerald-300 border-emerald-500/30">Aktif{c.is_lifetime ? " · Süresiz" : ""}</span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border bg-slate-500/15 text-slate-300 border-slate-500/30">Pasif</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right whitespace-nowrap">
                    {c.is_active && (
                      <>
                        <button onClick={() => regenerate(c.id)} disabled={busy}
                                className="text-xs px-2 py-1 rounded-md border border-white/10 bg-white/5 text-white/80 hover:bg-white/10 mr-1">Yenile</button>
                        <button onClick={() => deactivate(c.id)} disabled={busy}
                                className="text-xs px-2 py-1 rounded-md border border-rose-500/30 bg-rose-500/10 text-rose-300 hover:bg-rose-500/20">İptal</button>
                      </>
                    )}
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
            <div className="text-lg font-semibold text-white">Yeni Giriş Kodu</div>
            <input type="number" value={form.user_id} onChange={(e) => setForm((o) => ({ ...o, user_id: e.target.value }))}
                   placeholder="Kullanıcı ID"
                   className="w-full text-sm rounded-md border border-white/10 bg-navy-950 px-2 py-1.5 text-white placeholder:text-white/30" />
            <label className="flex items-center gap-2 text-sm text-white/80">
              <input type="checkbox" checked={form.is_lifetime}
                     onChange={(e) => setForm((o) => ({ ...o, is_lifetime: e.target.checked }))}
                     className="rounded border-white/20 bg-navy-950 text-blue-500" />
              Süresiz
            </label>
            {!form.is_lifetime && (
              <input type="datetime-local" value={form.expires_at}
                     onChange={(e) => setForm((o) => ({ ...o, expires_at: e.target.value }))}
                     className="w-full text-sm rounded-md border border-white/10 bg-navy-950 px-2 py-1.5 text-white" />
            )}
            <input type="number" min={1} value={form.max_uses}
                   onChange={(e) => setForm((o) => ({ ...o, max_uses: e.target.value }))}
                   placeholder="Maks. kullanım (boş = sınırsız)"
                   className="w-full text-sm rounded-md border border-white/10 bg-navy-950 px-2 py-1.5 text-white placeholder:text-white/30" />
            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setModalOpen(false)} className="text-sm px-3 py-1.5 rounded-md border border-white/10 text-white/70 hover:bg-white/5">Vazgeç</button>
              <button onClick={create} disabled={busy} className="text-sm px-3 py-1.5 rounded-md border border-blue-500/30 bg-blue-500/10 text-blue-300 hover:bg-blue-500/20 disabled:opacity-40">Üret</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
