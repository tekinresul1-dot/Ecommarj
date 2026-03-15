import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "KVKK Aydınlatma Metni — EcomMarj",
    description: "EcomMarj KVKK kapsamında kişisel verilerin korunması aydınlatma metni.",
};

export default function KvkkPage() {
    return (
        <div className="pt-28 pb-20">
            <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
                <h1 className="text-3xl sm:text-4xl font-bold text-white mb-8">KVKK Aydınlatma Metni</h1>
                <div className="prose prose-invert prose-slate max-w-none space-y-6 text-slate-300 leading-relaxed text-[15px]">
                    <p className="text-slate-400 text-sm">Son güncelleme: Mart 2026</p>

                    <p>
                        6698 sayılı Kişisel Verilerin Korunması Kanunu (&ldquo;KVKK&rdquo;) kapsamında, veri sorumlusu sıfatıyla
                        EcomMarj olarak kişisel verilerinizin işlenmesine ilişkin aşağıdaki bilgilendirmeyi sunarız.
                    </p>

                    <section>
                        <h2 className="text-xl font-semibold text-white mt-8 mb-3">1. Veri Sorumlusu</h2>
                        <p>EcomMarj platformu, KVKK kapsamında veri sorumlusu sıfatıyla hareket etmektedir.</p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mt-8 mb-3">2. İşlenen Kişisel Veriler</h2>
                        <ul className="list-disc pl-5 space-y-1 mt-2">
                            <li><strong className="text-white">Kimlik Bilgileri:</strong> Ad, soyad</li>
                            <li><strong className="text-white">İletişim Bilgileri:</strong> E-posta adresi, telefon numarası</li>
                            <li><strong className="text-white">İşlem Güvenliği:</strong> Şifre (hash olarak), IP adresi, oturum bilgileri</li>
                            <li><strong className="text-white">Ticari Bilgiler:</strong> Trendyol API kimlik bilgileri (şifreli), sipariş ve ürün verileri</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mt-8 mb-3">3. İşleme Amaçları</h2>
                        <ul className="list-disc pl-5 space-y-1 mt-2">
                            <li>Platform üyelik ve hesap yönetimi süreçlerinin yürütülmesi</li>
                            <li>E-ticaret karlılık analizi hizmetlerinin sunulması</li>
                            <li>Pazaryeri entegrasyonlarının gerçekleştirilmesi</li>
                            <li>Yasal yükümlülüklerin yerine getirilmesi</li>
                            <li>Bilgi güvenliği süreçlerinin yürütülmesi</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mt-8 mb-3">4. Hukuki Sebepler</h2>
                        <p>Kişisel verileriniz KVKK&apos;nın 5. maddesinde belirtilen aşağıdaki hukuki sebeplere dayanılarak işlenir:</p>
                        <ul className="list-disc pl-5 space-y-1 mt-2">
                            <li>Açık rızanızın bulunması</li>
                            <li>Sözleşmenin kurulması ve ifası</li>
                            <li>Hukuki yükümlülüğün yerine getirilmesi</li>
                            <li>Meşru menfaat</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mt-8 mb-3">5. Veri Aktarımı</h2>
                        <p>
                            Kişisel verileriniz üçüncü taraflarla ticari amaçla paylaşılmaz.
                            Yalnızca yasal zorunluluklar çerçevesinde yetkili kamu kurum ve kuruluşlarına aktarılabilir.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mt-8 mb-3">6. Haklarınız</h2>
                        <p>KVKK&apos;nın 11. maddesi kapsamında aşağıdaki haklara sahipsiniz:</p>
                        <ul className="list-disc pl-5 space-y-1 mt-2">
                            <li>Kişisel verilerinizin işlenip işlenmediğini öğrenme</li>
                            <li>İşlenmişse buna ilişkin bilgi talep etme</li>
                            <li>İşlenme amacını ve amacına uygun kullanılıp kullanılmadığını öğrenme</li>
                            <li>Eksik veya yanlış işlenmişse düzeltilmesini isteme</li>
                            <li>Silinmesini veya yok edilmesini isteme</li>
                            <li>İtiraz etme</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mt-8 mb-3">7. Başvuru</h2>
                        <p>
                            KVKK kapsamındaki taleplerinizi destek@ecommarj.com adresine yazılı olarak
                            veya platformdaki iletişim formu aracılığıyla iletebilirsiniz.
                            Başvurunuz en geç 30 gün içinde yanıtlanacaktır.
                        </p>
                    </section>
                </div>
            </div>
        </div>
    );
}
