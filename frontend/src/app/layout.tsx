import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Toaster } from "sonner";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-geist-sans",
});

export const metadata: Metadata = {
  title: "EcomPro – Trendyol Satıcıları İçin Karlılık ve Büyüme Platformu",
  description:
    "Trendyol mağazanızın gerçek karlılığını saniyeler içinde görün. Komisyon, kargo, iade ve tüm giderlerinizi otomatik hesaplayarak büyümenizi hızlandırın.",
  keywords: "trendyol, karlılık, e-ticaret, satıcı, analiz, sipariş, komisyon",
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
