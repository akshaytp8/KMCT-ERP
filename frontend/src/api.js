const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export function getToken() { return localStorage.getItem('kmct_superadmin_token'); }
export function setToken(token) { localStorage.setItem('kmct_superadmin_token', token); }
export function clearToken() { localStorage.removeItem('kmct_superadmin_token'); }

export async function api(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401) clearToken();
    throw new Error(body.detail || `Request failed (${response.status})`);
  }
  return body;
}
