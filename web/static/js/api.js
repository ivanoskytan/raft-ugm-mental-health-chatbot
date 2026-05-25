export async function apiFetch(url, options={}) {
    const token = localStorage.getItem("access_token");

    const defaultHeaders = {
        "Content-Type": "application/json",
        ...(token && { "Authorization": `Bearer ${token}`})
    };

    options.headers = {
        ...defaultHeaders,
        ...options.headers
    };

    const res = await fetch(url, options);

    if (!res.ok) {
        let errorMessage = `Error ${res.status}`;
        try {
            const errorData= await res.json();
            errorMessage = errorData.error || errorMessage;
        } catch (e) {
            console.error("[API Fetch] Failed to parse error response:", e);
        }
        throw new Error(errorMessage);
    }
    if (res.status === 204) return null;
    return res.json();
}