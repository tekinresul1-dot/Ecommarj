import type { Metadata } from "next";
import { CheckCircle2, AlertTriangle } from "lucide-react";

export const metadata: Metadata = {
    title: "Sistem Durumu — EcomMarj",
    description: "EcomMarj servislerinin anlık durumunu görüntüleyin.",
};

const services = [
    { name: "Web Uygulaması", status: "operational" },
    { name: "Backend API", status: "operational" },
    { name: "Trendyol Senkronizasyon", status: "operational" },
    { name: "Veritabanı", status: "operational" },
    { name: "Kimlik Doğrulama", status: "operational" },
];

export default function StatusPage() {
    const allOk = services.every((s) => s.status === "operational");

    return (
        <div className="pt-28 pb-20">
            <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="text-center mb-12">
                    <h1 className="text-4xl sm:text-5xl font-bold text-white mb-4">
                        Sistem <span className="gradient-text">Durumu</span>
                    </h1>
                </div>

                <div className={`rounded-2xl p-6 mb-8 text-center ${allOk ? "bg-emerald-500/10 border border-emerald-500/20" : "bg-amber-500/10 border border-amber-500/20"}`}>
                    {allOk ? (
                        <div className="flex items-center justify-center gap-2 text-emerald-400 font-medium">
                            <CheckCircle2 className="w-5 h-5" /> Tüm sistemler çalışıyor
                        </div>
                    ) : (
                        <div className="flex items-center justify-center gap-2 text-amber-400 font-medium">
                            <AlertTriangle className="w-5 h-5" /> Bazı servislerde sorun var
                        </div>
                    )}
                </div>

                <div className="glass-card rounded-2xl divide-y divide-white/5">
                    {services.map((svc) => (
                        <div key={svc.name} className="flex items-center justify-between px-6 py-4">
                            <span className="text-sm text-white font-medium">{svc.name}</span>
                            <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-400">
                                <div className="w-2 h-2 rounded-full bg-emerald-400" />
                                Çalışıyor
                            </span>
                        </div>
                    ))}
                </div>

                <p className="text-center text-xs text-slate-600 mt-6">Son güncelleme: Bugün</p>
            </div>
        </div>
    );
}
