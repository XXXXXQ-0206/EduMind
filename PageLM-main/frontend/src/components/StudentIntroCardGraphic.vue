<template>
  <div class="student-card-graphic" :class="`graphic-${graphicKey}`" aria-hidden="true">
    <svg class="student-card-graphic-svg" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="s-cyan" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#22d3ee" stop-opacity="0.95" />
          <stop offset="100%" stop-color="#10b981" stop-opacity="0.85" />
        </linearGradient>
        <linearGradient id="s-soft" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#ffffff" stop-opacity="0.55" />
          <stop offset="100%" stop-color="#d1fae5" stop-opacity="0.2" />
        </linearGradient>
        <radialGradient id="s-core" cx="0.5" cy="0.5" r="0.55">
          <stop offset="0%" stop-color="#67e8f9" stop-opacity="0.9" />
          <stop offset="70%" stop-color="#34d399" stop-opacity="0.45" />
          <stop offset="100%" stop-color="#10b981" stop-opacity="0.1" />
        </radialGradient>
      </defs>

      <template v-if="graphicKey === 'chat'">
        <circle cx="50" cy="50" r="34" fill="url(#s-soft)" stroke="url(#s-cyan)" stroke-opacity="0.65" />
        <path class="chat-orbit orbit-a" d="M18 50C18 31.2 32.8 16 50 16C67.2 16 82 31.2 82 50C82 68.8 67.2 84 50 84C32.8 84 18 68.8 18 50Z" stroke="url(#s-cyan)" stroke-width="1.4" stroke-opacity="0.7" />
        <path class="chat-orbit orbit-b" d="M50 14C64 14 75.6 29.4 75.6 50C75.6 70.6 64 86 50 86C36 86 24.4 70.6 24.4 50C24.4 29.4 36 14 50 14Z" stroke="url(#s-cyan)" stroke-width="1.2" stroke-opacity="0.55" />
        <circle cx="50" cy="50" r="12" fill="url(#s-core)" />
        <circle class="spark s1" cx="30" cy="36" r="1.8" fill="#67e8f9" />
        <circle class="spark s2" cx="68" cy="62" r="1.6" fill="#67e8f9" />
        <circle class="spark s3" cx="58" cy="30" r="1.4" fill="#67e8f9" />
      </template>

      <template v-else-if="graphicKey === 'file'">
        <rect class="file-pane fp1" x="22" y="27" width="50" height="14" rx="3" fill="url(#s-soft)" stroke="url(#s-cyan)" stroke-opacity="0.7" />
        <rect class="file-pane fp2" x="18" y="40" width="52" height="15" rx="3" fill="url(#s-soft)" stroke="url(#s-cyan)" stroke-opacity="0.75" />
        <rect class="file-pane fp3" x="26" y="54" width="50" height="14" rx="3" fill="url(#s-soft)" stroke="url(#s-cyan)" stroke-opacity="0.7" />
        <rect x="48" y="18" width="4" height="64" rx="2" fill="url(#s-cyan)" opacity="0.75" class="file-beam" />
        <text class="bit-flow" x="45" y="35">01 01 10</text>
      </template>

      <template v-else-if="graphicKey === 'notes'">
        <rect x="20" y="18" width="60" height="64" rx="6" fill="url(#s-soft)" stroke="url(#s-cyan)" stroke-opacity="0.7" />
        <line x1="38" y1="18" x2="38" y2="82" stroke="url(#s-cyan)" stroke-opacity="0.6" />
        <line x1="20" y1="34" x2="80" y2="34" stroke="url(#s-cyan)" stroke-opacity="0.55" />
        <path class="note-map" d="M52 51C58 45 64 44 70 48M52 51C58 54 64 58 72 64M52 51C56 61 63 68 70 74" stroke="url(#s-cyan)" stroke-width="1.2" stroke-linecap="round" />
        <polygon class="note-star" points="52,41 54.8,46.8 61.2,47.7 56.6,52.2 57.6,58.5 52,55.5 46.4,58.5 47.4,52.2 42.8,47.7 49.2,46.8" fill="#fbbf24" />
      </template>

      <template v-else-if="graphicKey === 'podcast'">
        <circle class="pod-ring ring-1" cx="50" cy="50" r="26" stroke="url(#s-cyan)" stroke-width="2" stroke-opacity="0.75" />
        <circle class="pod-ring ring-2" cx="50" cy="50" r="18" stroke="url(#s-cyan)" stroke-width="2" stroke-opacity="0.6" />
        <rect x="46" y="40" width="8" height="15" rx="4" fill="url(#s-cyan)" />
        <path d="M42 48C42 54 46 58 50 58C54 58 58 54 58 48" stroke="url(#s-cyan)" stroke-width="2" stroke-linecap="round" />
        <line x1="50" y1="58" x2="50" y2="64" stroke="url(#s-cyan)" stroke-width="2" stroke-linecap="round" />
        <circle class="pod-ripple rp1" cx="50" cy="50" r="33" stroke="url(#s-cyan)" stroke-opacity="0.35" />
        <circle class="pod-ripple rp2" cx="50" cy="50" r="39" stroke="url(#s-cyan)" stroke-opacity="0.25" />
      </template>

      <template v-else-if="graphicKey === 'quiz'">
        <circle cx="50" cy="50" r="26" fill="url(#s-soft)" stroke="url(#s-cyan)" stroke-opacity="0.75" />
        <circle cx="50" cy="50" r="18" stroke="url(#s-cyan)" stroke-opacity="0.7" />
        <circle cx="50" cy="50" r="9" stroke="url(#s-cyan)" stroke-opacity="0.8" />
        <path class="quiz-arrow" d="M18 63L40 54L50 44" stroke="url(#s-cyan)" stroke-width="2" stroke-linecap="round" />
        <polygon points="50,44 47,46 52,50 54,45" fill="#67e8f9" />
        <circle class="quiz-progress q1" cx="50" cy="50" r="31" stroke="url(#s-cyan)" stroke-width="2" stroke-linecap="round" stroke-dasharray="82 112" />
        <circle class="quiz-progress q2" cx="50" cy="50" r="35" stroke="url(#s-cyan)" stroke-width="2" stroke-linecap="round" stroke-dasharray="92 128" />
      </template>

      <template v-else-if="graphicKey === 'cards'">
        <rect class="card-spin cs1" x="24" y="28" width="28" height="18" rx="3" fill="url(#s-soft)" stroke="url(#s-cyan)" stroke-opacity="0.7" />
        <rect class="card-spin cs2" x="37" y="34" width="28" height="18" rx="3" fill="url(#s-soft)" stroke="url(#s-cyan)" stroke-opacity="0.75" />
        <rect class="card-spin cs3" x="21" y="48" width="28" height="18" rx="3" fill="url(#s-soft)" stroke="url(#s-cyan)" stroke-opacity="0.7" />
        <path class="card-spiral" d="M20 52C26 30 45 24 61 34C73 42 74 60 60 68C46 76 29 72 22 61" stroke="url(#s-cyan)" stroke-width="1.3" stroke-opacity="0.65" />
      </template>

      <template v-else-if="graphicKey === 'wrong'">
        <rect x="30" y="36" width="28" height="28" rx="4" fill="#fecaca" fill-opacity="0.4" stroke="#ef4444" stroke-opacity="0.75" />
        <rect x="42" y="36" width="16" height="28" rx="4" fill="url(#s-core)" opacity="0.65" />
        <circle cx="40" cy="46" r="15" fill="url(#s-soft)" stroke="url(#s-cyan)" stroke-opacity="0.8" />
        <line x1="25" y1="46" x2="55" y2="46" stroke="url(#s-cyan)" stroke-width="1.6" class="scan-line" />
        <circle cx="40" cy="46" r="5" stroke="url(#s-cyan)" stroke-opacity="0.8" />
      </template>

      <template v-else-if="graphicKey === 'records'">
        <path class="records-trend" d="M14 68C28 58 34 64 46 52C58 40 69 44 84 30" stroke="url(#s-cyan)" stroke-width="1.2" stroke-opacity="0.5" />
        <rect class="records-bar rb1" x="22" y="54" width="10" height="20" rx="2" fill="url(#s-soft)" stroke="url(#s-cyan)" stroke-opacity="0.7" />
        <rect class="records-bar rb2" x="38" y="45" width="10" height="29" rx="2" fill="url(#s-soft)" stroke="url(#s-cyan)" stroke-opacity="0.75" />
        <rect class="records-bar rb3" x="54" y="34" width="10" height="40" rx="2" fill="url(#s-soft)" stroke="url(#s-cyan)" stroke-opacity="0.78" />
        <circle cx="27" cy="58" r="1.8" fill="#67e8f9" />
        <circle cx="43" cy="50" r="1.8" fill="#67e8f9" />
        <circle cx="59" cy="40" r="1.8" fill="#67e8f9" />
      </template>

      <template v-else-if="graphicKey === 'speaking'">
        <path d="M26 40C30 33 38 30 46 31C57 32 64 39 64 49C64 58 57 66 46 67C38 68 31 64 27 58" fill="url(#s-soft)" stroke="url(#s-cyan)" stroke-opacity="0.75" />
        <path d="M36 50C41 47 46 47 52 50" stroke="url(#s-cyan)" stroke-width="1.6" stroke-linecap="round" />
        <path class="speak-wave" d="M64 48C70 46 74 42 77 36" stroke="url(#s-cyan)" stroke-width="1.8" stroke-linecap="round" />
        <path class="speak-wave" d="M64 52C71 54 75 58 79 64" stroke="url(#s-cyan)" stroke-width="1.8" stroke-linecap="round" />
        <polygon class="speak-star st1" points="72,44 73.8,47.3 77.5,47.8 74.8,50.4 75.3,54 72,52.2 68.8,54 69.2,50.4 66.5,47.8 70.2,47.3" fill="#67e8f9" />
        <polygon class="speak-star st2" points="77,59 78.4,61.5 81.2,61.9 79.1,63.9 79.5,66.7 77,65.4 74.5,66.7 74.9,63.9 72.8,61.9 75.6,61.5" fill="#67e8f9" />
      </template>

      <template v-else>
        <path d="M50 26C60 26 68 34 68 44V56C68 66 60 74 50 74C40 74 32 66 32 56V44C32 34 40 26 50 26Z" fill="url(#s-soft)" stroke="url(#s-cyan)" stroke-opacity="0.75" />
        <path class="bag-vortex" d="M32 50C34 44 38 40 44 38C50 36 57 38 61 43C65 48 65 55 62 60C58 66 51 69 44 68C39 67 35 64 33 59" stroke="url(#s-cyan)" stroke-width="1.5" />
        <path class="bag-flow f1" d="M14 42L30 50" stroke="url(#s-cyan)" stroke-width="1.4" />
        <path class="bag-flow f2" d="M20 70L34 60" stroke="url(#s-cyan)" stroke-width="1.4" />
        <path class="bag-flow f3" d="M86 38L68 48" stroke="url(#s-cyan)" stroke-width="1.4" />
        <circle cx="13" cy="42" r="3" fill="url(#s-soft)" stroke="url(#s-cyan)" />
        <rect x="16" y="66" width="6" height="6" rx="1.2" fill="url(#s-soft)" stroke="url(#s-cyan)" />
        <polygon points="87,36 91,42 84,43" fill="url(#s-soft)" stroke="url(#s-cyan)" />
      </template>
    </svg>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  graphicKey: "chat" | "file" | "notes" | "podcast" | "quiz" | "cards" | "wrong" | "records" | "speaking" | "bag";
}>();
</script>

<style scoped>
.student-card-graphic {
  position: absolute;
  inset: 8px 8px 102px 8px;
  border-radius: 14px;
  overflow: hidden;
}

.student-card-graphic-svg {
  width: 100%;
  height: 100%;
  filter: drop-shadow(0 10px 28px rgba(16, 185, 129, 0.22));
}

.bit-flow {
  font-size: 5px;
  fill: rgba(16, 185, 129, 0.75);
  letter-spacing: 0.4px;
}

.graphic-chat .orbit-a { transform-origin: 50% 50%; animation: rotate-ccw 14s linear infinite; }
.graphic-chat .orbit-b { transform-origin: 50% 50%; animation: rotate-cw 10s linear infinite; }
.graphic-chat .spark { animation: pulse 2s ease-in-out infinite; }
.graphic-chat .s2 { animation-delay: .4s; }
.graphic-chat .s3 { animation-delay: .8s; }

.graphic-file .file-pane { animation: float-y 4s ease-in-out infinite; }
.graphic-file .fp2 { animation-delay: .25s; }
.graphic-file .fp3 { animation-delay: .45s; }
.graphic-file .file-beam { animation: beam 2.1s ease-in-out infinite; }
.graphic-file .bit-flow { animation: bits 2s linear infinite; }

.graphic-notes .note-star { transform-origin: 52px 50px; animation: pulse 2.4s ease-in-out infinite; }
.graphic-notes .note-map { stroke-dasharray: 4 4; animation: dash 3.2s linear infinite; }

.graphic-podcast .ring-1 { transform-origin: 50% 50%; animation: wobble 4.5s ease-in-out infinite; }
.graphic-podcast .ring-2 { transform-origin: 50% 50%; animation: wobble 3.6s ease-in-out infinite reverse; }
.graphic-podcast .pod-ripple { animation: ripple 2.6s ease-out infinite; }
.graphic-podcast .rp2 { animation-delay: .8s; }

.graphic-quiz .quiz-arrow { animation: nudge 2s ease-in-out infinite; }
.graphic-quiz .quiz-progress { transform-origin: 50% 50%; animation: rotate-cw 8s linear infinite; }
.graphic-quiz .q2 { animation-direction: reverse; animation-duration: 10s; }

.graphic-cards .card-spin { transform-origin: 50% 50%; animation: cards-spin 6s linear infinite; }
.graphic-cards .cs2 { animation-delay: .6s; }
.graphic-cards .cs3 { animation-delay: 1.1s; }
.graphic-cards .card-spiral { stroke-dasharray: 5 5; animation: dash 4s linear infinite; }

.graphic-wrong .scan-line { animation: scan 2.1s ease-in-out infinite; }

.graphic-records .records-bar { transform-origin: bottom center; animation: grow 2.3s ease-in-out infinite; }
.graphic-records .rb2 { animation-delay: .35s; }
.graphic-records .rb3 { animation-delay: .7s; }
.graphic-records .records-trend { stroke-dasharray: 3 4; animation: dash 4.5s linear infinite; }

.graphic-speaking .speak-wave { animation: pulse 1.8s ease-in-out infinite; }
.graphic-speaking .speak-star { animation: twinkle 1.6s ease-in-out infinite; }
.graphic-speaking .st2 { animation-delay: .5s; }

.graphic-bag .bag-vortex { transform-origin: 50% 50%; animation: rotate-cw 7s linear infinite; }
.graphic-bag .bag-flow { animation: pull 1.9s ease-in-out infinite; }
.graphic-bag .f2 { animation-delay: .4s; }
.graphic-bag .f3 { animation-delay: .8s; }

@keyframes rotate-cw { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
@keyframes rotate-ccw { from { transform: rotate(0deg); } to { transform: rotate(-360deg); } }
@keyframes pulse { 0%,100% { opacity: .65; transform: scale(1); } 50% { opacity: 1; transform: scale(1.08); } }
@keyframes float-y { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-1.8px); } }
@keyframes beam { 0%,100% { opacity: .45; } 50% { opacity: .95; } }
@keyframes bits { 0% { transform: translateY(0); } 100% { transform: translateY(18px); } }
@keyframes wobble { 0%,100% { transform: scale(1); } 50% { transform: scale(1.04) rotate(2deg); } }
@keyframes ripple { 0% { opacity: .5; } 100% { opacity: 0; transform: scale(1.12); } }
@keyframes nudge { 0%,100% { transform: translateX(0); } 50% { transform: translateX(2px); } }
@keyframes cards-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
@keyframes scan { 0%,100% { transform: translateY(-5px); opacity: .5; } 50% { transform: translateY(5px); opacity: 1; } }
@keyframes grow { 0%,100% { transform: scaleY(.8); opacity: .8; } 50% { transform: scaleY(1.07); opacity: 1; } }
@keyframes twinkle { 0%,100% { opacity: .5; transform: scale(.9); } 50% { opacity: 1; transform: scale(1.15); } }
@keyframes pull { 0%,100% { opacity: .6; } 50% { opacity: 1; } }
@keyframes dash { to { stroke-dashoffset: -24; } }

@media (prefers-reduced-motion: reduce) {
  .student-card-graphic-svg * {
    animation: none !important;
  }
}

@media (min-width: 768px) {
  .student-card-graphic {
    inset: 10px 10px 116px 10px;
  }
}
</style>