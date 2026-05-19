import type { MetadataRoute } from "next";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://ecommarj.com";

// Herkese açık (auth gerektirmeyen) sayfalar
const ROUTES = [
  "",
  "/giris",
  "/ucretsiz-basla",
  "/ozellikler",
  "/fiyatlandirma",
  "/entegrasyonlar",
  "/hakkimizda",
  "/iletisim",
  "/sss",
  "/yardim",
  "/blog",
  "/dokumantasyon",
  "/api-dokumantasyonu",
  "/kariyer",
  "/durum",
  "/kvkk",
  "/gizlilik",
  "/kullanim-sartlari",
];

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  return ROUTES.map((path) => ({
    url: `${SITE_URL}${path}`,
    lastModified: now,
    changeFrequency: "weekly",
    priority: path === "" ? 1 : 0.7,
  }));
}
