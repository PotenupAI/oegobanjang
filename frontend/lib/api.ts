import { API_BASE_URL } from "./constants";

type ApiOptions = {
  requestId?: string;
};

export async function fetchApi<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "content-type": "application/json",
      ...(options.requestId ? { "x-request-id": options.requestId } : {}),
    },
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}
