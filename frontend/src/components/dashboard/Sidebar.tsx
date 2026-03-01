"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
    BarChart3, Activity, Percent, FileText, AlertTriangle,
    CreditCard, Settings, ShoppingBag, Package, Layers,
    RotateCcw, Megaphone, Tag, Sliders, X
} from "lucide-react";
import clsx from "clsx";

const navigation = [
    { name: "Genel Bakış", href: "/dashboard", icon: BarChart3 },
    { name: "Canlı Performans", href: "/live", icon: Activity },
    { name: "Promosyon Kârlılık", href: "/promo-profit", icon: Percent },
    {
        name: "Raporlar",
        icon: FileText,
        children: [
            { name: "Sipariş Analizi", href: "/reports/orders", icon: ShoppingBag },
            { name: "Ürün Analizi", href: "/reports/products", icon: Package },
            { name: "Kategori Analizi", href: "/reports/categories", icon: Layers },
            { name: "İade Zarar Analizi", href: "/reports/returns", icon: RotateCcw },
            { name: "Reklam Analizi", href: "/reports/ads", icon: Megaphone },
        ],
    },
    { name: "Kâr Marjı Listesi", href: "/margins", icon: FileText },
    { name: "Ürün Fiyatlandırma", href: "/pricing-rules", icon: Tag },
    { name: "Ürün Ayarları", href: "/products", icon: Sliders },
    { name: "Uyarılar", href: "/alerts", icon: AlertTriangle },
    { name: "Hakediş Kontrolü", href: "/payouts", icon: CreditCard },
    { name: "Ayarlar", href: "/settings", icon: Settings },
];

export function Sidebar({ mobileNavOpen, setMobileNavOpen }: { mobileNavOpen: boolean, setMobileNavOpen: (v: boolean) => void }) {
    const pathname = usePathname();

    const NavContent = () => (
        <div className="flex grow flex-col gap-y-5 overflow-y-auto border-r border-white/10 bg-navy-950 px-6 pb-4">
            <div className="flex h-16 shrink-0 items-center justify-between">
                <Link href="/" className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-indigo-400">
                    EcomPro
                </Link>
                {mobileNavOpen && (
                    <button type="button" onClick={() => setMobileNavOpen(false)} className="-m-2.5 p-2.5 text-white/70 hover:text-white lg:hidden">
                        <X className="h-6 w-6" aria-hidden="true" />
                    </button>
                )}
            </div>
            <nav className="flex flex-1 flex-col">
                <ul role="list" className="flex flex-1 flex-col gap-y-7">
                    <li>
                        <ul role="list" className="-mx-2 space-y-1">
                            {navigation.map((item) => {
                                if (item.children) {
                                    return (
                                        <li key={item.name} className="mt-4">
                                            <div className="text-xs font-semibold leading-6 text-white/40 ml-2 mb-1 uppercase tracking-wider">
                                                {item.name}
                                            </div>
                                            <ul className="space-y-1">
                                                {item.children.map((child) => {
                                                    const isActive = pathname === child.href;
                                                    return (
                                                        <li key={child.name}>
                                                            <Link
                                                                href={child.href}
                                                                onClick={() => setMobileNavOpen(false)}
                                                                className={clsx(
                                                                    isActive
                                                                        ? "bg-blue-600/10 text-blue-400 border border-blue-500/20"
                                                                        : "text-white/70 hover:text-white hover:bg-white/5 border border-transparent",
                                                                    "group flex gap-x-3 rounded-lg p-2 px-3 text-sm leading-6 font-medium transition-all"
                                                                )}
                                                            >
                                                                <child.icon className={clsx(isActive ? "text-blue-400" : "text-white/40 group-hover:text-white", "h-5 w-5 shrink-0")} />
                                                                {child.name}
                                                            </Link>
                                                        </li>
                                                    )
                                                })}
                                            </ul>
                                        </li>
                                    )
                                }

                                const isActive = pathname === item.href;
                                return (
                                    <li key={item.name}>
                                        <Link
                                            href={item.href}
                                            onClick={() => setMobileNavOpen(false)}
                                            className={clsx(
                                                isActive
                                                    ? "bg-blue-600/10 text-blue-400 border border-blue-500/20 shadow-[0_0_15px_rgba(59,130,246,0.1)]"
                                                    : "text-white/70 hover:text-white hover:bg-white/5 border border-transparent",
                                                "group flex gap-x-3 rounded-lg p-2.5 text-sm leading-6 font-medium transition-all"
                                            )}
                                        >
                                            <item.icon className={clsx(isActive ? "text-blue-400" : "text-white/40 group-hover:text-white", "h-5 w-5 shrink-0")} />
                                            {item.name}
                                        </Link>
                                    </li>
                                );
                            })}
                        </ul>
                    </li>
                </ul>
            </nav>
        </div>
    );

    return (
        <>
            {/* Mobile sidebar */}
            <div className={clsx("relative z-50 lg:hidden", mobileNavOpen ? "block" : "hidden")}>
                <div className="fixed inset-0 bg-navy-950/80 backdrop-blur-sm transition-opacity" onClick={() => setMobileNavOpen(false)} />
                <div className="fixed inset-0 flex">
                    <div className="relative flex w-full max-w-xs flex-1 transform transition transition-transform ease-in-out duration-300">
                        <NavContent />
                    </div>
                </div>
            </div>

            {/* Desktop sidebar */}
            <div className="hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-72 lg:flex-col">
                <NavContent />
            </div>
        </>
    );
}
