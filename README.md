# EcomMarj - Premium SaaS E-Ticaret Karlılık Platformu

EcomMarj, e-ticaret satıcıları (özellikle Trendyol) için geliştirilmiş, ürün bazlı karlılık analizi, sipariş takibi ve detaylı finansal raporlama sunan premium bir SaaS platformudur. 

Farklı platformlardaki (başlangıçta Trendyol) mağazalarınızı bağlayarak; komisyon, kargo, KDV ve ek giderlerinizi tek bir ekranda görerek gerçek net kârınızı anlık olarak takip edebilirsiniz.

## 🚀 Teknolojiler (Tech Stack)

### Frontend
- **Framework:** Next.js 15 (App Router)
- **Dil:** TypeScript
- **Stil:** Tailwind CSS v4
- **Tasarım Dili:** Premium Dark UI, Glassmorphism, Responsive Design

### Backend
- **Framework:** Django 5 & Django REST Framework (DRF)
- **Dil:** Python
- **Veritabanı:** SQLite (Geliştirme) / PostgreSQL (Üretim planı)
- **Kimlik Doğrulama:** JWT (JSON Web Tokens)
- **Asenkron İşlemler:** Celery & Redis (API entegrasyonları ve senkronizasyon için)

## 🗺️ Yol Haritası (Roadmap)

### Faz 1: Temel Mimari ve Landing/Auth Sayfaları (✅ Tamamlandı)
- [x] Next.js ve Tailwind CSS v4 kurulumu
- [x] Premium SaaS Landing Page tasarımı (Hero, Özellikler, Dashboard Showcase, CTA)
- [x] Responsive düzenlemeler
- [x] Django Backend API altyapısı kurulumu
- [x] Kayıt (Register) ve Giriş (Login) endpoint'lerinin ve JWT yetkilendirmesinin yapılması
- [x] Frontend Auth sayfalarının oluşturulması ve API entegrasyonu (Test edildi ✅)

### Faz 2: Dashboard ve Core Mimari (⏳ Sonraki Adım)
- [ ] Giriş sonrası kullanıcıları genel durumu özetleyen Dashboard'a yönlendirme.
- [ ] Trendyol API entegrasyonu sayfasının yapılması (API Key vs. girişi).
- [ ] Trendyol entegrasyon menüsünün kullanıcı arayüzüne eklenmesi.
- [ ] Backend'de Trendyol'dan Ürün (Product) verilerinin çekilip SQLite/veritabanına yazılması.

### Faz 3: Siparişler ve Karlılık Analizi
- [ ] Sipariş verilerinin çekilmesi ve sipariş listesinin UI'da gösterilmesi.
- [ ] Gelişmiş karlılık hesaplama algoritmasının (Komisyon, Kargo, KDV, Stopaj, vb.) entegrasyonu.
- [ ] Her sipariş ve ürün için net kâr/zarar ekranlarının tasarımı ve backend bağlantısı.

### Faz 4: İleri Seviye Özellikler ve Diğer Pazaryerleri
- [ ] Ek giderlerin (Personel, Depo, Reklam) sisteme manuel girilebilmesi.
- [ ] Hepsiburada, N11, Amazon TR gibi diğer pazaryeri entegrasyonlarının eklenmesi.
- [ ] Fiyat optimizasyon bildirimleri ve yapay zeka destekli öneriler.

## ⚙️ Kurulum ve Çalıştırma

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows için: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Platform varsayılan olarak `http://localhost:3000` adresinde çalışacaktır. API istekleri `http://localhost:8000` adresine yönlendirilecektir.

---

## 🚀 Üretim (Production) Ortamına Kurulum (Hetzner vb.)

Bu proje tam otomatik Docker üretim ortamına hazırdır. 

**Adım 1:** Sunucuda repository'i indirin ve ayarları yapın:
```bash
git clone https://github.com/KULLANICI_ADI/EcomMarj.git
cd EcomMarj
cp .env.example backend/.env
# .env dosyasındaki şifreleri ve alan adınızı kendinize göre güncelleyin!
nano backend/.env
```

**Adım 2:** Tek Dokunuşla Canlıya Alın:
```bash
./deploy.sh
```

**Arkaplanda Neler Oluyor?**
- `deploy.sh` güncel kodları çeker ve Docker imajlarını derler.
- PostgreSQL ayağa kalkana kadar backend bekler (Healthcheck).
- `python manage.py collectstatic` ve `migrate` otomatik çalışır.
- Eğer veritabanı boşsa `.env` dosyasındaki bilgilerle otomatik bir Superuser yaratılır.
- Son olarak Django sunucusu performansı artırmak için **Gunicorn** ile ayağa kalkar.
