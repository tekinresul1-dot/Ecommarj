"use client";

import { useState, useEffect } from "react";
import { User, Bell, Menu, LogOut, ExternalLink } from "lucide-react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";

export function Topbar({ setMobileNavOpen }: { setMobileNavOpen: (v: boolean) => void }) {
    const [userMenuOpen, setUserMenuOpen] = useState(false);
    const [userData, setUserData] = useState<{ first_name: string, email: string } | null>(null);
    const router = useRouter();

    useEffect(() => {
        // Profil bilgisini çek
        const fetchUser = async () => {
            const token = localStorage.getItem("access_token");
            if (!token) {
                router.push("/giris");
                return;
            }
            try {
                const data = await api.get("/auth/me/");
                setUserData(data);
            } catch (err) {
                console.error("Topbar fetchUser failed:", err);
            }
        };
        fetchUser();
    }, [router]);

    const handleLogout = () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        router.push("/");
    };

    return (
        <div className="sticky top-0 z-40 flex h-16 shrink-0 items-center gap-x-4 border-b border-white/10 bg-navy-950/90 backdrop-blur-md px-4 shadow-sm sm:gap-x-6 sm:px-6 lg:px-8">
            <button
                type="button"
                className="-m-2.5 p-2.5 text-white/70 hover:text-white lg:hidden"
                onClick={() => setMobileNavOpen(true)}
            >
                <span className="sr-only">Menüyü aç</span>
                <Menu className="h-6 w-6" aria-hidden="true" />
            </button>

            {/* Separator */}
            <div className="h-6 w-px bg-white/10 lg:hidden" aria-hidden="true" />

            <div className="flex flex-1 gap-x-4 self-stretch lg:gap-x-6 justify-end">
                <div className="flex items-center gap-x-4 lg:gap-x-6">
                    <Link href="https://trendyol.com" target="_blank" className="hidden sm:flex items-center gap-2 text-sm text-white/60 hover:text-white transition-colors">
                        Satıcı Paneli <ExternalLink className="h-4 w-4" />
                    </Link>
                    <button type="button" className="-m-2.5 p-2.5 text-white/60 hover:text-white relative">
                        <span className="sr-only">Bildirimleri Gör</span>
                        <Bell className="h-5 w-5" aria-hidden="true" />
                        <span className="absolute top-2 right-2.5 w-2 h-2 rounded-full bg-red-500 border-2 border-navy-950" />
                    </button>

                    {/* Separator */}
                    <div className="hidden lg:block lg:h-6 lg:w-px lg:bg-white/10" aria-hidden="true" />

                    {/* Profile dropdown */}
                    <div className="relative">
                        <button
                            type="button"
                            className="-m-1.5 flex items-center p-1.5"
                            onClick={() => setUserMenuOpen(!userMenuOpen)}
                        >
                            <span className="sr-only">Kullanıcı menüsünü aç</span>
                            <div className="h-8 w-8 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-semibold">
                                {userData?.first_name ? userData.first_name.charAt(0).toUpperCase() : <User className="h-4 w-4" />}
                            </div>
                            <span className="hidden lg:flex lg:items-center">
                                <span className="ml-3 text-sm font-medium leading-6 text-white" aria-hidden="true">
                                    {userData?.first_name || "Yükleniyor..."}
                                </span>
                            </span>
                        </button>

                        {userMenuOpen && (
                            <div className="absolute right-0 z-10 mt-2.5 w-48 origin-top-right rounded-xl bg-navy-900 border border-white/10 py-2 shadow-lg ring-1 ring-black/5 focus:outline-none">
                                <div className="px-4 py-2 border-b border-white/5 mb-1 pb-2">
                                    <p className="text-sm font-medium text-white truncate">{userData?.first_name}</p>
                                    <p className="text-xs text-white/50 truncate mt-0.5">{userData?.email}</p>
                                </div>
                                <Link href="/settings" className="block px-4 py-2 text-sm leading-6 text-white/70 hover:text-white hover:bg-white/5 mx-1 rounded-md transition-colors">
                                    Ayarlar
                                </Link>
                                <button
                                    onClick={handleLogout}
                                    className="w-full text-left block px-4 py-2 text-sm leading-6 text-red-400 hover:text-red-300 hover:bg-red-400/10 mx-1 rounded-md transition-colors"
                                >
                                    <div className="flex items-center gap-2">
                                        <LogOut className="h-4 w-4" />
                                        Çıkış Yap
                                    </div>
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
