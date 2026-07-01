const defaultBackend = window.location.origin;

export const env = {
  backend: import.meta.env.VITE_BACKEND_URL || defaultBackend,
  timeout: Number(import.meta.env.VITE_TIMEOUT || 90000),
};