import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Routes that require an authenticated session. Anything outside these
// prefixes (marketing/static pages, auth pages, payment result pages) stays
// public.
const PROTECTED_PREFIXES = [
  "/dashboard",
  "/live",
  "/products",
  "/reports",
  "/settings",
  "/subscription",
  "/margins",
  "/payouts",
  "/alerts",
  "/pricing-rules",
  "/product-settings",
  "/promo-profit",
  // Yönetici paneli — token şart; is_staff doğrulaması (admin) layout'unda
  // /auth/me/ üzerinden yapılır.
  "/admin",
];

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  const isProtected = PROTECTED_PREFIXES.some(
    (p) => pathname === p || pathname.startsWith(p + "/"),
  );
  if (!isProtected) return NextResponse.next();

  const token = req.cookies.get("access_token")?.value;
  if (!token) {
    const url = req.nextUrl.clone();
    url.pathname = "/giris";
    url.searchParams.set("next", pathname);
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  // Run on every route except Next internals, API proxy ve Django admin
  // (Django session ile authentic edilir, JWT cookie kontrolü uygulanmamalı).
  matcher: ["/((?!_next/static|_next/image|favicon.ico|api/|django-admin/).*)"],
};
