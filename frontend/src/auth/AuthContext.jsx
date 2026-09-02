import { createContext, useContext, useEffect, useState } from "react";
import {
  AUTH_LOST,
  clearSession,
  getStoredToken,
  getStoredUser,
  persistSession,
  loginRequest,
  registerRequest,
} from "./session";
import { api, setAuthToken } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => getStoredUser());
  const [loading, setLoading] = useState(() => Boolean(getStoredToken()));

  useEffect(() => {
    const token = getStoredToken();
    setAuthToken(token);
    if (!token) {
      setLoading(false);
      return;
    }

    api
      .me()
      .then((me) => {
        persistSession(token, me);
        setUser(me);
      })
      .catch(() => {
        clearSession();
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    function onLost() {
      setUser(null);
    }
    window.addEventListener(AUTH_LOST, onLost);
    return () => window.removeEventListener(AUTH_LOST, onLost);
  }, []);

  async function login(email, password, role) {
    const next = await loginRequest(email, password, role);
    setUser(next);
    return next;
  }

  async function register(name, email, password, role) {
    const next = await registerRequest(name, email, password, role);
    setUser(next);
    return next;
  }

  function logout() {
    clearSession();
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
