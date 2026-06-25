const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";

export async function request(path, { token, method = "GET", body } = {}) {
  let response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new Error("Không thể kết nối API. Hãy chạy FastAPI tại http://localhost:8000.");
  }
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail ?? "Không thể kết nối đến máy chủ");
  }
  return response.status === 204 ? null : response.json();
}
