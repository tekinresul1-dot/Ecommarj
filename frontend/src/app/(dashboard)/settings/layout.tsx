"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Settings, Truck } from "lucide-react";
import clsx from "clsx";

const settingsNavigation = [
  { name: "Entegrasyonlar", href: "/settings", icon: Settings },
  { name: "Kargo Ayarları", href: "/settings/cargo", icon: Truck },
];

export default function SettingsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  return (
    <div className="max-w-6xl mx-auto py-8 px-4 sm:px-6 lg:px-8 animate-in fade-in duration-500">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-white mb-2">Ayarlar</h1>
        <p className="text-slate-400">Sistem ayarlarını ve entegrasyonları buradan yönetebilirsiniz.</p>
      </div>

      <div className="flex flex-col lg:flex-row gap-8">
        <aside className="w-full lg:w-64 shrink-0">
          <nav className="flex flex-col gap-2">
            {settingsNavigation.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={clsx(
                    isActive
                      ? "bg-blue-600/10 text-blue-400 border border-blue-500/20 shadow-[0_0_15px_rgba(59,130,246,0.1)]"
                      : "text-slate-400 hover:text-slate-200 hover:bg-white/5 border border-transparent",
                    "group flex items-center gap-x-3 rounded-lg p-3 text-sm font-medium transition-all"
                  )}
                >
                  <item.icon
                    className={clsx(
                      isActive ? "text-blue-400" : "text-slate-500 group-hover:text-slate-300",
                      "h-5 w-5 shrink-0"
                    )}
                  />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </aside>

        <main className="flex-1">
          {children}
        </main>
      </div>
    </div>
  );
}
