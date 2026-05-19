"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { LucideIcon } from "lucide-react";
import { LayoutDashboard, Users, CreditCard, Receipt, KeyRound, ClipboardList, X } from "lucide-react";
import clsx from "clsx";

interface NavItem {
  name: string;
  href: string;
  icon: LucideIcon;
}

const NAV: NavItem[] = [
  { name: "Dashboard", href: "/admin", icon: LayoutDashboard },
  { name: "Kullanıcılar", href: "/admin/users", icon: Users },
  { name: "Abonelikler", href: "/admin/subscriptions", icon: CreditCard },
  { name: "Ödemeler", href: "/admin/payments", icon: Receipt },
  { name: "Giriş Kodları", href: "/admin/access-codes", icon: KeyRound },
  { name: "Loglar", href: "/admin/logs", icon: ClipboardList },
];

function NavContent({
  pathname,
  showClose,
  onClose,
}: {
  pathname: string;
  showClose: boolean;
  onClose: () => void;
}) {
  return (
    <div className="flex grow flex-col gap-y-5 overflow-y-auto border-r border-white/10 bg-navy-950 px-6 pb-4">
      <div className="flex h-16 shrink-0 items-center justify-between">
        <Link
          href="/admin"
          className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-400"
        >
          EcomMarj{" "}
          <span className="text-xs font-semibold uppercase tracking-wider text-amber-400 ml-1">
            Yönetici
          </span>
        </Link>
        {showClose && (
          <button
            type="button"
            onClick={onClose}
            className="-m-2.5 p-2.5 text-white/70 hover:text-white lg:hidden"
            aria-label="Menüyü kapat"
          >
            <X className="h-6 w-6" aria-hidden="true" />
          </button>
        )}
      </div>
      <nav className="flex flex-1 flex-col">
        <ul role="list" className="-mx-2 space-y-1">
          {NAV.map((item) => {
            const isActive =
              pathname === item.href ||
              (item.href !== "/admin" && pathname.startsWith(item.href + "/"));
            return (
              <li key={item.name}>
                <Link
                  href={item.href}
                  onClick={onClose}
                  className={clsx(
                    isActive
                      ? "bg-blue-600/10 text-blue-400 border border-blue-500/20 shadow-[0_0_15px_rgba(59,130,246,0.1)]"
                      : "text-white/70 hover:text-white hover:bg-white/5 border border-transparent",
                    "group flex gap-x-3 rounded-lg p-2.5 text-sm leading-6 font-medium transition-all"
                  )}
                >
                  <item.icon
                    className={clsx(
                      isActive
                        ? "text-blue-400"
                        : "text-white/40 group-hover:text-white",
                      "h-5 w-5 shrink-0"
                    )}
                  />
                  {item.name}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </div>
  );
}

export function AdminSidebar({
  open,
  setOpen,
}: {
  open: boolean;
  setOpen: (v: boolean) => void;
}) {
  const pathname = usePathname();
  return (
    <>
      <div className={clsx("relative z-50 lg:hidden", open ? "block" : "hidden")}>
        <div
          className="fixed inset-0 bg-navy-950/80 backdrop-blur-sm"
          onClick={() => setOpen(false)}
        />
        <div className="fixed inset-0 flex">
          <div className="relative flex w-full max-w-xs flex-1">
            <NavContent pathname={pathname || ""} showClose={open} onClose={() => setOpen(false)} />
          </div>
        </div>
      </div>
      <div className="hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-72 lg:flex-col">
        <NavContent pathname={pathname || ""} showClose={false} onClose={() => setOpen(false)} />
      </div>
    </>
  );
}
