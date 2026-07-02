export const env = {
  apiBaseUrl: (import.meta.env.VITE_BACKEND_URL as string | undefined)?.replace(/\/$/, "") ?? "",
  timeout: Number(import.meta.env.VITE_TIMEOUT ?? 90000),
};

export function apiUrl(path: string) {
  if (/^https?:\/\//.test(path)) return path;
  const clean = path.startsWith("/") ? path : `/${path}`;
  return `${env.apiBaseUrl}${clean}`;
}
