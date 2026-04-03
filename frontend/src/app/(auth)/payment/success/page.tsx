"use client";
import { useRouter } from "next/navigation";
import { CheckCircle } from "lucide-react";
export default function PaymentSuccessPage() {
    const router = useRouter();
    return (
        <div className="min-h-screen bg-[#070B14] flex items-center justify-center p-6">
            <div className="w-full max-w-md rounded-2xl border border-green-500/20 bg-slate-900/60 p-8 text-center">
                <div className="flex items-center justify-center w-16 h-16 rounded-full bg-green-500/15 border border-green-500/30 mb-6 mx-auto">
                    <CheckCircle size={30} className="text-green-400" />
                </div>
                <h1 className="text-xl font-bold text-white mb-3">Ödemeniz Alındı!</h1>
                <p className="text-slate-400 text-sm leading-relaxed mb-6">
                    Aboneliğiniz başarıyla aktif edildi. Tüm özelliklere erişebilirsiniz.
                </p>
                <button onClick={() => router.push("/dashboard")}
                    className="w-full py-3 rounded-lg bg-green-600 hover:bg-green-500 text-white font-semibold text-sm transition-colors">
                    Dashboard'a Git
                </button>
            </div>
        </div>
    );
}
