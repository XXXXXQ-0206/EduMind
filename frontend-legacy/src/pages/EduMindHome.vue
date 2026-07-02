<template>
  <div
    ref="homeRootRef"
    class="edumind-home min-h-screen relative overflow-hidden"
    :class="{ 'home-dark': themeStore.mode === 'dark' }"
    :style="parallaxVars"
    @mousemove="onParallaxMove"
    @mouseleave="onParallaxLeave"
  >
    <div class="bg-neuron-layer" aria-hidden="true">
      <canvas ref="neuronCanvasRef" class="neuron-canvas"></canvas>
      <div class="parallax-elements">
        <div class="parallax-lane lane-left">
          <div
            v-for="item in leftParallaxItems"
            :key="item.id"
            class="p-el"
            :class="`p-${item.kind}`"
            :style="{
              left: item.x,
              top: item.top,
              '--dx': String(item.dx),
              '--dy': String(item.dy),
              '--s': `${item.size}px`,
              '--delay': `${item.delay}s`,
              '--dur': `${item.duration}s`,
            }"
          >
            <span v-if="item.kind === 'code'" class="p-symbol">&lt;/&gt;</span>
            <span v-else-if="item.kind === 'book'" class="p-symbol">[ ]</span>
            <span v-else-if="item.kind === 'pen'" class="p-symbol">∥</span>
          </div>
        </div>

        <div class="parallax-lane lane-right">
          <div
            v-for="item in rightParallaxItems"
            :key="item.id"
            class="p-el"
            :class="`p-${item.kind}`"
            :style="{
              left: item.x,
              top: item.top,
              '--dx': String(item.dx),
              '--dy': String(item.dy),
              '--s': `${item.size}px`,
              '--delay': `${item.delay}s`,
              '--dur': `${item.duration}s`,
            }"
          >
            <span v-if="item.kind === 'code'" class="p-symbol">&lt;/&gt;</span>
            <span v-else-if="item.kind === 'book'" class="p-symbol">[ ]</span>
            <span v-else-if="item.kind === 'pen'" class="p-symbol">∥</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Ambient glows -->
    <div
      class="home-glow home-glow-blue absolute top-0 left-0 w-[50%] h-[70%] blur-3xl pointer-events-none"
    ></div>
    <div
      class="home-glow home-glow-cyan absolute top-0 right-0 w-[50%] h-[70%] blur-3xl pointer-events-none"
    ></div>

    <!-- Top nav -->
    <nav
      class="home-nav fixed top-0 left-0 right-0 z-50 py-4 px-4 backdrop-blur-xl border-b"
    >
      <div class="max-w-6xl mx-auto grid items-center gap-3 lg:grid-cols-[auto_1fr_auto]">
        <div class="flex items-center justify-center gap-2 lg:justify-self-start">
          <img
            :src="logoImg"
            alt="EduMind"
            class="w-10 h-10 rounded-xl object-contain flex-shrink-0"
          />
          <span class="home-brand text-xl font-bold tracking-tight">EduMind</span>
        </div>

        <div class="order-3 flex justify-center lg:order-none lg:justify-self-center">
          <template v-if="isAuthenticated">
            <button
              type="button"
              class="home-account-trigger"
              aria-label="打开账户设置"
              @click="showSettings = true"
            >
              <span class="home-account-trigger-avatar">
                {{ usernameInitial }}
              </span>
              <div class="min-w-0 text-left leading-tight">
                <div class="home-account-kicker text-[11px] font-semibold uppercase tracking-[0.16em]">当前账户</div>
                <div class="home-account-name max-w-[10rem] truncate text-sm font-semibold mt-0.5">{{ authStore.username }}</div>
              </div>
              <span class="home-account-trigger-tag">
                <svg viewBox="0 0 24 24" class="size-3.5" fill="none" stroke="currentColor" stroke-width="1.8">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317a1.724 1.724 0 0 1 3.35 0 1.724 1.724 0 0 0 2.573 1.066 1.724 1.724 0 0 1 2.302.989 1.724 1.724 0 0 0 2.02 1.442 1.724 1.724 0 0 1 1.441 2.02 1.724 1.724 0 0 0 .99 2.302 1.724 1.724 0 0 1 0 3.35 1.724 1.724 0 0 0-.99 2.573 1.724 1.724 0 0 1-.989 2.302 1.724 1.724 0 0 0-1.442 2.02 1.724 1.724 0 0 1-2.02 1.441 1.724 1.724 0 0 0-2.302.99 1.724 1.724 0 0 1-3.35 0 1.724 1.724 0 0 0-2.573-1.066 1.724 1.724 0 0 1-2.302-.989 1.724 1.724 0 0 0-2.02-1.442 1.724 1.724 0 0 1-1.441-2.02 1.724 1.724 0 0 0-.99-2.302 1.724 1.724 0 0 1 0-3.35 1.724 1.724 0 0 0 .99-2.573 1.724 1.724 0 0 1 .989-2.302 1.724 1.724 0 0 0 1.442-2.02 1.724 1.724 0 0 1 2.02-1.441 1.724 1.724 0 0 0 2.302-.99Z" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 15.75A3.75 3.75 0 1 0 12 8.25a3.75 3.75 0 0 0 0 7.5Z" />
                </svg>
                设置
              </span>
            </button>
          </template>
        </div>

        <div class="order-2 flex items-center justify-center gap-2 flex-wrap sm:flex-nowrap lg:order-none lg:justify-self-end">
          <template v-if="isAuthenticated">
            <button type="button" class="home-auth-btn home-auth-btn-secondary" @click="enterRole('teacher')">教师端</button>
            <button type="button" class="home-auth-btn home-auth-btn-secondary" @click="enterRole('student')">学生端</button>
            <button type="button" class="home-auth-btn home-auth-btn-primary" @click="logout">退出</button>
          </template>

          <template v-else>
            <button type="button" class="home-auth-btn home-auth-btn-secondary" @click="openAuth('teacher', 'login')">教师登录/注册</button>
            <button type="button" class="home-auth-btn home-auth-btn-primary" @click="openAuth('student', 'register')">学生登录/注册</button>
          </template>
        </div>
      </div>
    </nav>

    <!-- Hero: Split-screen -->
    <section class="relative z-10 pt-24 pb-16 px-4 md:px-8">
      <div class="max-w-6xl mx-auto">
        <div class="text-center mb-12">
          <h1
            class="hero-title text-3xl md:text-4xl lg:text-5xl font-bold mb-4 leading-tight"
          >
            EduMind：链接教学灵感，刻画学习深度
          </h1>
          <p class="hero-subtitle text-lg md:text-xl max-w-[72rem] mx-auto leading-relaxed">
            <span class="subtitle-main-art md:whitespace-nowrap">基于多模态 AI，将静态教材转化为交互资源，一键生成教案、视频与播客，构建师生协同教育生态。</span>
          </p>
        </div>

        <!-- Split cards -->
        <div class="grid md:grid-cols-2 gap-6 md:gap-8 max-w-5xl mx-auto">
          <!-- Teacher side -->
          <RouterLink
            :to="teacherEntryRoute"
            class="home-card teacher-card group block rounded-3xl p-8 md:p-10 border backdrop-blur-md transition-all duration-300 cursor-pointer"
          >
            <div class="card-shine" aria-hidden="true"></div>
            <div class="flex items-center gap-3 mb-6">
              <div
                class="entry-icon-wrap entry-icon-wrap-teacher w-12 h-12 rounded-xl flex items-center justify-center transition-colors relative overflow-hidden"
              >
                <svg
                  viewBox="0 0 24 24"
                  class="w-6 h-6 entry-icon entry-icon-teacher"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.9"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path d="M12 4 3 8.2 12 12.4 21 8.2 12 4Z" />
                  <path d="M7.2 11.8v2.8c0 1.7 2.15 3.1 4.8 3.1s4.8-1.4 4.8-3.1v-2.8" />
                  <path d="M21 10v4.9" />
                  <circle cx="21" cy="16.8" r="1.1" />
                </svg>
              </div>
              <span class="entry-badge teacher-badge badge-breathe-blue">教师端</span>
            </div>
            <h2 class="home-card-title text-2xl font-bold mb-2">智教 · 让备课更从容</h2>
            <p class="home-card-copy text-sm leading-relaxed mb-4">
              覆盖教案生成、课件设计、微课视频与智能组卷，支持一键产出、快速复用与教学复盘。
            </p>
            <span
              class="home-card-link home-card-link-teacher inline-flex items-center gap-2 font-medium text-sm group-hover:gap-3 transition-all"
            >
              查看功能详情
              <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </span>
          </RouterLink>

          <!-- Student side -->
          <RouterLink
            :to="studentEntryRoute"
            class="home-card student-card group block rounded-3xl p-8 md:p-10 border backdrop-blur-md transition-all duration-300 cursor-pointer"
          >
            <div class="card-shine" aria-hidden="true"></div>
            <div class="flex items-center gap-3 mb-6">
              <div
                class="entry-icon-wrap entry-icon-wrap-student w-12 h-12 rounded-xl flex items-center justify-center transition-colors relative overflow-hidden"
              >
                <svg
                  viewBox="0 0 24 24"
                  class="w-6 h-6 entry-icon entry-icon-student"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.9"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path d="M4 5.6h5.3c1.5 0 2.7 1.2 2.7 2.7V19c-.6-.85-1.7-1.35-2.9-1.35H4z" />
                  <path d="M20 5.6h-5.3c-1.5 0-2.7 1.2-2.7 2.7V19c.6-.85 1.7-1.35 2.9-1.35H20z" />
                  <path d="M9.25 8.4h1.5v2.05l-.75-.45-.75.45Z" />
                  <path d="M15.1 8.9h2" />
                  <path d="M16.1 7.9v2" />
                </svg>
              </div>
              <span class="entry-badge student-badge badge-breathe-green">学生端</span>
            </div>
            <h2 class="home-card-title text-2xl font-bold mb-2">智学 · 让学习更从容</h2>
            <p class="home-card-copy text-sm leading-relaxed mb-4">
              覆盖智能笔记、AI 播客、闪卡复习与错题归纳，支持多场景学习与薄弱点精准强化。
            </p>
            <span
              class="home-card-link home-card-link-student inline-flex items-center gap-2 font-medium text-sm group-hover:gap-3 transition-all"
            >
              查看功能详情
              <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </span>
          </RouterLink>
        </div>

        <!-- CTA buttons -->
        <div class="flex flex-col sm:flex-row items-center justify-center gap-4 mt-10">
          <button
            type="button"
            class="entry-btn teacher-entry-btn group relative overflow-hidden px-8 py-4 rounded-2xl font-semibold text-white transition-all duration-200 min-w-[180px] text-center cursor-pointer"
            @click="goToTeacherChat"
          >
            <span class="entry-btn-scan" aria-hidden="true"></span>
            <span class="entry-btn-text">教师端入口</span>
          </button>
          <button
            type="button"
            class="entry-btn student-entry-btn group relative overflow-hidden px-8 py-4 rounded-2xl font-semibold text-white transition-all duration-200 min-w-[180px] text-center cursor-pointer"
            @click="goToStudentChat"
          >
            <span class="entry-btn-scan" aria-hidden="true"></span>
            <span class="entry-btn-text">学生端入口</span>
          </button>
        </div>

        <section class="max-w-5xl mx-auto mt-10">
          <div class="info-nav-shell rounded-2xl backdrop-blur-md border">
            <div class="info-nav-row" role="tablist" aria-label="项目信息导航">
              <button
                v-for="(card, i) in infoCards"
                :key="card.title"
                type="button"
                class="info-nav-btn"
                :class="{ active: activeInfoIndex === i }"
                :aria-selected="activeInfoIndex === i"
                role="tab"
                @click="toggleInfoNav(i)"
              >
                <span class="info-title-chip">{{ card.title }}</span>
              </button>
            </div>
          </div>

          <article v-if="activeInfoCard" class="info-panel rounded-2xl backdrop-blur-md border mt-4">
            <div class="info-panel-inner">
              <h3 class="info-panel-title">{{ activeInfoCard?.title }}</h3>
              <p class="info-text">{{ activeInfoCard?.content }}</p>

              <div v-if="activeInfoCard?.title === '项目团队'" class="team-extra">
                <p class="team-line"><strong>成员：</strong>重庆大学本科生 20231312 叶博豪</p>
                <p class="team-line"><strong>邮箱：</strong>2453221645@qq.com</p>
                <a
                  href="https://github.com/XXXXXQ-0206"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="team-github"
                >
                  <svg viewBox="0 0 24 24" class="w-4 h-4" fill="currentColor" aria-hidden="true">
                    <path d="M12 .5a12 12 0 0 0-3.79 23.39c.6.11.82-.26.82-.58v-2.24c-3.34.73-4.04-1.42-4.04-1.42a3.18 3.18 0 0 0-1.33-1.76c-1.08-.74.08-.72.08-.72a2.5 2.5 0 0 1 1.82 1.23 2.53 2.53 0 0 0 3.46 1 2.54 2.54 0 0 1 .76-1.59c-2.67-.3-5.48-1.34-5.48-5.97a4.67 4.67 0 0 1 1.24-3.24 4.33 4.33 0 0 1 .12-3.2s1.01-.33 3.31 1.23a11.39 11.39 0 0 1 6.02 0c2.3-1.56 3.3-1.23 3.3-1.23a4.32 4.32 0 0 1 .12 3.2 4.66 4.66 0 0 1 1.24 3.24c0 4.64-2.81 5.66-5.49 5.96a2.84 2.84 0 0 1 .81 2.2v3.25c0 .32.22.7.83.58A12 12 0 0 0 12 .5Z" />
                  </svg>
                  GitHub：github.com/XXXXXQ-0206
                </a>
              </div>
            </div>
          </article>
        </section>
      </div>
    </section>

    <AccountSettingsModal
      :open="showSettings"
      :username="authStore.username || '当前账户'"
      @close="showSettings = false"
      @session-ended="handleSessionEnded"
    />
  </div>
</template>

<script setup lang="ts">
import { RouterLink, useRouter } from "vue-router";
import { computed, onMounted, onUnmounted, ref } from "vue";
import logoImg from "@logo/logo.png";
import AccountSettingsModal from "../components/AccountSettingsModal.vue";
import { useAuthStore } from "../stores/auth";
import { useRoleStore } from "../stores/role";
import { useThemeStore } from "../stores/theme";

const router = useRouter();
const authStore = useAuthStore();
const roleStore = useRoleStore();
const themeStore = useThemeStore();
const isAuthenticated = computed(() => authStore.isAuthenticated);
const usernameInitial = computed(() => authStore.username.slice(0, 1).toUpperCase() || "U");
const showSettings = ref(false);

const entryRoute = (role: "teacher" | "student") =>
  authStore.isAuthenticated
    ? role === "teacher" ? "/intro/teacher" : "/intro/student"
    : { path: "/auth", query: { role, redirect: role === "teacher" ? "/intro/teacher" : "/intro/student" } };

const teacherEntryRoute = computed(() => entryRoute("teacher"));
const studentEntryRoute = computed(() => entryRoute("student"));

function goToTeacherChat() {
  enterRole("teacher");
}

function goToStudentChat() {
  enterRole("student");
}

function openAuth(role: "teacher" | "student", mode: "login" | "register") {
  router.push({
    path: "/auth",
    query: {
      role,
      mode,
      redirect: role === "teacher" ? "/intro/teacher" : "/intro/student",
    },
  });
}

function enterRole(role: "teacher" | "student") {
  roleStore.setRole(role);
  router.push(entryRoute(role));
}

async function logout() {
  showSettings.value = false;
  await authStore.logout();
  router.push("/");
}

async function handleSessionEnded(reason: "password-changed" | "account-deleted") {
  showSettings.value = false;
  await router.push({
    path: "/auth",
    query: {
      role: roleStore.role,
      reason,
    },
  });
}

type Particle = {
  x: number;
  y: number;
  vx: number;
  vy: number;
  r: number;
};

type ParallaxItem = {
  id: string;
  lane: "left" | "right";
  kind: "cube" | "book" | "sphere" | "pen" | "code";
  x: string;
  top: string;
  dx: number;
  dy: number;
  size: number;
  delay: number;
  duration: number;
};

const homeRootRef = ref<HTMLElement | null>(null);
const neuronCanvasRef = ref<HTMLCanvasElement | null>(null);
const pointerX = ref(0);
const pointerY = ref(0);
const reduceMotion = ref(false);

let rafId = 0;
let particles: Particle[] = [];
let resizeHandler: (() => void) | null = null;

const parallaxItems: readonly ParallaxItem[] = [
  { id: "cube-a", lane: "left", kind: "cube", x: "18%", top: "16%", dx: 14, dy: 11, size: 58, delay: 0.1, duration: 8.4 },
  { id: "book-a", lane: "left", kind: "book", x: "52%", top: "56%", dx: 11, dy: -9, size: 52, delay: 0.2, duration: 7.8 },
  { id: "sphere-b", lane: "left", kind: "sphere", x: "22%", top: "76%", dx: 8, dy: -7, size: 40, delay: 0.35, duration: 7.2 },
  { id: "pen-a", lane: "left", kind: "pen", x: "64%", top: "30%", dx: 9, dy: -8, size: 46, delay: 0.5, duration: 8.6 },
  { id: "sphere-a", lane: "right", kind: "sphere", x: "64%", top: "14%", dx: -13, dy: 10, size: 52, delay: 0.4, duration: 9.2 },
  { id: "code-a", lane: "right", kind: "code", x: "24%", top: "64%", dx: -10, dy: -8, size: 54, delay: 0.6, duration: 8.8 },
  { id: "cube-b", lane: "right", kind: "cube", x: "58%", top: "78%", dx: -8, dy: -7, size: 46, delay: 0.75, duration: 9.4 },
];

const leftParallaxItems = computed(() => parallaxItems.filter((item) => item.lane === "left"));
const rightParallaxItems = computed(() => parallaxItems.filter((item) => item.lane === "right"));

const parallaxVars = computed(() => ({
  "--mx": String(pointerX.value),
  "--my": String(pointerY.value),
}));

const activeInfoIndex = ref<number | null>(0);

const infoCards = [
  {
    title: "项目介绍",
    content: "EduMind（智教）定位为师生协同的 AI 全场景教育生态平台，围绕“备课—授课—学习—复盘”构建完整业务链路。教师端覆盖教案、课件、微课视频、测验与试卷生成，学生端支持智能笔记、播客复习、闪卡巩固、错题追踪与学习记录沉淀；平台通过多模态资源解析与智能生成能力，把静态教材转化为可交互、可复用、可持续优化的教学与学习资源，服务课堂效率提升与学习成效提升双目标。",
  },
  {
    title: "项目立意",
    content: "项目聚焦‘减负增效与教育公平’：教师侧减少重复备课与资源整理成本，学生侧提升复习效率与知识内化质量；同时关注学习资源相对匮乏区域，希望通过 AI 生成式能力提供更可及、更均衡的优质学习支持。",
  },
  {
    title: "项目技术",
    content: "前端采用 Vue 3、TypeScript、Vite 与 TailwindCSS 构建页面交互；后端采用 Python FastAPI，并结合 LangChain、LangGraph 进行 AI 流程编排。通过多模态内容处理与检索增强，实现从教材解析、内容生成到教学落地的一体化链路。",
  },
  {
    title: "项目团队",
    content: "项目由重庆大学本科生团队推进，围绕真实教学场景持续迭代，聚焦产品可用性、教学效率与学习成效的协同提升。",
  },
] as const;

const activeInfoCard = computed(() => {
  if (activeInfoIndex.value === null) return null;
  return infoCards[activeInfoIndex.value];
});

function toggleInfoNav(index: number) {
  activeInfoIndex.value = activeInfoIndex.value === index ? null : index;
}

function onParallaxMove(event: MouseEvent) {
  if (reduceMotion.value) return;
  const el = homeRootRef.value;
  if (!el) return;
  const rect = el.getBoundingClientRect();
  const x = (event.clientX - rect.left) / rect.width;
  const y = (event.clientY - rect.top) / rect.height;
  pointerX.value = (x - 0.5) * 2;
  pointerY.value = (y - 0.5) * 2;
}

function onParallaxLeave() {
  pointerX.value = 0;
  pointerY.value = 0;
}

function resizeCanvas() {
  const canvas = neuronCanvasRef.value;
  if (!canvas) return;
  const parent = canvas.parentElement;
  if (!parent) return;
  const ratio = window.devicePixelRatio || 1;
  canvas.width = Math.floor(parent.clientWidth * ratio);
  canvas.height = Math.floor(parent.clientHeight * ratio);
  canvas.style.width = `${parent.clientWidth}px`;
  canvas.style.height = `${parent.clientHeight}px`;
}

function initParticles() {
  const canvas = neuronCanvasRef.value;
  if (!canvas) return;
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  const count = Math.min(70, Math.max(36, Math.floor((width * height) / 42000)));
  particles = Array.from({ length: count }, () => ({
    x: Math.random() * width,
    y: Math.random() * height,
    vx: (Math.random() - 0.5) * 0.45,
    vy: (Math.random() - 0.5) * 0.45,
    r: Math.random() * 1.5 + 1.1,
  }));
}

function drawParticleNetwork() {
  const canvas = neuronCanvasRef.value;
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const ratio = window.devicePixelRatio || 1;
  ctx.save();
  ctx.scale(ratio, ratio);

  const linkDistance = 140;
  const isDarkTheme = document.documentElement.classList.contains("theme-dark");
  const linkColor = isDarkTheme ? "125, 211, 252" : "56, 189, 248";
  const dotColor = isDarkTheme ? "125, 211, 252" : "14, 165, 233";
  for (let i = 0; i < particles.length; i++) {
    const particleA = particles[i];
    if (!reduceMotion.value) {
      particleA.x += particleA.vx;
      particleA.y += particleA.vy;
      if (particleA.x < 0 || particleA.x > width) particleA.vx *= -1;
      if (particleA.y < 0 || particleA.y > height) particleA.vy *= -1;
      particleA.x = Math.max(0, Math.min(width, particleA.x));
      particleA.y = Math.max(0, Math.min(height, particleA.y));
    }

    for (let j = i + 1; j < particles.length; j++) {
      const particleB = particles[j];
      const dx = particleA.x - particleB.x;
      const dy = particleA.y - particleB.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < linkDistance) {
        const alpha = (1 - dist / linkDistance) * (isDarkTheme ? 0.22 : 0.28);
        ctx.strokeStyle = `rgba(${linkColor}, ${alpha.toFixed(3)})`;
        ctx.lineWidth = 0.8;
        ctx.beginPath();
        ctx.moveTo(particleA.x, particleA.y);
        ctx.lineTo(particleB.x, particleB.y);
        ctx.stroke();
      }
    }
  }

  for (const particle of particles) {
    ctx.fillStyle = `rgba(${dotColor}, ${isDarkTheme ? "0.46" : "0.52"})`;
    ctx.beginPath();
    ctx.arc(particle.x, particle.y, particle.r, 0, Math.PI * 2);
    ctx.fill();
  }

  ctx.restore();
  if (!reduceMotion.value) {
    rafId = requestAnimationFrame(drawParticleNetwork);
  }
}

onMounted(() => {
  authStore.hydrate();
  reduceMotion.value = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  resizeCanvas();
  initParticles();
  drawParticleNetwork();

  resizeHandler = () => {
    resizeCanvas();
    initParticles();
    if (reduceMotion.value) drawParticleNetwork();
  };
  window.addEventListener("resize", resizeHandler);
});

onUnmounted(() => {
  if (rafId) cancelAnimationFrame(rafId);
  if (resizeHandler) window.removeEventListener("resize", resizeHandler);
});
</script>

<style scoped>
.edumind-home {
  background:
    radial-gradient(circle at 14% 8%, rgba(56, 189, 248, 0.16), transparent 34%),
    radial-gradient(circle at 86% 12%, rgba(16, 185, 129, 0.12), transparent 32%),
    linear-gradient(180deg, #f8fbff 0%, #eef8ff 48%, #f4fff9 100%);
  color: #0f172a;
  transition: background 220ms ease, color 220ms ease;
}

.edumind-home.home-dark {
  background:
    radial-gradient(circle at 14% 8%, rgba(14, 165, 233, 0.22), transparent 34%),
    radial-gradient(circle at 86% 12%, rgba(16, 185, 129, 0.14), transparent 32%),
    radial-gradient(circle at 50% 100%, rgba(99, 102, 241, 0.11), transparent 42%),
    linear-gradient(180deg, #07111f 0%, #0b1728 48%, #08131f 100%);
  color: #e5f2ff;
}

.home-glow-blue {
  background: linear-gradient(to bottom right, rgba(29, 78, 216, 0.1), transparent);
}

.home-glow-cyan {
  background: linear-gradient(to bottom left, rgba(8, 145, 178, 0.1), transparent);
}

.home-dark .home-glow-blue {
  background: linear-gradient(to bottom right, rgba(37, 99, 235, 0.28), transparent);
}

.home-dark .home-glow-cyan {
  background: linear-gradient(to bottom left, rgba(34, 211, 238, 0.2), transparent);
}

.bg-neuron-layer {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}

.neuron-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  opacity: 0.72;
}

.home-dark .neuron-canvas {
  opacity: 0.5;
}

.home-nav {
  background: rgba(255, 255, 255, 0.72);
  border-color: rgba(226, 232, 240, 0.5);
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
}

.home-dark .home-nav {
  background: rgba(7, 17, 31, 0.78);
  border-color: rgba(56, 189, 248, 0.18);
  box-shadow: 0 14px 34px rgba(0, 0, 0, 0.26);
}

.home-brand,
.home-account-name {
  color: #0f172a;
}

.home-account-kicker {
  color: #94a3b8;
}

.home-dark .home-brand,
.home-dark .home-account-name {
  color: #eff6ff;
}

.home-dark .home-account-kicker {
  color: #7dd3fc;
}

.parallax-elements {
  position: absolute;
  inset: 0;
}

.home-auth-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 42px;
  border-radius: 9999px;
  padding: 0.7rem 1rem;
  line-height: 1;
  font-size: 0.875rem;
  font-weight: 700;
  transition: transform 180ms ease, box-shadow 180ms ease, background-color 180ms ease, color 180ms ease, border-color 180ms ease;
  cursor: pointer;
}

.home-auth-btn:hover {
  transform: translateY(-1px);
}

.home-auth-btn:focus-visible {
  outline: 3px solid rgba(14, 165, 233, 0.22);
  outline-offset: 2px;
}

.home-auth-btn-primary {
  border: 1px solid rgba(14, 165, 233, 0.18);
  background: linear-gradient(135deg, #0f172a 0%, #0369a1 100%);
  color: #fff;
  box-shadow: 0 16px 30px rgba(3, 105, 161, 0.18);
}

.home-dark .home-auth-btn-primary {
  border-color: rgba(56, 189, 248, 0.36);
  background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%);
  color: #f8fbff;
  box-shadow: 0 16px 30px rgba(14, 165, 233, 0.22);
}

.home-auth-btn-secondary {
  border: 1px solid rgba(148, 163, 184, 0.35);
  background: rgba(255, 255, 255, 0.88);
  color: #0f172a;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
}

.home-dark .home-auth-btn-secondary {
  border-color: rgba(125, 211, 252, 0.28);
  background: rgba(15, 23, 42, 0.74);
  color: #e0f2fe;
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.22);
}

.home-account-trigger {
  display: inline-flex;
  align-items: center;
  gap: 0.8rem;
  min-height: 54px;
  max-width: min(100%, 22rem);
  border-radius: 9999px;
  border: 1px solid rgba(148, 163, 184, 0.28);
  background: rgba(255, 255, 255, 0.92);
  padding: 0.75rem 1rem;
  box-shadow:
    0 12px 26px rgba(15, 23, 42, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.72);
  transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease, background-color 180ms ease;
  cursor: pointer;
}

.home-dark .home-account-trigger {
  border-color: rgba(125, 211, 252, 0.24);
  background: rgba(15, 23, 42, 0.72);
  box-shadow:
    0 14px 30px rgba(0, 0, 0, 0.28),
    inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.home-account-trigger:hover {
  transform: translateY(-1px);
  border-color: rgba(14, 165, 233, 0.34);
  box-shadow:
    0 16px 32px rgba(15, 23, 42, 0.1),
    0 0 0 1px rgba(56, 189, 248, 0.12);
}

.home-dark .home-account-trigger:hover {
  border-color: rgba(56, 189, 248, 0.42);
  box-shadow:
    0 18px 36px rgba(0, 0, 0, 0.34),
    0 0 0 1px rgba(56, 189, 248, 0.16);
}

.home-account-trigger:focus-visible {
  outline: 3px solid rgba(14, 165, 233, 0.2);
  outline-offset: 2px;
}

.home-account-trigger-avatar {
  display: inline-flex;
  width: 2.15rem;
  height: 2.15rem;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border-radius: 9999px;
  background: linear-gradient(135deg, #0ea5e9 0%, #22d3ee 100%);
  color: #fff;
  font-size: 0.8rem;
  font-weight: 700;
  box-shadow: 0 10px 20px rgba(14, 165, 233, 0.24);
}

.home-account-trigger-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  flex-shrink: 0;
  border-radius: 9999px;
  border: 1px solid rgba(125, 211, 252, 0.52);
  background: linear-gradient(135deg, rgba(240, 249, 255, 0.94), rgba(224, 242, 254, 0.9));
  color: #0369a1;
  padding: 0.34rem 0.6rem;
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.01em;
}

.home-dark .home-account-trigger-tag {
  border-color: rgba(125, 211, 252, 0.34);
  background: linear-gradient(135deg, rgba(8, 47, 73, 0.88), rgba(12, 74, 110, 0.72));
  color: #bae6fd;
}

.parallax-lane {
  position: absolute;
  top: 0;
  bottom: 0;
  width: clamp(130px, 22vw, 270px);
  overflow: hidden;
}

.lane-left {
  left: 0;
}

.lane-right {
  right: 0;
}

.p-el {
  position: absolute;
  width: var(--s);
  height: var(--s);
  transform:
    translate3d(calc(var(--mx) * var(--dx) * 1px), calc(var(--my) * var(--dy) * 1px), 0)
    rotateX(8deg)
    rotateY(-10deg);
  animation: p-float var(--dur) ease-in-out infinite;
  animation-delay: var(--delay);
  transition: transform 0.18s linear;
  border-radius: 14px;
  backdrop-filter: blur(3px);
  -webkit-backdrop-filter: blur(3px);
  opacity: 0.58;
}

.p-cube {
  border: 1px solid rgba(59, 130, 246, 0.34);
  background: linear-gradient(145deg, rgba(219, 234, 254, 0.6), rgba(186, 230, 253, 0.32));
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.62), 0 8px 20px rgba(14, 165, 233, 0.15);
}

.home-dark .p-cube {
  border-color: rgba(56, 189, 248, 0.36);
  background: linear-gradient(145deg, rgba(30, 64, 175, 0.24), rgba(8, 47, 73, 0.34));
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.08), 0 10px 26px rgba(14, 165, 233, 0.18);
}

.p-sphere {
  border-radius: 999px;
  border: 1px solid rgba(16, 185, 129, 0.28);
  background: radial-gradient(circle at 30% 28%, rgba(255,255,255,0.72), rgba(110,231,183,0.34) 52%, rgba(56,189,248,0.2) 100%);
  box-shadow: 0 10px 24px rgba(16, 185, 129, 0.16);
}

.home-dark .p-sphere {
  border-color: rgba(52, 211, 153, 0.32);
  background: radial-gradient(circle at 30% 28%, rgba(240,253,250,0.22), rgba(6,95,70,0.36) 52%, rgba(14,165,233,0.16) 100%);
  box-shadow: 0 12px 28px rgba(16, 185, 129, 0.18);
}

.p-book,
.p-code,
.p-pen {
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(14, 165, 233, 0.34);
  background: linear-gradient(145deg, rgba(255,255,255,0.7), rgba(224,242,254,0.4));
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.66), 0 8px 20px rgba(2, 132, 199, 0.14);
}

.home-dark .p-book,
.home-dark .p-code,
.home-dark .p-pen {
  border-color: rgba(56, 189, 248, 0.34);
  background: linear-gradient(145deg, rgba(15,23,42,0.54), rgba(8,47,73,0.36));
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.08), 0 10px 24px rgba(2, 132, 199, 0.18);
}

.p-symbol {
  color: rgba(3, 105, 161, 0.62);
  font-weight: 700;
  letter-spacing: 0.04em;
}

.home-dark .p-symbol {
  color: rgba(186, 230, 253, 0.72);
}

@media (max-width: 1024px) {
  .parallax-lane {
    width: clamp(100px, 18vw, 190px);
  }

  .p-el {
    opacity: 0.48;
  }
}

@media (max-width: 768px) {
  .home-account-trigger {
    width: 100%;
    justify-content: center;
  }

  .parallax-lane {
    width: clamp(72px, 14vw, 120px);
  }

  .p-el {
    opacity: 0.42;
  }
}

@keyframes p-float {
  0%, 100% { transform: translate3d(calc(var(--mx) * var(--dx) * 1px), calc(var(--my) * var(--dy) * 1px), 0) translateY(0px); }
  50% { transform: translate3d(calc(var(--mx) * var(--dx) * 1px), calc(var(--my) * var(--dy) * 1px), 0) translateY(-10px); }
}

.hero-title {
  color: #0f172a;
  background: linear-gradient(92deg, #0f172a 8%, #0369a1 48%, #10b981 86%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow:
    0 2px 10px rgba(14, 165, 233, 0.14),
    0 8px 24px rgba(16, 185, 129, 0.14);
  letter-spacing: 0.015em;
  position: relative;
}

.home-dark .hero-title {
  color: #e0f2fe;
  background: linear-gradient(92deg, #eff6ff 8%, #7dd3fc 48%, #5eead4 86%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow:
    0 2px 12px rgba(14, 165, 233, 0.22),
    0 10px 28px rgba(16, 185, 129, 0.16);
}

.hero-title::after {
  content: "EduMind：链接教学灵感，刻画学习深度";
  position: absolute;
  inset: 0;
  z-index: -1;
  color: rgba(14, 165, 233, 0.2);
  filter: blur(10px);
  transform: translateY(2px);
  pointer-events: none;
}

.home-dark .hero-title::after {
  color: rgba(125, 211, 252, 0.24);
}

.hero-subtitle {
  color: #334155;
  padding: 0.68rem 1.6rem;
  border-radius: 999px;
  background: linear-gradient(120deg, rgba(255,255,255,0.74), rgba(240,249,255,0.84));
  border: 1px solid rgba(56, 189, 248, 0.3);
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,0.7),
    0 8px 20px rgba(15, 23, 42, 0.06);
}

.home-dark .hero-subtitle {
  color: #cbd5e1;
  background: linear-gradient(120deg, rgba(15,23,42,0.72), rgba(8,47,73,0.54));
  border-color: rgba(56, 189, 248, 0.24);
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,0.08),
    0 10px 26px rgba(0, 0, 0, 0.22);
}

.subtitle-main-art {
  display: inline-block;
  color: #0f172a;
  background: linear-gradient(96deg, #0f172a 8%, #0369a1 48%, #047857 86%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow:
    0 2px 9px rgba(14, 165, 233, 0.12),
    0 6px 16px rgba(16, 185, 129, 0.12);
}

.home-dark .subtitle-main-art {
  color: #e0f2fe;
  background: linear-gradient(96deg, #e0f2fe 8%, #7dd3fc 48%, #86efac 86%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow:
    0 2px 10px rgba(14, 165, 233, 0.22),
    0 8px 20px rgba(16, 185, 129, 0.16);
}

.home-card {
  position: relative;
  overflow: hidden;
  box-shadow:
    0 8px 22px rgba(0,0,0,0.08),
    0 0 0 1px rgba(14,165,233,0.22),
    0 0 18px rgba(14,165,233,0.18);
}

.teacher-card {
  background: linear-gradient(135deg, rgba(240, 249, 255, 0.92), rgba(239, 246, 255, 0.85) 48%, rgba(236, 254, 255, 0.88));
  border-color: rgba(125, 211, 252, 0.4);
}

.student-card {
  background: linear-gradient(135deg, rgba(236, 253, 245, 0.92), rgba(240, 253, 250, 0.85) 48%, rgba(236, 254, 255, 0.88));
  border-color: rgba(110, 231, 183, 0.4);
}

.home-dark .home-card {
  box-shadow:
    0 12px 30px rgba(0,0,0,0.28),
    0 0 0 1px rgba(14,165,233,0.16),
    0 0 24px rgba(14,165,233,0.12);
}

.home-dark .teacher-card {
  background: linear-gradient(135deg, rgba(8, 47, 73, 0.82), rgba(30, 64, 175, 0.42) 48%, rgba(15, 23, 42, 0.72));
  border-color: rgba(56, 189, 248, 0.3);
}

.home-dark .student-card {
  background: linear-gradient(135deg, rgba(6, 78, 59, 0.72), rgba(15, 118, 110, 0.34) 48%, rgba(15, 23, 42, 0.72));
  border-color: rgba(52, 211, 153, 0.28);
}

.home-card::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  padding: 1px;
  background: linear-gradient(125deg, rgba(56,189,248,0.76), rgba(14,165,233,0.42), rgba(16,185,129,0.6));
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
  opacity: 0.9;
}

.home-card:hover {
  transform: translateY(-8px) scale(1.02);
  box-shadow:
    0 20px 40px rgba(0,0,0,0.12),
    0 0 0 1px rgba(34,211,238,0.58),
    0 0 24px rgba(34,211,238,0.35),
    0 0 52px rgba(34,211,238,0.22);
}

.home-dark .home-card:hover {
  box-shadow:
    0 24px 48px rgba(0,0,0,0.34),
    0 0 0 1px rgba(34,211,238,0.44),
    0 0 28px rgba(34,211,238,0.22),
    0 0 54px rgba(34,211,238,0.16);
}

.teacher-card:hover {
  filter: drop-shadow(0 0 24px rgba(14,165,233,0.45));
}

.student-card:hover {
  filter: drop-shadow(0 0 24px rgba(16,185,129,0.38));
}

.card-shine {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    105deg,
    transparent 0%,
    transparent 40%,
    rgba(255,255,255,0.35) 50%,
    transparent 60%,
    transparent 100%
  );
  background-size: 200% 100%;
  background-position: 200% 0;
  pointer-events: none;
  border-radius: inherit;
  transition: background-position 0s;
}

.home-dark .card-shine {
  background: linear-gradient(
    105deg,
    transparent 0%,
    transparent 40%,
    rgba(255,255,255,0.14) 50%,
    transparent 60%,
    transparent 100%
  );
}

.home-card-title {
  color: #0f172a;
}

.home-card-copy {
  color: #475569;
}

.home-card-link-teacher {
  color: #0369a1;
}

.home-card-link-student {
  color: #047857;
}

.home-dark .home-card-title {
  color: #f0f9ff;
}

.home-dark .home-card-copy {
  color: #cbd5e1;
}

.home-dark .home-card-link-teacher {
  color: #7dd3fc;
}

.home-dark .home-card-link-student {
  color: #86efac;
}

.home-card:hover .card-shine {
  transition: background-position 0.6s ease-out;
  background-position: -100% 0;
}

.entry-icon-wrap {
  border: 1px solid rgba(148, 163, 184, 0.3);
  background: linear-gradient(135deg, rgba(255,255,255,0.92), rgba(248,250,252,0.86));
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,0.8),
    0 0 0 1px rgba(148, 163, 184, 0.14),
    0 0 12px rgba(15, 23, 42, 0.08);
}

.home-dark .entry-icon-wrap {
  border-color: rgba(125, 211, 252, 0.24);
  background: linear-gradient(135deg, rgba(15,23,42,0.74), rgba(30,41,59,0.58));
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,0.08),
    0 0 0 1px rgba(125, 211, 252, 0.08),
    0 0 16px rgba(14, 165, 233, 0.14);
}

.entry-icon-wrap-teacher {
  border-color: rgba(56, 189, 248, 0.52);
  background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(224, 242, 254, 0.84));
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,0.8),
    0 0 0 1px rgba(14,165,233,0.18),
    0 0 14px rgba(14,165,233,0.2);
}

.home-dark .entry-icon-wrap-teacher {
  border-color: rgba(56, 189, 248, 0.4);
  background: linear-gradient(135deg, rgba(8,47,73,0.74), rgba(12,74,110,0.5));
}

.entry-icon-wrap-student {
  border-color: rgba(52, 211, 153, 0.46);
  background: linear-gradient(135deg, rgba(255,255,255,0.92), rgba(220, 252, 231, 0.86));
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,0.82),
    0 0 0 1px rgba(16, 185, 129, 0.16),
    0 0 14px rgba(16, 185, 129, 0.18);
}

.home-dark .entry-icon-wrap-student {
  border-color: rgba(52, 211, 153, 0.36);
  background: linear-gradient(135deg, rgba(6,78,59,0.66), rgba(20,83,45,0.42));
}

.entry-icon-wrap::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: linear-gradient(120deg, transparent 0%, rgba(255,255,255,0.5) 45%, transparent 72%);
  transform: translateX(-140%);
  opacity: 0;
  transition: transform 0.45s ease, opacity 0.35s ease;
}

.entry-icon-wrap-teacher::before {
  background: linear-gradient(120deg, transparent 0%, rgba(56,189,248,0.42) 45%, transparent 72%);
}

.entry-icon-wrap-student::before {
  background: linear-gradient(120deg, transparent 0%, rgba(16,185,129,0.42) 45%, transparent 72%);
}

.home-card:hover .entry-icon-wrap::before {
  transform: translateX(140%);
  opacity: 1;
}

.entry-icon {
  color: #0284c7;
  filter: drop-shadow(0 0 6px rgba(14,165,233,0.5));
  transition: color 0.3s ease, filter 0.3s ease;
}

.entry-icon-teacher {
  color: #0369a1;
  filter: drop-shadow(0 0 6px rgba(14,165,233,0.55));
}

.entry-icon-student {
  color: #047857;
  filter: drop-shadow(0 0 6px rgba(16,185,129,0.42));
}

.teacher-card:hover .entry-icon-teacher {
  color: #0369a1;
  filter: drop-shadow(0 0 10px rgba(14,165,233,0.66));
}

.student-card:hover .entry-icon-student {
  color: #065f46;
  filter: drop-shadow(0 0 10px rgba(16,185,129,0.62));
}

.entry-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.16rem 0.58rem;
  border-radius: 999px;
  font-weight: 700;
  font-size: 1rem;
  border: 1px solid transparent;
}

.teacher-badge {
  color: #0369a1;
  background: linear-gradient(120deg, rgba(240, 249, 255, 0.96), rgba(224, 242, 254, 0.9));
  border-color: rgba(56,189,248,0.36);
}

.home-dark .teacher-badge {
  color: #bae6fd;
  background: linear-gradient(120deg, rgba(8,47,73,0.88), rgba(12,74,110,0.7));
  border-color: rgba(56,189,248,0.32);
}

.student-badge {
  color: #047857;
  background: linear-gradient(120deg, rgba(236, 253, 245, 0.96), rgba(209, 250, 229, 0.9));
  border-color: rgba(16,185,129,0.34);
}

.home-dark .student-badge {
  color: #bbf7d0;
  background: linear-gradient(120deg, rgba(6,78,59,0.82), rgba(20,83,45,0.64));
  border-color: rgba(52,211,153,0.3);
}

.badge-breathe-blue,
.badge-breathe-green {
  animation: badge-breathe 2.6s ease-in-out infinite;
}

.badge-breathe-blue {
  box-shadow: 0 0 0 rgba(56, 189, 248, 0.0);
}

.badge-breathe-green {
  box-shadow: 0 0 0 rgba(52, 211, 153, 0.0);
}

@keyframes badge-breathe {
  0%, 100% { opacity: 0.88; }
  50% { opacity: 1; }
}

.entry-btn {
  border: 1px solid transparent;
}

.teacher-entry-btn {
  background: linear-gradient(135deg, rgba(240,249,255,0.96) 0%, rgba(224,242,254,0.94) 48%, rgba(219,234,254,0.96) 100%);
  border-color: rgba(125, 211, 252, 0.7);
  color: #0c4a6e;
  box-shadow:
    0 10px 20px rgba(14, 116, 144, 0.16),
    0 0 0 1px rgba(186, 230, 253, 0.62),
    0 0 16px rgba(56, 189, 248, 0.22);
}

.home-dark .teacher-entry-btn {
  background: linear-gradient(135deg, rgba(14,165,233,0.22) 0%, rgba(37,99,235,0.32) 48%, rgba(15,23,42,0.7) 100%);
  border-color: rgba(125, 211, 252, 0.36);
  color: #e0f2fe;
  box-shadow:
    0 12px 24px rgba(14, 116, 144, 0.24),
    0 0 0 1px rgba(56, 189, 248, 0.18),
    0 0 18px rgba(56, 189, 248, 0.18);
}

.student-entry-btn {
  background: linear-gradient(135deg, rgba(236,253,245,0.96) 0%, rgba(209,250,229,0.94) 48%, rgba(204,251,241,0.96) 100%);
  border-color: rgba(167, 243, 208, 0.72);
  color: #065f46;
  box-shadow:
    0 10px 20px rgba(5, 150, 105, 0.15),
    0 0 0 1px rgba(209, 250, 229, 0.62),
    0 0 16px rgba(16, 185, 129, 0.2);
}

.home-dark .student-entry-btn {
  background: linear-gradient(135deg, rgba(16,185,129,0.2) 0%, rgba(15,118,110,0.28) 48%, rgba(15,23,42,0.7) 100%);
  border-color: rgba(110, 231, 183, 0.34);
  color: #dcfce7;
  box-shadow:
    0 12px 24px rgba(5, 150, 105, 0.22),
    0 0 0 1px rgba(52, 211, 153, 0.16),
    0 0 18px rgba(16, 185, 129, 0.16);
}

.entry-btn:hover {
  transform: translateY(-2px) scale(1.03);
}

.teacher-entry-btn:hover {
  box-shadow:
    0 12px 24px rgba(3, 105, 161, 0.2),
    0 0 0 1px rgba(56, 189, 248, 0.62),
    0 0 24px rgba(56, 189, 248, 0.28);
}

.student-entry-btn:hover {
  box-shadow:
    0 12px 24px rgba(5, 150, 105, 0.2),
    0 0 0 1px rgba(52, 211, 153, 0.62),
    0 0 24px rgba(52, 211, 153, 0.25);
}

.entry-btn-scan {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  pointer-events: none;
  background:
    linear-gradient(115deg, transparent 15%, rgba(255, 255, 255, 0.04) 45%, rgba(255, 255, 255, 0.32) 50%, rgba(255, 255, 255, 0.04) 55%, transparent 85%),
    linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0));
  background-size: 240% 100%, 100% 100%;
  background-position: 200% 0, 0 0;
  animation: entry-scan 2.8s ease-in-out infinite;
}

.entry-btn-text {
  position: relative;
  z-index: 2;
}

@keyframes entry-scan {
  0% { background-position: 200% 0, 0 0; opacity: 0.65; }
  55% { background-position: -40% 0, 0 0; opacity: 1; }
  100% { background-position: -60% 0, 0 0; opacity: 0.7; }
}

.info-nav-shell {
  position: relative;
  overflow: hidden;
  box-shadow:
    0 10px 24px rgba(15, 23, 42, 0.08),
    0 0 0 1px rgba(56,189,248,0.18),
    0 0 16px rgba(56,189,248,0.14);
}

.info-nav-shell {
  background: rgba(255, 255, 255, 0.8);
  border-color: rgba(125, 211, 252, 0.45);
}

.home-dark .info-nav-shell {
  background: rgba(15, 23, 42, 0.7);
  border-color: rgba(56, 189, 248, 0.22);
  box-shadow:
    0 14px 30px rgba(0, 0, 0, 0.28),
    0 0 0 1px rgba(56,189,248,0.12),
    0 0 18px rgba(56,189,248,0.1);
}

.info-nav-shell::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  padding: 1px;
  background: linear-gradient(125deg, rgba(56,189,248,0.72), rgba(14,165,233,0.4), rgba(16,185,129,0.52));
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
  opacity: 0.95;
}

.info-nav-shell::after {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: linear-gradient(112deg, transparent 10%, rgba(255,255,255,0.26) 50%, transparent 90%);
  background-size: 220% 100%;
  background-position: 180% 0;
  pointer-events: none;
  animation: info-shine 3.2s ease-in-out infinite;
  opacity: 0.56;
}

.home-dark .info-nav-shell::after {
  background: linear-gradient(112deg, transparent 10%, rgba(125,211,252,0.18) 50%, transparent 90%);
}

.info-nav-row {
  position: relative;
  z-index: 1;
  display: flex;
  gap: 0.6rem;
  padding: 0.62rem;
  overflow-x: auto;
  background:
    linear-gradient(180deg, rgba(255,255,255,0.54), rgba(248,250,252,0.3));
}

.home-dark .info-nav-row {
  background: linear-gradient(180deg, rgba(15,23,42,0.5), rgba(8,47,73,0.22));
}

.info-nav-row::before,
.info-nav-row::after {
  content: "";
  position: absolute;
  width: 8px;
  height: 8px;
  border-radius: 999px;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(14,165,233,0.88);
  box-shadow: 0 0 10px rgba(14,165,233,0.5);
  pointer-events: none;
}

.info-nav-row::before {
  left: 8px;
}

.info-nav-row::after {
  right: 8px;
}

.info-nav-btn {
  flex: 1 1 0;
  min-width: 132px;
  border-radius: 0.9rem;
  border: 1px solid rgba(56,189,248,0.28);
  background: linear-gradient(120deg, rgba(255,255,255,0.88), rgba(240,249,255,0.8));
  padding: 0.7rem 0.8rem;
  transition: all 0.22s ease-out;
  cursor: pointer;
}

.home-dark .info-nav-btn {
  border-color: rgba(56,189,248,0.24);
  background: linear-gradient(120deg, rgba(15,23,42,0.68), rgba(8,47,73,0.44));
}

.info-nav-btn.active {
  border-color: rgba(14,165,233,0.55);
  box-shadow:
    0 0 0 1px rgba(56,189,248,0.22),
    0 0 18px rgba(14,165,233,0.26);
  background: linear-gradient(120deg, rgba(240,249,255,0.96), rgba(224,242,254,0.88));
}

.home-dark .info-nav-btn.active {
  border-color: rgba(125,211,252,0.45);
  box-shadow:
    0 0 0 1px rgba(56,189,248,0.18),
    0 0 18px rgba(14,165,233,0.22);
  background: linear-gradient(120deg, rgba(8,47,73,0.76), rgba(12,74,110,0.58));
}

.info-title-wrap {
  display: flex;
  align-items: center;
}

.info-title-chip {
  display: inline-flex;
  align-items: center;
  padding: 0.18rem 0.58rem;
  border-radius: 999px;
  color: #0369a1;
  font-weight: 700;
  font-size: 0.95rem;
  background: linear-gradient(120deg, rgba(240,249,255,0.96), rgba(224,242,254,0.88));
  border: 1px solid rgba(56,189,248,0.35);
}

.home-dark .info-title-chip {
  color: #bae6fd;
  background: linear-gradient(120deg, rgba(8,47,73,0.78), rgba(12,74,110,0.52));
  border-color: rgba(56,189,248,0.28);
}

.info-chevron {
  color: #0284c7;
  transition: transform 0.24s ease-out, color 0.24s ease-out;
}

.info-panel {
  position: relative;
  overflow: hidden;
  box-shadow:
    0 10px 24px rgba(15, 23, 42, 0.08),
    0 0 0 1px rgba(56,189,248,0.18),
    0 0 16px rgba(56,189,248,0.14);
  background:
    radial-gradient(circle at 8% 14%, rgba(56,189,248,0.12), transparent 46%),
    radial-gradient(circle at 92% 86%, rgba(16,185,129,0.10), transparent 44%),
    linear-gradient(120deg, rgba(255,255,255,0.86), rgba(248,250,252,0.8));
}

.home-dark .info-panel {
  background:
    radial-gradient(circle at 8% 14%, rgba(56,189,248,0.16), transparent 46%),
    radial-gradient(circle at 92% 86%, rgba(16,185,129,0.12), transparent 44%),
    linear-gradient(120deg, rgba(15,23,42,0.78), rgba(8,47,73,0.54));
  border-color: rgba(56, 189, 248, 0.22);
  box-shadow:
    0 14px 30px rgba(0, 0, 0, 0.28),
    0 0 0 1px rgba(56,189,248,0.12),
    0 0 18px rgba(56,189,248,0.1);
}

.info-panel::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  padding: 1px;
  background: linear-gradient(125deg, rgba(56,189,248,0.72), rgba(14,165,233,0.4), rgba(16,185,129,0.52));
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
  opacity: 0.95;
}

.info-panel-inner {
  position: relative;
  z-index: 1;
  padding: 1rem 1.15rem 1.15rem;
}

.info-panel-inner::before {
  content: "";
  position: absolute;
  top: 0;
  left: 1.15rem;
  right: 1.15rem;
  height: 1px;
  background: linear-gradient(90deg, rgba(56,189,248,0.2), rgba(14,165,233,0.62), rgba(16,185,129,0.2));
}

.info-panel-title {
  margin: 0 0 0.35rem;
  color: #0f172a;
  font-size: 1rem;
  font-weight: 700;
  letter-spacing: 0.01em;
  background: linear-gradient(96deg, #0f172a 8%, #0369a1 48%, #10b981 86%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow:
    0 2px 8px rgba(14, 165, 233, 0.14),
    0 5px 14px rgba(16, 185, 129, 0.12);
}

.home-dark .info-panel-title {
  color: #e0f2fe;
  background: linear-gradient(96deg, #e0f2fe 8%, #7dd3fc 48%, #86efac 86%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.info-text {
  margin: 0;
  color: #334155;
  font-size: 0.96rem;
  line-height: 1.75;
}

.home-dark .info-text {
  color: #cbd5e1;
}

.team-extra {
  margin-top: 0.75rem;
  padding-top: 0.7rem;
  border-top: 1px dashed rgba(56,189,248,0.42);
}

.team-line {
  margin: 0 0 0.32rem;
  color: #334155;
  font-size: 0.88rem;
}

.home-dark .team-line {
  color: #cbd5e1;
}

.team-github {
  margin-top: 0.2rem;
  display: inline-flex;
  align-items: center;
  gap: 0.42rem;
  color: #0369a1;
  font-size: 0.88rem;
  font-weight: 600;
  text-decoration: none;
}

.home-dark .team-github {
  color: #7dd3fc;
}

.team-github:hover {
  color: #075985;
  text-decoration: underline;
}

@keyframes info-shine {
  0% { background-position: 180% 0; opacity: 0.42; }
  50% { background-position: -20% 0; opacity: 0.68; }
  100% { background-position: -40% 0; opacity: 0.5; }
}

@media (max-width: 640px) {
  .hero-subtitle {
    border-radius: 1rem;
    padding: 0.7rem 0.85rem;
  }

  .info-nav-btn {
    min-width: 120px;
    padding: 0.62rem 0.68rem;
  }
}

@media (prefers-reduced-motion: reduce) {
  .p-el {
    animation: none;
    transform: none;
  }

  .neuron-canvas {
    opacity: 0.46;
  }

  .entry-btn-scan {
    animation: none;
    background-position: 0 0, 0 0;
  }

  .badge-breathe-blue,
  .badge-breathe-green,
  .info-nav-shell::after {
    animation: none;
    opacity: 1;
  }

  .info-nav-row::before,
  .info-nav-row::after {
    box-shadow: none;
  }
}
</style>

