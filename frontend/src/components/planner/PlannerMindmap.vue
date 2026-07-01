<template>
  <div
    ref="wrapRef"
    class="relative w-full h-full bg-black overflow-hidden"
    style="overscroll-behavior: contain; touch-action: none"
    @pointermove="onMove"
    @pointerup="onUp"
    @pointerdown="startPan"
    @wheel.prevent="onWheel"
  >
    <div class="absolute inset-0 opacity-40" :style="gridStyle" />
    <div class="pointer-events-none absolute inset-0" :style="glowStyle" />

    <div class="absolute top-3 left-3 z-20 text-[11px] text-stone-400 bg-stone-900/60 border border-zinc-800 rounded px-2 py-1 backdrop-blur">
      拖动平移，滚动缩放，拖动节点进行排列。双击节点聚焦。
    </div>

    <svg class="absolute inset-0 w-full h-full pointer-events-none" xmlns="http://www.w3.org/2000/svg">
      <template v-for="t in tasks" :key="t.id">
        <template v-for="label in labelsForTask(t)" :key="`${t.id}-${label}`">
          <line v-if="lineForStep(t, label)" v-bind="lineForStep(t, label)" stroke="#27272a" :stroke-width="1.5" />
        </template>
      </template>
    </svg>

    <div v-if="tasks.length === 0 && customNodes.length === 0" class="absolute inset-0 flex items-center justify-center pointer-events-none">
      <svg width="520" height="280" viewBox="0 0 700 380" class="opacity-60">
        <defs>
          <radialGradient id="pulse1" cx="50%" cy="50%">
            <stop offset="0%" stop-color="#22d3ee" stop-opacity="0.7" />
            <stop offset="100%" stop-color="#22d3ee" stop-opacity="0" />
          </radialGradient>
          <radialGradient id="pulse2" cx="50%" cy="50%">
            <stop offset="0%" stop-color="#a78bfa" stop-opacity="0.6" />
            <stop offset="100%" stop-color="#a78bfa" stop-opacity="0" />
          </radialGradient>
          <radialGradient id="pulse3" cx="50%" cy="50%">
            <stop offset="0%" stop-color="#4ade80" stop-opacity="0.6" />
            <stop offset="100%" stop-color="#4ade80" stop-opacity="0" />
          </radialGradient>
        </defs>
        <g>
          <circle cx="350" cy="190" r="5" fill="#93c5fd" class="tw" />
          <circle cx="520" cy="120" r="3" fill="#fca5a5" class="tw2" />
          <circle cx="210" cy="90" r="2.5" fill="#86efac" class="tw3" />
          <circle cx="140" cy="250" r="3" fill="#a78bfa" class="tw2" />
          <circle cx="580" cy="250" r="2.5" fill="#67e8f9" class="tw" />
          <g stroke="#3f3f46" stroke-width="1">
            <line x1="350" y1="190" x2="520" y2="120" />
            <line x1="350" y1="190" x2="210" y2="90" />
            <line x1="350" y1="190" x2="140" y2="250" />
            <line x1="350" y1="190" x2="580" y2="250" />
            <line x1="520" y1="120" x2="580" y2="250" />
            <line x1="210" y1="90" x2="140" y2="250" />
          </g>
          <g font-family="Inter, ui-sans-serif" font-size="12" fill="#e4e4e7" text-anchor="middle">
            <rect x="325" y="172" width="54" height="24" rx="7" fill="#18181b" stroke="#27272a" />
            <text x="352" y="189">专注</text>
            <rect x="495" y="104" width="54" height="22" rx="7" fill="#111827" stroke="#1f2937" />
            <text x="522" y="119">回忆</text>
            <rect x="185" y="74" width="54" height="22" rx="7" fill="#0f172a" stroke="#1f2937" />
            <text x="212" y="89">大纲</text>
            <rect x="115" y="234" width="54" height="22" rx="7" fill="#111827" stroke="#1f2937" />
            <text x="142" y="249">复习</text>
            <rect x="555" y="234" width="54" height="22" rx="7" fill="#0f172a" stroke="#1f2937" />
            <text x="582" y="249">优化</text>
          </g>
          <g opacity="0.35">
            <circle cx="350" cy="190" r="28" fill="url(#pulse1)" />
            <circle cx="520" cy="120" r="22" fill="url(#pulse2)" />
            <circle cx="140" cy="250" r="22" fill="url(#pulse2)" />
            <circle cx="210" cy="90" r="18" fill="url(#pulse3)" />
            <circle cx="580" cy="250" r="18" fill="url(#pulse1)" />
          </g>
        </g>
      </svg>
    </div>

    <svg class="absolute inset-0 w-full h-full pointer-events-none" xmlns="http://www.w3.org/2000/svg">
      <line
        v-for="(edge, i) in customEdges"
        :key="`edge-${i}`"
        :x1="edge.ax"
        :y1="edge.ay"
        :x2="edge.bx"
        :y2="edge.by"
        stroke="#3f3f46"
        :stroke-width="1"
      />
    </svg>

    <div
      v-for="t in tasks"
      :key="t.id"
      class="absolute select-none"
      data-node
      :style="{ left: `${pan.x + (positions[t.id]?.x || 0) * zoom}px`, top: `${pan.y + (positions[t.id]?.y || 0) * zoom}px` }"
    >
      <div :style="{ transform: `scale(${zoom})`, transformOrigin: 'top left', position: 'relative' }">
        <div
          :ref="setNodeRef(t.id)"
          @dblclick="focusNode(t.id)"
        >
          <div class="pointer-events-none absolute -inset-2 opacity-35" :style="{ background: 'radial-gradient(22px 22px at 50% 65%, rgba(56,189,248,0.2), transparent 70%)' }" />
          <div class="cursor-grab active:cursor-grabbing rounded-full border bg-[#0b1220]/70 border-[#1f2937] pl-3 pr-1.5 py-1.5 shadow-[0_2px_8px_rgba(0,0,0,0.4)] backdrop-blur flex items-center gap-1.5" @pointerdown="(e) => onDown(e, t.id)">
            <div class="text-[12px] text-slate-200 whitespace-nowrap max-w-[260px] truncate">{{ t.title }}</div>
            <button class="text-[12px] text-slate-300 hover:text-slate-100 px-1 rounded hover:bg-stone-800" @click.stop="toggleMenu(t.id)">⋯</button>
          </div>

          <div v-if="menuOpen === t.id" class="absolute left-0 top-[120%] z-30 bg-stone-900/95 border border-zinc-800 rounded-md shadow-lg min-w-[160px] p-1">
            <button class="w-full text-left text-[12px] text-stone-200 px-2 py-1 rounded hover:bg-stone-800" @click="startTaskNow(t.id)">立即开始</button>
            <button class="w-full text-left text-[12px] text-stone-200 px-2 py-1 rounded hover:bg-stone-800" @click="handlePlan(t.id)">计划</button>
            <div class="border-t border-zinc-800 my-1" />
            <button class="w-full text-left text-[12px] text-stone-200 px-2 py-1 rounded hover:bg-stone-800" @click="handleAssist(t.id, 'summary')">协助：摘要</button>
            <button class="w-full text-left text-[12px] text-stone-200 px-2 py-1 rounded hover:bg-stone-800" @click="handleAssist(t.id, 'studyGuide')">协助：学习指南</button>
            <button class="w-full text-left text-[12px] text-stone-200 px-2 py-1 rounded hover:bg-stone-800" @click="handleAssist(t.id, 'flashcards')">协助：闪卡</button>
            <div class="border-t border-zinc-800 my-1" />
            <label class="block text-[12px] text-stone-200 px-2 py-1 rounded hover:bg-stone-800 cursor-pointer">
              上传文件
              <input type="file" class="hidden" @change="(e) => onUploadFile(t.id, e)" />
            </label>
            <button class="w-full text-left text-[12px] text-stone-200 px-2 py-1 rounded hover:bg-stone-800" @click="addNote(t.id)">添加笔记...</button>
            <button class="w-full text-left text-[12px] text-stone-200 px-2 py-1 rounded hover:bg-stone-800" @click="recenterSteps(t.id)">重新居中步骤</button>
            <div class="border-t border-zinc-800 my-1" />
            <button class="w-full text-left text-[12px] text-red-400 px-2 py-1 rounded hover:bg-red-950/40" @click="handleDelete(t.id)">删除任务</button>
          </div>
        </div>

        <div v-for="label in labelsForTask(t)" :key="`${t.id}-${label}`">
          <div
            v-if="stepPos[`${t.id}::${label}`]"
            class="absolute rounded-full border border-zinc-800 bg-stone-950/80 text-center text-stone-300 cursor-grab active:cursor-grabbing"
            :style="stepBubbleStyle(t.id, label)"
            @pointerdown="(e) => onDownStep(e, t.id, label)"
          >
            <div class="pointer-events-none absolute -inset-2" :style="{ background: 'radial-gradient(18px 18px at 50% 60%, rgba(125,211,252,0.12), rgba(0,0,0,0) 70%)' }" />
            <button
              class="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-stone-800 text-stone-100 hover:bg-red-600 hover:text-white flex items-center justify-center z-20"
              aria-label="删除气泡"
              @click.stop="removeStep(t.id, label)"
            >
              ×
            </button>
            <span class="relative px-2">{{ label }}{{ stepCountLabel(t.id, label) }}</span>
          </div>
        </div>
      </div>
    </div>

    <div
      v-for="n in customNodes"
      :key="n.id"
      class="absolute select-none"
      data-node
      :style="{ left: `${pan.x + n.x * zoom}px`, top: `${pan.y + n.y * zoom}px` }"
    >
      <div :style="{ transform: `scale(${zoom})`, transformOrigin: 'top left', position: 'relative' }">
        <div class="pointer-events-none absolute -inset-2 opacity-35" :style="{ background: `radial-gradient(22px 22px at 50% 65%, ${n.color}33, transparent 70%)` }" />
        <div class="cursor-grab active:cursor-grabbing rounded-lg border bg-[#0b1220]/70 border-[#1f2937] px-2.5 py-1 shadow-[0_2px_8px_rgba(0,0,0,0.4)] backdrop-blur" @pointerdown="(e) => onDownCustom(e, n.id)">
          <div class="flex items-center gap-2">
            <input
              v-if="editingId === n.id"
              v-model="editingLabel"
              class="bg-transparent text-[12px] text-slate-200 outline-none"
              @blur="saveCustomLabel(n.id)"
            />
            <div v-else class="text-[12px] text-slate-200" @dblclick="editCustomLabel(n)">{{ n.label }}</div>
            <button class="text-[11px] text-slate-400 hover:text-slate-200" @click.stop="removeCustomNode(n.id)">×</button>
          </div>
        </div>
      </div>
    </div>

    <div class="absolute top-3 right-3 z-20 bg-stone-900/70 backdrop-blur border border-zinc-800 rounded-lg px-2 py-1 flex items-center gap-2 text-xs text-stone-300">
      <button class="px-2 py-1 bg-stone-800 rounded" @click="addBubble">添加气泡</button>
      <button class="px-2 py-1 bg-stone-800 rounded" @click="zoomOut">-</button>
      <div class="px-2">{{ Math.round(zoom * 100) }}%</div>
      <button class="px-2 py-1 bg-stone-800 rounded" @click="zoomIn">+</button>
      <button class="px-2 py-1 bg-stone-800 rounded" @click="resetView">重置</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch, type CSSProperties, type ComponentPublicInstance } from "vue";
import { forceSimulation, forceManyBody, forceCollide, forceRadial, type Simulation } from "d3-force";
import { anchorLine } from "./mindmap/geometry";
import { plannerMaterials, type PlannerSlot, type PlannerTask, type WeeklyPlan } from "../../lib/api";

type Props = {
  tasks: PlannerTask[];
  plan: WeeklyPlan | null;
  onPlan: (id: string) => void;
  onAssist: (id: string, kind: "summary" | "flashcards" | "studyGuide" | "quiz") => void;
  onUpdateStatus: (id: string, s: PlannerTask["status"]) => void;
  onUpload: (id: string, file: File) => void;
  onDelete: (id: string) => void;
  onStartNow?: (id: string) => void;
  onUpdateNotes?: (id: string, notes: string) => void;
};

type Pt = { x: number; y: number };

type CustomNode = { id: string; x: number; y: number; label: string; color: string };

type DragState = { id: string; off: Pt } | null;

type Step = { label: string; w: number };

type MindmapNode = {
  id: string;
  x: number;
  y: number;
  fx?: number | null;
  fy?: number | null;
  type: "center" | "step";
  taskId?: string;
  label?: string;
};

type NodeMap = Record<string, MindmapNode>;

type SimMap = Record<string, Simulation<MindmapNode>>;

type StepPos = Record<string, Pt>;

type Edge = { ax: number; ay: number; bx: number; by: number };

const props = defineProps<Props>();

const wrapRef = ref<HTMLDivElement | null>(null);
const nodeRefs = ref<Record<string, HTMLDivElement | null>>({});
const positions = ref<Record<string, Pt>>({});
const drag = ref<DragState>(null);
const dragCustom = ref<DragState>(null);
const dragStep = ref<DragState>(null);
const pan = ref<Pt>({ x: 0, y: 0 });
const zoom = ref(1.25);
const customNodes = ref<CustomNode[]>([]);
const editingId = ref<string | null>(null);
const editingLabel = ref("");
const aiSteps = ref<Record<string, string[]>>({});
const stepPos = ref<StepPos>({});
const menuOpen = ref<string | null>(null);
const simsRef = ref<SimMap>({});
const nodeMapRef = ref<NodeMap>({});

const MIN_ZOOM = 0.3;
const MAX_ZOOM = 3;

const gridStyle = computed<CSSProperties>(() => ({
  backgroundImage: "radial-gradient(circle at 1px 1px, #1f2937 1px, transparent 0)",
  backgroundSize: "24px 24px",
  zIndex: 0,
}));

const glowStyle = computed<CSSProperties>(() => ({
  zIndex: 1,
  opacity: 0.7,
  mixBlendMode: "screen" as CSSProperties["mixBlendMode"],
  backgroundImage: [
    "radial-gradient(900px 500px at 18% 8%, rgba(56,189,248,0.10), rgba(56,189,248,0) 60%)",
    "radial-gradient(700px 420px at 82% 28%, rgba(147,51,234,0.09), rgba(147,51,234,0) 60%)",
    "radial-gradient(800px 600px at 50% 88%, rgba(34,197,94,0.08), rgba(34,197,94,0) 60%)",
    "radial-gradient(1200px 800px at 50% 50%, rgba(255,255,255,0.06), rgba(0,0,0,0) 70%)",
  ].join(", "),
}));

const setNodeRef = (id: string) => (el: Element | ComponentPublicInstance | null) => {
  nodeRefs.value[id] = el instanceof HTMLDivElement ? el : null;
};

const labelsForTask = (t: PlannerTask) => {
  const labels = aiSteps.value[t.id];
  return labels && labels.length ? labels : inferSteps(t).map((s) => s.label);
};

const slotsByTask = computed(() => {
  const m: Record<string, PlannerSlot[]> = {};
  for (const d of props.plan?.days || []) {
    for (const s of d.slots) (m[s.taskId] ||= []).push(s);
  }
  return m;
});

const stepCountsFor = (t: PlannerTask, steps: Step[]) => {
  const total = slotsByTask.value[t.id]?.length || 0;
  if (total <= 0) return {} as Record<string, number>;
  const sumW = steps.reduce((s, x) => s + x.w, 0);
  const raw = steps.map((x) => ({ label: x.label, v: (total * x.w) / Math.max(1, sumW) }));
  const floored = raw.map((x) => ({ label: x.label, v: Math.floor(x.v) }));
  let rem = total - floored.reduce((s, x) => s + x.v, 0);
  const frac = raw.map((x, i) => ({ i, frac: x.v - Math.floor(x.v) })).sort((a, b) => b.frac - a.frac);
  for (let k = 0; k < floored.length && rem > 0; k++) {
    floored[frac[k].i].v += 1;
    rem -= 1;
  }
  return Object.fromEntries(floored.map((x) => [x.label, x.v])) as Record<string, number>;
};

const stepCountLabel = (taskId: string, label: string) => {
  const task = props.tasks.find((t) => t.id === taskId);
  if (!task) return "";
  const counts = stepCountsFor(task, labelsForTask(task).map((l) => ({ label: l, w: 1 })));
  return counts[label] ? ` (${counts[label]})` : "";
};

const inferSteps = (t: PlannerTask): Step[] => {
  const title = (t.title || "").toLowerCase();
  const isEssay = /(essay|paper|report|write|draft)/.test(title);
  const isExam = /(exam|quiz|midterm|final|test|mock)/.test(title);
  const isReading = /(read|chapter|book|article)/.test(title);
  const isProblem = /(hw|pset|problem|assignment|calc|algebra|math|physics|chem|bio)/.test(title);
  if (isEssay) {
    return [
      { label: "研究", w: 2 },
      { label: "大纲", w: 1 },
      { label: "草稿", w: 3 },
      { label: "修订", w: 2 },
      { label: "校对", w: 1 },
      { label: "提交", w: 1 },
    ];
  }
  if (isExam) {
    return [
      { label: "主题地图", w: 1 },
      { label: "闪卡", w: 2 },
      { label: "练习", w: 3 },
      { label: "薄弱点", w: 2 },
      { label: "模拟测试", w: 2 },
      { label: "复习", w: 1 },
    ];
  }
  if (isReading) {
    return [
      { label: "浏览", w: 1 },
      { label: "阅读", w: 3 },
      { label: "笔记", w: 2 },
      { label: "摘要", w: 1 },
      { label: "讨论/问题", w: 1 },
    ];
  }
  if (isProblem) {
    return [
      { label: "复习笔记", w: 1 },
      { label: "例题", w: 2 },
      { label: "解题集", w: 3 },
      { label: "检查/验证", w: 2 },
      { label: "写答案", w: 1 },
      { label: "提交", w: 1 },
    ];
  }
  return [
    { label: "计划", w: 1 },
    { label: "研究", w: 2 },
    { label: "制作", w: 3 },
    { label: "审核", w: 2 },
    { label: "完善", w: 1 },
    { label: "提交", w: 1 },
  ];
};

const initPositions = () => {
  if (!wrapRef.value || Object.keys(positions.value).length) return;
  const rect = wrapRef.value.getBoundingClientRect();
  const cx = rect.width / 2;
  const cy = rect.height / 2;
  const r = Math.min(cx, cy) * 0.6;
  const n = Math.max(1, props.tasks.length);
  const init: Record<string, Pt> = {};
  props.tasks.forEach((t, i) => {
    const ang = (i / n) * Math.PI * 2;
    init[t.id] = { x: cx + r * Math.cos(ang) - 120, y: cy + r * Math.sin(ang) - 40 };
  });
  positions.value = init;
};

const computeStepPos = () => {
  const out = { ...stepPos.value };
  for (const t of props.tasks) {
    const base = positions.value[t.id];
    if (!base) continue;
    const labels = labelsForTask(t);
    const n = Math.max(1, labels.length);
    const r = 120;
    const node = nodeRefs.value[t.id];
    const w = node?.offsetWidth ?? 140;
    const h = node?.offsetHeight ?? 36;
    const cx = base.x + w / 2;
    const cy = base.y + h / 2;
    labels.forEach((label, i) => {
      const key = `${t.id}::${label}`;
      if (out[key]) return;
      const ang = (i / n) * Math.PI * 2;
      out[key] = { x: cx + r * Math.cos(ang) - 42, y: cy + r * Math.sin(ang) - 14 };
    });
  }
  stepPos.value = out;
};

const buildSims = () => {
  for (const id of Object.keys(simsRef.value)) {
    try {
      simsRef.value[id].stop();
    } catch {
      return;
    }
  }
  simsRef.value = {};
  const nm: NodeMap = {};
  for (const t of props.tasks) {
    const base = positions.value[t.id];
    if (!base) continue;
    const node = nodeRefs.value[t.id];
    const w = node?.offsetWidth ?? 140;
    const h = node?.offsetHeight ?? 36;
    const cx = base.x + w / 2;
    const cy = base.y + h / 2;
    const cid = `t:${t.id}`;
    const center: MindmapNode = { id: cid, x: cx, y: cy, fx: cx, fy: cy, type: "center" };
    const nodes: MindmapNode[] = [center];
    nm[cid] = center;
    const labels = labelsForTask(t);
    for (const label of labels) {
      const sid = `${t.id}::${label}`;
      const sp = stepPos.value[sid];
      const sx = (sp?.x ?? cx + 120) + 42;
      const sy = (sp?.y ?? cy) + 14;
      const nid = `s:${sid}`;
      const sn: MindmapNode = { id: nid, x: sx, y: sy, type: "step", taskId: t.id, label };
      nodes.push(sn);
      nm[nid] = sn;
    }
    const sim = forceSimulation(nodes)
      .force("charge", forceManyBody().strength(-60))
      .force("radial", forceRadial(120, cx, cy).strength(0.09))
      .force("collide", forceCollide(36))
      .alpha(0.6)
      .alphaDecay(0.08);
    sim.on("tick", () => {
      const next: StepPos = {};
      for (const n of nodes) {
        if (n.type === "step") next[`${n.taskId}::${n.label}`] = { x: (n.x || 0) - 42, y: (n.y || 0) - 14 };
      }
      if (Object.keys(next).length) stepPos.value = { ...stepPos.value, ...next };
    });
    simsRef.value[t.id] = sim as any;
  }
  nodeMapRef.value = nm;
};

const recenterSteps = (taskId: string) => {
  const t = props.tasks.find((x) => x.id === taskId);
  if (!t) return;
  const base = positions.value[taskId];
  if (!base) return;
  const labels = labelsForTask(t);
  const n = Math.max(1, labels.length);
  const r = 120;
  const node = nodeRefs.value[taskId];
  const w = node?.offsetWidth ?? 140;
  const h = node?.offsetHeight ?? 36;
  const cx = base.x + w / 2;
  const cy = base.y + h / 2;
  const out = { ...stepPos.value };
  labels.forEach((label, i) => {
    const key = `${taskId}::${label}`;
    const ang = (i / n) * Math.PI * 2;
    out[key] = { x: cx + r * Math.cos(ang) - 42, y: cy + r * Math.sin(ang) - 14 };
  });
  stepPos.value = out;
};

const loadCustomNodes = () => {
  try {
    const raw = localStorage.getItem("planner.customNodes");
    if (raw) customNodes.value = JSON.parse(raw);
  } catch {
    return;
  }
};

const loadStepPos = () => {
  try {
    const raw = localStorage.getItem("planner.stepPos");
    if (raw) stepPos.value = JSON.parse(raw);
  } catch {
    return;
  }
};

const loadAiSteps = () => {
  try {
    const m: Record<string, string[]> = {};
    for (const t of props.tasks) {
      const raw = localStorage.getItem(`planner.aiSteps.${t.id}`);
      if (raw) m[t.id] = JSON.parse(raw);
    }
    if (Object.keys(m).length) aiSteps.value = { ...aiSteps.value, ...m };
  } catch {
    return;
  }
};

const fetchAiSteps = async () => {
  let cancelled = false;
  for (const t of props.tasks) {
    if (aiSteps.value[t.id]) continue;
    try {
      const res = await plannerMaterials(t.id, "studyGuide");
      if (cancelled) return;
      const data: any = res?.data || {};
      const labels: string[] = [];
      if (Array.isArray(data.mainConcepts)) labels.push(...data.mainConcepts);
      if (Array.isArray(data.importantTerms)) labels.push(...data.importantTerms.map((x: any) => x?.term).filter(Boolean));
      if (labels.length === 0 && Array.isArray(data.questions)) labels.push(...data.questions);
      const uniq = Array.from(new Set(labels.map((x) => String(x).trim()).filter(Boolean))).slice(0, 6);
      if (uniq.length) {
        aiSteps.value = { ...aiSteps.value, [t.id]: uniq };
        try {
          localStorage.setItem(`planner.aiSteps.${t.id}`, JSON.stringify(uniq));
        } catch {
          return;
        }
      }
    } catch {
      return;
    }
  }
  return () => {
    cancelled = true;
  };
};

const onDown = (e: PointerEvent, id: string) => {
  const rect = wrapRef.value?.getBoundingClientRect();
  const localX = rect ? e.clientX - rect.left : e.clientX;
  const localY = rect ? e.clientY - rect.top : e.clientY;
  const p = positions.value[id] || { x: 0, y: 0 };
  const screenX = pan.value.x + p.x * zoom.value;
  const screenY = pan.value.y + p.y * zoom.value;
  drag.value = { id, off: { x: localX - screenX, y: localY - screenY } };
};

const onDownCustom = (e: PointerEvent, id: string) => {
  const rect = wrapRef.value?.getBoundingClientRect();
  const localX = rect ? e.clientX - rect.left : e.clientX;
  const localY = rect ? e.clientY - rect.top : e.clientY;
  const node = customNodes.value.find((n) => n.id === id);
  if (!node) return;
  const screenX = pan.value.x + node.x * zoom.value;
  const screenY = pan.value.y + node.y * zoom.value;
  dragCustom.value = { id, off: { x: localX - screenX, y: localY - screenY } };
};

const onDownStep = (e: PointerEvent, taskId: string, label: string) => {
  const rect = wrapRef.value?.getBoundingClientRect();
  const localX = rect ? e.clientX - rect.left : e.clientX;
  const localY = rect ? e.clientY - rect.top : e.clientY;
  const sp = stepPos.value[`${taskId}::${label}`];
  if (!sp) return;
  const screenX = pan.value.x + sp.x * zoom.value;
  const screenY = pan.value.y + sp.y * zoom.value;
  dragStep.value = { id: `${taskId}::${label}`, off: { x: localX - screenX, y: localY - screenY } };
};

const onMove = (e: PointerEvent) => {
  const rect = wrapRef.value?.getBoundingClientRect();
  const localX = rect ? e.clientX - rect.left : e.clientX;
  const localY = rect ? e.clientY - rect.top : e.clientY;
  if (panning.value?.on) {
    const dx = localX - panning.value.start.x;
    const dy = localY - panning.value.start.y;
    pan.value = { x: panning.value.base.x + dx, y: panning.value.base.y + dy };
    return;
  }
  if (drag.value) {
    const screenX = localX - drag.value.off.x;
    const screenY = localY - drag.value.off.y;
    const x = (screenX - pan.value.x) / zoom.value;
    const y = (screenY - pan.value.y) / zoom.value;
    const prev = positions.value[drag.value.id] || { x, y };
    const dx = x - prev.x;
    const dy = y - prev.y;
    positions.value = { ...positions.value, [drag.value.id]: { x, y } };
    const nn = { ...stepPos.value };
    const prefix = `${drag.value.id}::`;
    for (const k of Object.keys(nn)) {
      if (k.startsWith(prefix)) nn[k] = { x: nn[k].x + dx, y: nn[k].y + dy };
    }
    stepPos.value = nn;
    const cnode = nodeMapRef.value[`t:${drag.value.id}`];
    const refNode = nodeRefs.value[drag.value.id];
    const w = refNode?.offsetWidth ?? 140;
    const h = refNode?.offsetHeight ?? 36;
    if (cnode) {
      const cx = x + w / 2;
      const cy = y + h / 2;
      cnode.fx = cx;
      cnode.fy = cy;
      const sim = simsRef.value[drag.value.id];
      if (sim) {
        sim.force("radial", forceRadial(120, cx, cy).strength(0.09));
        sim.alphaTarget(0.7).restart();
      }
    }
    return;
  }
  if (dragStep.value) {
    const screenX = localX - dragStep.value.off.x;
    const screenY = localY - dragStep.value.off.y;
    const x = (screenX - pan.value.x) / zoom.value;
    const y = (screenY - pan.value.y) / zoom.value;
    stepPos.value = { ...stepPos.value, [dragStep.value.id]: { x, y } };
    const snode = nodeMapRef.value[`s:${dragStep.value.id}`];
    const tid = dragStep.value.id.split("::")[0];
    if (snode) {
      snode.fx = x + 42;
      snode.fy = y + 14;
      const sim = simsRef.value[tid];
      sim?.alphaTarget(0.7).restart();
    }
    return;
  }
  if (dragCustom.value) {
    const screenX = localX - dragCustom.value.off.x;
    const screenY = localY - dragCustom.value.off.y;
    const x = (screenX - pan.value.x) / zoom.value;
    const y = (screenY - pan.value.y) / zoom.value;
    customNodes.value = customNodes.value.map((n) => (n.id === dragCustom.value?.id ? { ...n, x, y } : n));
  }
};

const onUp = () => {
  drag.value = null;
  if (dragStep.value) {
    const snode = nodeMapRef.value[`s:${dragStep.value.id}`];
    const tid = dragStep.value.id.split("::")[0];
    if (snode) {
      snode.fx = null;
      snode.fy = null;
      const sim = simsRef.value[tid];
      sim?.alphaTarget(0);
    }
    dragStep.value = null;
  }
  dragCustom.value = null;
  panning.value = null;
};

const onWheel = (e: WheelEvent) => {
  const rect = wrapRef.value?.getBoundingClientRect();
  const localX = rect ? e.clientX - rect.left : e.clientX;
  const localY = rect ? e.clientY - rect.top : e.clientY;
  const delta = -e.deltaY;
  const step = delta > 0 ? 0.1 : -0.1;
  const newZoom = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, zoom.value + step));
  if (newZoom === zoom.value) return;
  const worldX = (localX - pan.value.x) / zoom.value;
  const worldY = (localY - pan.value.y) / zoom.value;
  pan.value = { x: localX - worldX * newZoom, y: localY - worldY * newZoom };
  zoom.value = newZoom;
};

const panning = ref<{ on: boolean; start: Pt; base: Pt } | null>(null);

const startPan = (e: PointerEvent) => {
  const target = e.target as HTMLElement;
  if (target.closest("[data-node]")) return;
  const rect = wrapRef.value?.getBoundingClientRect();
  const localX = rect ? e.clientX - rect.left : e.clientX;
  const localY = rect ? e.clientY - rect.top : e.clientY;
  panning.value = { on: true, start: { x: localX, y: localY }, base: { ...pan.value } };
};

const focusNode = (id: string) => {
  const rect = wrapRef.value?.getBoundingClientRect();
  const cx = rect ? rect.width / 2 : 0;
  const cy = rect ? rect.height / 2 : 0;
  const node = nodeRefs.value[id];
  const w = node?.offsetWidth ?? 140;
  const h = node?.offsetHeight ?? 36;
  const worldX = positions.value[id].x + w / 2;
  const worldY = positions.value[id].y + h / 2;
  const newZoom = Math.min(MAX_ZOOM, Math.max(zoom.value, 1.5));
  pan.value = { x: cx - worldX * newZoom, y: cy - worldY * newZoom };
  zoom.value = newZoom;
};

const toggleMenu = (id: string) => {
  menuOpen.value = menuOpen.value === id ? null : id;
};

const startTaskNow = (id: string) => {
  menuOpen.value = null;
  props.onUpdateStatus(id, "doing");
  props.onPlan(id);
  props.onStartNow?.(id);
};

const handlePlan = (id: string) => {
  menuOpen.value = null;
  props.onPlan(id);
};

const handleAssist = (id: string, kind: "summary" | "flashcards" | "studyGuide" | "quiz") => {
  menuOpen.value = null;
  props.onAssist(id, kind);
};

const handleDelete = (id: string) => {
  menuOpen.value = null;
  props.onDelete(id);
};

const onUploadFile = (id: string, e: Event) => {
  const file = (e.target as HTMLInputElement).files?.[0];
  if (file) props.onUpload(id, file);
  menuOpen.value = null;
};

const addNote = (id: string) => {
  const val = window.prompt("添加笔记");
  if (val != null) props.onUpdateNotes?.(id, val);
  menuOpen.value = null;
};

const removeStep = (taskId: string, label: string) => {
  const task = props.tasks.find((t) => t.id === taskId);
  if (!task) return;
  const baseLabels = aiSteps.value[taskId] && aiSteps.value[taskId].length ? aiSteps.value[taskId] : labelsForTask(task);
  aiSteps.value = { ...aiSteps.value, [taskId]: baseLabels.filter((l) => l !== label) };
  try {
    localStorage.setItem(`planner.aiSteps.${taskId}`, JSON.stringify(aiSteps.value[taskId]));
  } catch {
    return;
  }
  const next = { ...stepPos.value };
  delete next[`${taskId}::${label}`];
  stepPos.value = next;
};

const stepBubbleStyle = (taskId: string, label: string) => {
  const sp = stepPos.value[`${taskId}::${label}`];
  const p = positions.value[taskId];
  if (!sp || !p) return {};
  return {
    left: `${sp.x - p.x}px`,
    top: `${sp.y - p.y}px`,
    width: "84px",
    height: "28px",
    lineHeight: "28px",
    fontSize: "11px",
  };
};

const lineForStep = (t: PlannerTask, label: string) => {
  const p = positions.value[t.id];
  if (!p) return null;
  const node = nodeRefs.value[t.id];
  const w = Math.max(1, node?.offsetWidth ?? 140);
  const h = Math.max(1, node?.offsetHeight ?? 36);
  const cxWorld = p.x + w / 2;
  const cyWorld = p.y + h / 2;
  const rxC = w / 2;
  const ryC = h / 2;
  const sp = stepPos.value[`${t.id}::${label}`];
  if (!sp) return null;
  const sxWorld = sp.x + 42;
  const syWorld = sp.y + 14;
  const { ax: axWorld, ay: ayWorld, bx: bxWorld, by: byWorld } = anchorLine(cxWorld, cyWorld, rxC, ryC, sxWorld, syWorld);
  return {
    x1: pan.value.x + axWorld * zoom.value,
    y1: pan.value.y + ayWorld * zoom.value,
    x2: pan.value.x + bxWorld * zoom.value,
    y2: pan.value.y + byWorld * zoom.value,
  };
};

const customEdges = computed<Edge[]>(() => {
  const edges = new Map<string, Edge>();
  for (const a of customNodes.value) {
    const neigh = customNodes.value
      .filter((n) => n.id !== a.id)
      .map((n) => ({ n, d: (n.x - a.x) ** 2 + (n.y - a.y) ** 2 }))
      .sort((x, y) => x.d - y.d)
      .slice(0, 2);
    for (const { n: b } of neigh) {
      const key = a.id < b.id ? `${a.id}|${b.id}` : `${b.id}|${a.id}`;
      if (!edges.has(key)) {
        edges.set(key, {
          ax: pan.value.x + a.x * zoom.value,
          ay: pan.value.y + a.y * zoom.value,
          bx: pan.value.x + b.x * zoom.value,
          by: pan.value.y + b.y * zoom.value,
        });
      }
    }
  }
  return Array.from(edges.values());
});

const addBubble = () => {
  const rect = wrapRef.value?.getBoundingClientRect();
  const cx = rect ? rect.width / 2 : 300;
  const cy = rect ? rect.height / 2 : 200;
  const worldX = (cx - pan.value.x) / zoom.value;
  const worldY = (cy - pan.value.y) / zoom.value;
  const colors = ["#22d3ee", "#a78bfa", "#4ade80", "#f472b6", "#f59e0b"];
  const color = colors[Math.floor(Math.random() * colors.length)];
  const id = Math.random().toString(36).slice(2, 9);
  customNodes.value = [...customNodes.value, { id, x: worldX, y: worldY, label: "想法", color }];
  editingId.value = id;
  editingLabel.value = "想法";
};

const editCustomLabel = (n: CustomNode) => {
  editingId.value = n.id;
  editingLabel.value = n.label;
};

const saveCustomLabel = (id: string) => {
  customNodes.value = customNodes.value.map((n) => (n.id === id ? { ...n, label: editingLabel.value || n.label } : n));
  editingId.value = null;
  editingLabel.value = "";
};

const removeCustomNode = (id: string) => {
  customNodes.value = customNodes.value.filter((n) => n.id !== id);
};

const zoomOut = () => {
  const rect = wrapRef.value?.getBoundingClientRect();
  const cx = rect ? rect.width / 2 : 0;
  const cy = rect ? rect.height / 2 : 0;
  const newZoom = Math.max(MIN_ZOOM, zoom.value - 0.1);
  const worldX = (cx - pan.value.x) / zoom.value;
  const worldY = (cy - pan.value.y) / zoom.value;
  pan.value = { x: cx - worldX * newZoom, y: cy - worldY * newZoom };
  zoom.value = newZoom;
};

const zoomIn = () => {
  const rect = wrapRef.value?.getBoundingClientRect();
  const cx = rect ? rect.width / 2 : 0;
  const cy = rect ? rect.height / 2 : 0;
  const newZoom = Math.min(MAX_ZOOM, zoom.value + 0.1);
  const worldX = (cx - pan.value.x) / zoom.value;
  const worldY = (cy - pan.value.y) / zoom.value;
  pan.value = { x: cx - worldX * newZoom, y: cy - worldY * newZoom };
  zoom.value = newZoom;
};

const resetView = () => {
  pan.value = { x: 0, y: 0 };
  zoom.value = 1.25;
};

watch(
  () => props.tasks.length,
  () => {
    initPositions();
    loadAiSteps();
    nextTick().then(() => {
      computeStepPos();
      buildSims();
    });
  },
  { immediate: true }
);

watch(
  () => [props.tasks, positions.value, aiSteps.value],
  () => {
    nextTick().then(() => {
      computeStepPos();
      buildSims();
    });
  },
  { deep: true }
);

watch(
  () => stepPos.value,
  () => {
    try {
      localStorage.setItem("planner.stepPos", JSON.stringify(stepPos.value));
    } catch {
      return;
    }
  },
  { deep: true }
);

watch(
  () => customNodes.value,
  () => {
    try {
      localStorage.setItem("planner.customNodes", JSON.stringify(customNodes.value));
    } catch {
      return;
    }
  },
  { deep: true }
);

onMounted(async () => {
  initPositions();
  loadCustomNodes();
  loadStepPos();
  loadAiSteps();
  await fetchAiSteps();
  computeStepPos();
  buildSims();
});

onBeforeUnmount(() => {
  for (const id of Object.keys(simsRef.value)) {
    try {
      simsRef.value[id].stop();
    } catch {
      return;
    }
  }
});
</script>

<style scoped>
@keyframes twinkle { 0%, 100% { opacity: 0.2 } 50% { opacity: 1 } }
.tw { animation: twinkle 3.0s ease-in-out infinite; }
.tw2 { animation: twinkle 3.8s ease-in-out infinite; }
.tw3 { animation: twinkle 4.6s ease-in-out infinite; }
</style>
