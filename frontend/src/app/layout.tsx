import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import { Toaster } from "sonner";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-geist-sans",
});

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL || "https://ecommarj.com";
const TITLE = "EcomMarj – Trendyol Satıcıları İçin Karlılık ve Büyüme Platformu";
const DESCRIPTION =
  "Trendyol mağazanızın gerçek kârlılığını tek ekranda görün. Komisyon, kargo, iade ve gizli maliyetleri otomatik hesaplayın. EcomMarj ile zarar eden ürünlerinizi tespit edip büyümeye odaklanın.";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: TITLE,
  description: DESCRIPTION,
  keywords: "trendyol, karlılık, e-ticaret, satıcı, analiz, sipariş, komisyon",
  alternates: { canonical: "/" },
  robots: {
    index: true,
    follow: true,
    googleBot: { index: true, follow: true },
  },
  openGraph: {
    type: "website",
    locale: "tr_TR",
    url: SITE_URL,
    siteName: "EcomMarj",
    title: TITLE,
    description: DESCRIPTION,
  },
  twitter: {
    card: "summary_large_image",
    title: TITLE,
    description: DESCRIPTION,
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#0a0e1a",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="tr" className="dark">
      <body className={`${inter.variable} antialiased`}>
        {children}
        <Toaster position="top-right" richColors theme="dark" />
      </body>
    </html>
  );
}
