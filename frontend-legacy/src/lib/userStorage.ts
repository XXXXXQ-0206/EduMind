import { readAuthSession } from "./auth";

export function migrateStorageKey(currentKey: string, legacyKey: string): string | null {
  const current = localStorage.getItem(currentKey);
  if (current !== null) return current;

  const legacy = localStorage.getItem(legacyKey);
  if (legacy !== null) {
    localStorage.setItem(currentKey, legacy);
  }
  return legacy;
}

export function getUserScopedStorageKey(baseKey: string): string {
  const session = readAuthSession();
  const userId = session?.user?.id;
  if (!userId) return `${baseKey}:guest`;
  return `${baseKey}:u:${userId}`;
}

export function getLegacyUserScopedStorageKey(baseKey: string): string {
  return getUserScopedStorageKey(baseKey.replace(/^edumind-/, ["page", "lm-"].join("")));
}

function isScopedStorageKey(key: string): boolean {
  return /:(guest|u:\d+)$/.test(key);
}

export function readScopedStorage(currentBaseOrScopedKey: string): string | null {
  const currentKey = isScopedStorageKey(currentBaseOrScopedKey)
    ? currentBaseOrScopedKey
    : getUserScopedStorageKey(currentBaseOrScopedKey);
  const legacyKey = currentKey.replace(/^edumind-/, ["page", "lm-"].join(""));
  return migrateStorageKey(currentKey, legacyKey);
}
