const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";

/** Error that keeps the HTTP status, so the UI can react to 404 / 409 differently. */
export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });

  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") {
        message = body.detail;
      } else if (Array.isArray(body.detail)) {
        // FastAPI 422 validation errors
        message = body.detail.map((d: { msg: string }) => d.msg).join(", ");
      }
    } catch {
      // Error body was not JSON; keep the default message
    }
    throw new ApiError(response.status, message);
  }

  return response.json() as Promise<T>;
}