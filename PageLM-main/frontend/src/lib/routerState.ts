export function getRouteState<T extends Record<string, unknown> = Record<string, unknown>>(): Partial<T> {
  const raw = window.history.state as Record<string, unknown> | null;
  const nested = raw?.userState;
  if (nested && typeof nested === "object") {
    return nested as Partial<T>;
  }
  if (raw && typeof raw === "object") {
    return raw as Partial<T>;
  }
  return {};
}
