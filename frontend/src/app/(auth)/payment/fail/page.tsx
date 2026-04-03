"use client";
import { useRouter } from "next/navigation";
import { XCircle } from "lucide-react";
export default function PaymentFailPage() {
    const router = useRouter();
    return (
        <div className="min-h-screen bg-[#070B14] flex items-center justify-center p-6">
            <div className="w-full max-w-md rounded-2xl border border-red-500/20 bg-slate-900/60 p-8 text-center">
                <div className="flex items-center justify-center w-16 h-16 rounded-full bg-red-500/15 border border-red-500/30 mb-6 mx-auto">
                    <XCircle size={30} className="text-red-400" />
                </div>
                <h1 className="text-xl font-bold text-white mb-3">Ödeme Başarısız</h1>
                <p className="text-slate-400 text-sm leading-relaxed mb-6">
                    Ödemeniz işlenemedi. Lütfen kart bilgilerinizi kontrol edip tekrar deneyin.
                </p>
                <button onClick={() => router.push("/subscription")}
                    className="w-full py-3 rounded-lg bg-slate-700 hover:bg-slate-600 text-white font-semibold text-sm transition-colors border border-slate-600">
                    Tekrar Dene
                </button>
            </div>
        </div>
    );
}
