"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Menu, LogOut, ShieldAlert } from "lucide-react";
import { AdminSidebar } from "@/components/admin/AdminSidebar";
import { api } from "@/lib/api";
import { clearSession } from "@/lib/session";

type Me = { id: number; email: string; name?: string; is_staff?: boolean };

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [checking, setChecking] = useState(true);
  const [user, setUser] = useState<Me | null>(null);
  const [denied, setDenied] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function check() {
      try {
        const me = (await api.get("/auth/me/")) as Me;
        if (cancelled) return;
        if (!me.is_staff) {
          setDenied(true);
          setTimeout(() => router.replace("/dashboard"), 1500);
          return;
        }
        setUser(me);
      } catch {
        if (!cancelled) router.replace("/giris?next=/admin");
      } finally {
        if (!cancelled) setChecking(false);
      }
    }
    check();
    return () => {
      cancelled = true;
    };
  }, [router]);

  const handleLogout = async () => {
    const refresh = typeof window !== "undefined" ? localStorage.getItem("refresh_token") : null;
    try {
      if (refresh) await api.post("/auth/logout/", { refresh });
    } catch {
      /* ignore */
    } finally {
      clearSession();
      router.push("/giris");
    }
  };

  if (checking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#070B14]">
        <div className="w-8 h-8 rounded-full border-t-2 border-accent-500 animate-spin" />
      </div>
    );
  }

  if (denied) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-[#070B14] text-white gap-3">
        <ShieldAlert className="h-10 w-10 text-rose-400" />
        <div className="text-lg font-semibold">Erişim reddedildi</div>
        <div className="text-sm text-white/60">Bu sayfa yalnızca yöneticiler içindir. Dashboard&apos;a yönlendiriliyorsunuz…</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#070B14] selection:bg-accent-500/30 font-sans">
      <AdminSidebar open={open} setOpen={setOpen} />

      <div className="lg:pl-72 flex flex-col min-h-screen">
        <div className="sticky top-0 z-40 flex h-16 items-center gap-x-4 border-b border-white/10 bg-navy-950/90 backdrop-blur-md px-4 sm:gap-x-6 sm:px-6 lg:px-8">
          <button
            type="button"
            onClick={() => setOpen(true)}
            className="-m-2.5 p-2.5 text-white/70 lg:hidden"
            aria-label="Menü"
          >
            <Menu className="h-6 w-6" aria-hidden="true" />
          </button>
          <div className="flex-1 text-sm font-semibold text-white">Yönetici Paneli</div>
          <div className="flex items-center gap-3">
            <span className="hidden sm:inline text-sm text-white/60">{user?.email}</span>
            <button
              onClick={handleLogout}
              className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-sm text-white/80 hover:bg-white/10 transition"
            >
              <LogOut className="h-4 w-4" /> Çıkış
            </button>
          </div>
        </div>

        <main className="flex-1 overflow-x-hidden">{children}</main>
      </div>
    </div>
  );
}
