import { api, setAuthToken } from "../api/client";

const TOKEN_KEY = "sep_token";
const USER_KEY = "sep_user";
const AUTH_LOST = "sep-auth-lost";

export function getStoredToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser() {
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function persistSession(token, user) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
  if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
  else localStorage.removeItem(USER_KEY);
  setAuthToken(token);
}

export function clearSession() {
  persistSession(null, null);
}

export { AUTH_LOST };

export async function loginRequest(email, password, role) {
  const data = await api.login({ email, password, role });
  persistSession(data.access_token, data.user);
  return data.user;
}

export async function registerRequest(name, email, password, role) {
  const data = await api.register({ name, email, password, role });
  persistSession(data.access_token, data.user);
  return data.user;
}
