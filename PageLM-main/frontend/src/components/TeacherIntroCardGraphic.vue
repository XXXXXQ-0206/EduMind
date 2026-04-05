<template>
  <div class="card-graphic" :class="`graphic-${graphicKey}`" aria-hidden="true">
    <svg
      class="card-graphic-svg"
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        <linearGradient id="royal-blue" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#1e40af" />
          <stop offset="100%" stop-color="#2563eb" />
        </linearGradient>
        <linearGradient id="cyan-glow" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#0891b2" />
          <stop offset="100%" stop-color="#22d3ee" />
        </linearGradient>
        <radialGradient id="sphere-glow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.9" />
          <stop offset="70%" stop-color="#0ea5e9" stop-opacity="0.6" />
          <stop offset="100%" stop-color="#0369a1" stop-opacity="0.3" />
        </radialGradient>
        <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="1" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      <!-- 1. 对话：脉动球体 + 双环 + 气泡节点 -->
      <template v-if="graphicKey === 'chat'">
        <circle class="graphic-pulse" cx="32" cy="32" r="10" fill="url(#sphere-glow)" filter="url(#glow)" />
        <circle class="graphic-ring graphic-ring-1" cx="32" cy="32" r="18" stroke="url(#cyan-glow)" stroke-width="0.8" stroke-opacity="0.7" fill="none" />
        <circle class="graphic-ring graphic-ring-2" cx="32" cy="32" r="24" stroke="url(#royal-blue)" stroke-width="0.6" stroke-opacity="0.5" fill="none" />
        <circle class="graphic-node" cx="32" cy="14" r="2.5" fill="#22d3ee" filter="url(#glow)" />
        <circle class="graphic-node" cx="48" cy="32" r="2.5" fill="#22d3ee" filter="url(#glow)" />
        <circle class="graphic-node" cx="32" cy="50" r="2.5" fill="#22d3ee" filter="url(#glow)" />
        <circle class="graphic-node" cx="16" cy="32" r="2.5" fill="#22d3ee" filter="url(#glow)" />
        <line class="graphic-flow" x1="32" y1="32" x2="32" y2="14" stroke="url(#cyan-glow)" stroke-width="0.6" stroke-opacity="0.6" />
        <line class="graphic-flow" x1="32" y1="32" x2="48" y2="32" stroke="url(#cyan-glow)" stroke-width="0.6" stroke-opacity="0.6" />
      </template>

      <!-- 2. 文件库：悬浮方块 + 光导纤维 + 中心 -->
      <template v-else-if="graphicKey === 'file'">
        <rect class="graphic-cube" x="14" y="18" width="12" height="14" rx="2" fill="rgba(14,165,233,0.2)" stroke="url(#royal-blue)" stroke-width="0.8" stroke-opacity="0.8" />
        <rect class="graphic-cube" x="26" y="22" width="12" height="14" rx="2" fill="rgba(14,165,233,0.25)" stroke="url(#royal-blue)" stroke-width="0.8" stroke-opacity="0.8" />
        <rect class="graphic-cube" x="38" y="18" width="12" height="14" rx="2" fill="rgba(14,165,233,0.2)" stroke="url(#royal-blue)" stroke-width="0.8" stroke-opacity="0.8" />
        <circle cx="32" cy="32" r="6" fill="url(#sphere-glow)" stroke="url(#cyan-glow)" stroke-width="0.6" opacity="0.9" />
        <line class="graphic-fiber" x1="26" y1="29" x2="32" y2="32" stroke="url(#cyan-glow)" stroke-width="0.8" stroke-opacity="0.8" />
        <line class="graphic-fiber" x1="38" y1="29" x2="32" y2="32" stroke="url(#cyan-glow)" stroke-width="0.8" stroke-opacity="0.8" />
        <line class="graphic-fiber" x1="20" y1="25" x2="32" y2="32" stroke="url(#cyan-glow)" stroke-width="0.8" stroke-opacity="0.8" />
      </template>

      <!-- 3. 教案：阶梯 + 知识树线框 + 标签 -->
      <template v-else-if="graphicKey === 'lesson'">
        <path class="graphic-step" d="M18 44 L18 36 L28 36 L28 28 L38 28 L38 20 L48 20 L48 44 Z" fill="rgba(14,165,233,0.15)" stroke="url(#royal-blue)" stroke-width="0.7" stroke-opacity="0.7" />
        <path class="graphic-tree" d="M48 20 L52 12 L56 16 L54 22 M48 20 L44 14 L40 18 L42 24" stroke="url(#cyan-glow)" stroke-width="0.6" stroke-opacity="0.8" fill="none" />
        <circle cx="52" cy="12" r="2" fill="#22d3ee" opacity="0.9" />
        <circle cx="40" cy="18" r="1.8" fill="#22d3ee" opacity="0.8" />
        <rect x="50" y="10" width="14" height="5" rx="1" fill="rgba(14,165,233,0.3)" stroke="url(#royal-blue)" stroke-width="0.5" opacity="0.9" />
      </template>

      <!-- 4. 教学幻灯片：扇形展开矩形 + 扫描线 -->
      <template v-else-if="graphicKey === 'slides'">
        <rect class="graphic-slide graphic-slide-bg" x="8" y="16" width="20" height="28" rx="2" fill="rgba(14,165,233,0.12)" stroke="url(#royal-blue)" stroke-width="0.6" stroke-opacity="0.6" transform="rotate(-12 18 30)" />
        <rect class="graphic-slide graphic-slide-center" x="22" y="12" width="20" height="28" rx="2" fill="rgba(255,255,255,0.4)" stroke="url(#cyan-glow)" stroke-width="0.9" stroke-opacity="0.9" />
        <rect class="graphic-slide graphic-slide-bg" x="36" y="16" width="20" height="28" rx="2" fill="rgba(14,165,233,0.12)" stroke="url(#royal-blue)" stroke-width="0.6" stroke-opacity="0.6" transform="rotate(12 46 30)" />
        <line class="graphic-scan" x1="32" y1="14" x2="32" y2="40" stroke="url(#cyan-glow)" stroke-width="1.2" stroke-opacity="0.9" />
        <rect x="24" y="18" width="16" height="3" rx="1" fill="rgba(14,165,233,0.25)" />
        <rect x="24" y="24" width="12" height="3" rx="1" fill="rgba(14,165,233,0.2)" />
      </template>

      <!-- 5. 教学视频：播放器窗口 + 环状振幅线 -->
      <template v-else-if="graphicKey === 'video'">
        <rect class="graphic-player" x="20" y="18" width="24" height="16" rx="2" fill="rgba(15,23,42,0.5)" stroke="url(#cyan-glow)" stroke-width="0.8" stroke-opacity="0.9" />
        <polygon points="28,22 28,30 34,26" fill="url(#cyan-glow)" opacity="0.95" />
        <circle class="graphic-wave" cx="32" cy="44" r="14" stroke="url(#royal-blue)" stroke-width="0.6" stroke-opacity="0.5" fill="none" />
        <circle class="graphic-wave" cx="32" cy="44" r="10" stroke="url(#cyan-glow)" stroke-width="0.6" stroke-opacity="0.6" fill="none" />
        <path class="graphic-amp" d="M24 44 L26 40 L28 44 L30 38 L32 44 L34 42 L36 44 L38 40 L40 44" stroke="url(#cyan-glow)" stroke-width="0.8" stroke-opacity="0.9" fill="none" stroke-linecap="round" />
      </template>

      <!-- 6. 测验：六边形网络 + 中心勾选 + 节点 -->
      <template v-else-if="graphicKey === 'quiz'">
        <path class="graphic-hex" d="M32 14 L44 23 L44 41 L32 50 L20 41 L20 23 Z" fill="rgba(14,165,233,0.08)" stroke="url(#royal-blue)" stroke-width="0.7" stroke-opacity="0.7" />
        <path class="graphic-check" d="M28 32 L31 35 L38 28" stroke="#22d3ee" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" fill="none" />
        <circle class="graphic-dot graphic-dot-ok" cx="32" cy="20" r="2" fill="#22d3ee" />
        <circle class="graphic-dot graphic-dot-ok" cx="42" cy="32" r="2" fill="#22d3ee" />
        <circle class="graphic-dot graphic-dot-parse" cx="22" cy="32" r="2" fill="#f472b6" opacity="0.9" />
        <circle class="graphic-dot" cx="32" cy="44" r="2" fill="#22d3ee" />
        <line x1="32" y1="32" x2="32" y2="20" stroke="url(#cyan-glow)" stroke-width="0.4" stroke-opacity="0.5" stroke-dasharray="2 2" class="graphic-jump" />
        <line x1="32" y1="32" x2="42" y2="32" stroke="url(#cyan-glow)" stroke-width="0.4" stroke-opacity="0.5" stroke-dasharray="2 2" class="graphic-jump" />
      </template>

      <!-- 7. 试卷：卷轴 + 光笔 + 题型符号 + PDF -->
      <template v-else-if="graphicKey === 'paper'">
        <path class="graphic-scroll" d="M14 28 L14 40 Q14 48 32 48 Q50 48 50 40 L50 28 Q50 20 32 20 Q14 20 14 28 Z" fill="rgba(255,255,255,0.9)" stroke="url(#royal-blue)" stroke-width="0.8" stroke-opacity="0.8" />
        <line x1="32" y1="20" x2="32" y2="12" stroke="url(#cyan-glow)" stroke-width="1" stroke-opacity="0.9" class="graphic-pen" />
        <circle cx="32" cy="10" r="2" fill="url(#cyan-glow)" />
        <rect x="20" y="26" width="8" height="4" rx="1" fill="rgba(14,165,233,0.3)" class="graphic-symbol" />
        <rect x="36" y="30" width="6" height="4" rx="1" fill="rgba(14,165,233,0.25)" class="graphic-symbol" />
        <path d="M44 44 L46 42 L48 44 L46 46 Z" fill="url(#cyan-glow)" opacity="0.8" class="graphic-pdf" />
        <rect x="43" y="45" width="8" height="3" rx="0.5" fill="rgba(14,165,233,0.4)" />
      </template>

      <!-- 8. 教学记录汇：词云球体 + 上升折线 + 三圆环 -->
      <template v-else-if="graphicKey === 'records'">
        <circle class="graphic-sphere" cx="32" cy="32" r="16" fill="rgba(14,165,233,0.15)" stroke="url(#royal-blue)" stroke-width="0.7" stroke-opacity="0.7" />
        <path class="graphic-chart" d="M24 44 L28 40 L32 42 L36 36 L40 38 L44 30" stroke="url(#cyan-glow)" stroke-width="0.8" stroke-opacity="0.9" fill="none" stroke-linecap="round" stroke-linejoin="round" />
        <circle class="graphic-ring graphic-ring-1" cx="32" cy="32" r="22" stroke="url(#cyan-glow)" stroke-width="0.5" stroke-opacity="0.5" fill="none" />
        <circle class="graphic-ring graphic-ring-2" cx="32" cy="32" r="26" stroke="url(#royal-blue)" stroke-width="0.5" stroke-opacity="0.4" fill="none" transform="rotate(60 32 32)" />
        <circle class="graphic-ring graphic-ring-3" cx="32" cy="32" r="26" stroke="url(#royal-blue)" stroke-width="0.5" stroke-opacity="0.4" fill="none" transform="rotate(-60 32 32)" />
        <circle cx="32" cy="18" r="2" fill="#22d3ee" opacity="0.9" />
        <circle cx="20" cy="32" r="1.8" fill="#22d3ee" opacity="0.8" />
        <circle cx="44" cy="32" r="1.8" fill="#22d3ee" opacity="0.8" />
      </template>
    </svg>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  graphicKey: 'chat' | 'file' | 'lesson' | 'slides' | 'video' | 'quiz' | 'paper' | 'records';
}>();
</script>

<style scoped>
.card-graphic {
  position: absolute;
  inset: 8px 8px 102px 8px;
  border-radius: 14px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-graphic-svg {
  width: 100%;
  height: 100%;
  color: #0ea5e9;
  filter: drop-shadow(0 10px 28px rgba(14,165,233,0.25));
  transition: filter 0.25s ease;
}

/* 对话：脉动 + 波纹 */
.graphic-chat .graphic-pulse {
  animation: graphic-pulse 2s ease-in-out infinite;
}
.graphic-chat .graphic-ring-1 { animation: graphic-ring-rotate 8s linear infinite; }
.graphic-chat .graphic-ring-2 { animation: graphic-ring-rotate 12s linear infinite reverse; }
.graphic-chat .graphic-node { animation: graphic-node-glow 2s ease-in-out infinite; }
.graphic-chat .graphic-flow { animation: graphic-flow 1.5s ease-in-out infinite; }

/* 文件库：光纤流动 */
.graphic-file .graphic-fiber { animation: graphic-fiber 2s ease-in-out infinite; }
.graphic-file .graphic-cube { animation: graphic-float 3s ease-in-out infinite; }

/* 教案：阶梯层级 */
.graphic-lesson .graphic-step { animation: graphic-step-glow 2.5s ease-in-out infinite; }
.graphic-lesson .graphic-tree { animation: graphic-tree-pulse 2s ease-in-out infinite; }

/* 幻灯片：扫描线 */
.graphic-slides .graphic-scan { animation: graphic-scan 2s ease-in-out infinite; }
.graphic-slides .graphic-slide-center { filter: drop-shadow(0 0 6px rgba(14,165,233,0.3)); }

/* 教学视频：振幅线 */
.graphic-video .graphic-wave { animation: graphic-wave 1.5s ease-in-out infinite; }
.graphic-video .graphic-amp { animation: graphic-amp 0.8s ease-in-out infinite; }

/* 测验：节点跳动 */
.graphic-quiz .graphic-dot { animation: graphic-dot-jump 1.2s ease-in-out infinite; }
.graphic-quiz .graphic-dot-parse { animation-delay: 0.3s; }
.graphic-quiz .graphic-check { animation: graphic-check-pulse 1.5s ease-in-out infinite; }

/* 试卷：卷轴舒展 */
.graphic-paper .graphic-scroll { animation: graphic-scroll-open 3s ease-in-out infinite; }
.graphic-paper .graphic-pen { animation: graphic-pen-glow 2s ease-in-out infinite; }
.graphic-paper .graphic-symbol { animation: graphic-symbol-flow 2.5s ease-in-out infinite; }

/* 记录汇：折线上升 + 圆环 */
.graphic-records .graphic-chart { animation: graphic-chart-rise 2.5s ease-in-out infinite; }
.graphic-records .graphic-ring-1 { animation: graphic-ring-rotate 15s linear infinite; }
.graphic-records .graphic-ring-2,
.graphic-records .graphic-ring-3 { animation: graphic-ring-rotate 18s linear infinite reverse; }

@keyframes graphic-pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.08); opacity: 0.9; }
}
@keyframes graphic-ring-rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
@keyframes graphic-node-glow {
  0%, 100% { opacity: 0.9; }
  50% { opacity: 1; filter: drop-shadow(0 0 4px #22d3ee); }
}
@keyframes graphic-flow {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 0.9; }
}
@keyframes graphic-fiber {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}
@keyframes graphic-float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-2px); }
}
@keyframes graphic-step-glow {
  0%, 100% { opacity: 0.9; }
  50% { opacity: 1; }
}
@keyframes graphic-tree-pulse {
  0%, 100% { stroke-opacity: 0.7; }
  50% { stroke-opacity: 1; }
}
@keyframes graphic-scan {
  0% { opacity: 0.6; transform: translateY(0); }
  50% { opacity: 1; transform: translateY(12px); }
  100% { opacity: 0.6; transform: translateY(26px); }
}
@keyframes graphic-wave {
  0%, 100% { opacity: 0.5; transform: scale(1); }
  50% { opacity: 0.8; transform: scale(1.05); }
}
@keyframes graphic-amp {
  0%, 100% { opacity: 0.7; }
  50% { opacity: 1; }
}
@keyframes graphic-dot-jump {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.2); }
}
@keyframes graphic-check-pulse {
  0%, 100% { opacity: 0.9; }
  50% { opacity: 1; }
}
@keyframes graphic-scroll-open {
  0%, 100% { opacity: 0.95; }
  50% { opacity: 1; }
}
@keyframes graphic-pen-glow {
  0%, 100% { opacity: 0.8; }
  50% { opacity: 1; }
}
@keyframes graphic-symbol-flow {
  0%, 100% { opacity: 0.8; }
  50% { opacity: 1; }
}
@keyframes graphic-chart-rise {
  0%, 100% { opacity: 0.8; transform: translateY(2px); }
  50% { opacity: 1; transform: translateY(-2px); }
}

@media (prefers-reduced-motion: reduce) {
  .card-graphic-svg * {
    animation: none !important;
  }
}

@media (min-width: 768px) {
  .card-graphic {
    inset: 10px 10px 116px 10px;
  }
}
</style>
