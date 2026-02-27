const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

const getHeaders = () => {
    const token = localStorage.getItem("access_token");
    return {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
};

export const api = {
    get: async (endpoint: string) => {
        const res = await fetch(`${API_BASE}${endpoint}`, {
            headers: getHeaders(),
        });

        if (!res.ok) {
            if (res.status === 401) {
                localStorage.removeItem("access_token");
                window.location.href = "/giris";
            }
            throw new Error(`API Hatası: ${res.statusText}`);
        }

        // Sometimes responses from DELETE/empty actions have no JSON
        const text = await res.text();
        return text ? JSON.parse(text) : {};
    },

    post: async (endpoint: string, data: any) => {
        const res = await fetch(`${API_BASE}${endpoint}`, {
            method: "POST",
            headers: getHeaders(),
            body: JSON.stringify(data),
        });

        if (!res.ok) {
            if (res.status === 401) {
                localStorage.removeItem("access_token");
                window.location.href = "/giris";
            }

            let errorData = null;
            try {
                errorData = await res.json();
            } catch {
                throw new Error(`API Hatası sunucudan anlaşılamadı.`);
            }

            // Return structured error message if provided by DRF
            const errorMsg = errorData?.error || errorData?.detail || Object.values(errorData)[0];
            throw new Error(errorMsg ? String(errorMsg) : `API Hatası: ${res.statusText}`);
        }

        const text = await res.text();
        return text ? JSON.parse(text) : {};
    },
};
