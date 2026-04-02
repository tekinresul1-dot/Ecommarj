"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import Script from "next/script";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "";

type GoogleCredentialResponse = {
    credential?: string;
};

type GoogleAccountsId = {
    initialize: (config: {
        client_id: string;
        callback: (response: GoogleCredentialResponse) => void;
        ux_mode?: "popup" | "redirect";
        auto_select?: boolean;
        cancel_on_tap_outside?: boolean;
    }) => void;
    renderButton: (
        element: HTMLElement,
        options: {
            theme?: "outline" | "filled_blue" | "filled_black";
            size?: "large" | "medium" | "small";
            width?: number;
            text?: string;
            shape?: "rectangular" | "pill" | "circle" | "square";
            logo_alignment?: "left" | "center";
        }
    ) => void;
};

type GoogleWindow = Window & {
    google?: {
        accounts?: {
            id?: GoogleAccountsId;
        };
    };
};

export default function GoogleLoginPage() {
    const router = useRouter();
    const buttonRef = useRef<HTMLDivElement | null>(null);
    const initializedRef = useRef(false);

    const [scriptReady, setScriptReady] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState("");
    const [toast, setToast] = useState("");
    const [toastType, setToastType] = useState<"success" | "error">("success");

    function showToast(message: string, type: "success" | "error" = "success") {
        setToast(message);
        setToastType(type);
        setTimeout(() => setToast(""), 4000);
    }

    useEffect(() => {
        const token = localStorage.getItem("access_token");
        if (token) {
            router.replace("/dashboard");
        }
    }, [router]);

    useEffect(() => {
        const googleWindow = window as GoogleWindow;
        const googleApi = googleWindow.google;
        if (!scriptReady || !buttonRef.current || initializedRef.current || !googleApi?.accounts?.id) {
            return;
        }

        if (!GOOGLE_CLIENT_ID) {
            setError("Google giriş yapılandırması henüz tamamlanmamış.");
            return;
        }

        googleApi.accounts.id.initialize({
            client_id: GOOGLE_CLIENT_ID,
            callback: async (response: GoogleCredentialResponse) => {
                if (!response?.credential) {
                    showToast("Google doğrulaması alınamadı. Lütfen tekrar deneyin.", "error");
                    return;
                }

                setIsLoading(true);
                setError("");

                try {
                    const data = await api.post("/auth/google/", { id_token: response.credential });
                    localStorage.setItem("access_token", data.tokens.access);
                    localStorage.setItem("refresh_token", data.tokens.refresh);
                    localStorage.setItem("user", JSON.stringify(data.user));
                    showToast("Google ile giriş başarılı. Yönlendiriliyorsunuz...", "success");
                    setTimeout(() => router.push("/dashboard"), 1200);
                } catch (err: unknown) {
                    const message = err instanceof Error ? err.message : "Google ile giriş sırasında bir hata oluştu.";
                    setError(message);
                    showToast(message, "error");
                } finally {
                    setIsLoading(false);
                }
            },
            ux_mode: "popup",
            auto_select: false,
            cancel_on_tap_outside: true,
        });

        googleApi.accounts.id.renderButton(buttonRef.current, {
            theme: "outline",
            size: "large",
            width: 360,
            text: "continue_with",
            shape: "pill",
            logo_alignment: "left",
        });

        initializedRef.current = true;
    }, [router, scriptReady]);

    return (
        <>
            <Script
                src="https://accounts.google.com/gsi/client"
                strategy="afterInteractive"
                onLoad={() => setScriptReady(true)}
            />

            <div className="w-full max-w-md">
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
                    <div className="text-center mb-8">
                        <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl border border-white/10 bg-white/5 shadow-inner shadow-white/5">
                            <span className="text-2xl font-bold text-white">G</span>
                        </div>
                        <h1 className="text-3xl md:text-4xl font-semibold text-white tracking-tight">
                            Google ile Giriş
                        </h1>
                        <p className="mt-3 text-sm md:text-base text-white/60 leading-relaxed">
                            Mevcut giriş yöntemleri aynen korunur. Bu ekran, Google hesabınızla hızlıca oturum açmanız için eklendi.
                        </p>
                    </div>

                    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">
                        <div className="mb-4 flex items-start gap-3 rounded-xl border border-accent-500/15 bg-accent-500/8 p-4">
                            <div className="mt-0.5 h-2.5 w-2.5 rounded-full bg-accent-400" />
                            <p className="text-sm leading-relaxed text-white/75">
                                İlk girişte hesabınız mevcut e-posta ile eşleştirilir. Aynı e-posta ile daha önce açılmış hesabınız varsa mevcut verileriniz korunur.
                            </p>
                        </div>

                        <div className="flex min-h-14 items-center justify-center rounded-xl border border-white/10 bg-white/5 px-3">
                            {GOOGLE_CLIENT_ID ? (
                                <div ref={buttonRef} className="w-full flex justify-center" />
                            ) : (
                                <p className="text-sm text-white/45">
                                    Google Client ID tanımlandıktan sonra bu alanda giriş butonu görünecek.
                                </p>
                            )}
                        </div>

                        {isLoading && (
                            <div className="mt-4 flex items-center justify-center gap-2 text-sm text-white/60">
                                <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                                    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" className="opacity-25" />
                                    <path d="M4 12a8 8 0 018-8" stroke="currentColor" strokeWidth="3" strokeLinecap="round" className="opacity-75" />
                                </svg>
                                Google hesabınız doğrulanıyor…
                            </div>
                        )}

                        {error && (
                            <div className="mt-4 rounded-xl border border-rose-500/20 bg-rose-500/10 p-3 text-sm text-rose-300">
                                {error}
                            </div>
                        )}
                    </div>

                    <div className="mt-6 grid gap-3 sm:grid-cols-2">
                        <Link
                            href="/giris"
                            className="h-11 rounded-xl border border-white/10 bg-white/5 hover:bg-white/8 text-white/80 hover:text-white transition-all flex items-center justify-center"
                        >
                            Diğer Giriş Yöntemleri
                        </Link>
                        <Link
                            href="/ucretsiz-basla"
                            className="h-11 rounded-xl bg-gradient-to-r from-accent-500 to-electric-500 hover:from-accent-400 hover:to-electric-400 text-white font-semibold transition-all flex items-center justify-center"
                        >
                            Hesap Oluştur
                        </Link>
                    </div>

                    <p className="mt-6 text-center text-sm text-white/45">
                        Canlı ortam için hem frontend hem backend tarafında aynı Google OAuth istemci kimliği tanımlanmalıdır.
                    </p>
                </div>
            </div>
        </>
    );
}
