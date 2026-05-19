"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft, Shield, ShieldAlert, ShieldCheck, ShieldOff, Star, AlertTriangle,
  Save, Plus, KeyRound, CalendarPlus, Sparkles, XCircle,
} from "lucide-react";
import { api } from "@/lib/api";
import { fmtDate, fmtTL, subBadge, payBadge } from "@/lib/admin";

interface Plan { id: number; name: string; price: string; interval: string; }
interface SubData {
  id: number; plan_id: number | null; plan_name: string | null; status: string;
  start_date: string | null; end_date: string | null; trial_end_date: string | null;
  admin_override: boolean; notes: string;
}
interface PayData {
  id: number; amount: string; status: string; plan_name: string | null;
  payment_date: string | null; due_date: string | null; invoice_note: string;
  added_by_admin: boolean; created_at: string;
}
interface CodeData {
  id: number; code: string; is_active: boolean; is_lifetime: boolean;
  expires_at: string | null; max_uses: number | null; use_count: number; last_used_at: string | null;
}
interface LogData {
  id: number; admin_email: string | null; action_type: string; description: string; created_at: string;
}
interface UserDetail {
  id: number; email: string; full_name: string; is_active: boolean;
  date_joined: string | null; last_login: string | null;
  profile: {
    phone: string; company: string; is_suspended: boolean; suspension_reason: string;
    admin_note: string; is_priority: boolean; is_risky: boolean; admin_override: boolean;
    last_login_ip: string; email_verified: boolean; google_connected: boolean;
    trendyol_store_count: number;
  } | null;
  subscription: SubData | null;
  payments: PayData[];
  access_codes: CodeData[];
  recent_logs: LogData[];
}

export default function AdminUserDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const id = params?.id;
  const [u, setU] = useState<UserDetail | null>(null);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [adminNote, setAdminNote] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [suspendReason, setSuspendReason] = useState("");
  const [selectedPlanId, setSelectedPlanId] = useState<string>("");
  const [newCodeOpts, setNewCodeOpts] = useState({ is_lifetime: false, expires_at: "", max_uses: "" });
  const [newPayment, setNewPayment] = useState({ amount: "", status: "paid", invoice_note: "" });
  const [revealedCode, setRevealedCode] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const data = (await api.get(`/admin/users/${id}/`)) as UserDetail;
      setU(data);
      setAdminNote(data.profile?.admin_note || "");
      setSelectedPlanId(data.subscription?.plan_id ? String(data.subscription.plan_id) : "");
      if (plans.length === 0) {
        const ps = (await api.get(`/admin/plans/`)) as Plan[];
        setPlans(ps);
      }
    } catch (e) {
      alert(e instanceof Error ? e.message : "Yüklenemedi");
    } finally {
      setLoading(false);
    }
  }, [id, plans.length]);

  useEffect(() => { void load(); }, [load]);

  if (loading || !u) return <div className="p-6 text-white/60">Yükleniyor…</div>;
  const p = u.profile;
  const s = u.subscription;

  const patchProfile = async (patch: Record<string, unknown>) => {
    setBusy(true);
    try {
      await api.patch(`/admin/users/${u.id}/`, patch);
      await load();
    } catch (e) { alert(e instanceof Error ? e.message : "Hata"); }
    finally { setBusy(false); }
  };

  const suspend = async () => {
    if (!suspendReason.trim()) return alert("Sebep zorunlu.");
    setBusy(true);
    try {
      await api.post(`/admin/users/${u.id}/suspend/`, { reason: suspendReason });
      setSuspendReason("");
      await load();
    } catch (e) { alert(e instanceof Error ? e.message : "Hata"); }
    finally { setBusy(false); }
  };
  const unsuspend = async () => {
    setBusy(true);
    try {
      await api.post(`/admin/users/${u.id}/activate/`, {});
      await load();
    } catch (e) { alert(e instanceof Error ? e.message : "Hata"); }
    finally { setBusy(false); }
  };

  const setPlan = async () => {
    if (!selectedPlanId) return;
    setBusy(true);
    try {
      await api.post(`/admin/users/${u.id}/subscription/`, { plan_id: Number(selectedPlanId) });
      await load();
    } catch (e) { alert(e instanceof Error ? e.message : "Hata"); }
    finally { setBusy(false); }
  };

  const extend = async (days: number) => {
    if (!s) return;
    setBusy(true);
    try {
      await api.post(`/admin/subscriptions/${s.id}/extend/`, { days });
      await load();
    } catch (e) { alert(e instanceof Error ? e.message : "Hata"); }
    finally { setBusy(false); }
  };

  const startTrial = async () => {
    if (!s) return;
    setBusy(true);
    try {
      await api.post(`/admin/subscriptions/${s.id}/trial/`, { days: 14 });
      await load();
    } catch (e) { alert(e instanceof Error ? e.message : "Hata"); }
    finally { setBusy(false); }
  };

  const cancelSub = async () => {
    if (!s) return;
    if (!confirm("Aboneliği iptal etmek istediğinize emin misiniz?")) return;
    setBusy(true);
    try {
      await api.post(`/admin/subscriptions/${s.id}/cancel/`, {});
      await load();
    } catch (e) { alert(e instanceof Error ? e.message : "Hata"); }
    finally { setBusy(false); }
  };

  const addPayment = async () => {
    if (!newPayment.amount) return alert("Tutar zorunlu.");
    setBusy(true);
    try {
      await api.post(`/admin/payments/`, {
        user_id: u.id,
        amount: newPayment.amount,
        status: newPayment.status,
        invoice_note: newPayment.invoice_note,
      });
      setNewPayment({ amount: "", status: "paid", invoice_note: "" });
      await load();
    } catch (e) { alert(e instanceof Error ? e.message : "Hata"); }
    finally { setBusy(false); }
  };

  const createCode = async () => {
    setBusy(true);
    try {
      const body: Record<string, unknown> = { user_id: u.id, is_lifetime: newCodeOpts.is_lifetime };
      if (!newCodeOpts.is_lifetime && newCodeOpts.expires_at) body.expires_at = newCodeOpts.expires_at;
      if (newCodeOpts.max_uses) body.max_uses = Number(newCodeOpts.max_uses);
      const res = (await api.post(`/admin/access-codes/`, body)) as CodeData;
      setRevealedCode(res.code);
      setNewCodeOpts({ is_lifetime: false, expires_at: "", max_uses: "" });
      await load();
    } catch (e) { alert(e instanceof Error ? e.message : "Hata"); }
    finally { setBusy(false); }
  };

  const deactivateCode = async (cid: number) => {
    setBusy(true);
    try {
      await api.delete(`/admin/access-codes/${cid}/`);
      await load();
    } catch (e) { alert(e instanceof Error ? e.message : "Hata"); }
    finally { setBusy(false); }
  };

  return (
    <div className="p-6 space-y-6">
      <button onClick={() => router.back()} className="inline-flex items-center gap-1 text-sm text-white/60 hover:text-white">
        <ArrowLeft className="h-4 w-4" /> Geri
      </button>

      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-white">{u.full_name || u.email}</h1>
          <p className="text-sm text-white/60">{u.email}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {p?.is_suspended ? (
            <button onClick={unsuspend} disabled={busy}
                    className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-md border border-emerald-500/30 bg-emerald-500/10 text-emerald-300 hover:bg-emerald-500/20">
              <ShieldCheck className="h-4 w-4" /> Askıdan Çıkar
            </button>
          ) : null}
          <button onClick={() => patchProfile({ is_active: !u.is_active })} disabled={busy}
                  className="inline-flex items-center gap-1.5 text-sm px-3 py-1.5 rounded-md border border-white/10 bg-white/5 text-white hover:bg-white/10">
            {u.is_active ? <ShieldOff className="h-4 w-4" /> : <ShieldCheck className="h-4 w-4" />}
            {u.is_active ? "Pasifleştir" : "Aktifleştir"}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sol — Profil */}
        <div className="space-y-4">
          <Card title="Profil">
            <KV k="Şirket" v={p?.company} />
            <KV k="Telefon" v={p?.phone} />
            <KV k="Kayıt" v={fmtDate(u.date_joined)} />
            <KV k="Son Giriş" v={fmtDate(u.last_login)} />
            <KV k="Son IP" v={p?.last_login_ip} />
            <KV k="E-posta Doğrulandı" v={p?.email_verified ? "Evet" : "Hayır"} />
            <KV k="Google Bağlı" v={p?.google_connected ? "Evet" : "Hayır"} />
            <KV k="Trendyol Mağaza" v={String(p?.trendyol_store_count ?? 0)} />
          </Card>

          <Card title="Durum & Bayraklar">
            <label className="flex items-center gap-2 py-1 text-sm text-white/80">
              <input type="checkbox" checked={!!p?.admin_override}
                     onChange={(e) => patchProfile({ admin_override: e.target.checked })}
                     className="rounded border-white/20 bg-navy-900 text-blue-500" />
              <Shield className="h-4 w-4 text-violet-400" /> Admin Override (paywall&apos;u atla)
            </label>
            <label className="flex items-center gap-2 py-1 text-sm text-white/80">
              <input type="checkbox" checked={!!p?.is_priority}
                     onChange={(e) => patchProfile({ is_priority: e.target.checked })}
                     className="rounded border-white/20 bg-navy-900 text-blue-500" />
              <Star className="h-4 w-4 text-amber-400" /> Öncelikli
            </label>
            <label className="flex items-center gap-2 py-1 text-sm text-white/80">
              <input type="checkbox" checked={!!p?.is_risky}
                     onChange={(e) => patchProfile({ is_risky: e.target.checked })}
                     className="rounded border-white/20 bg-navy-900 text-rose-500" />
              <AlertTriangle className="h-4 w-4 text-rose-400" /> Riskli
            </label>

            {!p?.is_suspended && (
              <div className="mt-3 pt-3 border-t border-white/10">
                <div className="text-xs text-white/50 mb-1">Askıya Al</div>
                <input value={suspendReason} onChange={(e) => setSuspendReason(e.target.value)}
                       placeholder="Sebep…"
                       className="w-full text-sm rounded-md border border-white/10 bg-navy-900 px-2 py-1.5 text-white placeholder:text-white/30" />
                <button onClick={suspend} disabled={busy || !suspendReason.trim()}
                        className="mt-2 inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-md border border-rose-500/30 bg-rose-500/10 text-rose-300 hover:bg-rose-500/20 disabled:opacity-40">
                  <ShieldAlert className="h-3.5 w-3.5" /> Askıya Al
                </button>
              </div>
            )}
            {p?.is_suspended && (
              <div className="mt-3 pt-3 border-t border-rose-500/30">
                <div className="text-xs text-rose-300 font-semibold">Askıda</div>
                <div className="text-sm text-white/70 mt-1">{p.suspension_reason || "—"}</div>
              </div>
            )}
          </Card>

          <Card title="Admin Notu">
            <textarea value={adminNote} onChange={(e) => setAdminNote(e.target.value)} rows={4}
                      className="w-full text-sm rounded-md border border-white/10 bg-navy-900 px-2 py-1.5 text-white placeholder:text-white/30" />
            <button onClick={() => patchProfile({ admin_note: adminNote })} disabled={busy}
                    className="mt-2 inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-md border border-blue-500/30 bg-blue-500/10 text-blue-300 hover:bg-blue-500/20">
              <Save className="h-3.5 w-3.5" /> Kaydet
            </button>
          </Card>
        </div>

        {/* Orta — Abonelik */}
        <div className="space-y-4">
          <Card title="Abonelik">
            <KV k="Durum" v={
              <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border ${subBadge(s?.status || "passive")}`}>
                {s?.status || "—"}
              </span>
            } />
            <KV k="Plan" v={s?.plan_name} />
            <KV k="Başlangıç" v={fmtDate(s?.start_date)} />
            <KV k="Bitiş" v={fmtDate(s?.end_date)} />
            <KV k="Trial Bitiş" v={fmtDate(s?.trial_end_date)} />

            <div className="mt-3 pt-3 border-t border-white/10 space-y-2">
              <div className="text-xs text-white/50">Plan Değiştir</div>
              <div className="flex gap-2">
                <select value={selectedPlanId} onChange={(e) => setSelectedPlanId(e.target.value)}
                        className="flex-1 text-sm rounded-md border border-white/10 bg-navy-900 px-2 py-1.5 text-white">
                  <option value="">Plan seç…</option>
                  {plans.map((pl) => (
                    <option key={pl.id} value={pl.id}>{pl.name} — {fmtTL(pl.price)} / {pl.interval}</option>
                  ))}
                </select>
                <button onClick={setPlan} disabled={busy || !selectedPlanId}
                        className="text-xs px-3 py-1.5 rounded-md border border-blue-500/30 bg-blue-500/10 text-blue-300 hover:bg-blue-500/20 disabled:opacity-40">
                  Uygula
                </button>
              </div>

              <div className="text-xs text-white/50 mt-3">Uzat</div>
              <div className="flex gap-2 flex-wrap">
                {[30, 90, 180, 365].map((d) => (
                  <button key={d} onClick={() => extend(d)} disabled={busy || !s}
                          className="inline-flex items-center gap-1 text-xs px-2.5 py-1.5 rounded-md border border-white/10 bg-white/5 text-white/80 hover:bg-white/10">
                    <CalendarPlus className="h-3.5 w-3.5" /> {d === 365 ? "1 Yıl" : `${d / 30 | 0} Ay`}
                  </button>
                ))}
                <button onClick={startTrial} disabled={busy || !s}
                        className="inline-flex items-center gap-1 text-xs px-2.5 py-1.5 rounded-md border border-amber-400/30 bg-amber-400/10 text-amber-300 hover:bg-amber-400/20">
                  <Sparkles className="h-3.5 w-3.5" /> +14g Trial
                </button>
                <button onClick={cancelSub} disabled={busy || !s}
                        className="inline-flex items-center gap-1 text-xs px-2.5 py-1.5 rounded-md border border-rose-500/30 bg-rose-500/10 text-rose-300 hover:bg-rose-500/20">
                  <XCircle className="h-3.5 w-3.5" /> İptal Et
                </button>
              </div>
            </div>
          </Card>

          <Card title="Giriş Kodları">
            {revealedCode && (
              <div className="rounded-md border border-emerald-500/30 bg-emerald-500/10 p-3 mb-3">
                <div className="text-xs text-emerald-300 mb-1">Yeni kod (tek seferlik gösterim):</div>
                <div className="font-mono text-lg text-emerald-200 select-all">{revealedCode}</div>
                <button onClick={() => navigator.clipboard?.writeText(revealedCode)} className="text-xs mt-1 text-emerald-300 hover:underline">Kopyala</button>
              </div>
            )}
            {u.access_codes.length === 0 && <div className="text-sm text-white/40">Henüz kod yok.</div>}
            <div className="space-y-1.5">
              {u.access_codes.map((c) => (
                <div key={c.id} className="flex items-center justify-between text-sm rounded-md border border-white/10 px-3 py-1.5">
                  <div className="flex items-center gap-2">
                    <KeyRound className="h-3.5 w-3.5 text-white/40" />
                    <span className="font-mono text-white/80">{c.code}</span>
                    {!c.is_active && <span className="text-xs text-rose-300">[pasif]</span>}
                    {c.is_lifetime && <span className="text-xs text-violet-300">[süresiz]</span>}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-white/40">{c.use_count} kullanım</span>
                    {c.is_active && (
                      <button onClick={() => deactivateCode(c.id)} className="text-xs text-rose-300 hover:text-rose-200">Pasife al</button>
                    )}
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-3 pt-3 border-t border-white/10 space-y-2">
              <div className="text-xs text-white/50">Yeni Kod Oluştur</div>
              <label className="flex items-center gap-2 text-sm text-white/80">
                <input type="checkbox" checked={newCodeOpts.is_lifetime}
                       onChange={(e) => setNewCodeOpts((o) => ({ ...o, is_lifetime: e.target.checked }))}
                       className="rounded border-white/20 bg-navy-900 text-blue-500" />
                Süresiz
              </label>
              {!newCodeOpts.is_lifetime && (
                <input type="datetime-local" value={newCodeOpts.expires_at}
                       onChange={(e) => setNewCodeOpts((o) => ({ ...o, expires_at: e.target.value }))}
                       className="w-full text-sm rounded-md border border-white/10 bg-navy-900 px-2 py-1.5 text-white" />
              )}
              <input type="number" min={1} value={newCodeOpts.max_uses}
                     onChange={(e) => setNewCodeOpts((o) => ({ ...o, max_uses: e.target.value }))}
                     placeholder="Maks. kullanım (boş = sınırsız)"
                     className="w-full text-sm rounded-md border border-white/10 bg-navy-900 px-2 py-1.5 text-white placeholder:text-white/30" />
              <button onClick={createCode} disabled={busy}
                      className="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-md border border-blue-500/30 bg-blue-500/10 text-blue-300 hover:bg-blue-500/20">
                <Plus className="h-3.5 w-3.5" /> Üret
              </button>
            </div>
          </Card>
        </div>

        {/* Sağ — Ödemeler + Loglar */}
        <div className="space-y-4">
          <Card title="Ödeme Geçmişi">
            {u.payments.length === 0 && <div className="text-sm text-white/40">Henüz ödeme yok.</div>}
            <div className="space-y-1.5">
              {u.payments.map((pm) => (
                <div key={pm.id} className="flex items-center justify-between text-sm rounded-md border border-white/10 px-3 py-1.5">
                  <div>
                    <div className="text-white">{fmtTL(pm.amount)}</div>
                    <div className="text-xs text-white/40">{fmtDate(pm.payment_date || pm.created_at)} · {pm.plan_name || "—"}</div>
                  </div>
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border ${payBadge(pm.status)}`}>{pm.status}</span>
                </div>
              ))}
            </div>
            <div className="mt-3 pt-3 border-t border-white/10 space-y-2">
              <div className="text-xs text-white/50">Manuel Ödeme Ekle</div>
              <input type="number" step="0.01" value={newPayment.amount}
                     onChange={(e) => setNewPayment((o) => ({ ...o, amount: e.target.value }))}
                     placeholder="Tutar (₺)"
                     className="w-full text-sm rounded-md border border-white/10 bg-navy-900 px-2 py-1.5 text-white placeholder:text-white/30" />
              <select value={newPayment.status}
                      onChange={(e) => setNewPayment((o) => ({ ...o, status: e.target.value }))}
                      className="w-full text-sm rounded-md border border-white/10 bg-navy-900 px-2 py-1.5 text-white">
                <option value="paid">Ödendi</option>
                <option value="pending">Bekliyor</option>
                <option value="failed">Başarısız</option>
                <option value="refunded">İade</option>
                <option value="overdue">Gecikmiş</option>
              </select>
              <input value={newPayment.invoice_note}
                     onChange={(e) => setNewPayment((o) => ({ ...o, invoice_note: e.target.value }))}
                     placeholder="Fatura notu"
                     className="w-full text-sm rounded-md border border-white/10 bg-navy-900 px-2 py-1.5 text-white placeholder:text-white/30" />
              <button onClick={addPayment} disabled={busy}
                      className="inline-flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-md border border-blue-500/30 bg-blue-500/10 text-blue-300 hover:bg-blue-500/20">
                <Plus className="h-3.5 w-3.5" /> Ekle
              </button>
            </div>
          </Card>

          <Card title="Yakın İşlemler (log)">
            {u.recent_logs.length === 0 && <div className="text-sm text-white/40">Henüz log yok.</div>}
            <div className="space-y-1.5">
              {u.recent_logs.slice(0, 20).map((l) => (
                <div key={l.id} className="text-xs border-l-2 border-blue-500/40 pl-2 py-0.5">
                  <div className="text-white/70">{l.description}</div>
                  <div className="text-white/40">{fmtDate(l.created_at)} · {l.admin_email || "system"} · {l.action_type}</div>
                </div>
              ))}
            </div>
            <Link href="/admin/logs" className="mt-3 inline-block text-xs text-blue-400 hover:text-blue-300">Tüm loglar →</Link>
          </Card>
        </div>
      </div>
    </div>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-white/10 bg-navy-900/40 p-4">
      <div className="text-sm font-semibold text-white/90 mb-3">{title}</div>
      <div className="space-y-1">{children}</div>
    </div>
  );
}

function KV({ k, v }: { k: string; v: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between text-sm py-1">
      <div className="text-white/50">{k}</div>
      <div className="text-white/90 text-right">{v ?? "—"}</div>
    </div>
  );
}
