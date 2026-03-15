import type { Metadata } from "next";

export const metadata: Metadata = {
    title: "Gizlilik Politikası — EcomMarj",
    description: "EcomMarj gizlilik politikası. Kişisel verilerinizin korunması hakkında bilgilendirme.",
};

export default function PrivacyPage() {
    return (
        <div className="pt-28 pb-20">
            <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
                <h1 className="text-3xl sm:text-4xl font-bold text-white mb-8">Gizlilik Politikası</h1>
                <div className="prose prose-invert prose-slate max-w-none space-y-6 text-slate-300 leading-relaxed text-[15px]">
                    <p className="text-slate-400 text-sm">Son güncelleme: Mart 2026</p>

                    <section>
                        <h2 className="text-xl font-semibold text-white mt-8 mb-3">1. Toplanan Veriler</h2>
                        <p>EcomMarj, hizmetlerini sunmak için aşağıdaki verileri toplar:</p>
                        <ul className="list-disc pl-5 space-y-1 mt-2">
                            <li>Ad, soyad ve iletişim bilgileri (kayıt sırasında)</li>
                            <li>E-posta adresi ve şifre (kimlik doğrulama amacıyla)</li>
                            <li>Trendyol API kimlik bilgileri (pazaryeri entegrasyonu için, şifreli olarak saklanır)</li>
                            <li>Sipariş ve ürün verileri (Trendyol API üzerinden otomatik çekilir)</li>
                            <li>IP adresi ve tarayıcı bilgileri (güvenlik ve analitik amaçlı)</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mt-8 mb-3">2. Verilerin Kullanımı</h2>
                        <p>Toplanan veriler yalnızca aşağıdaki amaçlarla kullanılır:</p>
                        <ul className="list-disc pl-5 space-y-1 mt-2">
                            <li>Karlılık analizi ve raporlama hizmetlerinin sunulması</li>
                            <li>Hesap yönetimi ve kimlik doğrulama</li>
                            <li>Platform performansının iyileştirilmesi</li>
                            <li>Müşteri desteği sağlanması</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mt-8 mb-3">3. Veri Güvenliği</h2>
                        <p>
                            Tüm API bilgileri 256-bit şifreleme (AES) ile saklanır. SSL/TLS sertifikaları ile
                            tüm veri iletişimi şifrelenir. Veritabanı erişimleri yetkilendirme seviyelerinde kontrol edilir.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mt-8 mb-3">4. Üçüncü Taraflarla Paylaşım</h2>
                        <p>
                            Kişisel verileriniz hiçbir üçüncü tarafla ticari amaçla paylaşılmaz. Yalnızca yasal zorunluluk
                            halinde yetkili makamlarla paylaşım yapılabilir.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mt-8 mb-3">5. Çerezler</h2>
                        <p>
                            EcomMarj, oturum yönetimi için JWT tabanlı kimlik doğrulama tokenları kullanır.
                            Üçüncü taraf izleme çerezleri kullanılmaz.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mt-8 mb-3">6. İletişim</h2>
                        <p>
                            Gizlilik politikamız hakkında sorularınız için destek@ecommarj.com adresinden
                            bizimle iletişime geçebilirsiniz.
                        </p>
                    </section>
                </div>
            </div>
        </div>
    );
}
