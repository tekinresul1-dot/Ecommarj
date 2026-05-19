"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import type { LucideIcon } from "lucide-react";
import { Users, UserCheck, UserX, Sparkles, Wallet, AlertTriangle } from "lucide-react";
import { api } from "@/lib/api";
import { fmtDate, fmtTL, subBadge } from "@/lib/admin";

interface DashboardData {
  totals: {
    users: number; active: number; passive: number; trial: number; paid: number;
    revenue_this_month: string; overdue_payments: number;
  };
  expiring_soon: Array<{
    id: number; user_email: string; plan_name: string | null;
    end_date: string | null; status: string;
  }>;
  recent_signups: Array<{ id: number; email: string; name: string; date_joined: string | null }>;
  recent_logins: Array<{ id: number; user_email: string | null; ip_address: string | null; attempted_at: string }>;
  recent_logs: Array<{ id: number; admin_email: string | null; target_user_email: string | null; action_type: string; description: string; created_at: string }>;
}

const StatCard = ({ icon: Icon, label, value, accent }: { icon: LucideIcon; label: string; value: string | number; accent: string }) => (
  <div className="rounded-xl border border-white/10 bg-navy-900/60 p-5 hover:border-white/20 transition-colors">
    <div className="flex items-center gap-3">
      <div className={`h-10 w-10 rounded-lg flex items-center justify-center ${accent}`}>
        <Icon className="h-5 w-5" />
      </div>
      <div>
        <div className="text-xs uppercase tracking-wider text-white/40">{label}</div>
        <div className="text-2xl font-semibold text-white mt-0.5">{value}</div>
      </div>
    </div>
  </div>
);

export default function AdminDashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setData((await api.get("/admin/dashboard/")) as DashboardData);
      } catch (e: unknown) {
        setErr(e instanceof Error ? e.message : "Yüklenemedi");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return (
      <div className="p-6 text-white/60">Yükleniyor…</div>
    );
  }
  if (err || !data) return <div className="p-6 text-rose-300">{err || "Veri yok"}</div>;

  const t = data.totals;

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-white">Yönetici Paneli</h1>
        <p className="text-sm text-white/60 mt-1">Genel bakış ve son hareketler</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <StatCard icon={Users}      label="Toplam"    value={t.users}    accent="bg-blue-500/15 text-blue-300" />
        <StatCard icon={UserCheck}  label="Aktif"     value={t.active}   accent="bg-emerald-500/15 text-emerald-300" />
        <StatCard icon={UserX}      label="Pasif"     value={t.passive}  accent="bg-slate-500/15 text-slate-300" />
        <StatCard icon={Sparkles}   label="Trial"     value={t.trial}    accent="bg-amber-400/15 text-amber-300" />
        <StatCard icon={Wallet}     label="Bu Ay (₺)" value={fmtTL(t.revenue_this_month)} accent="bg-violet-500/15 text-violet-300" />
        <StatCard icon={AlertTriangle} label="Gecikmiş" value={t.overdue_payments} accent="bg-rose-500/15 text-rose-300" />
      </div>

      <Section title="Süresi 7 Günde Dolacaklar">
        <Table headers={["Kullanıcı", "Plan", "Bitiş", "Durum", ""]}>
          {data.expiring_soon.length === 0 && <EmptyRow cols={5} text="Yakında süresi dolan abonelik yok." />}
          {data.expiring_soon.map((s) => (
            <tr key={s.id} className="border-t border-white/5">
              <td className="px-4 py-3 text-white">{s.user_email}</td>
              <td className="px-4 py-3 text-white/70">{s.plan_name || "—"}</td>
              <td className="px-4 py-3 text-white/70">{fmtDate(s.end_date)}</td>
              <td className="px-4 py-3"><Badge cls={subBadge(s.status)}>{s.status}</Badge></td>
              <td className="px-4 py-3 text-right">
                <Link href={`/admin/subscriptions`} className="text-blue-400 hover:text-blue-300 text-sm">Görüntüle →</Link>
              </td>
            </tr>
          ))}
        </Table>
      </Section>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Section title="Son Kayıt Olanlar">
          <Table headers={["Email", "Ad", "Tarih"]}>
            {data.recent_signups.length === 0 && <EmptyRow cols={3} text="Henüz kayıt yok." />}
            {data.recent_signups.map((u) => (
              <tr key={u.id} className="border-t border-white/5">
                <td className="px-4 py-2.5 text-white">
                  <Link href={`/admin/users/${u.id}`} className="hover:text-blue-300">{u.email}</Link>
                </td>
                <td className="px-4 py-2.5 text-white/70">{u.name || "—"}</td>
                <td className="px-4 py-2.5 text-white/60">{fmtDate(u.date_joined)}</td>
              </tr>
            ))}
          </Table>
        </Section>

        <Section title="Son Başarılı Girişler">
          <Table headers={["Kullanıcı", "IP", "Zaman"]}>
            {data.recent_logins.length === 0 && <EmptyRow cols={3} text="Henüz giriş yok." />}
            {data.recent_logins.map((la) => (
              <tr key={la.id} className="border-t border-white/5">
                <td className="px-4 py-2.5 text-white">{la.user_email || "—"}</td>
                <td className="px-4 py-2.5 text-white/70 font-mono text-xs">{la.ip_address || "—"}</td>
                <td className="px-4 py-2.5 text-white/60">{fmtDate(la.attempted_at)}</td>
              </tr>
            ))}
          </Table>
        </Section>
      </div>

      <Section title="Son Yönetici İşlemleri">
        <Table headers={["Tarih", "Admin", "Hedef", "İşlem", "Açıklama"]}>
          {data.recent_logs.length === 0 && <EmptyRow cols={5} text="Henüz log yok." />}
          {data.recent_logs.map((l) => (
            <tr key={l.id} className="border-t border-white/5">
              <td className="px-4 py-2.5 text-white/60 text-xs">{fmtDate(l.created_at)}</td>
              <td className="px-4 py-2.5 text-white/80">{l.admin_email || "—"}</td>
              <td className="px-4 py-2.5 text-white/80">{l.target_user_email || "—"}</td>
              <td className="px-4 py-2.5"><Badge cls="bg-white/10 text-white/70 border-white/20">{l.action_type}</Badge></td>
              <td className="px-4 py-2.5 text-white/60 text-sm">{l.description}</td>
            </tr>
          ))}
        </Table>
      </Section>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-white/10 bg-navy-900/40 overflow-hidden">
      <div className="px-5 py-3 border-b border-white/10 text-sm font-semibold text-white/90">{title}</div>
      <div className="overflow-x-auto">{children}</div>
    </div>
  );
}

function Table({ headers, children }: { headers: string[]; children: React.ReactNode }) {
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="text-left text-xs uppercase tracking-wider text-white/40 bg-navy-950/50">
          {headers.map((h, i) => (
            <th key={i} className="px-4 py-2.5 font-medium">{h}</th>
          ))}
        </tr>
      </thead>
      <tbody>{children}</tbody>
    </table>
  );
}

function EmptyRow({ cols, text }: { cols: number; text: string }) {
  return (
    <tr>
      <td colSpan={cols} className="px-4 py-6 text-center text-sm text-white/40">{text}</td>
    </tr>
  );
}

function Badge({ cls, children }: { cls: string; children: React.ReactNode }) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border ${cls}`}>
      {children}
    </span>
  );
}
