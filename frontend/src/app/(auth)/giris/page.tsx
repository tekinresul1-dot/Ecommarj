"use client";

import { useState, FormEvent, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

type LoginMode = "password" | "otp";
type OtpStep = "email" | "code";

export default function LoginPage() {
    const router = useRouter();
    const [mode, setMode] = useState<LoginMode>("password");

    // Password login state
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [remember, setRemember] = useState(false);

    // OTP login state
    const [otpEmail, setOtpEmail] = useState("");
    const [otpCode, setOtpCode] = useState("");
    const [otpStep, setOtpStep] = useState<OtpStep>("email");

    const [isLoading, setIsLoading] = useState(false);
    const [errors, setErrors] = useState<Record<string, string>>({});
    const [toast, setToast] = useState("");
    const [toastType, setToastType] = useState<"success" | "error">("success");

    useEffect(() => {
        const token = localStorage.getItem("access_token");
        if (token) router.replace("/dashboard");
    }, [router]);

    function showToast(msg: string, type: "success" | "error" = "success") {
        setToast(msg);
        setToastType(type);
        setTimeout(() => setToast(""), 4000);
    }

    // ── Password login ──────────────────────────────────────────────
    function validatePassword() {
        const e: Record<string, string> = {};
        if (!email.trim()) e.email = "E-posta gerekli";
        else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))
            e.email = "Geçerli bir e-posta girin";
        if (!password) e.password = "Şifre gerekli";
        else if (password.length < 8)
            e.password = "Şifre en az 8 karakter olmalı";
        return e;
    }

    async function handlePasswordSubmit(ev: FormEvent) {
        ev.preventDefault();
        const v = validatePassword();
        setErrors(v);
        if (Object.keys(v).length) return;

        setIsLoading(true);
        try {
            const data = await api.post("/auth/login/", { email, password });
            localStorage.setItem("access_token", data.tokens.access);
            localStorage.setItem("refresh_token", data.tokens.refresh);
            localStorage.setItem("user", JSON.stringify(data.user));
            showToast("Giriş başarılı! Yönlendiriliyorsunuz...", "success");
            setTimeout(() => router.push("/dashboard"), 1500);
        } catch (error: any) {
            showToast(error.message || "Sunucuya bağlanılamadı. Lütfen tekrar deneyin.", "error");
        } finally {
            setIsLoading(false);
        }
    }

    // ── OTP: send code ──────────────────────────────────────────────
    async function handleSendOtp(ev: FormEvent) {
        ev.preventDefault();
        if (!otpEmail.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(otpEmail)) {
            setErrors({ otpEmail: "Geçerli bir e-posta girin" });
            return;
        }
        setErrors({});
        setIsLoading(true);
        try {
            await api.post("/auth/send-otp/", { email: otpEmail });
            showToast("Doğrulama kodu e-posta adresinize gönderildi.", "success");
            setOtpStep("code"); // otomatik kod giriş ekranına geç
        } catch (error: any) {
            showToast(error.message || "Kod gönderilemedi. Lütfen tekrar deneyin.", "error");
        } finally {
            setIsLoading(false);
        }
    }

    // ── OTP: verify code ────────────────────────────────────────────
    async function handleVerifyOtp(ev: FormEvent) {
        ev.preventDefault();
        if (!otpCode.trim() || otpCode.length !== 6) {
            setErrors({ otpCode: "6 haneli kodu girin" });
            return;
        }
        setErrors({});
        setIsLoading(true);
        try {
            const data = await api.post("/auth/verify-otp/", { email: otpEmail, otp: otpCode });
            localStorage.setItem("access_token", data.tokens.access);
            localStorage.setItem("refresh_token", data.tokens.refresh);
            localStorage.setItem("user", JSON.stringify(data.user));
            showToast("Giriş başarılı! Yönlendiriliyorsunuz...", "success");
            setTimeout(() => router.push("/dashboard"), 1500);
        } catch (error: any) {
            showToast(error.message || "Geçersiz veya süresi dolmuş kod.", "error");
        } finally {
            setIsLoading(false);
        }
    }

    function switchMode(m: LoginMode) {
        setMode(m);
        setErrors({});
        setOtpStep("email");
        setOtpCode("");
    }

    const inputBase =
        "w-full h-11 rounded-xl bg-white/5 border px-4 text-sm text-white placeholder:text-white/30 outline-none focus:ring-2 focus:ring-accent-500/40 focus:border-accent-500/40 transition-all";

    return (
        <div className="w-full max-w-md">
            {/* Toast */}
            {toast && (
                <div
                    className={`fixed top-20 left-1/2 -translate-x-1/2 z-50 px-6 py-3 rounded-xl backdrop-blur-xl text-sm text-white shadow-xl animate-slide-up border ${
                        toastType === "success"
                            ? "bg-emerald-500/20 border-emerald-400/30"
                            : "bg-rose-500/20 border-rose-400/30"
                    }`}
                >
                    {toast}
                </div>
            )}

            <div className="glass-card rounded-2xl border border-white/10 p-8 sm:p-10 shadow-2xl shadow-black/20">
                {/* Header */}
                <div className="text-center mb-8">
                    <h1 className="text-3xl md:text-4xl font-semibold text-white tracking-tight">
                        EcomMarj&apos;ya Giriş Yap
                    </h1>
                    <p className="mt-3 text-sm md:text-base text-white/60 leading-relaxed">
                        Kârlılık paneline erişin, sipariş ve ürün performansınızı tek ekranda görün.
                    </p>
                </div>

                {/* Mode tabs */}
                <div className="flex rounded-xl bg-white/5 border border-white/10 p-1 mb-6">
                    <button
                        type="button"
                        onClick={() => switchMode("password")}
                        className={`flex-1 h-9 rounded-lg text-sm font-medium transition-all ${
                            mode === "password"
                                ? "bg-accent-500/20 text-accent-300 border border-accent-500/30"
                                : "text-white/50 hover:text-white/80"
                        }`}
                    >
                        Şifre ile Giriş
                    </button>
                    <button
                        type="button"
                        onClick={() => switchMode("otp")}
                        className={`flex-1 h-9 rounded-lg text-sm font-medium transition-all ${
                            mode === "otp"
                                ? "bg-accent-500/20 text-accent-300 border border-accent-500/30"
                                : "text-white/50 hover:text-white/80"
                        }`}
                    >
                        Kod ile Giriş
                    </button>
                </div>

                {/* ── Password form ── */}
                {mode === "password" && (
                    <form onSubmit={handlePasswordSubmit} className="space-y-5">
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
                                className={`${inputBase} ${errors.email ? "border-rose-400/60" : "border-white/10"}`}
                            />
                            {errors.email && <p className="mt-1 text-xs text-rose-400">{errors.email}</p>}
                        </div>

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
                                className={`${inputBase} ${errors.password ? "border-rose-400/60" : "border-white/10"}`}
                            />
                            {errors.password && <p className="mt-1 text-xs text-rose-400">{errors.password}</p>}
                        </div>

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
                )}

                {/* ── OTP form ── */}
                {mode === "otp" && (
                    <div className="space-y-5">
                        {/* Step indicator */}
                        <div className="flex items-center gap-2 mb-2">
                            <div className={`flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold ${
                                otpStep === "email" ? "bg-accent-500 text-white" : "bg-accent-500/30 text-accent-300"
                            }`}>1</div>
                            <div className={`flex-1 h-px ${otpStep === "code" ? "bg-accent-500/50" : "bg-white/10"}`} />
                            <div className={`flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold ${
                                otpStep === "code" ? "bg-accent-500 text-white" : "bg-white/10 text-white/30"
                            }`}>2</div>
                        </div>

                        {otpStep === "email" ? (
                            <form onSubmit={handleSendOtp} className="space-y-5">
                                <div>
                                    <label htmlFor="otp-email" className="block text-sm text-white/80 mb-1.5">
                                        E-posta adresiniz
                                    </label>
                                    <input
                                        id="otp-email"
                                        type="email"
                                        autoComplete="email"
                                        value={otpEmail}
                                        onChange={(e) => setOtpEmail(e.target.value)}
                                        placeholder="ornek@sirket.com"
                                        className={`${inputBase} ${errors.otpEmail ? "border-rose-400/60" : "border-white/10"}`}
                                    />
                                    {errors.otpEmail && (
                                        <p className="mt-1 text-xs text-rose-400">{errors.otpEmail}</p>
                                    )}
                                    <p className="mt-1.5 text-xs text-white/40">
                                        E-postanıza 6 haneli doğrulama kodu gönderilecek.
                                    </p>
                                </div>

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
                                            Kod gönderiliyor…
                                        </span>
                                    ) : (
                                        "Kod Gönder"
                                    )}
                                </button>
                            </form>
                        ) : (
                            <form onSubmit={handleVerifyOtp} className="space-y-5">
                                <div>
                                    <div className="flex items-center justify-between mb-1.5">
                                        <label htmlFor="otp-code" className="block text-sm text-white/80">
                                            Doğrulama kodu
                                        </label>
                                        <button
                                            type="button"
                                            onClick={() => { setOtpStep("email"); setOtpCode(""); setErrors({}); }}
                                            className="text-xs text-accent-400 hover:text-accent-300 transition-colors"
                                        >
                                            E-postayı değiştir
                                        </button>
                                    </div>
                                    <p className="text-xs text-white/50 mb-3">
                                        <span className="text-white/70 font-medium">{otpEmail}</span> adresine gönderildi.
                                    </p>
                                    <input
                                        id="otp-code"
                                        type="text"
                                        inputMode="numeric"
                                        maxLength={6}
                                        autoComplete="one-time-code"
                                        autoFocus
                                        value={otpCode}
                                        onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ""))}
                                        placeholder="000000"
                                        className={`${inputBase} tracking-[0.5em] text-center text-lg font-semibold ${errors.otpCode ? "border-rose-400/60" : "border-white/10"}`}
                                    />
                                    {errors.otpCode && (
                                        <p className="mt-1 text-xs text-rose-400">{errors.otpCode}</p>
                                    )}
                                </div>

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
                                            Doğrulanıyor…
                                        </span>
                                    ) : (
                                        "Giriş Yap"
                                    )}
                                </button>

                                <button
                                    type="button"
                                    disabled={isLoading}
                                    onClick={handleSendOtp as any}
                                    className="w-full text-sm text-white/40 hover:text-white/70 transition-colors"
                                >
                                    Kodu tekrar gönder
                                </button>
                            </form>
                        )}
                    </div>
                )}

                <div className="mt-6">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="h-px flex-1 bg-white/10" />
                        <span className="text-[11px] uppercase tracking-[0.24em] text-white/30">
                            Alternatif Giriş
                        </span>
                        <div className="h-px flex-1 bg-white/10" />
                    </div>

                    <Link
                        href="/google-giris"
                        className="w-full h-12 rounded-xl border border-white/10 bg-white/5 hover:bg-white/7 hover:border-white/20 text-white font-medium transition-all flex items-center justify-center gap-3"
                    >
                        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-white text-[#4285F4] text-sm font-bold">
                            G
                        </span>
                        Google ile Devam Et
                    </Link>
                </div>

                <p className="mt-6 text-center text-sm text-white/50">
                    Hesabın yok mu?{" "}
                    <Link href="/ucretsiz-basla" className="text-accent-400 hover:text-accent-300 font-medium transition-colors">
                        Ücretsiz başla
                    </Link>
                </p>
            </div>
        </div>
    );
}
