"use client";

import { useState, FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

const API_BASE = "http://localhost:8000/api";

export default function LoginPage() {
    const router = useRouter();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [remember, setRemember] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [errors, setErrors] = useState<Record<string, string>>({});
    const [toast, setToast] = useState("");
    const [toastType, setToastType] = useState<"success" | "error">("success");

    function validate() {
        const e: Record<string, string> = {};
        if (!email.trim()) e.email = "E-posta gerekli";
        else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))
            e.email = "Geçerli bir e-posta girin";
        if (!password) e.password = "Şifre gerekli";
        else if (password.length < 8)
            e.password = "Şifre en az 8 karakter olmalı";
        return e;
    }

    function showToast(msg: string, type: "success" | "error" = "success") {
        setToast(msg);
        setToastType(type);
        setTimeout(() => setToast(""), 4000);
    }

    async function handleSubmit(ev: FormEvent) {
        ev.preventDefault();
        const v = validate();
        setErrors(v);
        if (Object.keys(v).length) return;

        setIsLoading(true);
        try {
            const res = await fetch(`${API_BASE}/auth/login/`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            });

            const data = await res.json();

            if (!res.ok) {
                if (data.errors?.non_field_errors) {
                    const msg = Array.isArray(data.errors.non_field_errors)
                        ? data.errors.non_field_errors.join(" ")
                        : data.errors.non_field_errors;
                    showToast(msg, "error");
                } else {
                    showToast("E-posta veya şifre hatalı.", "error");
                }
                return;
            }

            // Save tokens
            localStorage.setItem("access_token", data.tokens.access);
            localStorage.setItem("refresh_token", data.tokens.refresh);
            localStorage.setItem("user", JSON.stringify(data.user));

            showToast("Giriş başarılı! Yönlendiriliyorsunuz...", "success");
            setTimeout(() => router.push("/"), 1500);
        } catch {
            showToast("Sunucuya bağlanılamadı. Lütfen tekrar deneyin.", "error");
        } finally {
            setIsLoading(false);
        }
    }

    return (
        <div className="w-full max-w-md">
            {/* Toast */}
            {toast && (
                <div className={`fixed top-20 left-1/2 -translate-x-1/2 z-50 px-6 py-3 rounded-xl backdrop-blur-xl text-sm text-white shadow-xl animate-slide-up border ${toastType === "success"
                        ? "bg-emerald-500/20 border-emerald-400/30"
                        : "bg-rose-500/20 border-rose-400/30"
                    }`}>
                    {toast}
                </div>
            )}

            <div className="glass-card rounded-2xl border border-white/10 p-8 sm:p-10 shadow-2xl shadow-black/20">
                {/* Header */}
                <div className="text-center mb-8">
                    <h1 className="text-3xl md:text-4xl font-semibold text-white tracking-tight">
                        EcomPro&apos;ya Giriş Yap
                    </h1>
                    <p className="mt-3 text-sm md:text-base text-white/60 leading-relaxed">
                        Kârlılık paneline erişin, sipariş ve ürün
                        performansınızı tek ekranda görün.
                    </p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-5">
                    {/* Email */}
                    <div>
                        <label htmlFor="login-email" className="block text-sm text-white/80 mb-1.5">
                            E-posta
                        </label>
                        <input
                            id="login-email"
                            type="email"
                            autoComplete="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="ornek@sirket.com"
                            className={`w-full h-11 rounded-xl bg-white/5 border ${errors.email ? "border-rose-400/60" : "border-white/10"
                                } px-4 text-sm text-white placeholder:text-white/30 outline-none focus:ring-2 focus:ring-accent-500/40 focus:border-accent-500/40 transition-all`}
                        />
                        {errors.email && <p className="mt-1 text-xs text-rose-400">{errors.email}</p>}
                    </div>

                    {/* Password */}
                    <div>
                        <label htmlFor="login-password" className="block text-sm text-white/80 mb-1.5">
                            Şifre
                        </label>
                        <input
                            id="login-password"
                            type="password"
                            autoComplete="current-password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="••••••••"
                            className={`w-full h-11 rounded-xl bg-white/5 border ${errors.password ? "border-rose-400/60" : "border-white/10"
                                } px-4 text-sm text-white placeholder:text-white/30 outline-none focus:ring-2 focus:ring-accent-500/40 focus:border-accent-500/40 transition-all`}
                        />
                        {errors.password && <p className="mt-1 text-xs text-rose-400">{errors.password}</p>}
                    </div>

                    {/* Remember + Forgot */}
                    <div className="flex items-center justify-between">
                        <label className="flex items-center gap-2 cursor-pointer select-none">
                            <input
                                type="checkbox"
                                checked={remember}
                                onChange={(e) => setRemember(e.target.checked)}
                                className="w-4 h-4 rounded bg-white/5 border border-white/20 accent-accent-500"
                            />
                            <span className="text-sm text-white/60">Beni hatırla</span>
                        </label>
                        <button
                            type="button"
                            className="text-sm text-accent-400 hover:text-accent-300 transition-colors"
                            onClick={() => showToast("Şifre sıfırlama yakında aktif olacak.", "error")}
                        >
                            Şifremi unuttum
                        </button>
                    </div>

                    {/* Submit */}
                    <button
                        type="submit"
                        disabled={isLoading}
                        className="w-full h-12 rounded-xl bg-gradient-to-r from-accent-500 to-electric-500 hover:from-accent-400 hover:to-electric-400 text-white font-semibold text-base shadow-xl shadow-accent-500/25 hover:shadow-accent-500/40 hover:scale-[1.02] transition-all duration-300 disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:scale-100"
                    >
                        {isLoading ? (
                            <span className="inline-flex items-center gap-2">
                                <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" className="opacity-25" />
                                    <path d="M4 12a8 8 0 018-8" stroke="currentColor" strokeWidth="3" strokeLinecap="round" className="opacity-75" />
                                </svg>
                                Devam ediliyor…
                            </span>
                        ) : (
                            "Giriş Yap"
                        )}
                    </button>
                </form>

                {/* Footer link */}
                <p className="mt-8 text-center text-sm text-white/50">
                    Hesabın yok mu?{" "}
                    <Link href="/ucretsiz-basla" className="text-accent-400 hover:text-accent-300 font-medium transition-colors">
                        Ücretsiz başla
                    </Link>
                </p>
            </div>
        </div>
    );
}
