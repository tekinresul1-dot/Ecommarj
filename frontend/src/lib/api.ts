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

const getHeaders = (endpoint?: string) => {
    const token = localStorage.getItem("access_token");
    const isPublicAuthEndpoint = endpoint && (endpoint.includes('/auth/login') || endpoint.includes('/auth/register'));
    return {
        "Content-Type": "application/json",
        ...(token && !isPublicAuthEndpoint ? { Authorization: `Bearer ${token}` } : {}),
    };
};

export const api = {
    get: async (endpoint: string) => {
        let cleanEndpoint = endpoint.startsWith('/') ? endpoint : '/' + endpoint;
        const [pathPart, queryPart] = cleanEndpoint.split('?');
        if (!pathPart.endsWith('/')) {
            cleanEndpoint = pathPart + '/' + (queryPart ? '?' + queryPart : '');
        }
        console.log("API_BASE:", API_BASE, "endpoint:", cleanEndpoint);
        const res = await fetch(`${API_BASE}${cleanEndpoint}`, {
            headers: getHeaders(cleanEndpoint),
        });

        if (!res.ok) {
            if (res.status === 401 && !cleanEndpoint.includes("/auth/")) {
                console.error("401 Unauthorized from API. Redirecting to login. Endpoint:", cleanEndpoint);
                localStorage.removeItem("access_token");
                if (typeof window !== "undefined" && window.location.pathname !== "/giris") {
                    if (!window.location.search.includes("session_expired")) {
                        window.location.href = "/giris?session_expired=true";
                    }
                }
            }
            const text = await res.text();
            console.log("API_BASE:", API_BASE, "endpoint:", cleanEndpoint); console.error(`API Error on GET ${endpoint} (${res.status}): ${text.substring(0, 150)}`);
            throw new Error(`API Hatası (${res.status}): ${res.statusText}`);
        }

        // Sometimes responses from DELETE/empty actions have no JSON
        const text = await res.text();
        return text ? JSON.parse(text) : {};
    },

    post: async (endpoint: string, data: any) => {
        let cleanEndpoint = endpoint.startsWith('/') ? endpoint : '/' + endpoint;
        const [pathPart, queryPart] = cleanEndpoint.split('?');
        if (!pathPart.endsWith('/')) {
            cleanEndpoint = pathPart + '/' + (queryPart ? '?' + queryPart : '');
        }
        const res = await fetch(`${API_BASE}${cleanEndpoint}`, {
            method: "POST",
            headers: getHeaders(cleanEndpoint),
            body: JSON.stringify(data),
        });

        if (!res.ok) {
            if (res.status === 401 && !cleanEndpoint.includes("/auth/")) {
                localStorage.removeItem("access_token");
                if (typeof window !== "undefined" && window.location.pathname !== "/giris") {
                    if (!window.location.search.includes("session_expired")) {
                        window.location.href = "/giris?session_expired=true";
                    }
                }
            }

            let errorData = null;
            let errorText = "";
            try {
                errorText = await res.text();
                errorData = JSON.parse(errorText);
            } catch {
                // Return plain text if JSON parsing fails (e.g., 500 HTML pages)
                console.error(`[api.post] ${cleanEndpoint} → ${res.status} (non-JSON):`, errorText.substring(0, 200));
                throw new Error(`Sunucu hatası (${res.status}): ${errorText.substring(0, 150)}`);
            }

            // Log structured error for debugging
            console.error(`[api.post] ${cleanEndpoint} → ${res.status}:`, errorData);

            // Return structured error message if provided by DRF
            let errorMsg = `API Hatası (${res.status}): ${res.statusText}`;
            if (errorData) {
                if (typeof errorData === 'string') {
                    errorMsg = errorData;
                } else if (errorData.message) {
                    errorMsg = String(errorData.message);
                } else if (errorData.error) {
                    errorMsg = String(errorData.error);
                } else if (errorData.detail) {
                    errorMsg = String(errorData.detail);
                } else if (typeof errorData === 'object') {
                    const firstVal = Object.values(errorData)[0];
                    if (firstVal && typeof firstVal === 'string') {
                        errorMsg = firstVal;
                    }
                }
            }
            throw new Error(errorMsg);
        }

        const text = await res.text();
        return text ? JSON.parse(text) : {};
    },

    patch: async (endpoint: string, data: any) => {
        let cleanEndpoint = endpoint.startsWith('/') ? endpoint : '/' + endpoint;
        const [pathPart, queryPart] = cleanEndpoint.split('?');
        if (!pathPart.endsWith('/')) {
            cleanEndpoint = pathPart + '/' + (queryPart ? '?' + queryPart : '');
        }
        const res = await fetch(`${API_BASE}${cleanEndpoint}`, {
            method: "PATCH",
            headers: getHeaders(cleanEndpoint),
            body: JSON.stringify(data),
        });

        if (!res.ok) {
            if (res.status === 401 && !cleanEndpoint.includes("/auth/")) {
                localStorage.removeItem("access_token");
                if (typeof window !== "undefined" && window.location.pathname !== "/giris") {
                    if (!window.location.search.includes("session_expired")) {
                        window.location.href = "/giris?session_expired=true";
                    }
                }
            }

            let errorData = null;
            let errorText = "";
            try {
                errorText = await res.text();
                errorData = JSON.parse(errorText);
            } catch {
                throw new Error(`${res.status} ${res.statusText}: ${errorText.substring(0, 150)}...`);
            }

            let errorMsg = `API Hatası (${res.status}): ${res.statusText}`;
            if (errorData) {
                if (typeof errorData === 'string') {
                    errorMsg = errorData;
                } else if (errorData.error) {
                    errorMsg = String(errorData.error);
                } else if (errorData.detail) {
                    errorMsg = String(errorData.detail);
                } else if (errorData.message) {
                    errorMsg = String(errorData.message);
                } else if (typeof errorData === 'object') {
                    const firstVal = Object.values(errorData)[0];
                    if (firstVal && typeof firstVal === 'string') {
                        errorMsg = firstVal;
                    }
                }
            }
            throw new Error(errorMsg);
        }

        const text = await res.text();
        return text ? JSON.parse(text) : {};
    },
};
