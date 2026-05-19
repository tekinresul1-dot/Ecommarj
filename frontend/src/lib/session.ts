/**
 * Centralised client session storage.
 *
 * Tokens are kept in localStorage (used by the fetch client) AND mirrored to
 * a path-wide `access_token` cookie so the server-side middleware can guard
 * protected routes (middleware cannot read localStorage).
 *
 * NOTE: the cookie is JS-readable by necessity (the SPA reads it on refresh).
 * Moving to an HttpOnly, server-set cookie is the next hardening step and is
 * tracked separately — this still removes the "no server-side guard at all"
 * gap.
 */

const ACCESS_KEY = "access_token";
const REFRESH_KEY = "refresh_token";
const USER_KEY = "user";

// ~8h, aligned with the backend access-token lifetime.
const ACCESS_MAX_AGE = 8 * 60 * 60;

function writeCookie(name: string, value: string, maxAge: number) {
  if (typeof document === "undefined") return;
  const secure = location.protocol === "https:" ? "; Secure" : "";
  document.cookie = `${name}=${encodeURIComponent(value)}; path=/; max-age=${maxAge}; SameSite=Lax${secure}`;
}

function deleteCookie(name: string) {
  if (typeof document === "undefined") return;
  document.cookie = `${name}=; path=/; max-age=0; SameSite=Lax`;
}

export function setSession(access: string, refresh?: string, user?: unknown) {
  if (typeof window === "undefined") return;
  localStorage.setItem(ACCESS_KEY, access);
  writeCookie(ACCESS_KEY, access, ACCESS_MAX_AGE);
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
  if (user !== undefined) localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(USER_KEY);
  deleteCookie(ACCESS_KEY);
}

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_KEY);
}
