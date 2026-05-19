// Thin compatibility adapter over the single source-of-truth API client
// (src/lib/api.ts). Previously this file duplicated its own fetch + 401 +
// session logic, which drifted out of sync with api.ts. It now delegates so
// there is exactly ONE implementation of auth/refresh/401/403 handling, while
// keeping the `{ ok, data, message }` return contract its consumers expect.

import { api } from "../api";

type ApiResult<T> = { ok: boolean; data: T; message?: string };

function unwrap<T>(payload: unknown): T {
    if (payload && typeof payload === "object" && "data" in payload) {
        const inner = (payload as { data?: unknown }).data;
        if (inner !== undefined) return inner as T;
    }
    return payload as T;
}

async function wrap<T>(p: Promise<unknown>): Promise<ApiResult<T>> {
    try {
        const payload = await p;
        return { ok: true, data: unwrap<T>(payload) };
    } catch (error) {
        const message = error instanceof Error ? error.message : "İstek başarısız oldu.";
        return { ok: false, data: null as T, message };
    }
}

const apiClient = {
    get: <T>(endpoint: string) => wrap<T>(api.get(endpoint)),
    post: <T>(endpoint: string, body: unknown) => wrap<T>(api.post(endpoint, body)),
    patch: <T>(endpoint: string, body: unknown) => wrap<T>(api.patch(endpoint, body)),
    put: <T>(endpoint: string, body: unknown) => wrap<T>(api.put(endpoint, body)),
    delete: <T>(endpoint: string) => wrap<T>(api.delete(endpoint)),
};

export default apiClient;
