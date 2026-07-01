import { env } from "../config/env";
import { getAuthToken, writeAuthSession } from "./auth";

export type TaskStartLinks = { stream: string; events?: string };
export type ChatStartResponse = { ok: true; chatId: string } & TaskStartLinks;
export type ChatMessage = { role: "user" | "assistant"; content: string; at: number };
export type ChatInfo = { id: string; title?: string; createdAt?: number };
export type ChatsList = { ok: true; chats: ChatInfo[] };
export type ChatDetail = { ok: true; chat: ChatInfo; messages: ChatMessage[] };
export type AuthUser = { id: number; username: string; createdAt?: string };
export type AuthResponse = { ok: true; token: string; user: AuthUser };
export type SessionResponse = { ok: true; user: AuthUser };
export type ChatJSONBody = {
  q: string;
  chatId?: string;
  length?: "Short" | "Medium" | "Long";
  includeMaterials?: boolean;
  materialIds?: string[];
  role?: "student" | "teacher";
};
export type ChatPhase = "upload_start" | "upload_done" | "generating";
export type FlashCard = { q: string; a: string; tags?: string[] };
export type Question = { id: number; question: string; options: string[]; correct: number; hint: string; explanation: string; imageHtml?: string; };
export type QuizRecordStatus = "pending" | "generating" | "packaging" | "ready" | "error";
export type QuizMeta = {
  id: string;
  title?: string;
  count?: number;
  at?: number;
  status?: QuizRecordStatus;
  difficulty?: "easy" | "medium" | "hard";
  includeMaterials?: boolean;
  created_at?: string;
  updated_at?: string;
  error?: string;
};
export type GenerationRecordStatus = "pending" | "generating" | "ready" | "error";
export type SmartNoteMeta = {
  id: string;
  title?: string;
  length?: string;
  file?: string;
  at?: number;
  created_at?: string;
  updated_at?: string;
  status?: GenerationRecordStatus;
  error?: string;
};
export type PodcastMeta = {
  id: string;
  title?: string;
  length?: string;
  file?: string;
  static?: string;
  at?: number;
  created_at?: string;
  updated_at?: string;
  status?: GenerationRecordStatus;
  error?: string;
};
export type QuizStartResponse = { ok: true; quizId: string } & TaskStartLinks
export type QuizEvent =
  | { type: "ready"; quizId?: string }
  | { type: "phase"; value: string }
  | { type: "quiz"; quiz: unknown }
  | { type: "done" }
  | { type: "error"; error: string }
  | { type: "ping"; t?: number }
export type PaperItem = {
  id: number;
  type: "choice" | "fill" | "application";
  question: string;
  options?: string[];
  correct?: number;
  answer?: string;
  explanation?: string;
};
export type PaperStartResponse = { ok: true; paperId: string } & TaskStartLinks;
export type PaperEvent = { type: "ready" | "phase" | "paper" | "done" | "error"; paperId?: string; value?: string; paper?: PaperItem[]; error?: string };
export type QuizAttempt = {
  questionId: number;
  selectedAnswer: number;
  correct: boolean;
  question: string;
  selectedOption: string;
  correctOption: string;
  explanation: string;
  at?: number;
};
export type WrongBookQuestion = {
  id: number;
  quizId: string;
  title: string;
  subject: string;
  time: number;
  topic: string;
  level: string;
  accuracy: number;
  reviewCount: number;
  tag: string;
  tone: string;
  note: string;
  options: string[];
  correct: number;
  explanation?: string;
  hint?: string;
};
export type WrongBookSummary = {
  ok: true;
  stats: {
    wrongCount: number;
    masteredCount: number;
    totalCount: number;
    masteryRate: number;
    reviewIntervalDays: number;
    newWrongCount: number;
  };
  breakdown: { name: string; value: number }[];
  weakTopics: { name: string; wrong: number; total: number; rate: number; level: string; badgeTone: string; barTone: string; suggestion: string }[];
  masteryTrend: number[];
  wrongQuestions: WrongBookQuestion[];
  masteredQuestions: WrongBookQuestion[];
};
export type WrongBookReport = {
  overview: string;
  highlights: { title: string; desc: string }[];
  strengths: string[];
  weaknesses: string[];
  actions: string[];
  weeklyPlan: string[];
  metrics: { currentAccuracy: number; targetAccuracy: number; reviewIntervalDays: number };
};
export type WeakPoint = {
  name: string;
  category: string;
  severity: 'high' | 'medium' | 'low';
  wrongCount: number;
  description: string;
  suggestion: string;
  questionIndices: number[];
};
export type SmartNotesStart = { ok: true; noteId: string } & TaskStartLinks
export type LibraryFile = {
  id: string;
  filename: string;
  originalName: string;
  mimeType: string;
  size: number;
  uploadedAt: number;
  url: string;
};
export type FileListResponse = { ok: true; files: LibraryFile[] };
export type FileUploadResponse = { ok: true; files: LibraryFile[] };
export type CompanionHistoryEntry = { role: "user" | "assistant"; content: string }
export type CompanionAnswer = { topic: string; answer: string; flashcards: FlashCard[] }
export type CompanionAskResponse = { ok: boolean; companion: CompanionAnswer }
export type SavedFlashcard = {
  id: string;
  question: string;
  answer: string;
  tag: string;
  created: number;
};
export type KnowledgeCard = {
  id: string;
  concept: string;
  question: string;
  fill_blank?: string | null;
  hint: string;
  answer: string;
  mnemonic: string;
  application: string;
};
export type KnowledgeDeck = {
  id: string;
  title: string;
  count: number;
  created_at: string;
  updated_at: string;
  cards: KnowledgeCard[];
};
export type KnowledgeDeckMeta = {
  id: string;
  title: string;
  count: number;
  created_at: string;
  updated_at: string;
};
export type ExamEvent =
  | { type: "ready"; runId: string }
  | { type: "phase"; value: string; examId?: string }
  | { type: "exam"; examId: string; payload: Question[] }
  | { type: "done" }
  | { type: "error"; examId?: string; error: string };
export type ExamMeta = { id: string; name: string; sections: unknown[] };
export type PodcastEvent =
  | { type: "ready"; pid: string }
  | { type: "phase"; value: string }
  | { type: "file"; filename: string; mime: string }
  | { type: "warn"; message: string }
  | { type: "script"; data: PodcastScript }
  | { type: "audio"; file: string; filename?: string; staticUrl?: string }
  | { type: "done" }
  | { type: "error"; error: string }
  | { type: "close"; code?: number }
export type SmartNotesPayload = {
  title?: string;
  notes?: string;
  summary?: string;
  questions?: string[];
  answers?: string[];
};
export type PodcastSegment = {
  spk: "A" | "B";
  voice?: string;
  md: string;
};
export type PodcastScript = {
  title?: string;
  summary?: string;
  segments?: PodcastSegment[];
};
export type SmartNotesEvent =
  | { type: "ready"; noteId: string }
  | { type: "phase"; value: string }
  | { type: "notes"; notes: SmartNotesPayload }
  | { type: "file"; file: string }
  | { type: "done" }
  | { type: "error"; error: string }
  | { type: "close"; code?: number }
  | { type: "ping"; t: number }
export type StudyMaterials = {
  summary: string;
  keyPoints: string[];
  topics: string[];
  categories: string[];
  searchableKeywords: string[];
  studyGuide: {
    mainConcepts: string[];
    importantTerms: { term: string; definition: string; }[];
    questions: string[];
    takeaways: string[];
  };
  timestamps?: { time: number; content: string; topic: string; }[];
};

export type TranscriptionResponse = {
  ok: boolean;
  transcription?: string;
  provider?: string;
  confidence?: number;
  error?: string;
  studyMaterials?: StudyMaterials;
}
export type SpeakingItem = {
  id: number;
  text: string;
  translation: string;
  phonetic: string;
  level: string;
  tag: string;
  audioUrl: string;
};
export type SpeakingGenerateBody = {
  count: number;
  difficulty: "easy" | "medium" | "hard";
  itemType: "word" | "phrase" | "sentence";
  topic?: string;
  voice: "american" | "british";
};
export type SpeakingGenerateResponse = {
  ok: true;
  sessionId: string;
  items: SpeakingItem[];
  voice: string;
};
export type SpeakingUploadResponse = {
  ok: true;
  sessionId: string;
  filename: string;
  staticUrl: string;
};
export type SpeakingEvaluateBody = {
  sessionId: string;
  filename: string;
  text: string;
  itemType: "word" | "phrase" | "sentence";
};
export type SpeakingEvaluateResponse = {
  ok: true;
  scores: {
    total_score?: number | null;
    accuracy_score?: number | null;
    fluency_score?: number | null;
    standard_score?: number | null;
    integrity_score?: number | null;
  };
  words?: {
    content: string;
    dp_message: number;
    total_score?: number | null;
    sylls?: {
      content: string;
      serr_msg: number;
      syll_score?: number | null;
    }[];
  }[];
};
export type ChatEvent =
  | { type: "ready"; chatId: string }
  | { type: "phase"; value: ChatPhase }
  | { type: "file"; filename: string; mime: string }
  | { type: "answer"; answer: AnswerPayload }
  | { type: "done" }
  | { type: "error"; error: string };

type O<T> = Promise<T>;
type AnswerPayload = string | { answer: string; flashcards?: FlashCard[] };

const timeoutCtl = (ms: number) => {
  const c = new AbortController();
  const t = setTimeout(() => c.abort(), ms);
  return { signal: c.signal, done: () => clearTimeout(t) };
};

async function req<T = unknown>(
  url: string,
  init: RequestInit & { timeout?: number } = {}
): O<T> {
  const { timeout = env.timeout, ...rest } = init;
  const { signal, done } = timeoutCtl(timeout);
  const headers = new Headers(rest.headers || undefined);
  const token = getAuthToken();
  if (token) headers.set("authorization", `Bearer ${token}`);
  try {
    const r = await fetch(url, { signal, ...rest, headers });
    if (!r.ok) {
      if (r.status === 401) {
        writeAuthSession(null);
      }
      const raw = await r.text().catch(() => "");
      let detail = raw || r.statusText;
      if (raw) {
        try {
          const parsed = JSON.parse(raw) as { detail?: unknown; message?: unknown; error?: unknown };
          const candidate = parsed.detail ?? parsed.message ?? parsed.error;
          if (typeof candidate === "string" && candidate.trim()) {
            detail = candidate;
          }
        } catch {
          // Keep original response text when body is not JSON.
        }
      }
      throw new Error(`http ${r.status}: ${detail}`);
    }
    const ct = r.headers.get("content-type") || "";
    if (ct.includes("application/json")) return (await r.json()) as T;
    return (await r.text()) as unknown as T;
  } finally {
    done();
  }
}

const jsonHeaders = (body?: unknown) => {
  void body;
  const h = new Headers();
  h.set("content-type", "application/json");
  const token = getAuthToken();
  if (token) h.set("authorization", `Bearer ${token}`);
  return h;
};

function wsURL(path: string) {
  const u = new URL(env.backend);
  const proto = u.protocol === "https:" ? "wss:" : "ws:";
  const full = new URL(`${proto}//${u.host}${path}`);
  const token = getAuthToken();
  if (token) full.searchParams.set("token", token);
  return full.toString();
}

function sseURL(path: string) {
  const u = new URL(env.backend);
  const full = new URL(`${u.protocol}//${u.host}${path}`);
  const token = getAuthToken();
  if (token) full.searchParams.set("token", token);
  return full.toString();
}

export type TaskEventKind = "chat" | "quiz" | "smartnotes" | "podcast" | "paper" | "exam" | "teaching-video";

export function connectTaskEvents<T extends { type?: string; error?: string }>(
  kind: TaskEventKind,
  taskId: string,
  onEvent: (ev: T) => void,
) {
  const source = new EventSource(sseURL(`/tasks/${kind}/${encodeURIComponent(taskId)}/events`));
  source.onmessage = (message) => {
    try {
      onEvent(JSON.parse(message.data) as T);
    } catch {
      onEvent({ type: "error", error: "invalid_message" } as T);
    }
  };
  source.onerror = () => onEvent({ type: "error", error: "stream_error" } as T);
  return {
    source,
    close: () => {
      try { source.close(); } catch { }
    },
  };
}

export async function register(username: string, password: string) {
  return req<AuthResponse>(`${env.backend}/auth/register`, {
    method: "POST",
    headers: jsonHeaders({}),
    body: JSON.stringify({ username, password }),
  });
}

export async function login(username: string, password: string) {
  return req<AuthResponse>(`${env.backend}/auth/login`, {
    method: "POST",
    headers: jsonHeaders({}),
    body: JSON.stringify({ username, password }),
  });
}

export async function logout() {
  return req<{ ok: true }>(`${env.backend}/auth/logout`, {
    method: "POST",
    headers: jsonHeaders({}),
  });
}

export async function getCurrentSession() {
  return req<SessionResponse>(`${env.backend}/auth/me`, {
    method: "GET",
  });
}

export async function changePassword(oldPassword: string, newPassword: string, confirmPassword: string) {
  return req<{ ok: true }>(`${env.backend}/auth/change-password`, {
    method: "POST",
    headers: jsonHeaders({}),
    body: JSON.stringify({
      old_password: oldPassword,
      new_password: newPassword,
      confirm_password: confirmPassword,
    }),
  });
}

export async function deleteAccount(password: string) {
  return req<{ ok: true }>(`${env.backend}/auth/delete-account`, {
    method: "POST",
    headers: jsonHeaders({}),
    body: JSON.stringify({ password }),
  });
}

export async function generateSpeakingItems(body: SpeakingGenerateBody) {
  return req<SpeakingGenerateResponse>(`${env.backend}/speaking/generate`, {
    method: "POST",
    headers: jsonHeaders(body),
    body: JSON.stringify(body),
  });
}

export async function uploadSpeakingRecording(
  file: File,
  sessionId?: string,
  itemId?: number
) {
  const form = new FormData();
  form.append("file", file);
  if (sessionId) form.append("sessionId", sessionId);
  if (typeof itemId === "number") form.append("itemId", String(itemId));
  return req<SpeakingUploadResponse>(`${env.backend}/speaking/upload`, {
    method: "POST",
    body: form,
  });
}

export async function evaluateSpeaking(body: SpeakingEvaluateBody) {
  return req<SpeakingEvaluateResponse>(`${env.backend}/speaking/evaluate`, {
    method: "POST",
    headers: jsonHeaders(body),
    body: JSON.stringify(body),
  });
}

export async function chatJSON(body: ChatJSONBody) {
  return req<ChatStartResponse>(`${env.backend}/chat`, {
    method: "POST",
    headers: jsonHeaders({}),
    body: JSON.stringify(body),
  });
}

export async function chatMultipart(q: string, files: File[], chatId?: string, length?: "Short" | "Medium" | "Long") {
  const f = new FormData();
  f.append("q", q);
  if (chatId) f.append("chatId", chatId);
  if (length) f.append("length", length);
  for (const file of files) f.append("file", file, file.name);
  return req<ChatStartResponse>(`${env.backend}/chat`, {
    method: "POST",
    body: f,
    timeout: Math.max(env.timeout, 300000),
  });
}

export function connectChatStream(chatId: string, onEvent: (ev: ChatEvent) => void) {
  const url = wsURL(`/ws/chat?chatId=${encodeURIComponent(chatId)}`);
  const ws = new WebSocket(url);
  ws.onmessage = (m) => {
    try {
      const data = JSON.parse(m.data as string) as ChatEvent;
      onEvent(data);
    } catch {
      // Ignore malformed stream messages.
    }
  };
  ws.onerror = () => {
    onEvent({ type: "error", error: "stream_error" });
  };
  return { ws, close: () => { try { ws.close(); } catch { /* already closed */ } } };
}

export async function chatAskOnce(opts: {
  q: string;
  files?: File[];
  chatId?: string;
  onEvent?: (ev: ChatEvent) => void;
}) {
  const { q, files = [], chatId, onEvent } = opts;
  const start = files.length ? await chatMultipart(q, files, chatId) : await chatJSON({ q, chatId });
  let answer = "";
  let flashcards: FlashCard[] | undefined;

  await new Promise<void>((resolve, reject) => {
    const { close } = connectChatStream(start.chatId, (ev) => {
      onEvent?.(ev);
      if (ev.type === "answer") {
        const p = ev.answer;
        if (typeof p === "string") {
          answer = p;
        } else if (p && typeof p === "object") {
          answer = p.answer ?? "";
          if (Array.isArray(p.flashcards)) flashcards = p.flashcards;
        }
      }
      if (ev.type === "done") { close(); resolve(); }
      if (ev.type === "error") { close(); reject(new Error(ev.error || "chat failed")); }
    });
  });

  return { chatId: start.chatId, answer, flashcards };
}

export async function companionAsk(input: {
  question: string;
  filePath?: string;
  documentText?: string;
  documentTitle?: string;
  topic?: string;
  history?: CompanionHistoryEntry[];
}) {
  const question = (input.question || "").trim();
  if (!question) throw new Error("Question is required");

  const payload: Record<string, unknown> = { question };
  if (input.filePath) payload.filePath = input.filePath;
  if (input.documentText) payload.documentText = input.documentText;
  if (input.documentTitle) payload.documentTitle = input.documentTitle;
  if (input.topic) payload.topic = input.topic;
  if (input.history && input.history.length) {
    payload.history = input.history.map((h) => ({ role: h.role, content: h.content }));
  }

  return req<CompanionAskResponse>(`${env.backend}/api/companion/ask`, {
    method: "POST",
    headers: jsonHeaders({}),
    body: JSON.stringify(payload),
    timeout: Math.max(env.timeout, 120000),
  });
}

export function getChats(query?: string, role?: "student" | "teacher") {
  const params = new URLSearchParams();
  if (query) params.set("q", query);
  if (role) params.set("role", role);
  const qs = params.toString() ? `?${params.toString()}` : "";
  return req<ChatsList>(`${env.backend}/chats${qs}`, { method: "GET" });
}

export function getChatDetail(id: string) {
  return req<ChatDetail>(`${env.backend}/chats/${encodeURIComponent(id)}`, { method: "GET" });
}

export function deleteChat(id: string) {
  return req<{ ok: true }>(`${env.backend}/chats/${encodeURIComponent(id)}`, { method: "DELETE" });
}

export async function createFlashcard(input: {
  question: string;
  answer: string;
  tag: string;
}) {
  return req<{ ok: true; flashcard: SavedFlashcard }>(`${env.backend}/flashcards`, {
    method: "POST",
    headers: jsonHeaders({}),
    body: JSON.stringify(input),
  });
}

export async function listFlashcards() {
  return req<{ ok: true; flashcards: SavedFlashcard[] }>(`${env.backend}/flashcards`, {
    method: "GET",
  });
}

export async function deleteFlashcard(id: string) {
  return req<{ ok: true }>(`${env.backend}/flashcards/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
}

export async function generateKnowledgeDeck(input: {
  topic: string;
  count?: number;
  includeMaterials?: boolean;
  materialIds?: string[];
}) {
  return req<{ ok: boolean; deck: KnowledgeDeck }>(`${env.backend}/flashcards/decks`, {
    method: "POST",
    headers: jsonHeaders({}),
    body: JSON.stringify(input),
    timeout: Math.max(env.timeout, 180000),
  });
}

export async function listKnowledgeDecks() {
  return req<{ ok: boolean; decks: KnowledgeDeckMeta[] }>(`${env.backend}/flashcards/decks`, {
    method: "GET",
  });
}

export async function getKnowledgeDeck(id: string) {
  return req<{ ok: boolean; deck: KnowledgeDeck }>(`${env.backend}/flashcards/decks/${encodeURIComponent(id)}`, {
    method: "GET",
  });
}

export async function deleteKnowledgeDeck(id: string) {
  return req<{ ok: boolean }>(`${env.backend}/flashcards/decks/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
}

export async function getExams() {
  return req<{ ok: true; exams: ExamMeta[] }>(
    `${env.backend}/exams`,
    { method: "GET" }
  )
}

export async function startExam(examId: string) {
  return req<{ ok: true; runId: string } & TaskStartLinks>(
    `${env.backend}/exam`,
    {
      method: "POST",
      headers: jsonHeaders({}),
      body: JSON.stringify({ examId }),
    }
  )
}

export function connectExamStream(runId: string, onEvent: (ev: ExamEvent) => void) {
  const url = wsURL(`/ws/exams?runId=${encodeURIComponent(runId)}`)
  const ws = new WebSocket(url)
  ws.onmessage = (m) => {
    try {
      onEvent(JSON.parse(m.data as string) as ExamEvent)
    } catch {
      // Ignore malformed stream messages.
    }
  }
  ws.onerror = () => onEvent({ type: "error", error: "stream_error" })
  return { ws, close: () => { try { ws.close() } catch { /* already closed */ } } }
}

export async function smartnotesStart(input: {
  topic?: string;
  notes?: string;
  filePath?: string;
  includeMaterials?: boolean;
  materialIds?: string[];
  length?: "rough" | "medium" | "detailed";
}) {
  return req<SmartNotesStart>(`${env.backend}/smartnotes`, {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify(input),
  });
}

export function listSmartNotes() {
  return req<{ ok: true; notes: SmartNoteMeta[] }>(
    `${env.backend}/smartnotes`,
    { method: "GET" }
  );
}

export function getSmartNoteDetail(id: string) {
  return req<{ ok: true; note: SmartNoteMeta; notes: SmartNotesPayload | null }>(
    `${env.backend}/smartnotes/${encodeURIComponent(id)}`,
    { method: "GET" }
  );
}

export function deleteSmartNote(id: string) {
  return req<{ ok: true }>(`${env.backend}/smartnotes/${encodeURIComponent(id)}`, { method: "DELETE" });
}

export function connectSmartnotesStream(noteId: string, onEvent: (ev: SmartNotesEvent) => void) {
  const url = wsURL(`/ws/smartnotes?noteId=${encodeURIComponent(noteId)}`);
  const ws = new WebSocket(url);
  let closedByClient = false;
  ws.onmessage = (m) => {
    try {
      onEvent(JSON.parse(m.data as string) as SmartNotesEvent);
    } catch {
      // Ignore malformed stream messages.
    }
  };
  ws.onerror = () => onEvent({ type: "error", error: "stream_error" });
  ws.onclose = (event) => {
    if (closedByClient) return;
    onEvent({ type: "close", code: event.code });
  };
  return {
    ws,
    close: () => {
      closedByClient = true;
      try {
        ws.close();
      } catch {
        // WebSocket may already be closed.
      }
    },
  };
}

export function flashcards(topic: string) {
  return req<{ cards: unknown[] }>(`${env.backend}/flashcards`, {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify({ topic }),
  });
}

export async function quizStart(payload: {
  topic: string;
  includeMaterials?: boolean;
  materialIds?: string[];
  count?: number;
  difficulty?: "easy" | "medium" | "hard";
  role?: "student" | "teacher";
}) {
  return req<QuizStartResponse>(`${env.backend}/quiz`, {
    method: "POST",
    headers: jsonHeaders({}),
    body: JSON.stringify(payload),
  });
}

export function listQuizzes(role?: "student" | "teacher") {
  const qs = role ? `?role=${encodeURIComponent(role)}` : "";
  return req<{ ok: true; quizzes: QuizMeta[] }>(
    `${env.backend}/quizzes${qs}`,
    { method: "GET" }
  );
}

export function getQuizDetail(id: string) {
  return req<{ ok: true; quiz: QuizMeta; questions: Question[] }>(
    `${env.backend}/quizzes/${encodeURIComponent(id)}`,
    { method: "GET" }
  );
}

export function getQuizAttempts(id: string) {
  return req<{ ok: true; attempts: QuizAttempt[] }>(
    `${env.backend}/quizzes/${encodeURIComponent(id)}/attempts`,
    { method: "GET" }
  );
}

export function deleteQuiz(id: string) {
  return req<{ ok: true }>(`${env.backend}/quizzes/${encodeURIComponent(id)}`, { method: "DELETE" });
}

export function saveQuizAttempts(quizId: string, answers: QuizAttempt[]) {
  return req<{ ok: true }>(`${env.backend}/quizzes/${encodeURIComponent(quizId)}/attempts`, {
    method: "POST",
    headers: jsonHeaders({}),
    body: JSON.stringify({ answers }),
  });
}

export function saveQuizAttemptAnswer(quizId: string, answer: QuizAttempt) {
  return req<{ ok: true; attempt: QuizAttempt }>(`${env.backend}/quizzes/${encodeURIComponent(quizId)}/attempts/answer`, {
    method: "POST",
    headers: jsonHeaders({}),
    body: JSON.stringify(answer),
  });
}

// ---------- 教学视频 (teaching video) ----------
export type TeachingVideoStartResponse = { ok: true; videoId: string } & TaskStartLinks;
export type TeachingVideoEvent =
  | { type: "ready"; videoId?: string }
  | { type: "phase"; value: string }
  | { type: "script"; script: string }
  | { type: "video"; videoUrl: string }
  | { type: "local_video"; localPath: string }
  | { type: "local_audio"; audioPath: string }
  | { type: "video_error"; error: string }
  | { type: "done" }
  | { type: "close"; code?: number }
  | { type: "error"; error: string };

export async function teachingVideoStart(payload: {
  topic: string;
  includeMaterials?: boolean;
  materialIds?: string[];
  role?: "student" | "teacher";
}) {
  return req<TeachingVideoStartResponse>(`${env.backend}/teaching-video`, {
    method: "POST",
    headers: jsonHeaders({}),
    body: JSON.stringify(payload),
  });
}

export function listTeachingVideos(role?: "student" | "teacher") {
  const qs = role ? `?role=${encodeURIComponent(role)}` : "";
  return req<{ ok: true; videos: { id: string; title?: string; at?: number }[] }>(
    `${env.backend}/teaching-videos${qs}`,
    { method: "GET" }
  );
}

export function getTeachingVideoDetail(id: string) {
  return req<{
    ok: true;
    video: { id: string; title?: string; updated_at?: string };
    script: string;
    videoUrl?: string;
    localVideoUrl?: string;
    localAudioUrl?: string;
    videoError?: string;
    videoSource?: "jimeng_remote" | "jimeng_local_merge" | "fallback_local" | "audio_only" | "script_only";
  }>(`${env.backend}/teaching-videos/${encodeURIComponent(id)}`, { method: "GET" });
}

export function deleteTeachingVideo(id: string) {
  return req<{ ok: true }>(`${env.backend}/teaching-videos/${encodeURIComponent(id)}`, { method: "DELETE" });
}

export function connectTeachingVideoStream(videoId: string, onEvent: (ev: TeachingVideoEvent) => void) {
  const url = wsURL(`/ws/teaching-video?videoId=${encodeURIComponent(videoId)}`);
  const ws = new WebSocket(url);
  let closedByClient = false;
  ws.onmessage = (m) => {
    try {
      onEvent(JSON.parse(m.data as string) as TeachingVideoEvent);
    } catch {
      // Ignore malformed stream messages.
    }
  };
  ws.onclose = (e) => {
    if (closedByClient) return;
    onEvent({ type: "close", code: e.code });
  };
  ws.onerror = () => onEvent({ type: "error", error: "stream_error" });
  return {
    ws,
    close: () => {
      closedByClient = true;
      try {
        ws.close();
      } catch {
        // WebSocket may already be closed.
      }
    },
  };
}

export function getWrongBookSummary() {
  return req<WrongBookSummary>(`${env.backend}/wrongbook/summary`, { method: "GET" });
}

export function generateWrongBookReport() {
  return req<{ ok: true; report: WrongBookReport }>(`${env.backend}/wrongbook/report`, {
    method: "POST",
    headers: jsonHeaders({}),
    body: JSON.stringify({}),
  });
}

export function analyzeWeakPoints() {
  return req<{ ok: true; points: WeakPoint[] }>(`${env.backend}/wrongbook/weak-points`, {
    method: "POST",
    headers: jsonHeaders({}),
    body: JSON.stringify({}),
  });
}

export async function podcastStart(payload: {
  topic: string;
  includeMaterials?: boolean;
  materialIds?: string[];
  length?: "short" | "medium" | "long";
}) {
  return req<{ ok: boolean; pid: string } & TaskStartLinks>(`${env.backend}/podcast`, {
    method: "POST",
    headers: jsonHeaders({}),
    body: JSON.stringify(payload),
  });
}

export function listPodcasts() {
  return req<{ ok: true; podcasts: PodcastMeta[] }>(
    `${env.backend}/podcasts`,
    { method: "GET" }
  );
}

export function getPodcastDetail(id: string) {
  return req<{ ok: true; podcast: PodcastMeta; script: PodcastScript | null }>(
    `${env.backend}/podcasts/${encodeURIComponent(id)}`,
    { method: "GET" }
  );
}

export function deletePodcast(id: string) {
  return req<{ ok: true }>(`${env.backend}/podcasts/${encodeURIComponent(id)}`, { method: "DELETE" });
}

// ---------- 教案 (lesson plan) ----------
export type LessonPlanMeta = { id: string; title?: string; created_at?: string; updated_at?: string; at?: number };
export type LessonPlanTeachingGoals = { knowledge?: string; process?: string; emotion?: string };
export type LessonPlanProcessStep = { title: string; content: string };
export type LessonPlanData = {
  title?: string;
  teaching_goals?: LessonPlanTeachingGoals;
  key_points?: string[];
  difficult_points?: string[];
  preparation?: string[];
  process?: LessonPlanProcessStep[];
  homework?: string;
};

export function createLessonPlan(payload: { topic: string; includeMaterials?: boolean; materialIds?: string[] }) {
  return req<{
    ok: true;
    lessonPlanId: string;
    plan: LessonPlanData;
    meta: LessonPlanMeta;
  }>(`${env.backend}/lesson-plan`, {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify(payload),
  });
}

export function listLessonPlans() {
  return req<{ ok: true; lessonPlans: LessonPlanMeta[] }>(`${env.backend}/lesson-plans`, { method: "GET" });
}

export function getLessonPlanDetail(id: string) {
  return req<{ ok: true; meta: LessonPlanMeta; plan: LessonPlanData }>(
    `${env.backend}/lesson-plans/${encodeURIComponent(id)}`,
    { method: "GET" }
  );
}

export function deleteLessonPlan(id: string) {
  return req<{ ok: true }>(`${env.backend}/lesson-plans/${encodeURIComponent(id)}`, { method: "DELETE" });
}

export function lessonPlanPdfUrl(id: string): string {
  const base = `${env.backend}/lesson-plans/${encodeURIComponent(id)}/pdf`;
  try {
    const token = getAuthToken();
    if (!token) return base;
    const parsed = new URL(base);
    parsed.searchParams.set("token", token);
    return parsed.toString();
  } catch {
    return base;
  }
}

export function connectPodcastStream(pid: string, onEvent: (ev: PodcastEvent) => void) {
  const wsUrl = wsURL(`/ws/podcast?pid=${encodeURIComponent(pid)}`)
  const ws = new WebSocket(wsUrl)
  let closedByClient = false

  ws.onmessage = (e) => {
    try {
      const msg = JSON.parse(e.data as string) as PodcastEvent
      onEvent(msg)
    } catch {
      onEvent({ type: "error", error: "invalid_message" })
    }
  }

  ws.onclose = (e) => {
    if (closedByClient) return
    onEvent({ type: "close", code: e.code })
  }

  ws.onerror = () => onEvent({ type: "error", error: "stream_error" })
  return {
    ws,
    close: () => {
      closedByClient = true
      try {
        ws.close()
      } catch {
        // WebSocket may already be closed.
      }
    },
  }
}

export function connectQuizStream(quizId: string, onEvent: (ev: QuizEvent) => void) {
  const url = wsURL(`/ws/quiz?quizId=${encodeURIComponent(quizId)}`);
  const ws = new WebSocket(url);
  let closedByClient = false;
  ws.onmessage = m => {
    try {
      onEvent(JSON.parse(m.data as string) as QuizEvent)
    } catch {
      // Ignore malformed stream messages.
    }
  };
  ws.onerror = () => onEvent({ type: "error", error: "stream_error" });
  ws.onclose = (event) => {
    if (closedByClient) return;
    const code = event?.code ?? 0;
    onEvent({ type: "error", error: code ? `stream_closed:${code}` : "stream_closed" });
  };
  return {
    ws,
    close: () => {
      closedByClient = true;
      try {
        ws.close()
      } catch {
        // WebSocket may already be closed.
      }
    },
  };
}

export async function paperStart(payload: {
  topic: string;
  includeMaterials?: boolean;
  materialIds?: string[];
  difficulty?: "easy" | "medium" | "hard";
  count_choice?: number;
  count_fill?: number;
  count_application?: number;
}) {
  return req<PaperStartResponse>(`${env.backend}/paper`, {
    method: "POST",
    headers: jsonHeaders({}),
    body: JSON.stringify(payload),
  });
}

export function connectPaperStream(paperId: string, onEvent: (ev: PaperEvent) => void) {
  const url = wsURL(`/ws/paper?paperId=${encodeURIComponent(paperId)}`);
  const ws = new WebSocket(url);
  ws.onmessage = (m) => {
    try {
      onEvent(JSON.parse(m.data as string) as PaperEvent);
    } catch {
      // Ignore malformed stream messages.
    }
  };
  ws.onerror = () => onEvent({ type: "error", error: "stream_error" });
  return {
    ws,
    close: () => {
      try {
        ws.close();
      } catch {
        // WebSocket may already be closed.
      }
    },
  };
}

export function listPapers() {
  return req<{ ok: true; papers: { id: string; title?: string; count_choice?: number; count_fill?: number; count_application?: number; at?: number }[] }>(
    `${env.backend}/papers`,
    { method: "GET" }
  );
}

export function getPaperDetail(id: string) {
  return req<{ ok: true; paper: { id: string; title?: string; difficulty?: string }; questions: PaperItem[] }>(
    `${env.backend}/papers/${encodeURIComponent(id)}`,
    { method: "GET" }
  );
}

export function deletePaper(id: string) {
  return req<{ ok: true }>(`${env.backend}/papers/${encodeURIComponent(id)}`, { method: "DELETE" });
}

export function paperPdfUrl(id: string) {
  return `${env.backend}/papers/${encodeURIComponent(id)}/pdf`;
}

export async function transcribeAudio(file: File) {
  const formData = new FormData();
  formData.append('file', file);

  return req<TranscriptionResponse>(`${env.backend}/transcriber`, {
    method: 'POST',
    body: formData,
    timeout: Math.max(env.timeout, 180000),
  });
}

export type PlannerTask = {
  id: string;
  course?: string;
  title: string;
  type?: string;
  notes?: string;
  dueAt: number;
  estMins: number;
  priority: 1 | 2 | 3 | 4 | 5;
  status: "todo" | "doing" | "done" | "blocked";
  createdAt: number;
  updatedAt: number;
  tags?: string[];
  files?: { id: string; filename: string; originalName: string; mimeType: string; size: number; uploadedAt: number }[];
  steps?: string[];
};
export type PlannerFile = NonNullable<PlannerTask["files"]>[number];

export type PlannerSlot = { id: string; taskId: string; start: number; end: number; kind: "focus" | "review" | "buffer"; done?: boolean }
export type WeeklyPlan = { days: { date: string; slots: PlannerSlot[] }[] }

export type PlannerEvent =
  | { type: "ready"; sid: string }
  | { type: "phase"; value: string }
  | { type: "plan.update"; taskId: string; slots: PlannerSlot[] }
  | { type: "materials.chunk"; id: string; idx: number; total: number; more: boolean; encoding: string; data: string }
  | { type: "materials.done"; id: string; total: number }
  | { type: "reminder"; text: string; at: number; taskId?: string; scheduledFor?: string }
  | { type: "daily.digest"; date: string; due: { id: string; title: string; dueAt: number }[]; sessions: number; message: string }
  | { type: "evening.review"; date: string; stats: unknown; tomorrowTasks: { id: string; title: string }[]; message: string }
  | { type: "break.reminder"; text: string; at: string }
  | { type: "task.created"; task: PlannerTask }
  | { type: "task.updated"; task: PlannerTask }
  | { type: "task.deleted"; taskId: string }
  | { type: "task.files.added"; taskId: string; files: PlannerFile[] }
  | { type: "task.file.removed"; taskId: string; fileId: string }
  | { type: "session.started"; session: { id: string; taskId: string; slotId?: string; startedAt: string; status: string } }
  | { type: "session.ended"; session: { id: string; endedAt: string; minutesWorked: number; completed: boolean; status: string } }
  | { type: "weekly.update"; plan: WeeklyPlan }
  | { type: "slot.update"; taskId: string; slotId: string; done: boolean; skip: boolean }
  | { type: "done" };

export async function plannerIngest(text: string) {
  return req<{ ok: boolean; task: PlannerTask }>(`${env.backend}/tasks/ingest`, {
    method: "POST",
    headers: jsonHeaders({}),
    body: JSON.stringify({ text })
  })
}

export async function plannerList(params?: { status?: string; dueBefore?: number; course?: string }) {
  const q = new URLSearchParams()
  if (params?.status) q.set("status", params.status)
  if (params?.dueBefore) q.set("dueBefore", String(params.dueBefore))
  if (params?.course) q.set("course", params.course)
  const url = `${env.backend}/tasks${q.toString() ? `?${q}` : ""}`
  return req<{ ok: boolean; tasks: PlannerTask[] }>(url, { method: "GET" })
}

export async function plannerPlan(id: string, cram?: boolean) {
  return req<{ ok: boolean; task: PlannerTask & { plan?: { slots: PlannerSlot[] } } }>(`${env.backend}/tasks/${encodeURIComponent(id)}/plan`, {
    method: "POST",
    headers: jsonHeaders({}),
    body: JSON.stringify({ cram: !!cram })
  })
}

export async function plannerWeekly(cram?: boolean) {
  return req<{ ok: boolean; plan: WeeklyPlan }>(`${env.backend}/planner/weekly`, {
    method: "POST",
    headers: jsonHeaders({}),
    body: JSON.stringify({ cram: !!cram })
  })
}

export async function plannerMaterials(id: string, kind: "summary" | "studyGuide" | "flashcards" | "quiz") {
  return req<{ ok: boolean; data: unknown }>(`${env.backend}/tasks/${encodeURIComponent(id)}/materials`, {
    method: "POST",
    headers: jsonHeaders({}),
    body: JSON.stringify({ kind })
  })
}

export function connectPlannerStream(sid: string, onEvent: (ev: PlannerEvent) => void) {
  const url = wsURL(`/ws/planner?sid=${encodeURIComponent(sid)}`)
  const ws = new WebSocket(url)
  ws.onmessage = (m) => {
    try {
      const ev = JSON.parse(m.data as string)
      onEvent(ev as PlannerEvent)
    } catch {
      // Ignore malformed stream messages.
    }
  }
  ws.onerror = () => { /* ignore for now */ }
  return {
    ws,
    close: () => {
      try {
        ws.close()
      } catch {
        // WebSocket may already be closed.
      }
    },
  }
}

export async function plannerUpdate(id: string, patch: Partial<PlannerTask>) {
  return req<{ ok: boolean; task: PlannerTask }>(`${env.backend}/tasks/${encodeURIComponent(id)}`, {
    method: "PATCH",
    headers: jsonHeaders({}),
    body: JSON.stringify(patch)
  })
}

export async function plannerDelete(id: string) {
  return req<{ ok: boolean }>(`${env.backend}/tasks/${encodeURIComponent(id)}`, { method: "DELETE" })
}

export async function plannerCreateWithFiles(data: { text?: string; title?: string; course?: string; type?: string; files?: File[] }) {
  const formData = new FormData()
  if (data.text) formData.append('q', data.text)
  if (data.title) formData.append('title', data.title)
  if (data.course) formData.append('course', data.course)
  if (data.type) formData.append('type', data.type)
  if (data.files) {
    for (const file of data.files) {
      formData.append('file', file, file.name)
    }
  }

  return req<{ ok: boolean; task: PlannerTask & { files?: PlannerFile[] } }>(`${env.backend}/tasks`, {
    method: "POST",
    body: formData,
    timeout: Math.max(env.timeout, 300000),
  })
}

export async function plannerUploadFiles(taskId: string, files: File[]) {
  const formData = new FormData()
  for (const file of files) {
    formData.append('file', file, file.name)
  }

  return req<{ ok: boolean; files: PlannerFile[] }>(`${env.backend}/tasks/${encodeURIComponent(taskId)}/files`, {
    method: "POST",
    body: formData,
    timeout: Math.max(env.timeout, 300000),
  })
}

export async function plannerDeleteFile(taskId: string, fileId: string) {
  return req<{ ok: boolean }>(`${env.backend}/tasks/${encodeURIComponent(taskId)}/files/${encodeURIComponent(fileId)}`, {
    method: "DELETE"
  })
}

export async function listFiles(role?: "student" | "teacher") {
  const qs = role ? `?role=${encodeURIComponent(role)}` : "";
  return req<FileListResponse>(`${env.backend}/files${qs}`, { method: "GET" });
}

export async function uploadFiles(files: File[], role?: "student" | "teacher") {
  const formData = new FormData();
  for (const file of files) formData.append("file", file, file.name);
  if (role) formData.append("role", role);
  return req<FileUploadResponse>(`${env.backend}/files`, {
    method: "POST",
    body: formData,
    timeout: Math.max(env.timeout, 300000),
  });
}

export async function deleteFile(fileId: string, role?: "student" | "teacher") {
  const qs = role ? `?role=${encodeURIComponent(role)}` : "";
  return req<{ ok: boolean }>(`${env.backend}/files/${encodeURIComponent(fileId)}${qs}`, {
    method: "DELETE",
  });
}

export type DebateStartResponse = {
  ok: boolean;
  debateId: string;
  session: {
    id: string;
    topic: string;
    position: "for" | "against";
    createdAt: number;
  };
  stream: string;
  error?: string;
}

export type DebateSession = {
  id: string;
  topic: string;
  position: "for" | "against";
  messages: Array<{
    role: "user" | "assistant";
    content: string;
    timestamp: number;
  }>;
  createdAt: number;
}
export type DebateSummary = Pick<DebateSession, "id" | "topic" | "position" | "createdAt"> & {
  messageCount?: number;
  updatedAt?: number;
}

export async function startDebate(topic: string, position: "for" | "against") {
  return req<DebateStartResponse>(`${env.backend}/debate/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ topic, position }),
    timeout: 30000,
  })
}

export async function submitDebateArgument(debateId: string, argument: string) {
  return req<{ ok: boolean; message: string; error?: string }>(`${env.backend}/debate/${encodeURIComponent(debateId)}/argue`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ argument }),
    timeout: 120000,
  })
}

export async function getDebateSession(debateId: string) {
  return req<{ ok: boolean; session: DebateSession; error?: string }>(`${env.backend}/debate/${encodeURIComponent(debateId)}`, {
    method: "GET",
  })
}

export async function listDebates() {
  return req<{ ok: boolean; debates: DebateSummary[]; error?: string }>(`${env.backend}/debates`, {
    method: "GET",
  })
}

export async function deleteDebate(debateId: string) {
  return req<{ ok: boolean; message: string; error?: string }>(`${env.backend}/debate/${encodeURIComponent(debateId)}`, {
    method: "DELETE",
  })
}

export async function surrenderDebate(debateId: string) {
  return req<{ ok: boolean; message: string; error?: string }>(`${env.backend}/debate/${encodeURIComponent(debateId)}/surrender`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  })
}

export type DebateAnalysis = {
  winner: "user" | "ai" | "draw";
  reason: string;
  userStrengths: string[];
  aiStrengths: string[];
  userWeaknesses: string[];
  aiWeaknesses: string[];
  keyMoments: string[];
  overallAssessment: string;
}

export async function analyzeDebate(debateId: string) {
  return req<{ ok: boolean; analysis: DebateAnalysis; session: DebateSession; error?: string }>(`${env.backend}/debate/${encodeURIComponent(debateId)}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    timeout: 60000,
  })
}

export type SlideItem = {
  title: string;
  bullets: string[];
  imageUrl?: string | null;
};
export type SlidesGenerateResponse = {
  ok: boolean;
  slideId?: string;
  title?: string;
  pageCount?: number;
  downloadUrl?: string;
  slides?: SlideItem[];
  error?: string;
};
export type SlideDetailResponse = {
  ok: boolean;
  slide?: { id: string; title?: string; pageCount?: number; at?: number };
  slides?: SlideItem[];
  error?: string;
};

export type BilibiliVideoItem = {
  title: string;
  cover: string;
  bvid: string;
  author: string;
  duration: string;
  description: string;
};

export type BilibiliSearchResponse = {
  ok: boolean;
  keyword: string;
  items: BilibiliVideoItem[];
  error?: string;
};

export async function generateSlides(payload: {
  topic: string;
  pageCount?: number;
  includeMaterials?: boolean;
  materialIds?: string[];
}) {
  return req<SlidesGenerateResponse>(`${env.backend}/slides/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      topic: payload.topic,
      pageCount: payload.pageCount ?? 10,
      includeMaterials: payload.includeMaterials ?? false,
      materialIds: payload.materialIds ?? [],
    }),
    timeout: Math.max(env.timeout, 300000),
  });
}

export function getSlideDetail(slideId: string) {
  return req<SlideDetailResponse>(`${env.backend}/slides/${encodeURIComponent(slideId)}`, {
    method: "GET",
  });
}

export function getSlideDownloadUrl(slideId: string): string {
  return `${env.backend}/slides/${encodeURIComponent(slideId)}/download`;
}

export function searchBilibiliVideos(keyword: string) {
  return req<BilibiliSearchResponse>(
    `${env.backend}/api/bilibili/search?keyword=${encodeURIComponent(keyword)}`,
    {
      method: "GET",
      timeout: Math.max(env.timeout, 60000),
    }
  );
}

export type FriendlyTaskFeature = "generic" | "smartnotes" | "podcast" | "quiz" | "slides" | "video";

const defaultFriendlyMessage: Record<FriendlyTaskFeature, string> = {
  generic: "这次没有顺利完成，请稍后再试。",
  smartnotes: "这次笔记还没有顺利准备好，请稍后再试。",
  podcast: "这次播客还没有顺利准备好，请稍后再试。",
  quiz: "这次测验还没有顺利准备好，请稍后再试。",
  slides: "这份幻灯片还没有顺利准备好，请稍后再试。",
  video: "这节微课还没有顺利准备好，请稍后再试。",
};

const cleanErrorMessage = (value: unknown) =>
  String(value ?? "")
    .replace(/^error:\s*/i, "")
    .replace(/\s+/g, " ")
    .trim();

export function friendlyTaskMessage(
  raw: unknown,
  options: { feature?: FriendlyTaskFeature; fallback?: string } = {},
) {
  const feature = options.feature ?? "generic";
  const fallback = options.fallback ?? defaultFriendlyMessage[feature];
  const message = cleanErrorMessage(raw);
  const normalized = message.toLowerCase();

  if (!message) return fallback;

  if (normalized.includes("http 401") || normalized.includes("unauthorized") || normalized.includes("forbidden")) {
    return "登录状态已过期，请重新登录后再试。";
  }

  if (normalized.includes("http 404") || normalized.includes("not found")) {
    return "内容还在准备中，请稍后再看。";
  }

  if (
    normalized.includes("provide topic")
    || normalized.includes("topic required")
    || normalized.includes("no valid input")
  ) {
    return "请先输入你想整理的主题。";
  }

  if (normalized.includes("noteid missing") || normalized.includes("pid missing")) {
    return "这次任务没有顺利创建，请再试一次。";
  }

  if (
    normalized.includes("stream_closed")
    || normalized.includes("stream_error")
    || normalized.includes("invalid_message")
    || normalized.includes("websocket")
    || normalized.includes("socket")
  ) {
    return "连接刚刚有点波动，请稍等，内容准备好后会继续显示。";
  }

  if (normalized.includes("timeout") || normalized.includes("aborterror") || normalized.includes("aborted")) {
    return "这次准备时间比平时久一点，请再稍等一会儿。";
  }

  if (normalized.includes("audio synthesis failed")) {
    if (feature === "podcast") return "音频暂时还没有准备好，不过脚本已经整理好了。";
    if (feature === "video") return "讲解音频暂时还没有准备好，请稍后再看。";
  }

  if (normalized.includes("429") || normalized.includes("rate limit") || normalized.includes("too many") || normalized.includes("concurrent limit")) {
    return "现在同时使用的人有点多，请稍后再试一次。";
  }

  if (
    normalized.includes("deepseek")
    || normalized.includes("jimeng")
    || normalized.includes("tts")
    || normalized.includes("api")
    || normalized.includes("http 500")
    || normalized.includes("generation failed")
    || normalized.includes("failed")
  ) {
    return fallback;
  }

  if (
    /[\u4e00-\u9fff]/.test(message)
    && !/(接口|落盘|轮询|服务端|websocket|socket|stream|provider|deepseek|即梦|tts)/i.test(message)
  ) {
    return message;
  }

  return fallback;
}

export function err(e: unknown) {
  return friendlyTaskMessage(e);
}
