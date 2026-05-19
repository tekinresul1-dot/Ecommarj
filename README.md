# EcomMarj - Premium SaaS E-Ticaret Karlılık Platformu

EcomMarj, e-ticaret satıcıları (özellikle Trendyol) için geliştirilmiş, ürün bazlı karlılık analizi, sipariş takibi ve detaylı finansal raporlama sunan premium bir SaaS platformudur.

## 🛡️ Yönetici Paneli (Admin Panel)

EcomMarj, kullanıcı, abonelik, ödeme ve giriş kodu yönetimi için tam özellikli bir yönetici paneline sahiptir.

| Yol | Açıklama |
|---|---|
| `/admin` | Yeni **Next.js yönetici paneli** (dashboard, kullanıcı/abonelik/ödeme/kod/log yönetimi). Yalnızca `is_staff` kullanıcılar. |
| `/django-admin/` | Klasik Django admin (Jazzmin) — düşük seviyeli model erişimi. |
| `/api/admin/...` | Yönetici REST API'leri (IsAdminUser ile korunur). |

### Kurulum

```bash
# Migration'ları uygula (yeni yönetici paneli modellerini kurar)
docker compose exec backend python manage.py migrate

# Test admin'i ve örnek test kullanıcılarını oluştur
docker compose exec backend python manage.py create_test_admin
```

**Test girişi:** `admin@ecommarj.com` / `Admin123!`  (üretimde **mutlaka değiştirin**).

### Özellikler

- **Kullanıcı yönetimi:** arama/filtre/sayfalama, aktif/pasif/askıya al, admin notu, öncelikli/riskli bayrakları, admin_override (paywall'u atla).
- **Abonelik:** plan değiştirme, 1/3/6 ay & 1 yıl uzatma, trial başlat/uzat, iptal, toplu işlem.
- **Ödeme:** PayTR + manuel kayıt, durum filtreleri, gelir istatistikleri, fatura notu, gecikmiş kontrolü.
- **Giriş kodu:** OTP yerine geçen 8 haneli alfanumerik kod; süreli/süresiz, maks. kullanım, 5 yanlışta 15 dk IP kilidi.
- **Audit log:** tüm yönetici eylemleri otomatik kayıt; CSV export.
- **Otomasyon (Celery beat):** her gece bitişi geçen abonelikleri *expired* yap, 3 gün öncesinden uyarı maili, 7+ gün gecikmiş ödemesi olanların erişimini kes.

### Yeni admin (superuser) oluşturma

```bash
# Yöntem 1: Django'nun yerleşik komutu
docker compose exec backend python manage.py createsuperuser

# Yöntem 2: hızlı test verisiyle birlikte
docker compose exec backend python manage.py create_test_admin
```

### Yeni zorunlu environment değişkenleri

Önceki güvenlik sertleştirmesi ile birlikte aşağıdaki env değişkenleri **zorunlu** hâle gelmiştir:

```
DJANGO_SECRET_KEY      # python -c "import secrets; print(secrets.token_urlsafe(64))"
ENCRYPTION_KEY         # python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
TRENDYOL_WEBHOOK_SECRET  # webhook için paylaşılan gizli (boşsa endpoint reddeder)
PAYTR_TEST_MODE=False  # üretimde mutlaka False
```

---

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

### Google OAuth

Google ile giriş için ortam değişkenlerinde `GOOGLE_CLIENT_ID` ve `GOOGLE_CLIENT_SECRET` tanımlanmalıdır. Frontend tarafında Google butonunun görünebilmesi için aynı istemci kimliği `NEXT_PUBLIC_GOOGLE_CLIENT_ID` olarak da verilebilir; boş bırakılırsa Next.js yapılandırması `GOOGLE_CLIENT_ID` değerini kullanır.

Google Cloud Console'da Authorized redirect URI olarak şunu ekleyin:

```text
https://www.ecommarj.com/auth/google/callback
```

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
