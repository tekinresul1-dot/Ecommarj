import type { Metadata } from "next";
import Link from "next/link";
import { Rocket, Heart } from "lucide-react";

export const metadata: Metadata = {
    title: "Kariyer — EcomMarj",
    description: "EcomMarj ekibine katılın. E-ticaretin geleceğini birlikte şekillendirelim.",
};

export default function CareerPage() {
    return (
        <div className="pt-28 pb-20">
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="text-center mb-16">
                    <h1 className="text-4xl sm:text-5xl font-bold text-white mb-4">
                        Birlikte <span className="gradient-text">Büyüyelim</span>
                    </h1>
                    <p className="text-lg text-slate-400 max-w-2xl mx-auto">
                        E-ticaretin geleceğini şekillendirmek isteyen tutkulu insanlar arıyoruz.
                    </p>
                </div>

                <div className="glass-card rounded-2xl p-10 text-center mb-10">
                    <div className="w-16 h-16 rounded-2xl bg-accent-500/10 border border-accent-500/20 flex items-center justify-center mx-auto mb-6">
                        <Rocket className="w-8 h-8 text-accent-400" />
                    </div>
                    <h2 className="text-2xl font-bold text-white mb-4">Şu an açık pozisyon bulunmuyor</h2>
                    <p className="text-slate-400 max-w-lg mx-auto mb-8 leading-relaxed">
                        Yeni pozisyonlar açıldığında burada paylaşacağız. Bize özgeçmişinizi göndermek isterseniz
                        aşağıdaki iletişim sayfamızdan ulaşabilirsiniz.
                    </p>
                    <Link
                        href="/iletisim"
                        className="inline-flex items-center gap-2 bg-gradient-to-r from-accent-500 to-electric-500 text-white px-8 py-3 rounded-xl font-medium hover:opacity-90 transition-opacity shadow-lg shadow-accent-500/20"
                    >
                        <Heart className="w-4 h-4" /> İletişime Geç
                    </Link>
                </div>

                <div className="glass-card rounded-2xl p-8">
                    <h3 className="text-lg font-semibold text-white mb-4">Neden EcomMarj?</h3>
                    <div className="grid gap-4 sm:grid-cols-2">
                        {["Uzaktan çalışma imkanı", "Esnek çalışma saatleri", "Hızlı büyüyen startup ekosistemi", "Teknoloji odaklı kültür"].map((perk) => (
                            <div key={perk} className="flex items-center gap-2 text-sm text-slate-300">
                                <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                                {perk}
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
