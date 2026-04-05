import { readAuthSession } from "./auth";

export function getUserScopedStorageKey(baseKey: string): string {
  const session = readAuthSession();
  const userId = session?.user?.id;
  if (!userId) return `${baseKey}:guest`;
  return `${baseKey}:u:${userId}`;
}
