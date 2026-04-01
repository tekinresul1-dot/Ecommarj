// Simple internal API wrapper pointing to Django
// Uses dynamic base URL to support LAN access (same as api.ts)

const getApiBase = () => {
    if (typeof window !== "undefined") {
        // Use relative /api — nginx proxies to backend, avoids hardcoded port 8000
        return `/api`;
    }
    // SSR: reach backend via internal Docker network
    return process.env.NEXT_PUBLIC_API_URL || 'http://backend:8000/api';
};

const API_BASE_URL = getApiBase();

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<{ ok: boolean, data: T, message?: string }> {
    // Ensure trailing slash before query string (Django APPEND_SLASH)
    let cleanEndpoint = endpoint.startsWith('/') ? endpoint : '/' + endpoint;
    const [pathPart, queryPart] = cleanEndpoint.split('?');
    if (!pathPart.endsWith('/')) {
        cleanEndpoint = pathPart + '/' + (queryPart ? '?' + queryPart : '');
    }

    const url = `${API_BASE_URL}${cleanEndpoint}`;

    // Attempt to get token if it's stored
    let token = '';
    if (typeof window !== 'undefined') {
        token = localStorage.getItem('access_token') || '';
    }

    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        ...options.headers as Record<string, string>,
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const config = {
        ...options,
        headers,
    };

    try {
        const response = await fetch(url, config);
        const text = await response.text();

        let data;
        try {
            data = text ? JSON.parse(text) : {};
        } catch (e) {
            data = { text };
        }

        if (!response.ok) {
            if (response.status === 401 && !cleanEndpoint.includes("/auth/")) {
                localStorage.removeItem("access_token");
                if (typeof window !== "undefined" && window.location.pathname !== "/giris") {
                    if (!window.location.search.includes("session_expired")) {
                        window.location.href = "/giris?session_expired=true";
                    }
                }
            }
            throw new Error(data.message || data.error || `HTTP error! status: ${response.status}`);
        }

        return { ok: true, data: data.data || data };
    } catch (error: any) {
        console.error('API Error:', error);
        return { ok: false, data: null as any, message: error.message };
    }
}

const apiClient = {
    get: <T>(endpoint: string) => request<T>(endpoint, { method: 'GET' }),
    post: <T>(endpoint: string, body: any) => request<T>(endpoint, { method: 'POST', body: JSON.stringify(body) }),
    patch: <T>(endpoint: string, body: any) => request<T>(endpoint, { method: 'PATCH', body: JSON.stringify(body) }),
    put: <T>(endpoint: string, body: any) => request<T>(endpoint, { method: 'PUT', body: JSON.stringify(body) }),
    delete: <T>(endpoint: string) => request<T>(endpoint, { method: 'DELETE' }),
};

export default apiClient;
