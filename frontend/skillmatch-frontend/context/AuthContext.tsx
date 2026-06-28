"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { auth, tokens, homeForRole, type MeResponse, type RegisterPayload, type UserRole } from "@/lib/api";

interface AuthState {
  user:            MeResponse | null;
  isAuthenticated: boolean;
  isLoading:       boolean;
  login:   (email: string, password: string) => Promise<MeResponse>;
  register:(payload: RegisterPayload)        => Promise<MeResponse>;
  logout:  ()                                => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user,      setUser]      = useState<MeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Restore session on mount
  useEffect(() => {
    const access = tokens.getAccess();
    if (!access) { setIsLoading(false); return; }
    auth.me()
      .then(setUser)
      .catch(() => tokens.clear())
      .finally(() => setIsLoading(false));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const { access, refresh } = await auth.login(email, password);
    tokens.set(access, refresh);
    const me = await auth.me();
    setUser(me);
    return me;
  }, []);

  const register = useCallback(async (payload: RegisterPayload) => {
    await auth.register(payload);
    // Auto-login after registration
    return login(payload.email, payload.password);
  }, [login]);

  const logout = useCallback(() => {
    tokens.clear();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be inside <AuthProvider>");
  return ctx;
}

/**
 * Redirect-to-login wrapper for protected pages.
 *
 * Pass `requiredRole` to also enforce role-based access: a logged-in user
 * whose role doesn't match is bounced to their own home (e.g. a candidate
 * who opens the employer/job-uploader page is sent back to their dashboard).
 */
export function useRequireAuth(redirectTo = "/login", requiredRole?: UserRole) {
  const { user, isAuthenticated, isLoading } = useAuth();

  const roleOk = !requiredRole || user?.role === requiredRole;

  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated) {
      window.location.href = redirectTo;
      return;
    }
    if (requiredRole && user && user.role !== requiredRole) {
      window.location.href = homeForRole(user.role);
    }
  }, [isAuthenticated, isLoading, requiredRole, user, redirectTo]);

  return { isAuthenticated, isLoading, user, roleOk };
}
