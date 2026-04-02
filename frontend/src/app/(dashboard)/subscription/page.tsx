"use client";

import { useRouter } from "next/navigation";
import { AlertTriangle, Mail, ArrowLeft } from "lucide-react";

export default function SubscriptionPage() {
    const router = useRouter();

    return (
        <div className="min-h-screen bg-[#070B14] flex items-center justify-center p-6">
            <div className="w-full max-w-md">
                <div className="rounded-2xl border border-orange-500/20 bg-slate-900/60 p-8 text-center shadow-2xl">
                    {/* Icon */}
                    <div className="flex items-center justify-center w-16 h-16 rounded-full bg-orange-500/15 border border-orange-500/30 mb-6 mx-auto">
                        <AlertTriangle size={30} className="text-orange-400" />
                    </div>

                    {/* Title */}
                    <h1 className="text-xl font-bold text-white mb-3">
                        Aboneliğiniz Aktif Değil
                    </h1>

                    {/* Description */}
                    <p className="text-slate-400 text-sm leading-relaxed mb-6">
                        Bu sayfaya erişebilmek için aktif bir aboneliğe ihtiyacınız var.
                        Aboneliğinizi yenilemek veya sorun yaşıyorsanız bizimle iletişime geçin.
                    </p>

                    {/* Contact */}
                    <a
                        href="mailto:destek@ecommarj.com"
                        className="inline-flex items-center gap-2 w-full justify-center py-3 rounded-lg bg-orange-500 hover:bg-orange-600 text-white font-semibold text-sm transition-colors mb-3"
                    >
                        <Mail size={16} />
                        destek@ecommarj.com
                    </a>

                    <button
                        onClick={() => router.back()}
                        className="inline-flex items-center gap-2 w-full justify-center py-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium text-sm transition-colors border border-slate-700"
                    >
                        <ArrowLeft size={15} />
                        Geri Dön
                    </button>
                </div>
            </div>
        </div>
    );
}
