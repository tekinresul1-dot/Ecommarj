"use client";

import { useState, useEffect } from "react";

export default function Navbar() {
    const [scrolled, setScrolled] = useState(false);
    const [menuOpen, setMenuOpen] = useState(false);

    useEffect(() => {
        const onScroll = () => setScrolled(window.scrollY > 20);
        window.addEventListener("scroll", onScroll);
        return () => window.removeEventListener("scroll", onScroll);
    }, []);

    /* Body scroll lock when mobile menu is open */
    useEffect(() => {
        document.body.style.overflow = menuOpen ? "hidden" : "";
        return () => { document.body.style.overflow = ""; };
    }, [menuOpen]);

    const links = [
        { label: "Özellikler", href: "#features" },
        { label: "Nasıl Çalışır", href: "#how-it-works" },
        { label: "Dashboard", href: "#dashboard" },
        { label: "Fiyatlandırma", href: "#pricing" },
    ];

    return (
        <nav
            className={`sticky top-0 z-50 h-16 flex items-center transition-all duration-300
        ${scrolled
                    ? "bg-navy-950/95 backdrop-blur-xl border-b border-white/5 shadow-lg shadow-black/30"
                    : "bg-transparent"
                }`}
        >
            <div className="w-full max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between">
                {/* Logo */}
                <a href="#" className="flex items-center gap-2.5 group shrink-0">
                    <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-accent-400 to-electric-500 flex items-center justify-center text-white font-bold text-sm shadow-lg shadow-accent-500/25 group-hover:shadow-accent-500/40 transition-shadow">
                        E
                    </div>
                    <span className="text-xl font-bold text-white tracking-tight">
                        Ecom<span className="gradient-text-blue">Pro</span>
                    </span>
                </a>

                {/* Desktop links */}
                <div className="hidden md:flex items-center gap-8">
                    {links.map((link) => (
                        <a
                            key={link.href}
                            href={link.href}
                            className="text-sm text-slate-400 hover:text-white transition-colors relative group"
                        >
                            {link.label}
                            <span className="absolute -bottom-1 left-0 w-0 h-[2px] bg-gradient-to-r from-accent-400 to-electric-500 group-hover:w-full transition-all duration-300" />
                        </a>
                    ))}
                </div>

                {/* Desktop CTAs */}
                <div className="hidden md:flex items-center gap-3">
                    <a href="/giris" className="text-sm text-slate-300 hover:text-white transition-colors px-4 py-2">
                        Giriş Yap
                    </a>
                    <a
                        href="/ucretsiz-basla"
                        className="text-sm font-medium text-white px-5 py-2.5 rounded-xl bg-gradient-to-r from-accent-500 to-electric-500 hover:from-accent-400 hover:to-electric-400 transition-all duration-300 shadow-lg shadow-accent-500/25 hover:shadow-accent-500/40 hover:scale-[1.02]"
                    >
                        Ücretsiz Başla
                    </a>
                </div>

                {/* Mobile toggle */}
                <button
                    className="md:hidden text-white p-2"
                    onClick={() => setMenuOpen(!menuOpen)}
                    aria-label="Menü"
                >
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        {menuOpen ? (
                            <path d="M18 6L6 18M6 6l12 12" />
                        ) : (
                            <path d="M3 12h18M3 6h18M3 18h18" />
                        )}
                    </svg>
                </button>
            </div>

            {/* Mobile menu */}
            {menuOpen && (
                <>
                    <div className="fixed inset-0 top-16 bg-black/60 z-40" onClick={() => setMenuOpen(false)} />
                    <div className="fixed top-16 left-0 right-0 z-50 bg-navy-950/98 backdrop-blur-xl border-b border-white/5 p-6 space-y-4 animate-slide-up">
                        {links.map((link) => (
                            <a
                                key={link.href}
                                href={link.href}
                                className="block text-slate-300 hover:text-white transition-colors py-2"
                                onClick={() => setMenuOpen(false)}
                            >
                                {link.label}
                            </a>
                        ))}
                        <div className="pt-4 border-t border-white/5 space-y-3">
                            <a href="/giris" className="block text-center text-slate-300 hover:text-white py-2">
                                Giriş Yap
                            </a>
                            <a
                                href="/ucretsiz-basla"
                                className="block text-center font-medium text-white px-5 py-3 rounded-xl bg-gradient-to-r from-accent-500 to-electric-500"
                            >
                                Ücretsiz Başla
                            </a>
                        </div>
                    </div>
                </>
            )}
        </nav>
    );
}
