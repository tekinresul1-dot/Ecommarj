import type { Metadata } from "next";
import Link from "next/link";
import { Code2, Lock, Zap } from "lucide-react";

export const metadata: Metadata = {
    title: "API — EcomMarj",
    description: "EcomMarj Geliştirici API. Karlılık verilerinize programatik erişim sağlayın.",
};

export default function ApiPage() {
    return (
        <div className="pt-28 pb-20">
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="text-center mb-16">
                    <div className="inline-flex items-center gap-2 bg-accent-500/10 border border-accent-500/20 text-accent-400 px-4 py-1.5 rounded-full text-sm font-medium mb-6">
                        <Code2 className="w-4 h-4" /> Geliştirici API
                    </div>
                    <h1 className="text-4xl sm:text-5xl font-bold text-white mb-4">
                        EcomMarj <span className="gradient-text">API</span>
                    </h1>
                    <p className="text-lg text-slate-400 max-w-2xl mx-auto">
                        Karlılık verilerinize programatik olarak erişin, kendi otomasyon ve raporlama araçlarınızı oluşturun.
                    </p>
                </div>

                <div className="glass-card rounded-2xl p-10 mb-10">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="w-3 h-3 rounded-full bg-amber-400 animate-pulse" />
                        <span className="text-amber-400 font-medium">Yakında Kullanıma Açılacak</span>
                    </div>
                    <p className="text-slate-300 leading-relaxed mb-8">
                        Public REST API şu anda geliştirme aşamasındadır. Kurumsal plan kullanıcılarımız için
                        öncelikli erken erişim sağlanacaktır. API ile sipariş verileri, ürün karlılığı ve finansal
                        raporlara programatik erişim mümkün olacak.
                    </p>

                    <div className="grid gap-6 sm:grid-cols-3">
                        <div className="flex items-start gap-3">
                            <Zap className="w-5 h-5 text-accent-400 mt-0.5 shrink-0" />
                            <div>
                                <h4 className="text-white font-medium mb-1">RESTful JSON</h4>
                                <p className="text-sm text-slate-400">Standart REST endpoint&apos;ler ve JSON yanıtları.</p>
                            </div>
                        </div>
                        <div className="flex items-start gap-3">
                            <Lock className="w-5 h-5 text-accent-400 mt-0.5 shrink-0" />
                            <div>
                                <h4 className="text-white font-medium mb-1">JWT Kimlik Doğrulama</h4>
                                <p className="text-sm text-slate-400">Güvenli token tabanlı erişim.</p>
                            </div>
                        </div>
                        <div className="flex items-start gap-3">
                            <Code2 className="w-5 h-5 text-accent-400 mt-0.5 shrink-0" />
                            <div>
                                <h4 className="text-white font-medium mb-1">Webhook Desteği</h4>
                                <p className="text-sm text-slate-400">Gerçek zamanlı veri bildirimleri.</p>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="text-center">
                    <Link
                        href="/iletisim"
                        className="inline-flex items-center gap-2 bg-gradient-to-r from-accent-500 to-electric-500 text-white px-8 py-3 rounded-xl font-medium hover:opacity-90 transition-opacity shadow-lg shadow-accent-500/20"
                    >
                        Erken Erişim İçin İletişime Geçin
                    </Link>
                </div>
            </div>
        </div>
    );
}
