"use client";

import { useState, FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export default function RegisterPage() {
    const router = useRouter();
    const [form, setForm] = useState({
        name: "",
        email: "",
        phone: "",
        password: "",
        passwordConfirm: "",
        company: "",
        kvkk: false,
    });
    const [isLoading, setIsLoading] = useState(false);
    const [errors, setErrors] = useState<Record<string, string>>({});
    const [toast, setToast] = useState("");
    const [toastType, setToastType] = useState<"success" | "error">("success");
    const [errorDetail, setErrorDetail] = useState<{
        code?: string;
        message?: string;
        nextAction?: string;
    } | null>(null);

    function update(field: string, value: string | boolean) {
        setForm((p) => ({ ...p, [field]: value }));
        if (errorDetail) setErrorDetail(null);
    }

    function validate() {
        const e: Record<string, string> = {};
        if (!form.name.trim()) e.name = "Ad Soyad gerekli";
        if (!form.email.trim()) e.email = "E-posta gerekli";
        else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email))
            e.email = "Geçerli bir e-posta girin";
        if (!form.password) e.password = "Şifre gerekli";
        else if (form.password.length < 8)
            e.password = "Şifre en az 8 karakter olmalı";
        if (form.password !== form.passwordConfirm)
            e.passwordConfirm = "Şifreler eşleşmiyor";
        if (!form.kvkk) e.kvkk = "Koşulları kabul etmelisiniz";
        return e;
    }

    function showToast(msg: string, type: "success" | "error" = "success") {
        setToast(msg);
        setToastType(type);
        setTimeout(() => setToast(""), 4000);
    }

    async function handleResendOTP() {
        if (!form.email) return;
        setIsLoading(true);
        try {
            await api.post("/auth/register/resend-otp/", { email: form.email });
            showToast("Doğrulama kodu tekrar gönderildi.", "success");
            setTimeout(() => router.push(`/dogrulama?email=${encodeURIComponent(form.email)}`), 1000);
        } catch (err: any) {
            showToast(err.message || "Kod gönderilemedi.", "error");
        } finally {
            setIsLoading(false);
        }
    }

    async function handleSubmit(ev: FormEvent) {
        ev.preventDefault();
        const v = validate();
        setErrors(v);
        setErrorDetail(null);
        if (Object.keys(v).length) return;

        setIsLoading(true);
        try {
            await api.post("/auth/register/", {
                full_name: form.name,
                email: form.email,
                password: form.password,
                password_confirm: form.passwordConfirm,
                phone: form.phone,
                company_name: form.company,
                kvkk_terms_accepted: form.kvkk,
            });

            showToast("Hesap oluşturuldu! Lütfen e-postanıza gönderilen kodu doğrulayın.", "success");
            setTimeout(() => router.push(`/dogrulama?email=${encodeURIComponent(form.email)}`), 1500);
        } catch (error: any) {
            const data = error.data;
            if (data && data.error_code) {
                setErrorDetail({
                    code: data.error_code,
                    message: data.message,
                    nextAction: data.next_action,
                });
            } else {
                showToast(error.message || "Sunucuya bağlanılamadı. Lütfen tekrar deneyin.", "error");
            }
        } finally {
            setIsLoading(false);
        }
    }

    const inputClass = (field: string) =>
        `w-full h-11 rounded-xl bg-white/5 border ${errors[field] ? "border-rose-400/60" : "border-white/10"
        } px-4 text-sm text-white placeholder:text-white/30 outline-none focus:ring-2 focus:ring-accent-500/40 focus:border-accent-500/40 transition-all`;

    const trustPoints = [
        {
            icon: (
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
                    <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
                </svg>
            ),
            title: "Trendyol API Entegrasyonu",
            desc: "Ürünler, siparişler ve finansal veriler otomatik senkronize edilir.",
        },
        {
            icon: (
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
                </svg>
            ),
            title: "Komisyon + Kargo + İade + KDV",
            desc: "Tüm giderler dahil net kâr hesaplaması, sipariş bazında.",
        },
        {
            icon: (
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                    <line x1="12" y1="9" x2="12" y2="13" />
                    <line x1="12" y1="17" x2="12.01" y2="17" />
                </svg>
            ),
            title: "Ürün Bazlı Kâr/Zarar Uyarıları",
            desc: "Zarar eden ürünleri anında tespit edin, fiyat optimizasyonu yapın.",
        },
    ];

    const badges = [
        { label: "7/24 Destek", icon: "💬" },
        { label: "KVKK Uyumlu", icon: "🛡️" },
        { label: "256-bit SSL", icon: "🔒" },
    ];

    return (
        <div className="w-full max-w-4xl">
            {/* Toast */}
            {toast && (
                <div className={`fixed top-20 left-1/2 -translate-x-1/2 z-50 px-6 py-3 rounded-xl backdrop-blur-xl text-sm text-white shadow-xl animate-slide-up border ${toastType === "success"
                    ? "bg-emerald-500/20 border-emerald-400/30"
                    : "bg-rose-500/20 border-rose-400/30"
                    }`}>
                    {toast}
                </div>
            )}

            <div className="grid md:grid-cols-5 gap-6 lg:gap-8">
                {/* ───── Form Card (3 cols) ───── */}
                <div className="md:col-span-3 glass-card rounded-2xl border border-white/10 p-8 sm:p-10 shadow-2xl shadow-black/20">
                    <div className="mb-8">
                        <h1 className="text-3xl md:text-4xl font-semibold text-white tracking-tight">
                            Ücretsiz Başla
                        </h1>
                        <p className="mt-3 text-sm md:text-base text-white/60 leading-relaxed">
                            14 gün ücretsiz deneyin. Kredi kartı gerekmez. 2
                            dakikada kurulum.
                        </p>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        {/* Name */}
                        <div>
                            <label htmlFor="reg-name" className="block text-sm text-white/80 mb-1.5">
                                Ad Soyad
                            </label>
                            <input
                                id="reg-name"
                                type="text"
                                autoComplete="name"
                                value={form.name}
                                onChange={(e) => update("name", e.target.value)}
                                placeholder="Ahmet Yılmaz"
                                className={inputClass("name")}
                            />
                            {errors.name && <p className="mt-1 text-xs text-rose-400">{errors.name}</p>}
                        </div>

                        {/* Email + Phone row */}
                        <div className="grid sm:grid-cols-2 gap-4">
                            <div>
                                <label htmlFor="reg-email" className="block text-sm text-white/80 mb-1.5">
                                    İş E-postası
                                </label>
                                <input
                                    id="reg-email"
                                    type="email"
                                    autoComplete="email"
                                    value={form.email}
                                    onChange={(e) => update("email", e.target.value)}
                                    placeholder="ornek@sirket.com"
                                    className={inputClass("email")}
                                />
                                {errors.email && <p className="mt-1 text-xs text-rose-400">{errors.email}</p>}
                            </div>
                            <div>
                                <label htmlFor="reg-phone" className="block text-sm text-white/80 mb-1.5">
                                    Telefon <span className="text-white/30">(opsiyonel)</span>
                                </label>
                                <input
                                    id="reg-phone"
                                    type="tel"
                                    autoComplete="tel"
                                    value={form.phone}
                                    onChange={(e) => update("phone", e.target.value)}
                                    placeholder="05XX XXX XX XX"
                                    className={inputClass("phone")}
                                />
                            </div>
                        </div>

                        {/* Password row */}
                        <div className="grid sm:grid-cols-2 gap-4">
                            <div>
                                <label htmlFor="reg-password" className="block text-sm text-white/80 mb-1.5">
                                    Şifre
                                </label>
                                <input
                                    id="reg-password"
                                    type="password"
                                    autoComplete="new-password"
                                    value={form.password}
                                    onChange={(e) => update("password", e.target.value)}
                                    placeholder="En az 8 karakter"
                                    className={inputClass("password")}
                                />
                                {errors.password && <p className="mt-1 text-xs text-rose-400">{errors.password}</p>}
                            </div>
                            <div>
                                <label htmlFor="reg-password-confirm" className="block text-sm text-white/80 mb-1.5">
                                    Şifre (tekrar)
                                </label>
                                <input
                                    id="reg-password-confirm"
                                    type="password"
                                    autoComplete="new-password"
                                    value={form.passwordConfirm}
                                    onChange={(e) => update("passwordConfirm", e.target.value)}
                                    placeholder="Şifrenizi tekrar girin"
                                    className={inputClass("passwordConfirm")}
                                />
                                {errors.passwordConfirm && <p className="mt-1 text-xs text-rose-400">{errors.passwordConfirm}</p>}
                            </div>
                        </div>

                        {/* Company */}
                        <div>
                            <label htmlFor="reg-company" className="block text-sm text-white/80 mb-1.5">
                                Şirket Adı <span className="text-white/30">(opsiyonel)</span>
                            </label>
                            <input
                                id="reg-company"
                                type="text"
                                autoComplete="organization"
                                value={form.company}
                                onChange={(e) => update("company", e.target.value)}
                                placeholder="Şirket veya mağaza adı"
                                className={inputClass("company")}
                            />
                        </div>

                        {/* KVKK */}
                        <div>
                            <label className="flex items-start gap-2.5 cursor-pointer select-none">
                                <input
                                    type="checkbox"
                                    checked={form.kvkk}
                                    onChange={(e) => update("kvkk", e.target.checked)}
                                    className="mt-0.5 w-4 h-4 rounded bg-white/5 border border-white/20 accent-accent-500 shrink-0"
                                />
                                <span className="text-sm text-white/60 leading-relaxed">
                                    <Link href="#" className="text-accent-400 hover:underline">KVKK Aydınlatma Metni</Link>{" "}
                                    ve{" "}
                                    <Link href="#" className="text-accent-400 hover:underline">Kullanım Şartları</Link>
                                    &apos;nı okudum ve kabul ediyorum.
                                </span>
                            </label>
                            {errors.kvkk && <p className="mt-1 text-xs text-rose-400">{errors.kvkk}</p>}
                        </div>

                        {/* Detailed Error Suggestion */}
                        {errorDetail && (
                            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-400/20 animate-in fade-in slide-in-from-top-2 duration-300">
                                <p className="text-sm text-rose-200 mb-3 leading-relaxed">
                                    {errorDetail.message}
                                </p>
                                <div className="flex flex-wrap gap-3">
                                    {errorDetail.nextAction === "login" && (
                                        <>
                                            <Link
                                                href="/giris"
                                                className="px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white text-xs font-semibold transition-colors"
                                            >
                                                Giriş Yap
                                            </Link>
                                            <Link
                                                href="/sifre-sifirla"
                                                className="px-4 py-2 rounded-lg border border-white/10 hover:border-white/20 text-white/70 hover:text-white text-xs font-medium transition-all"
                                            >
                                                Şifremi Unuttum
                                            </Link>
                                        </>
                                    )}
                                    {errorDetail.nextAction === "verify_or_resend" && (
                                        <>
                                            <button
                                                type="button"
                                                onClick={handleResendOTP}
                                                disabled={isLoading}
                                                className="px-4 py-2 rounded-lg bg-accent-500/20 hover:bg-accent-500/30 text-accent-400 text-xs font-semibold transition-colors disabled:opacity-50"
                                            >
                                                Doğrulama Kodunu Tekrar Gönder
                                            </button>
                                            <Link
                                                href={`/dogrulama?email=${encodeURIComponent(form.email)}`}
                                                className="px-4 py-2 rounded-lg border border-white/10 hover:border-white/20 text-white/70 hover:text-white text-xs font-medium transition-all"
                                            >
                                                Doğrulama Sayfasına Git
                                            </Link>
                                        </>
                                    )}
                                </div>
                            </div>
                        )}

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
                                "Hesap Oluştur"
                            )}
                        </button>
                    </form>

                    <p className="mt-6 text-center text-sm text-white/50">
                        Zaten hesabın var mı?{" "}
                        <Link href="/giris" className="text-accent-400 hover:text-accent-300 font-medium transition-colors">
                            Giriş yap
                        </Link>
                    </p>
                </div>

                {/* ───── Trust Panel (2 cols) ───── */}
                <div className="md:col-span-2 flex flex-col gap-6">
                    <div className="glass-card rounded-2xl border border-white/10 p-6 sm:p-7 shadow-xl shadow-black/10">
                        <h3 className="text-sm font-semibold text-white/90 uppercase tracking-widest mb-5">
                            Neden EcomMarj?
                        </h3>
                        <div className="space-y-5">
                            {trustPoints.map((item, i) => (
                                <div key={i} className="flex gap-3.5">
                                    <div className="shrink-0 w-9 h-9 rounded-lg bg-accent-500/10 border border-accent-400/20 flex items-center justify-center text-accent-400">
                                        {item.icon}
                                    </div>
                                    <div>
                                        <p className="text-sm font-medium text-white mb-0.5">{item.title}</p>
                                        <p className="text-xs text-white/50 leading-relaxed">{item.desc}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="glass-card rounded-2xl border border-white/10 p-6 shadow-xl shadow-black/10">
                        <div className="flex flex-wrap gap-3">
                            {badges.map((b, i) => (
                                <span key={i} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-xs text-white/70">
                                    <span>{b.icon}</span>
                                    {b.label}
                                </span>
                            ))}
                        </div>
                    </div>

                    <div className="glass-card rounded-2xl border border-white/10 p-6 shadow-xl shadow-black/10 text-center">
                        <p className="text-2xl font-extrabold gradient-text-blue mb-1">2,500+</p>
                        <p className="text-xs text-white/50">Aktif satıcı EcomMarj kullanıyor</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
