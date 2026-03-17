import type { Metadata } from "next";
import { Target, Eye, Users } from "lucide-react";

export const metadata: Metadata = {
    title: "Hakkımızda — EcomMarj",
    description: "EcomMarj'ın hikayesi, misyonu ve vizyonu. Trendyol satıcılarına gerçek karlılık görünürlüğü sağlıyoruz.",
};

export default function AboutPage() {
    return (
        <div className="pt-28 pb-20">
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="text-center mb-16">
                    <h1 className="text-4xl sm:text-5xl font-bold text-white mb-4">
                        <span className="gradient-text">EcomMarj</span> Hakkında
                    </h1>
                    <p className="text-lg text-slate-400 max-w-2xl mx-auto">
                        E-ticaret satıcılarına gerçek karlılık görünürlüğü kazandırıyoruz.
                    </p>
                </div>

                <div className="glass-card rounded-2xl p-10 mb-10">
                    <h2 className="text-2xl font-bold text-white mb-4">Hikayemiz</h2>
                    <p className="text-slate-300 leading-relaxed mb-4">
                        EcomMarj, Trendyol&apos;da satış yapan girişimcilerin en büyük sorunlarından birini çözmek için doğdu:
                        &ldquo;Gerçekten ne kadar kazanıyorum?&rdquo; sorusu. Komisyonlar, kargo maliyetleri, iadeler, KDV
                        ve gizli kesintiler nedeniyle birçok satıcı gerçek karlılığını bilmiyor.
                    </p>
                    <p className="text-slate-300 leading-relaxed">
                        Biz bu sorunu çözüyoruz. Trendyol API entegrasyonu ile tüm sipariş, ürün ve finansal verileri
                        otomatik çekerek her ürün, her sipariş ve her kategori için gerçek net karlılığı hesaplıyoruz.
                    </p>
                </div>

                <div className="grid gap-6 md:grid-cols-3">
                    {[
                        { icon: Target, title: "Misyonumuz", text: "E-ticaret satıcılarının veri odaklı kararlar almasını sağlayarak karlılıklarını artırmak." },
                        { icon: Eye, title: "Vizyonumuz", text: "Türkiye'nin lider e-ticaret karlılık ve büyüme platformu olmak." },
                        { icon: Users, title: "Ekibimiz", text: "Yazılım mühendisleri ve e-ticaret uzmanlarından oluşan tutkulu bir ekip." },
                    ].map((item) => (
                        <div key={item.title} className="glass-card rounded-2xl p-6 text-center">
                            <div className="w-12 h-12 rounded-xl bg-accent-500/10 border border-accent-500/20 flex items-center justify-center mx-auto mb-4">
                                <item.icon className="w-6 h-6 text-accent-400" />
                            </div>
                            <h3 className="text-lg font-semibold text-white mb-2">{item.title}</h3>
                            <p className="text-sm text-slate-400">{item.text}</p>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
