const getApiBase = () => {
    // Traverse proxy bug: Next.js strips trailing slashes on POST requests which breaks Django's APPEND_SLASH.
    // Connect directly to the port 8000 API relative to the current window hostname to continue supporting LAN usage.
    if (typeof window !== "undefined") {
        return `${window.location.protocol}//${window.location.hostname}:8000/api`;
    }
    let base = process.env.NEXT_PUBLIC_API_BASE || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
    return base.replace(/\/$/, ""); // Remove trailing slash if any
};

const API_BASE = getApiBase();

const getHeaders = () => {
    const token = localStorage.getItem("access_token");
    return {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
};

export const api = {
    get: async (endpoint: string) => {
        let cleanEndpoint = endpoint.startsWith('/') ? endpoint : '/' + endpoint;
        if (!cleanEndpoint.endsWith('/')) {
            cleanEndpoint += '/';
        }
        console.log("API_BASE:", API_BASE, "endpoint:", cleanEndpoint);
        const res = await fetch(`${API_BASE}${cleanEndpoint}`, {
            headers: getHeaders(),
        });

        if (!res.ok) {
            if (res.status === 401) {
                localStorage.removeItem("access_token");
                window.location.href = "/giris";
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
        if (!cleanEndpoint.endsWith('/')) {
            cleanEndpoint += '/';
        }
        const res = await fetch(`${API_BASE}${cleanEndpoint}`, {
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
            let errorText = "";
            try {
                errorText = await res.text();
                errorData = JSON.parse(errorText);
            } catch {
                // Return plain text if JSON parsing fails (e.g., 500 HTML pages)
                throw new Error(`${res.status} ${res.statusText}: ${errorText.substring(0, 150)}...`);
            }

            // Return structured error message if provided by DRF
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

    patch: async (endpoint: string, data: any) => {
        let cleanEndpoint = endpoint.startsWith('/') ? endpoint : '/' + endpoint;
        if (!cleanEndpoint.endsWith('/')) {
            cleanEndpoint += '/';
        }
        const res = await fetch(`${API_BASE}${cleanEndpoint}`, {
            method: "PATCH",
            headers: getHeaders(),
            body: JSON.stringify(data),
        });

        if (!res.ok) {
            if (res.status === 401) {
                localStorage.removeItem("access_token");
                window.location.href = "/giris";
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
