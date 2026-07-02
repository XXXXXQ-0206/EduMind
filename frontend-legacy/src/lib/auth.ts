export const AUTH_STORAGE_KEY = "edumind-auth-session";
const LEGACY_AUTH_STORAGE_KEY = ["page", "lm-auth-session"].join("");

export type AuthSession = {
  token: string;
  user: {
    id: number;
    username: string;
    createdAt?: string;
  };
};

export function readAuthSession(): AuthSession | null {
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY) || localStorage.getItem(LEGACY_AUTH_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as AuthSession;
    if (!parsed?.token || !parsed?.user?.username) return null;
    if (!localStorage.getItem(AUTH_STORAGE_KEY)) {
      localStorage.setItem(AUTH_STORAGE_KEY, raw);
    }
    return parsed;
  } catch {
    return null;
  }
}

export function writeAuthSession(session: AuthSession | null) {
  if (!session) {
    localStorage.removeItem(AUTH_STORAGE_KEY);
    localStorage.removeItem(LEGACY_AUTH_STORAGE_KEY);
    return;
  }
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session));
}

export function getAuthToken(): string {
  return readAuthSession()?.token || "";
}
