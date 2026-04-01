const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface FetchOptions {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
}

function extractErrorMessage(errorPayload: unknown, status: number): string {
  if (!errorPayload || typeof errorPayload !== 'object') {
    return `API error: ${status}`;
  }

  const detail = (errorPayload as { detail?: unknown }).detail;

  if (typeof detail === 'string') {
    return detail;
  }

  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { msg?: string; loc?: unknown[] };
    if (typeof first?.msg === 'string') {
      const field = Array.isArray(first.loc) ? String(first.loc[first.loc.length - 1] || '') : '';
      return field ? `${first.msg} (${field})` : first.msg;
    }
  }

  return `API error: ${status}`;
}

export async function api<T = unknown>(endpoint: string, options: FetchOptions = {}): Promise<T> {
  const { method = 'GET', body, headers = {} } = options;

  const config: RequestInit = {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...headers,
    },
  };

  if (body) {
    config.body = JSON.stringify(body);
  }

  const res = await fetch(`${API_URL}${endpoint}`, config);

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(extractErrorMessage(error, res.status));
  }

  return res.json();
}

export function apiUrl(path: string): string {
  return `${API_URL}${path}`;
}
