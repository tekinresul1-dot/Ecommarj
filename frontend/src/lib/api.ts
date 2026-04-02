const getApiBase = () => {
    if (typeof window !== "undefined") {
        // In production, Nginx proxies /api to port 8000.
        // Using relative path ensures it works on whatever port/domain the user is on.
        return "/api";
    }
    let base = process.env.NEXT_PUBLIC_API_BASE || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
    return base.replace(/\/$/, "");
};

const API_BASE = getApiBase();

const cleanPath = (endpoint: string): string => {
    let clean = endpoint.startsWith('/') ? endpoint : '/' + endpoint;
    const [pathPart, queryPart] = clean.split('?');
    if (!pathPart.endsWith('/')) {
        clean = pathPart + '/' + (queryPart ? '?' + queryPart : '');
    }
    return clean;
};

const getHeaders = (endpoint?: string): Record<string, string> => {
    const token = localStorage.getItem("access_token");
    const isPublicAuthEndpoint = endpoint && (
        endpoint.includes('/auth/login') ||
        endpoint.includes('/auth/register') ||
        endpoint.includes('/auth/token/refresh')
    );
    return {
        "Content-Type": "application/json",
        ...(token && !isPublicAuthEndpoint ? { Authorization: `Bearer ${token}` } : {}),
    };
};

/** Token yenilemeyi dener. Başarılıysa yeni access_token kaydeder ve true döner. */
let _isRefreshing = false;
let _refreshSubscribers: Array<(token: string | null) => void> = [];

async function tryRefreshToken(): Promise<string | null> {
    const refreshToken = localStorage.getItem("refresh_token");
    if (!refreshToken) return null;

    if (_isRefreshing) {
        // Başka bir istek zaten yenileme yapıyor, bekle
        return new Promise((resolve) => {
            _refreshSubscribers.push(resolve);
        });
    }

    _isRefreshing = true;
    try {
        const res = await fetch(`${API_BASE}/auth/token/refresh/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh: refreshToken }),
        });

        if (!res.ok) {
            // Refresh token da geçersiz — tamamen oturumu kapat
            _refreshSubscribers.forEach((cb) => cb(null));
            _refreshSubscribers = [];
            return null;
        }

        const data = await res.json();
        const newAccess: string = data.access;
        localStorage.setItem("access_token", newAccess);
        if (data.refresh) {
            localStorage.setItem("refresh_token", data.refresh);
        }
        _refreshSubscribers.forEach((cb) => cb(newAccess));
        _refreshSubscribers = [];
        return newAccess;
    } catch {
        _refreshSubscribers.forEach((cb) => cb(null));
        _refreshSubscribers = [];
        return null;
    } finally {
        _isRefreshing = false;
    }
}

function handleSubscriptionRequired(): void {
    if (typeof window !== "undefined" && window.location.pathname !== "/subscription") {
        window.location.href = "/subscription";
    }
}

function handleSessionExpired(): void {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
                if (typeof window !== "undefined" && window.location.pathname !== "/giris") {
        if (!window.location.search.includes("session_expired")) {
            window.location.href = "/giris?session_expired=true";
        }
    }
}

function parseErrorMsg(errorData: any, statusText: string, status: number): string {
    if (!errorData) return `API Hatası (${status}): ${statusText}`;
    if (typeof errorData === 'string') return errorData;
    
    // Handle DRF style {"errors": {...}}
    const target = errorData.errors || errorData;

    if (target.message) return String(target.message);
    if (target.error) return String(target.error);
    if (target.detail) return String(target.detail);
    
    if (typeof target === 'object') {
        // Handle field-specific errors: {"email": ["Already exists"], "password": [...]}
        const values = Object.values(target);
        if (values.length > 0) {
            const firstVal: any = values[0];
            if (Array.isArray(firstVal)) {
                return String(firstVal[0]);
            }
            if (typeof firstVal === 'string') {
                return firstVal;
            }
            if (typeof firstVal === 'object' && firstVal !== null) {
                // Nested object (like errors: { email: [...] })
                const nestedValues = Object.values(firstVal);
                if (nestedValues.length > 0 && Array.isArray(nestedValues[0])) {
                    return String(nestedValues[0][0]);
                }
            }
        }
    }
    
    return `API Hatası (${status}): ${statusText}`;
}

export const api = {
    get: async (endpoint: string) => {
        const cleanEndpoint = cleanPath(endpoint);

        let res = await fetch(`${API_BASE}${cleanEndpoint}`, {
            headers: getHeaders(cleanEndpoint),
        });

        // 401 → token yenilemeyi dene, sonra tekrar iste
        if (res.status === 401 && !cleanEndpoint.includes("/auth/")) {
            const newToken = await tryRefreshToken();
            if (newToken) {
                res = await fetch(`${API_BASE}${cleanEndpoint}`, {
                    headers: { "Content-Type": "application/json", Authorization: `Bearer ${newToken}` },
                });
            } else {
                handleSessionExpired();
                throw new Error("Oturum süresi doldu. Lütfen tekrar giriş yapın.");
            }
        }

        if (res.status === 403) {
            handleSubscriptionRequired();
            throw new Error("Bu özelliğe erişmek için aktif bir abonelik gereklidir.");
        }

        if (!res.ok) {
            const text = await res.text();
            console.error(`API Error on GET ${endpoint} (${res.status}): ${text.substring(0, 150)}`);
            throw new Error(`API Hatası (${res.status}): ${res.statusText}`);
        }

        const text = await res.text();
        return text ? JSON.parse(text) : {};
    },

    post: async (endpoint: string, data: any) => {
        const cleanEndpoint = cleanPath(endpoint);

        let res = await fetch(`${API_BASE}${cleanEndpoint}`, {
            method: "POST",
            headers: getHeaders(cleanEndpoint),
            body: JSON.stringify(data),
        });

        // 401 → token yenilemeyi dene, sonra tekrar iste
        if (res.status === 401 && !cleanEndpoint.includes("/auth/")) {
            const newToken = await tryRefreshToken();
            if (newToken) {
                res = await fetch(`${API_BASE}${cleanEndpoint}`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json", Authorization: `Bearer ${newToken}` },
                    body: JSON.stringify(data),
                });
            } else {
                handleSessionExpired();
                throw new Error("Oturum süresi doldu. Lütfen tekrar giriş yapın.");
            }
        }

        if (res.status === 403) {
            handleSubscriptionRequired();
            throw new Error("Bu özelliğe erişmek için aktif bir abonelik gereklidir.");
        }

        if (!res.ok) {
            let errorData = null;
            let errorText = "";
            try {
                errorText = await res.text();
                errorData = JSON.parse(errorText);
            } catch {
                console.error(`[api.post] ${cleanEndpoint} → ${res.status} (non-JSON):`, errorText.substring(0, 200));
                throw new Error(`Sunucu hatası (${res.status}): ${errorText.substring(0, 150)}`);
            }
            console.error(`[api.post] ${cleanEndpoint} → ${res.status}:`, errorData);
            const error = new Error(parseErrorMsg(errorData, res.statusText, res.status)) as any;
            error.data = errorData;
            error.status = res.status;
            throw error;
        }

        const text = await res.text();
        return text ? JSON.parse(text) : {};
    },

    patch: async (endpoint: string, data: any) => {
        const cleanEndpoint = cleanPath(endpoint);

        let res = await fetch(`${API_BASE}${cleanEndpoint}`, {
            method: "PATCH",
            headers: getHeaders(cleanEndpoint),
            body: JSON.stringify(data),
        });

        // 401 → token yenilemeyi dene, sonra tekrar iste
        if (res.status === 401 && !cleanEndpoint.includes("/auth/")) {
            const newToken = await tryRefreshToken();
            if (newToken) {
                res = await fetch(`${API_BASE}${cleanEndpoint}`, {
                    method: "PATCH",
                    headers: { "Content-Type": "application/json", Authorization: `Bearer ${newToken}` },
                    body: JSON.stringify(data),
                });
            } else {
                handleSessionExpired();
                throw new Error("Oturum süresi doldu. Lütfen tekrar giriş yapın.");
            }
        }

        if (res.status === 403) {
            handleSubscriptionRequired();
            throw new Error("Bu özelliğe erişmek için aktif bir abonelik gereklidir.");
        }

        if (!res.ok) {
            let errorData = null;
            let errorText = "";
            try {
                errorText = await res.text();
                errorData = JSON.parse(errorText);
            } catch {
                throw new Error(`${res.status} ${res.statusText}: ${errorText.substring(0, 150)}...`);
            }
            throw new Error(parseErrorMsg(errorData, res.statusText, res.status));
        }

        const text = await res.text();
        return text ? JSON.parse(text) : {};
    },
};
