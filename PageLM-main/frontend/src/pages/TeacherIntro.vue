<template>
  <div class="teacher-intro min-h-screen relative overflow-hidden">
    <div class="intro-bg">
      <div class="orb orb-1"></div>
      <div class="orb orb-2"></div>
      <div class="orb orb-3"></div>
      <div class="grid-overlay"></div>
    </div>

    <nav class="fixed top-0 left-0 right-0 z-50 flex items-center justify-between py-4 px-6 backdrop-blur-xl bg-sky-50/95 border-b border-sky-200/60">
      <RouterLink to="/" class="flex items-center gap-2 text-slate-700 hover:text-sky-700 transition-colors">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        返回首页
      </RouterLink>
      <div class="flex items-center gap-2">
        <div class="w-9 h-9 rounded-lg bg-sky-500 flex items-center justify-center shadow-[0_0_16px_rgba(14,165,233,0.4)]">
          <svg viewBox="0 0 24 24" class="w-5 h-5 text-white" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 10v6M2 10l10-5 10 5-10 5z" />
            <path d="M6 12v5c3 3 9 3 12 0v-5" />
          </svg>
        </div>
        <span class="font-bold text-slate-800">教师端</span>
      </div>
    </nav>

    <main class="relative z-10 pt-28 pb-20 px-4 md:px-8">
      <section class="max-w-5xl mx-auto text-center mb-12">
        <h1 class="hero-title text-4xl md:text-5xl font-bold mb-4 tracking-tight">
          智教 · 让备课更从容
        </h1>
        <p class="hero-subtitle text-lg max-w-2xl mx-auto">
          <span class="subtitle-main-art">AI 贯穿教案、课件到微课与试卷全流程，助你随时随地、随教随用。</span>
        </p>
      </section>

      <section class="max-w-5xl mx-auto">
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 md:gap-4">
          <RouterLink
            v-for="(item, i) in features"
            :key="item.path"
            :to="item.path"
            class="intro-card card-3d group rounded-xl relative overflow-hidden bg-white/80 border border-sky-200/40 backdrop-blur-md transition-all duration-300 cursor-pointer"
            :style="{ animationDelay: `${i * 50}ms`, boxShadow: '0 4px 20px rgba(0,0,0,0.06), 0 0 0 1px rgba(14,165,233,0.08)' }"
          >
            <div class="card-shine" aria-hidden="true"></div>
            <TeacherIntroCardGraphic :graphic-key="item.graphicKey" />
            <div
              class="icon-wrap absolute top-3 left-3 w-9 h-9 rounded-lg flex items-center justify-center transition-colors duration-300 relative overflow-hidden"
            >
              <component :is="item.icon" class="w-5 h-5 icon-svg relative z-[1]" />
            </div>
            <div class="card-info absolute inset-x-0 bottom-0 p-3 md:p-4">
              <h3 class="text-sm font-bold text-slate-800 mb-1">
                <span class="card-title-spot">{{ item.title }}</span>
              </h3>
              <p class="text-xs text-slate-600 leading-relaxed line-clamp-2">{{ item.desc }}</p>
              <span class="mt-2 inline-flex items-center gap-1 text-sky-600 text-xs font-medium opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                进入
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                </svg>
              </span>
            </div>
          </RouterLink>
        </div>
      </section>

      <section class="max-w-2xl mx-auto mt-12 text-center">
        <button
          @click="enterTeacher"
          class="teacher-enter-btn group relative overflow-hidden px-10 py-4 rounded-2xl font-bold text-white transition-all duration-300 cursor-pointer"
        >
          <span class="teacher-enter-scan" aria-hidden="true"></span>
          <span class="teacher-enter-text">进入教师端</span>
        </button>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { RouterLink, useRouter } from "vue-router";
import { h } from "vue";
import { useRoleStore } from "../stores/role";
import TeacherIntroCardGraphic from "../components/TeacherIntroCardGraphic.vue";

const router = useRouter();
const roleStore = useRoleStore();

const enterTeacher = () => {
  roleStore.setRole("teacher");
  router.push("/teacher/chat");
};

const iconChat = () => h("svg", { viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": "1.8" }, [
  h("path", { d: "M7 4.5h10a3.5 3.5 0 0 1 3.5 3.5v5a3.5 3.5 0 0 1-3.5 3.5H10l-3.5 3v-3H7A3.5 3.5 0 0 1 3.5 13V8A3.5 3.5 0 0 1 7 4.5Z" }),
]);
const iconFile = () => h("svg", { viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": "1.8" }, [
  h("path", { d: "M4 6.5a2.5 2.5 0 0 1 2.5-2.5h3l2 2h6.5A2.5 2.5 0 0 1 20.5 8.5v8A2.5 2.5 0 0 1 18 19H6.5A2.5 2.5 0 0 1 4 16.5v-10Z" }),
  h("path", { d: "M4 9.5h16.5" }),
]);
const iconLesson = () => h("svg", { viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": "1.8" }, [
  h("path", { d: "M7 3.5h7l3.5 3.5V18a2.5 2.5 0 0 1-2.5 2.5H7A2.5 2.5 0 0 1 4.5 18V6A2.5 2.5 0 0 1 7 3.5Z" }),
  h("path", { d: "M14 3.5V7h3.5" }),
  h("path", { d: "m8.5 12 2 2 4-4" }),
]);
const iconSlides = () => h("svg", { viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": "1.8" }, [
  h("path", { d: "M5 4.5h14A2.5 2.5 0 0 1 21.5 7v7A2.5 2.5 0 0 1 19 16.5H5A2.5 2.5 0 0 1 2.5 14V7A2.5 2.5 0 0 1 5 4.5Z" }),
  h("path", { d: "M8 19.5h8" }),
  h("path", { d: "m7 11 2.5-2.5 2.5 2.5 3-3 2 2" }),
]);
const iconVideo = () => h("svg", { viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": "1.8" }, [
  h("path", { d: "M5 6.5A2.5 2.5 0 0 1 7.5 4h6A2.5 2.5 0 0 1 16 6.5v11A2.5 2.5 0 0 1 13.5 20h-6A2.5 2.5 0 0 1 5 17.5v-11Z" }),
  h("path", { d: "m16 10 4-2.5v9L16 14" }),
]);
const iconQuiz = () => h("svg", { viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": "1.8" }, [
  h("path", { d: "M12 3.5a6.5 6.5 0 0 0-3.5 11.98V17.5h7v-2.02A6.5 6.5 0 0 0 12 3.5Z" }),
  h("path", { d: "M9.5 20.5h5" }),
]);
const iconPaper = () => h("svg", { viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": "1.8" }, [
  h("path", { d: "M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5v-7.5H8.25v7.5Z" }),
]);
const iconRecords = () => h("svg", { viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", "stroke-width": "1.8" }, [
  h("path", { d: "M4.5 6.5h15" }),
  h("path", { d: "M4.5 12h15" }),
  h("path", { d: "M4.5 17.5h10.5" }),
  h("path", { d: "M17 16.5 19.5 19l2-2" }),
]);

const features = [
  { title: "对话", desc: "AI 助教对话，答疑与备课灵感随时获取。", path: "/teacher/chat", icon: iconChat, graphicKey: "chat" as const },
  { title: "b站视频", desc: "检索优质教学视频素材，快速用于课堂导入与重难点讲解。", path: "/teacher/bili-learning", icon: iconVideo, graphicKey: "video" as const },
  { title: "教案", desc: "输入课题，AI 自动生成三维目标教案。", path: "/lesson-plan", icon: iconLesson, graphicKey: "lesson" as const },
  { title: "教学幻灯片", desc: "一键生成约 20 页精美 PPT，可直接授课使用。", path: "/slides", icon: iconSlides, graphicKey: "slides" as const },
  { title: "教学视频", desc: "自动生成课堂画面与配音，快速整理成有声微课。", path: "/teaching-video", icon: iconVideo, graphicKey: "video" as const },
  { title: "测验", desc: "根据备课资料生成测验题，即时检验学习效果。", path: "/teacher/quiz", icon: iconQuiz, graphicKey: "quiz" as const },
  { title: "试卷", desc: "一键生成多题型试卷，支持 PDF 导出。", path: "/teacher/paper", icon: iconPaper, graphicKey: "paper" as const },
  { title: "教学记录汇", desc: "集中查看教学与备课记录，便于复盘与改进。", path: "/teaching-records", icon: iconRecords, graphicKey: "records" as const },
];
</script>

<style scoped>
.teacher-intro {
  background: linear-gradient(160deg, #f0f9ff 0%, #e0f2fe 35%, #f0f9ff 100%);
}

.intro-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(70px);
  opacity: 0.6;
  animation: orb-float 18s ease-in-out infinite;
}

.orb-1 {
  width: 50vw;
  height: 50vw;
  max-width: 480px;
  max-height: 480px;
  background: rgba(14, 165, 233, 0.2);
  top: -15%;
  right: -10%;
  animation-delay: 0s;
}

.orb-2 {
  width: 40vw;
  height: 40vw;
  max-width: 400px;
  max-height: 400px;
  background: rgba(56, 189, 248, 0.18);
  top: 45%;
  left: -10%;
  animation-delay: -6s;
}

.orb-3 {
  width: 35vw;
  height: 35vw;
  max-width: 320px;
  max-height: 320px;
  background: rgba(14, 165, 233, 0.15);
  bottom: -5%;
  right: 25%;
  animation-delay: -12s;
}

@keyframes orb-float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(-20px, 15px) scale(1.03); }
  66% { transform: translate(15px, -15px) scale(0.97); }
}

.grid-overlay {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(14,165,233,0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(14,165,233,0.05) 1px, transparent 1px);
  background-size: 48px 48px;
  animation: grid-drift 40s linear infinite;
}

@keyframes grid-drift {
  0% { transform: translate(0, 0); }
  100% { transform: translate(48px, 48px); }
}

.hero-title {
  color: #0f172a;
  background: linear-gradient(92deg, #0f172a 8%, #0369a1 46%, #0ea5e9 82%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow:
    0 2px 10px rgba(14, 165, 233, 0.16),
    0 8px 24px rgba(56, 189, 248, 0.15);
  letter-spacing: 0.02em;
  position: relative;
}

.hero-title::after {
  content: "智教 · 让备课更从容";
  position: absolute;
  inset: 0;
  z-index: -1;
  color: rgba(14, 165, 233, 0.22);
  filter: blur(10px);
  transform: translateY(2px);
  pointer-events: none;
}

.hero-subtitle {
  color: #334155;
  line-height: 1.8;
  padding: 0.65rem 1rem;
  border-radius: 999px;
  background: linear-gradient(120deg, rgba(255,255,255,0.72), rgba(239, 246, 255, 0.82));
  border: 1px solid rgba(56, 189, 248, 0.32);
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,0.7),
    0 8px 20px rgba(15, 23, 42, 0.06);
}

.subtitle-main-art {
  display: inline-block;
  font-weight: 700;
  letter-spacing: 0.01em;
  color: #0f172a;
  background: linear-gradient(96deg, #0f172a 8%, #0369a1 48%, #0284c7 86%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow:
    0 2px 9px rgba(14, 165, 233, 0.14),
    0 6px 16px rgba(2, 132, 199, 0.14);
}

.card-title-spot {
  display: inline-flex;
  align-items: center;
  max-width: 100%;
  padding: 0.14rem 0.5rem;
  border-radius: 999px;
  color: #0369a1;
  font-weight: 700;
  font-size: 0.9em;
  line-height: 1.2;
  background: linear-gradient(120deg, rgba(240, 249, 255, 0.96), rgba(224, 242, 254, 0.88));
  border: 1px solid rgba(56, 189, 248, 0.36);
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,0.72),
    0 0 12px rgba(56, 189, 248, 0.2);
}

.intro-card:hover .card-title-spot {
  border-color: rgba(14,165,233,0.56);
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,0.78),
    0 0 16px rgba(14,165,233,0.26);
}

@media (max-width: 640px) {
  .hero-subtitle {
    border-radius: 1rem;
    padding: 0.7rem 0.85rem;
  }
}

.card-3d:hover {
  transform: translateY(-8px) scale(1.02);
  box-shadow:
    0 20px 40px rgba(0,0,0,0.12),
    0 0 0 1px rgba(14,165,233,0.65),
    0 0 20px rgba(14,165,233,0.44),
    0 0 52px rgba(14,165,233,0.28);
  border-color: rgba(14,165,233,0.56);
  filter: drop-shadow(0 0 28px rgba(14,165,233,0.58)) drop-shadow(0 0 68px rgba(14,165,233,0.30));
}

.intro-card {
  min-height: 280px;
  box-shadow:
    0 8px 22px rgba(0,0,0,0.08),
    0 0 0 1px rgba(14,165,233,0.30),
    0 0 18px rgba(14,165,233,0.24);
  filter: drop-shadow(0 0 18px rgba(14,165,233,0.40)) drop-shadow(0 0 48px rgba(14,165,233,0.20));
}

.icon-wrap {
  border: 1px solid rgba(56, 189, 248, 0.56);
  background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(224, 242, 254, 0.84));
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,0.8),
    0 0 0 1px rgba(14,165,233,0.22),
    0 0 18px rgba(14,165,233,0.22);
}

.icon-wrap::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: linear-gradient(120deg, transparent 0%, rgba(56,189,248,0.4) 45%, transparent 72%);
  transform: translateX(-140%);
  opacity: 0;
  transition: transform 0.45s ease, opacity 0.35s ease;
}

.icon-wrap::after {
  content: "";
  position: absolute;
  width: 8px;
  height: 8px;
  top: 2px;
  right: 2px;
  border-radius: 999px;
  background: rgba(56, 189, 248, 0.95);
  box-shadow: 0 0 0 2px rgba(255,255,255,0.7), 0 0 8px rgba(56,189,248,0.65);
}

.intro-card:hover .icon-wrap::before {
  transform: translateX(140%);
  opacity: 1;
}

.icon-svg {
  color: #0284c7;
  filter: drop-shadow(0 0 6px rgba(14,165,233,0.5));
  transition: color 0.3s ease, filter 0.3s ease;
}

.intro-card:hover .icon-svg {
  color: #0369a1;
  filter: drop-shadow(0 0 10px rgba(14,165,233,0.66));
}

.teacher-enter-btn {
  background: linear-gradient(135deg, #38bdf8 0%, #0ea5e9 45%, #0284c7 100%);
  box-shadow:
    0 12px 24px rgba(3, 105, 161, 0.22),
    0 0 0 1px rgba(186, 230, 253, 0.64),
    0 0 22px rgba(56, 189, 248, 0.32);
}

.teacher-enter-btn:hover {
  transform: translateY(-2px) scale(1.03);
  box-shadow:
    0 14px 30px rgba(3, 105, 161, 0.26),
    0 0 0 1px rgba(56, 189, 248, 0.74),
    0 0 36px rgba(56, 189, 248, 0.46);
}

.teacher-enter-btn:focus-visible {
  outline: 2px solid rgba(56, 189, 248, 0.72);
  outline-offset: 3px;
}

.teacher-enter-text {
  position: relative;
  z-index: 2;
  letter-spacing: 0.02em;
}

.teacher-enter-scan {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  pointer-events: none;
  background:
    linear-gradient(115deg, transparent 15%, rgba(224, 242, 254, 0.08) 45%, rgba(224, 242, 254, 0.56) 50%, rgba(224, 242, 254, 0.08) 55%, transparent 85%),
    linear-gradient(180deg, rgba(255,255,255,0.14), rgba(255,255,255,0));
  background-size: 240% 100%, 100% 100%;
  background-position: 200% 0, 0 0;
  animation: cta-scan 2.8s ease-in-out infinite;
}

@keyframes cta-scan {
  0% { background-position: 200% 0, 0 0; opacity: 0.65; }
  55% { background-position: -40% 0, 0 0; opacity: 1; }
  100% { background-position: -60% 0, 0 0; opacity: 0.7; }
}

@media (prefers-reduced-motion: reduce) {
  .grid-overlay {
    animation: none;
  }

  .teacher-enter-scan {
    animation: none;
    background-position: 0 0, 0 0;
  }
}

.intro-card::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  padding: 1px;
  background: linear-gradient(125deg, rgba(56,189,248,0.76), rgba(14,165,233,0.45), rgba(56,189,248,0.7));
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
  opacity: 0.9;
}

.card-3d:hover::before {
  opacity: 1;
}

.card-info {
  z-index: 3;
  margin-top: auto;
  padding-top: 1.1rem;
  background: linear-gradient(to top, rgba(255,255,255,0.96) 30%, rgba(255,255,255,0.76) 70%, rgba(255,255,255,0));
}

@media (min-width: 768px) {
  .intro-card {
    min-height: 320px;
  }
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

.card-3d:hover .card-shine {
  transition: background-position 0.6s ease-out;
  background-position: -100% 0;
}

.intro-card {
  animation: card-in 0.5s ease-out backwards;
}

@keyframes card-in {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
