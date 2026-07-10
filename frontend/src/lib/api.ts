import { apiUrl, env } from "@/config/env";
import { getAuthToken, setAuthToken } from "@/lib/auth";
import type { FeatureKind, Role } from "@/config/navigation";

export type AuthUser = { id: number; username: string; createdAt?: string };
export type AuthResponse = { ok: true; token: string; user: AuthUser };
export type ApiErrorPayload = { ok?: false; error?: string; detail?: string };
export type LibraryFile = {
  id: string;
  filename: string;
  originalName: string;
  mimeType: string;
  size: number;
  uploadedAt: number;
  url: string;
  ragStatus?: string;
  ragIndexedAt?: number;
  ragChunkCount?: number;
  ragTextChars?: number;
  ragVectorStatus?: string;
  ragError?: string;
};
export type RagSearchResponse = {
  ok: true;
  context: string;
  chunks: Array<Record<string, unknown>>;
  files: Array<Record<string, unknown>>;
  failedFiles: Array<Record<string, unknown>>;
};
export type TaskStart = { ok: true; stream?: string; events?: string };
export type ChatMessage = { role: "user" | "assistant"; content: string; at?: number };
export type ChatInfo = { id: string; title?: string; createdAt?: number; updated_at?: string };
export type RecordItem = { id: string; title?: string; created_at?: string; updated_at?: string; at?: number; status?: string; error?: string };
export type SlideRecord = RecordItem & { pageCount?: number; pptxReady?: boolean; downloadUrl?: string };
export type TaskEvent = { type: string; value?: string; error?: string; answer?: string; [key: string]: unknown };
export type SlideWorkflowResult = {
  ok: true;
  slideId: string;
  title?: string;
  pageCount?: number;
  pptxReady?: boolean;
  downloadUrl?: string;
  pptxAssetUrl?: string;
  slides?: Array<Record<string, unknown>>;
};
export type WrongbookSummary = {
  ok: true;
  stats: Record<string, number>;
  masteryTrend: number[];
  weakTopics: Array<Record<string, unknown>>;
  wrongQuestions?: Array<Record<string, unknown>>;
  masteredQuestions?: Array<Record<string, unknown>>;
};
export type FlashcardDeck = { id: string; title?: string; count?: number; created_at?: string; updated_at?: string; cards?: unknown[] };
export type SpeakingRecord = { id?: string; title?: string; topic?: string; score?: number; created_at?: string; at?: number; [key: string]: unknown };
export type VideoRecord = { id?: string; title?: string; status?: string; created_at?: string; updated_at?: string; [key: string]: unknown };
export type ExamRecord = { id?: string; name?: string; title?: string; created_at?: string; updated_at?: string; [key: string]: unknown };

class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), env.timeout);
  const token = getAuthToken();
  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type") && init.body && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (token) headers.set("Authorization", `Bearer ${token}`);

  try {
    const response = await fetch(apiUrl(path), { ...init, headers, signal: controller.signal });
    const contentType = response.headers.get("content-type") || "";
    const payload = contentType.includes("application/json") ? await response.json() : await response.text();
    if (!response.ok) {
      const body = payload as ApiErrorPayload;
      throw new ApiError(body?.detail || body?.error || `请求失败：${response.status}`, response.status);
    }
    return payload as T;
  } finally {
    window.clearTimeout(timeout);
  }
}

function filenameFromDisposition(header: string | null, fallback: string) {
  if (!header) return fallback;
  const utf8 = /filename\*=UTF-8''([^;]+)/i.exec(header);
  if (utf8?.[1]) return decodeURIComponent(utf8[1].replace(/"/g, ""));
  const plain = /filename="?([^";]+)"?/i.exec(header);
  return plain?.[1] || fallback;
}

export const api = {
  async login(username: string, password: string) {
    const data = await request<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    setAuthToken(data.token);
    return data;
  },
  async register(username: string, password: string) {
    const data = await request<AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    setAuthToken(data.token);
    return data;
  },
  async me() {
    return request<{ ok: true; user: AuthUser }>("/auth/me");
  },
  async logout() {
    return request<{ ok: true }>("/auth/logout", { method: "POST" });
  },
  async listFiles(role: Role) {
    return request<{ ok: true; files: LibraryFile[] }>(`/files?role=${role}`);
  },
  async uploadFiles(files: File[], role: Role) {
    const body = new FormData();
    files.forEach((file) => body.append("file", file));
    body.append("role", role);
    return request<{ ok: true; files: LibraryFile[] }>("/files", { method: "POST", body });
  },
  async deleteFile(id: string, role: Role) {
    return request<{ ok: true }>(`/files/${id}?role=${role}`, { method: "DELETE" });
  },
  async rebuildFileIndex(id: string, role: Role) {
    return request<{ ok: true; rag: Record<string, unknown> }>(`/files/${id}/rag/index?role=${role}`, { method: "POST" });
  },
  async ragSearch(query: string, role: Role, materialIds: string[]) {
    return request<RagSearchResponse>("/files/rag/search", {
      method: "POST",
      body: JSON.stringify({ query, role, materialIds, maxChunks: 10, maxChars: 12000 }),
    });
  },
  async startWorkflow(kind: FeatureKind, payload: Record<string, unknown>): Promise<TaskStart & Record<string, unknown>> {
    if (kind === "slides") {
      return request("/slides/generate", { method: "POST", body: JSON.stringify(payload) });
    }
    const endpoint = kind === "lesson-plan" ? "/lesson-plan" : kind === "smartnotes" ? "/smartnotes" : kind === "chat" ? "/chat" : `/${kind}`;
    return request(endpoint, { method: "POST", body: JSON.stringify(payload) });
  },
  async downloadSlidePptx(slideId: string) {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), env.timeout);
    const token = getAuthToken();
    const headers = new Headers();
    if (token) headers.set("Authorization", `Bearer ${token}`);

    try {
      const response = await fetch(apiUrl(`/slides/${encodeURIComponent(slideId)}/download`), { headers, signal: controller.signal });
      if (!response.ok) {
        const contentType = response.headers.get("content-type") || "";
        if (contentType.includes("application/json")) {
          const body = (await response.json()) as ApiErrorPayload;
          throw new ApiError(body?.detail || body?.error || `请求失败：${response.status}`, response.status);
        }
        const text = await response.text();
        throw new ApiError(text || `请求失败：${response.status}`, response.status);
      }
      const blob = await response.blob();
      const filename = filenameFromDisposition(response.headers.get("content-disposition"), `${slideId}.pptx`);
      return { blob, filename };
    } finally {
      window.clearTimeout(timeout);
    }
  },
  async listSlides() {
    return request<{ ok: true; slides: SlideRecord[] }>("/slides");
  },
  async listChats(role: Role) {
    return request<{ ok: true; chats: ChatInfo[] }>(`/chats?role=${role}`);
  },
  async getChat(id: string) {
    return request<{ ok: true; chat: ChatInfo; messages: ChatMessage[] }>(`/chats/${id}`);
  },
  async listRecords() {
    const [chats, quizzes, papers, lessonPlans, slides] = await Promise.allSettled([
      request<{ ok: true; chats: RecordItem[] }>("/chats"),
      request<{ ok: true; quizzes: RecordItem[] }>("/quizzes"),
      request<{ ok: true; papers: RecordItem[] }>("/papers"),
      request<{ ok: true; lessonPlans: RecordItem[] }>("/lesson-plans"),
      request<{ ok: true; slides: RecordItem[] }>("/slides"),
    ]);
    return { chats, quizzes, papers, lessonPlans, slides };
  },
  async wrongbookSummary() {
    return request<WrongbookSummary>("/wrongbook/summary");
  },
  async listFlashcards() {
    return request<{ ok: true; cards?: Array<Record<string, unknown>> }>("/flashcards");
  },
  async listFlashcardDecks() {
    return request<{ ok: true; decks?: FlashcardDeck[] }>("/flashcards/decks");
  },
  async listSpeakingHistory() {
    return request<{ ok: true; history?: SpeakingRecord[]; records?: SpeakingRecord[] }>("/speaking/history");
  },
  async listTeachingVideos() {
    return request<{ ok: true; videos?: VideoRecord[] }>("/teaching-videos");
  },
  async listExams() {
    return request<{ ok: true; exams?: ExamRecord[] }>("/exams");
  },
  async searchBilibili(q: string) {
    return request<{ ok?: boolean; items?: Array<Record<string, unknown>>; results?: Array<Record<string, unknown>> }>(
      `/api/bilibili/search?q=${encodeURIComponent(q || "数学")}`,
    );
  },
  async getJson<T = unknown>(path: string) {
    return request<T>(path);
  },
  async postJson<T = unknown>(path: string, payload: Record<string, unknown>) {
    return request<T>(path, { method: "POST", body: JSON.stringify(payload) });
  },
};

export function subscribeTaskEvents(eventsUrl: string, onEvent: (event: TaskEvent) => void, onError?: (error: Error) => void) {
  const token = getAuthToken();
  const url = new URL(apiUrl(eventsUrl), window.location.origin);
  if (token) url.searchParams.set("token", token);
  const source = new EventSource(url.toString());
  source.onmessage = (message) => {
    try {
      onEvent(JSON.parse(message.data) as TaskEvent);
    } catch (error) {
      onError?.(error as Error);
    }
  };
  source.onerror = () => {
    onError?.(new Error("任务事件连接中断"));
  };
  return () => source.close();
}

export { ApiError };
