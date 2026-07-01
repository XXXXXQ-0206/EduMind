import { getUserScopedStorageKey, readScopedStorage } from "./userStorage";

export type LearningBagRecordType = "chat" | "note" | "podcast" | "quiz" | "knowledge-card";

export type LearningBagRecord = {
  id: string;
  type: LearningBagRecordType;
  refId: string;
  title: string;
  subtitle?: string;
  path: string;
  query?: Record<string, string>;
  created: number;
};

const STORAGE_KEY = "edumind-learning-bag-records";

const normalize = (value: unknown): LearningBagRecord[] => {
  if (!Array.isArray(value)) return [];
  return value
    .filter((item) => item && typeof item === "object")
    .map((item) => item as LearningBagRecord)
    .filter((item) => item.id && item.type && item.refId && item.path)
    .sort((a, b) => (b.created || 0) - (a.created || 0));
};

const save = (items: LearningBagRecord[]) => {
  localStorage.setItem(getUserScopedStorageKey(STORAGE_KEY), JSON.stringify(items));
  window.dispatchEvent(new CustomEvent("learning-bag:updated"));
};

export const listLearningBagRecords = () => {
  try {
    const raw = readScopedStorage(STORAGE_KEY);
    return normalize(raw ? JSON.parse(raw) : []);
  } catch {
    return [] as LearningBagRecord[];
  }
};

export const addLearningBagRecord = (
  input: Omit<LearningBagRecord, "id" | "created">
) => {
  const all = listLearningBagRecords();
  const hit = all.find((item) => item.type === input.type && item.refId === input.refId);
  const next: LearningBagRecord = {
    id: hit?.id || `bag_${input.type}_${input.refId}`,
    created: Date.now(),
    ...input,
  };
  const merged = [next, ...all.filter((item) => item.id !== next.id)].sort(
    (a, b) => b.created - a.created
  );
  save(merged);
  return next;
};

export const removeLearningBagRecord = (id: string) => {
  if (!id) return;
  const all = listLearningBagRecords();
  save(all.filter((item) => item.id !== id));
};

export const clearLearningBagRecords = () => {
  save([]);
};

export const learningBagTypeLabel = (type: LearningBagRecordType) => {
  if (type === "chat") return "对话";
  if (type === "note") return "智能笔记";
  if (type === "podcast") return "AI播客";
  if (type === "quiz") return "测验";
  return "知识卡片";
};
