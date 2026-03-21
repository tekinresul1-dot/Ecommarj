"use client";

import { useState, useEffect, useRef, FormEvent, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";

function VerificationPageInner() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const email = searchParams.get("email") || "";

    const [code, setCode] = useState(["", "", "", "", "", ""]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState("");
    const [toast, setToast] = useState("");
    const [timer, setTimer] = useState(60);
    const [canResend, setCanResend] = useState(false);
    
    const inputRefs = [
        useRef<HTMLInputElement>(null),
        useRef<HTMLInputElement>(null),
        useRef<HTMLInputElement>(null),
        useRef<HTMLInputElement>(null),
        useRef<HTMLInputElement>(null),
        useRef<HTMLInputElement>(null),
    ];

    useEffect(() => {
        if (!email) {
            router.push("/ucretsiz-basla");
        }
    }, [email, router]);

    useEffect(() => {
        let interval: any;
        if (timer > 0) {
            interval = setInterval(() => {
                setTimer((prev) => prev - 1);
            }, 1000);
        } else {
            setCanResend(true);
        }
        return () => clearInterval(interval);
    }, [timer]);

    function showToast(msg: string) {
        setToast(msg);
        setTimeout(() => setToast(""), 4000);
    }

    const handleChange = (index: number, value: string) => {
        if (isNaN(Number(value))) return;
        
        const newCode = [...code];
        newCode[index] = value.substring(value.length - 1);
        setCode(newCode);

        // Move to next input
        if (value && index < 5) {
            inputRefs[index + 1].current?.focus();
        }
    };

    const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === "Backspace" && !code[index] && index > 0) {
            inputRefs[index - 1].current?.focus();
        }
    };

    const handlePaste = (e: React.ClipboardEvent) => {
        e.preventDefault();
        const data = e.clipboardData.getData("text").substring(0, 6);
        if (/^\d+$/.test(data)) {
            const newCode = data.split("").concat(Array(6 - data.length).fill(""));
            setCode(newCode);
            inputRefs[Math.min(data.length, 5)].current?.focus();
        }
    };

    async function handleSubmit(e?: FormEvent) {
        if (e) e.preventDefault();
        const fullCode = code.join("");
        if (fullCode.length !== 6) return;

        setIsLoading(true);
        setError("");

        try {
            const data = await api.post("/auth/register/verify/", {
                email,
                otp: fullCode,
            });

            localStorage.setItem("access_token", data.tokens.access);
            localStorage.setItem("refresh_token", data.tokens.refresh);
            localStorage.setItem("user", JSON.stringify(data.user));

            showToast("Hesap doğrulandı! Yönlendiriliyorsunuz...");
            setTimeout(() => router.push("/dashboard"), 1500);
        } catch (err: any) {
            setError(err.message || "Geçersiz veya süresi dolmuş kod.");
        } finally {
            setIsLoading(false);
        }
    }

    // Auto-submit when all 6 digits are filled
    useEffect(() => {
        if (code.every(digit => digit !== "") && code.join("").length === 6) {
            handleSubmit();
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [code]);

    async function handleResend() {
        if (!canResend) return;
        
        setIsLoading(true);
        try {
            await api.post("/auth/register/resend-otp/", { email });
            showToast("Yeni kod e-posta adresinize gönderildi.");
            setTimer(60);
            setCanResend(false);
            setCode(["", "", "", "", "", ""]);
            inputRefs[0].current?.focus();
        } catch (err: any) {
            setError(err.message || "Kod gönderilemedi.");
        } finally {
            setIsLoading(false);
        }
    }

    return (
        <div className="w-full max-w-md mx-auto">
            {/* Toast */}
            {toast && (
                <div className="fixed top-20 left-1/2 -translate-x-1/2 z-50 px-6 py-3 rounded-xl bg-emerald-500/20 border border-emerald-400/30 backdrop-blur-xl text-sm text-white shadow-xl animate-slide-up">
                    {toast}
                </div>
            )}

            <div className="glass-card rounded-2xl border border-white/10 p-8 sm:p-10 shadow-2xl shadow-black/20 text-center">
                <div className="mb-8">
                    <div className="w-16 h-16 rounded-2xl bg-accent-500/10 border border-accent-500/20 flex items-center justify-center text-accent-400 mx-auto mb-6">
                        <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                        </svg>
                    </div>
                    <h1 className="text-2xl font-bold text-white mb-2">E-postanızı Doğrulayın</h1>
                    <p className="text-sm text-white/50">
                        <span className="text-white/80 font-medium">{email}</span> adresine 6 haneli bir doğrulama kodu gönderdik.
                    </p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-8">
                    <div className="flex justify-between gap-2 sm:gap-4">
                        {code.map((digit, i) => (
                            <input
                                key={i}
                                ref={inputRefs[i]}
                                type="text"
                                inputMode="numeric"
                                maxLength={1}
                                value={digit}
                                onChange={(e) => handleChange(i, e.target.value)}
                                onKeyDown={(e) => handleKeyDown(i, e)}
                                onPaste={i === 0 ? handlePaste : undefined}
                                className="w-11 h-14 sm:w-12 sm:h-16 rounded-xl bg-white/5 border border-white/10 text-center text-xl font-bold text-white outline-none focus:ring-2 focus:ring-accent-500/40 focus:border-accent-500/40 transition-all"
                            />
                        ))}
                    </div>

                    {error && (
                        <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-xs text-rose-400">
                            {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={isLoading || code.some(d => d === "")}
                        className="w-full h-12 rounded-xl bg-gradient-to-r from-accent-500 to-electric-500 hover:from-accent-400 hover:to-electric-400 text-white font-semibold text-base shadow-xl shadow-accent-500/25 hover:shadow-accent-500/40 hover:scale-[1.02] transition-all duration-300 disabled:opacity-60 disabled:cursor-not-allowed disabled:hover:scale-100"
                    >
                        {isLoading ? "Doğrulanıyor..." : "Hesabı Doğrula"}
                    </button>
                </form>

                <div className="mt-8 pt-8 border-t border-white/5">
                    <p className="text-sm text-white/40 mb-3">Kodu almadınız mı?</p>
                    <button
                        onClick={handleResend}
                        disabled={!canResend || isLoading}
                        className={`text-sm font-medium transition-colors ${
                            canResend 
                            ? "text-accent-400 hover:text-accent-300" 
                            : "text-white/20 cursor-not-allowed"
                        }`}
                    >
                        {canResend ? "Yeni Kod Gönder" : `Yeni kod için bekle: ${timer}s`}
                    </button>
                </div>

                <div className="mt-6">
                    <Link href="/ucretsiz-basla" className="text-xs text-white/30 hover:text-white/60 transition-colors">
                        E-posta adresini değiştir
                    </Link>
                </div>
            </div>
        </div>
    );
}

export default function VerificationPage() {
    return (
        <Suspense>
            <VerificationPageInner />
        </Suspense>
    );
}
