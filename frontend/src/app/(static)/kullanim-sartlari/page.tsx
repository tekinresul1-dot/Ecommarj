import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Kullanım Şartları — EcomMarj",
    description: "EcomMarj kullanım şartları ve koşulları.",
};

export default function TermsPage() {
    return (
        <div className="pt-28 pb-20">
            <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
                <h1 className="text-3xl sm:text-4xl font-bold text-white mb-8">Kullanım Şartları</h1>
                <div className="prose prose-invert prose-slate max-w-none space-y-6 text-slate-300 leading-relaxed text-[15px]">
                    <p className="text-slate-400 text-sm">Son güncelleme: Mart 2026</p>

                    <section>
                        <h2 className="text-xl font-semibold text-white mt-8 mb-3">1. Kabul ve Onay</h2>
                        <p>
                            EcomMarj platformuna kayıt olarak veya hizmetleri kullanarak işbu kullanım şartlarını
                            kabul etmiş sayılırsınız. Bu şartları kabul etmiyorsanız platformu kullanmayınız.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mt-8 mb-3">2. Hizmet Tanımı</h2>
                        <p>
                            EcomMarj, e-ticaret satıcılarına pazaryeri verilerini analiz ederek karlılık raporları
                            sunan bir SaaS platformudur. Platform, Trendyol API entegrasyonu aracılığıyla sipariş,
                            ürün ve finansal verileri çekerek analiz eder.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mt-8 mb-3">3. Kullanıcı Sorumlulukları</h2>
                        <ul className="list-disc pl-5 space-y-1 mt-2">
                            <li>Hesap bilgilerinizin güvenliğinden siz sorumlusunuz</li>
                            <li>API kimlik bilgilerinizi üçüncü kişilerle paylaşmayınız</li>
                            <li>Platformu yasa dışı amaçlarla kullanmayınız</li>
                            <li>Sağladığınız bilgilerin doğruluğundan siz sorumlusunuz</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mt-8 mb-3">4. Hizmet Seviyesi</h2>
                        <p>
                            EcomMarj, hizmetlerinin kesintisiz ve hatasız olması için azami özeni gösterir ancak
                            teknik nedenlerle oluşabilecek geçici kesintilerden sorumlu tutulamaz. Planlı bakım
                            çalışmaları önceden bildirilir.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mt-8 mb-3">5. Fikri Mülkiyet</h2>
                        <p>
                            Platform ve içeriğinin tüm fikri mülkiyet hakları EcomMarj&apos;a aittir.
                            Platformun kopyalanması, tersine mühendislik yapılması veya izinsiz dağıtılması yasaktır.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mt-8 mb-3">6. Hesap İptali</h2>
                        <p>
                            Hesabınızı istediğiniz zaman iptal edebilirsiniz. İptal durumunda verileriniz
                            KVKK kapsamında belirtilen süre sonunda tamamen silinir.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mt-8 mb-3">7. Uyuşmazlık Çözümü</h2>
                        <p>
                            İşbu şartlardan doğan uyuşmazlıklar Türkiye Cumhuriyeti kanunlarına tabidir
                            ve İstanbul Mahkemeleri yetkilidir.
                        </p>
                    </section>
                </div>
            </div>
        </div>
    );
}
