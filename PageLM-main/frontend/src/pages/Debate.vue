<template>
  <div v-if="!debateId" class="flex flex-col items-center justify-center min-h-screen w-full px-4 lg:pl-28 lg:pr-4 bg-[color:var(--app-bg-1)] text-[color:var(--app-text)]">
    <div class="max-w-2xl w-full space-y-8">
      <div class="text-center space-y-4">
        <h1 class="text-4xl lg:text-5xl font-bold text-[color:var(--app-text)]">开始辩论</h1>
        <p class="text-lg text-stone-400">在任何主题上与AI进行结构化辩论</p>
      </div>

      <div class="bg-[color:var(--glass-bg)] backdrop-blur-xl border border-[color:var(--glass-border)] rounded-2xl p-8 space-y-6 shadow-[0_18px_40px_rgba(15,23,42,0.25)]">
        <div>
          <label class="block text-sm font-medium text-stone-300 mb-2">辩论主题</label>
          <input
            v-model="topic"
            type="text"
            placeholder="例如：人工智能在教育中的利与弊"
            class="w-full px-4 py-3 bg-[color:var(--app-bg-2)] border border-[color:var(--glass-border)] rounded-xl text-[color:var(--app-text)] placeholder-stone-500 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent"
            @keydown.enter.exact.prevent="startDebate"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-stone-300 mb-3">您的立场</label>
          <div class="flex gap-4">
            <button
              type="button"
              :class="[
                'flex-1 py-4 px-6 rounded-xl font-semibold transition-all',
                position === 'for'
                  ? 'bg-gradient-to-r from-emerald-500/90 to-emerald-600 text-white shadow-lg shadow-emerald-500/30 border border-emerald-400/30'
                  : 'bg-[color:var(--app-bg-2)] border border-[color:var(--glass-border)] text-stone-400 hover:bg-[color:var(--nav-hover-bg-strong)]'
              ]"
              @click="position = 'for'"
            >
              <div class="flex items-center justify-center gap-2">
                <svg class="size-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 10.5 10.5 8.25l2.25 2.25 3.75-3.75" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 21h11.25a2.25 2.25 0 0 0 2.25-2.25V10.5a2.25 2.25 0 0 0-2.25-2.25H13.5" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 21V8.25A2.25 2.25 0 0 1 8.25 6h3" />
                </svg>
                <div>
                  <div>支持</div>
                  <div class="text-xs mt-1 opacity-80">支持该主题</div>
                </div>
              </div>
            </button>
            <button
              type="button"
              :class="[
                'flex-1 py-4 px-6 rounded-xl font-semibold transition-all',
                position === 'against'
                  ? 'bg-gradient-to-r from-rose-500/90 to-rose-600 text-white shadow-lg shadow-rose-500/30 border border-rose-400/30'
                  : 'bg-[color:var(--app-bg-2)] border border-[color:var(--glass-border)] text-stone-400 hover:bg-[color:var(--nav-hover-bg-strong)]'
              ]"
              @click="position = 'against'"
            >
              <div class="flex items-center justify-center gap-2">
                <svg class="size-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 13.5 13.5 15.75 11.25 13.5 7.5 17.25" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 3h11.25A2.25 2.25 0 0 1 19.5 5.25V13.5a2.25 2.25 0 0 1-2.25 2.25H13.5" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 3v12.75A2.25 2.25 0 0 0 8.25 18h3" />
                </svg>
                <div>
                  <div>反对</div>
                  <div class="text-xs mt-1 opacity-80">反对该主题</div>
                </div>
              </div>
            </button>
          </div>
        </div>

        <button
          type="button"
          class="w-full py-4 bg-gradient-to-r from-cyan-500 to-purple-600 hover:from-cyan-400 hover:to-purple-500 disabled:from-[color:var(--app-bg-2)] disabled:to-[color:var(--app-bg-2)] disabled:text-stone-400 disabled:border disabled:border-[color:var(--glass-border)] disabled:cursor-not-allowed text-white font-bold rounded-xl transition-all shadow-lg"
          :disabled="!topic.trim()"
          @click="startDebate"
        >
          开始辩论
        </button>
      </div>

      <div v-if="error" class="bg-red-900/20 border border-red-800 rounded-xl p-4 text-red-400">
        {{ error }}
      </div>
    </div>
  </div>

  <div v-else class="flex flex-col h-screen w-full lg:pl-28 bg-[color:var(--app-bg-1)] text-[color:var(--app-text)]">
    <div class="flex-shrink-0 border-b border-zinc-900 bg-stone-950/90 backdrop-blur-sm">
      <div class="px-6 py-4">
        <div class="flex items-center justify-between">
          <div class="flex-1">
            <h1 class="text-xl font-bold text-[color:var(--app-text)] mb-1">{{ session?.topic || '辩论' }}</h1>
            <div class="flex items-center gap-3 text-sm">
              <span
                :class="[
                  'px-3 py-1 rounded-full font-semibold',
                  session?.position === 'for'
                    ? 'bg-green-600/20 text-green-400 border border-green-600/30'
                    : 'bg-red-600/20 text-red-400 border border-red-600/30'
                ]"
              >
                您：{{ session?.position === 'for' ? '支持' : '反对' }}
              </span>
              <span class="text-stone-500">对决</span>
              <span class="px-3 py-1 rounded-full font-semibold bg-purple-600/20 text-purple-400 border border-purple-600/30">
                AI：{{ session?.position === 'for' ? '反对' : '支持' }}
              </span>
            </div>
          </div>
          <button
            type="button"
            class="px-4 py-2 bg-stone-900/70 border border-zinc-800 hover:bg-stone-800 text-stone-300 rounded-lg transition-colors"
            @click="resetDebate"
          >
            新辩论
          </button>
        </div>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto px-6 py-6 space-y-6 custom-scroll">
      <div v-if="messages.length === 0 && !isStreaming" class="flex items-center justify-center h-full">
        <div class="text-center space-y-4 max-w-md">
          <div class="mx-auto size-16 rounded-full bg-gradient-to-br from-sky-600/30 to-indigo-600/30 flex items-center justify-center">
            <svg class="size-8 text-sky-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v18M6 7h12M5 11h14M6 15h12M8 19h8" />
            </svg>
          </div>
          <h2 class="text-2xl font-bold text-[color:var(--app-text)] animate-[fadeIn_0.6s_ease-in-out]">准备辩论！</h2>
          <p class="text-stone-400 animate-[fadeIn_0.7s_ease-in-out]">请在下方陈述您的开场论点。AI将以反驳论点回应。</p>
        </div>
      </div>

      <div
        v-for="(msg, idx) in messages"
        :key="idx"
        :class="['flex', msg.role === 'user' ? 'justify-end animate-[slideInRight_0.3s_ease-out]' : 'justify-start animate-[slideInLeft_0.3s_ease-out]']"
      >
        <div :class="['max-w-3xl flex flex-col gap-2', msg.role === 'user' ? 'items-end' : 'items-start']">
          <div class="flex items-center gap-2">
            <div
              v-if="msg.role === 'assistant'"
              class="w-8 h-8 rounded-full bg-gradient-to-br from-purple-600 to-purple-700 flex items-center justify-center text-white font-bold shadow-lg"
            >
              AI
            </div>
            <span class="text-sm font-semibold text-stone-400">{{ msg.role === 'user' ? '您' : 'AI对手' }}</span>
            <div
              v-if="msg.role === 'user'"
              :class="[
                'w-8 h-8 rounded-full flex items-center justify-center text-white font-bold shadow-lg',
                session?.position === 'for'
                  ? 'bg-gradient-to-br from-green-600 to-green-700'
                  : 'bg-gradient-to-br from-red-600 to-red-700'
              ]"
            >
              U
            </div>
          </div>
          <div
            :class="[
              'px-6 py-4 rounded-2xl shadow-lg transition-all hover:shadow-xl',
              msg.role === 'user'
                ? session?.position === 'for'
                  ? 'bg-gradient-to-br from-green-600 to-green-700 text-white shadow-green-600/20'
                  : 'bg-gradient-to-br from-red-600 to-red-700 text-white shadow-red-600/20'
                : 'bg-stone-950/90 border border-zinc-900 shadow-[0_10px_30px_rgba(0,0,0,0.45)] ring-1 ring-black/10 backdrop-blur text-[color:var(--app-text)]'
            ]"
          >
            <p class="whitespace-pre-wrap leading-relaxed">{{ msg.content }}</p>
          </div>
        </div>
      </div>

      <div v-if="isStreaming" class="flex justify-start animate-[slideInLeft_0.3s_ease-out]">
        <div class="max-w-3xl items-start flex flex-col gap-2">
          <div class="flex items-center gap-2">
            <div class="w-8 h-8 rounded-full bg-gradient-to-br from-purple-600 to-purple-700 flex items-center justify-center text-white font-bold shadow-lg">
              AI
            </div>
            <span class="text-sm font-semibold text-stone-400">AI对手</span>
          </div>
          <div class="px-6 py-4 rounded-2xl shadow-lg bg-stone-950/90 border border-zinc-900 shadow-[0_10px_30px_rgba(0,0,0,0.45)] ring-1 ring-black/10 backdrop-blur text-[color:var(--app-text)]">
            <p class="whitespace-pre-wrap leading-relaxed">
              {{ streamingContent }}
              <span class="inline-block w-2 h-5 bg-gradient-to-r from-purple-500 to-purple-600 ml-1 animate-pulse rounded-sm" />
            </p>
          </div>
        </div>
      </div>

      <div ref="messagesEndRef" />
    </div>

    <div class="flex-shrink-0 border-t border-zinc-900 bg-stone-950/90 backdrop-blur-sm p-4">
      <div class="max-w-4xl mx-auto">
        <div class="flex gap-3 mb-3">
          <textarea
            ref="textareaRef"
            v-model="argument"
            class="flex-1 px-4 py-3 bg-stone-900/70 border border-zinc-800 rounded-xl text-[color:var(--app-text)] placeholder-stone-500 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent resize-none disabled:opacity-50 disabled:cursor-not-allowed custom-scroll"
            rows="1"
            :disabled="isStreaming || isDebateEnded"
            :placeholder="isDebateEnded ? '辩论已结束' : isStreaming ? 'AI正在回应...' : '输入您的论点...（Shift+Enter换行）'"
            @input="handleTextareaInput"
            @keydown.enter.exact.prevent="handleKeyDown"
            style="min-height: 50px; max-height: 200px;"
          />
          <button
            type="button"
            :disabled="!argument.trim() || isStreaming || isDebateEnded"
            :class="[
              'px-6 py-3 rounded-xl font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg',
              session?.position === 'for'
                ? 'bg-gradient-to-r from-green-600 to-green-700 hover:from-green-500 hover:to-green-600 text-white shadow-green-600/20'
                : 'bg-gradient-to-r from-red-600 to-red-700 hover:from-red-500 hover:to-red-600 text-white shadow-red-600/20'
            ]"
            @click="submitArgument"
          >
            <span v-if="isStreaming" class="flex items-center gap-2">
              <span class="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              等待中...
            </span>
            <span v-else>辩论</span>
          </button>
        </div>
        <div class="flex items-center justify-center">
          <button
            type="button"
            class="px-4 py-2 bg-orange-600/20 hover:bg-orange-600/30 border border-orange-600/40 hover:border-orange-600/60 text-orange-400 hover:text-orange-300 rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed text-sm font-semibold"
            :disabled="isStreaming || messages.length === 0 || isDebateEnded"
            @click="handleSurrender"
          >
            <span class="inline-flex items-center gap-2">
              <svg class="size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4 5.25h9.5c2.623 0 4.75 2.127 4.75 4.75S16.123 14.75 13.5 14.75H4" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M4 3v18" />
              </svg>
              投降
            </span>
          </button>
        </div>
      </div>
    </div>

    <div v-if="isDebateEnded && analysis" class="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-[fadeIn_0.3s_ease-in-out]">
      <div class="bg-stone-950 border border-zinc-900 rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto custom-scroll shadow-2xl animate-[scaleIn_0.3s_ease-out]">
        <div class="p-8 space-y-6">
          <div class="text-center space-y-4">
            <div class="mx-auto size-16 rounded-full bg-stone-900 flex items-center justify-center">
              <component :is="winnerIcon" class="size-8 text-sky-300" />
            </div>
            <h2 class="text-3xl font-bold text-[color:var(--app-text)]">
              {{ analysis.winner === 'user' ? '您赢了！' : analysis.winner === 'ai' ? 'AI赢了！' : '平局！' }}
            </h2>
            <p class="text-lg text-stone-400">{{ analysis.reason }}</p>
          </div>

          <div class="bg-stone-900/50 border border-zinc-800 rounded-xl p-6">
            <h3 class="text-xl font-bold text-[color:var(--app-text)] mb-3 flex items-center gap-2">
              <svg class="size-5 text-sky-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 3v18h18" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M7 14l3-3 3 2 4-5" />
              </svg>
              总体评估
            </h3>
            <p class="text-stone-300 leading-relaxed">{{ analysis.overallAssessment }}</p>
          </div>

          <div class="grid md:grid-cols-2 gap-6">
            <div class="space-y-4">
              <div class="bg-green-900/20 border border-green-800/30 rounded-xl p-5">
                <h3 class="text-lg font-bold text-green-400 mb-3 flex items-center gap-2">
                  <svg class="size-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 3l3.5 6.5L22 10l-5 5.5L18 22l-6-3-6 3 1-6.5L2 10l6.5-.5L12 3z" />
                  </svg>
                  您的优势
                </h3>
                <ul class="space-y-2">
                  <li v-for="(strength, idx) in analysis.userStrengths" :key="`us-${idx}`" class="text-stone-300 text-sm flex items-start gap-2">
                    <span class="text-green-500 mt-0.5">•</span>
                    <span>{{ strength }}</span>
                  </li>
                </ul>
              </div>
              <div v-if="analysis.userWeaknesses.length > 0" class="bg-red-900/20 border border-red-800/30 rounded-xl p-5">
                <h3 class="text-lg font-bold text-red-400 mb-3 flex items-center gap-2">
                  <svg class="size-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v4m0 4h.01" />
                    <path stroke-linecap="round" stroke-linejoin="round" d="M10.29 3.86 1.82 18a2.25 2.25 0 0 0 1.93 3.38h16.5a2.25 2.25 0 0 0 1.93-3.38L13.71 3.86a2.25 2.25 0 0 0-3.42 0z" />
                  </svg>
                  需要改进的方面
                </h3>
                <ul class="space-y-2">
                  <li v-for="(weakness, idx) in analysis.userWeaknesses" :key="`uw-${idx}`" class="text-stone-300 text-sm flex items-start gap-2">
                    <span class="text-red-500 mt-0.5">•</span>
                    <span>{{ weakness }}</span>
                  </li>
                </ul>
              </div>
            </div>

            <div class="space-y-4">
              <div class="bg-purple-900/20 border border-purple-800/30 rounded-xl p-5">
                <h3 class="text-lg font-bold text-purple-400 mb-3 flex items-center gap-2">
                  <svg class="size-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m-3-12a9 9 0 1 1-9 9 9 9 0 0 1 9-9z" />
                  </svg>
                  AI的优势
                </h3>
                <ul class="space-y-2">
                  <li v-for="(strength, idx) in analysis.aiStrengths" :key="`as-${idx}`" class="text-stone-300 text-sm flex items-start gap-2">
                    <span class="text-purple-500 mt-0.5">•</span>
                    <span>{{ strength }}</span>
                  </li>
                </ul>
              </div>
              <div v-if="analysis.aiWeaknesses.length > 0" class="bg-red-900/20 border border-red-800/30 rounded-xl p-5">
                <h3 class="text-lg font-bold text-red-400 mb-3 flex items-center gap-2">
                  <svg class="size-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v4m0 4h.01" />
                    <path stroke-linecap="round" stroke-linejoin="round" d="M10.29 3.86 1.82 18a2.25 2.25 0 0 0 1.93 3.38h16.5a2.25 2.25 0 0 0 1.93-3.38L13.71 3.86a2.25 2.25 0 0 0-3.42 0z" />
                  </svg>
                  AI的弱点
                </h3>
                <ul class="space-y-2">
                  <li v-for="(weakness, idx) in analysis.aiWeaknesses" :key="`aw-${idx}`" class="text-stone-300 text-sm flex items-start gap-2">
                    <span class="text-red-500 mt-0.5">•</span>
                    <span>{{ weakness }}</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>

          <div v-if="analysis.keyMoments.length > 0" class="bg-stone-900/50 border border-zinc-800 rounded-xl p-6">
            <h3 class="text-xl font-bold text-[color:var(--app-text)] mb-4 flex items-center gap-2">
              <svg class="size-5 text-sky-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
              </svg>
              关键时刻
            </h3>
            <ul class="space-y-3">
              <li v-for="(moment, idx) in analysis.keyMoments" :key="`km-${idx}`" class="text-stone-300 flex items-start gap-3">
                <span class="text-sky-500 font-bold text-sm mt-0.5">{{ idx + 1 }}.</span>
                <span>{{ moment }}</span>
              </li>
            </ul>
          </div>

          <div class="flex gap-4 pt-4">
            <button
              type="button"
              class="flex-1 py-3 bg-gradient-to-r from-sky-600 to-blue-600 hover:from-sky-500 hover:to-blue-500 text-white font-bold rounded-xl transition-all shadow-lg"
              @click="resetDebate"
            >
              新辩论
            </button>
            <button
              type="button"
              class="px-6 py-3 bg-stone-900/70 border border-zinc-800 hover:bg-stone-800 text-stone-300 font-semibold rounded-xl transition-colors"
              @click="() => { isDebateEnded = false; analysis = null; }"
            >
              查看辩论
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="isAnalyzing && !analysis" class="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50">
      <div class="bg-stone-950 border border-zinc-900 rounded-2xl p-8 text-center space-y-4 min-w-[300px]">
        <div class="w-16 h-16 border-4 border-sky-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
        <p class="text-[color:var(--app-text)] font-semibold">正在分析辩论...</p>
        <p v-if="analysisPhase" class="text-sky-400 text-sm animate-pulse">{{ analysisPhase }}</p>
      </div>
    </div>

    <div v-if="error" class="fixed bottom-20 right-6 bg-red-900/90 border border-red-700 rounded-xl p-4 text-red-200 shadow-lg max-w-md">
      <div class="flex items-start gap-3">
        <svg class="size-5 text-red-200" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v4m0 4h.01" />
          <path stroke-linecap="round" stroke-linejoin="round" d="M10.29 3.86 1.82 18a2.25 2.25 0 0 0 1.93 3.38h16.5a2.25 2.25 0 0 0 1.93-3.38L13.71 3.86a2.25 2.25 0 0 0-3.42 0z" />
        </svg>
        <div class="flex-1">{{ error }}</div>
        <button type="button" class="text-red-200 hover:text-red-100" @click="error = null">
          <svg class="size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { env } from "../config/env";
import { getAuthToken } from "../lib/auth";

type DebateMessage = { role: "user" | "assistant"; content: string; timestamp: number };

type DebateSession = {
  id: string;
  topic: string;
  position: "for" | "against";
  messages: DebateMessage[];
  createdAt: number;
  status?: "active" | "user_surrendered" | "ai_conceded" | "completed";
  winner?: "user" | "ai" | "draw";
};

type DebateAnalysis = {
  winner: "user" | "ai" | "draw";
  reason: string;
  userStrengths: string[];
  aiStrengths: string[];
  userWeaknesses: string[];
  aiWeaknesses: string[];
  keyMoments: string[];
  overallAssessment: string;
};

const route = useRoute();
const router = useRouter();

const topic = ref("");
const position = ref<"for" | "against">("for");
const debateId = ref<string | null>((route.query.debateId as string) || null);
const session = ref<DebateSession | null>(null);
const messages = ref<DebateMessage[]>([]);
const argument = ref("");
const isStreaming = ref(false);
const streamingContent = ref("");
const error = ref<string | null>(null);
const isDebateEnded = ref(false);
const analysis = ref<DebateAnalysis | null>(null);
const isAnalyzing = ref(false);
const analysisPhase = ref("");

const wsRef = ref<WebSocket | null>(null);
const analysisWsRef = ref<WebSocket | null>(null);
const messagesEndRef = ref<HTMLDivElement | null>(null);
const textareaRef = ref<HTMLTextAreaElement | null>(null);

const backendBase = env.backend.replace(/\/$/, "");

const authHeaders = () => {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const token = getAuthToken();
  if (token) headers.authorization = `Bearer ${token}`;
  return headers;
};

const wsUrl = (path: string, params: Record<string, string> = {}) => {
  const base = new URL(backendBase);
  const proto = base.protocol === "https:" ? "wss:" : "ws:";
  const url = new URL(`${proto}//${base.host}${path}`);
  const token = getAuthToken();
  if (token) url.searchParams.set("token", token);
  for (const [key, value] of Object.entries(params)) {
    if (value) url.searchParams.set(key, value);
  }
  return url.toString();
};

const winnerIcon = computed(() => {
  if (analysis.value?.winner === "user") {
    return {
      template: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M8 5h8v3a4 4 0 0 1-8 0V5Z" /><path stroke-linecap="round" stroke-linejoin="round" d="M6 5H4a2 2 0 0 0 2 2m12-2h2a2 2 0 0 1-2 2" /><path stroke-linecap="round" stroke-linejoin="round" d="M12 12v4m-4 3h8" /></svg>`,
    };
  }
  if (analysis.value?.winner === "ai") {
    return {
      template: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9 10h6M9 14h6" /><path stroke-linecap="round" stroke-linejoin="round" d="M12 3a3 3 0 0 0-3 3v1H7a2 2 0 0 0-2 2v6a4 4 0 0 0 4 4h6a4 4 0 0 0 4-4V9a2 2 0 0 0-2-2h-2V6a3 3 0 0 0-3-3Z" /></svg>`,
    };
  }
  return {
    template: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M7 12a5 5 0 0 1 10 0" /><path stroke-linecap="round" stroke-linejoin="round" d="M4 14a8 8 0 0 1 16 0" /><path stroke-linecap="round" stroke-linejoin="round" d="M8 18h8" /></svg>`,
  };
});

const scrollToBottom = async () => {
  await nextTick();
  messagesEndRef.value?.scrollIntoView({ behavior: "smooth" });
};

watch([messages, streamingContent], () => {
  scrollToBottom();
});

watch(
  () => route.query.debateId,
  (next) => {
    debateId.value = (next as string) || null;
  }
);

watch(
  debateId,
  (next) => {
    if (next) {
      fetchDebateSession(next);
      connectWebSocket(next);
    }
  },
  { immediate: true }
);

const fetchDebateSession = async (id: string) => {
  try {
    const response = await fetch(`${backendBase}/debate/${id}`, {
      headers: authHeaders(),
    });
    const data = await response.json();
    if (data.ok) {
      session.value = data.session;
      messages.value = data.session.messages;
    } else {
      error.value = data.error || "加载辩论会话失败";
    }
  } catch (err: any) {
    error.value = err.message || "加载辩论会话失败";
  }
};

const connectWebSocket = (id: string) => {
  if (wsRef.value) wsRef.value.close();
  const ws = new WebSocket(wsUrl("/ws/debate", { debateId: id }));

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    switch (data.type) {
      case "user_argument":
        messages.value = [...messages.value, { role: "user", content: data.content, timestamp: Date.now() }];
        break;
      case "ai_thinking":
        isStreaming.value = true;
        streamingContent.value = "";
        break;
      case "ai_token":
        streamingContent.value = streamingContent.value + data.token;
        break;
      case "ai_complete":
        messages.value = [...messages.value, { role: "assistant", content: data.content, timestamp: Date.now() }];
        isStreaming.value = false;
        streamingContent.value = "";
        break;
      case "ai_concede":
        messages.value = [
          ...messages.value,
          { role: "assistant", content: `我必须承认在这场辩论中失败了。${data.reason}`, timestamp: Date.now() },
        ];
        isStreaming.value = false;
        streamingContent.value = "";
        isDebateEnded.value = true;
        setTimeout(() => fetchAnalysis(), 1000);
        break;
      case "error":
        error.value = data.error;
        isStreaming.value = false;
        streamingContent.value = "";
        break;
    }
  };

  ws.onerror = () => {
    error.value = "连接错误";
  };

  wsRef.value = ws;
};

const startDebate = async () => {
  if (!topic.value.trim()) return;

  try {
    const response = await fetch(`${backendBase}/debate/start`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ topic: topic.value.trim(), position: position.value }),
    });

    const data = await response.json();
    if (data.ok) {
      debateId.value = data.debateId;
      session.value = data.session;
      messages.value = [];
      router.push({ path: "/debate", query: { debateId: data.debateId } });
    } else {
      error.value = data.error || "开始辩论失败";
    }
  } catch (err: any) {
    error.value = err.message || "开始辩论失败";
  }
};

const submitArgument = async () => {
  if (!argument.value.trim() || !debateId.value || isStreaming.value) return;

  const userArgument = argument.value.trim();
  argument.value = "";

  if (textareaRef.value) textareaRef.value.style.height = "auto";

  try {
    const response = await fetch(`${backendBase}/debate/${debateId.value}/argue`, {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ argument: userArgument }),
    });

    const data = await response.json();
    if (!data.ok) error.value = data.error || "提交论点失败";
  } catch (err: any) {
    error.value = err.message || "提交论点失败";
  }
};

const handleTextareaInput = (e: Event) => {
  const el = e.target as HTMLTextAreaElement;
  el.style.height = "auto";
  el.style.height = `${el.scrollHeight}px`;
};

const handleKeyDown = () => {
  submitArgument();
};

const handleSurrender = async () => {
  if (!debateId.value || isDebateEnded.value) return;
  if (!window.confirm("您确定要投降吗？")) return;

  try {
    const response = await fetch(`${backendBase}/debate/${debateId.value}/surrender`, {
      method: "POST",
      headers: authHeaders(),
    });

    const data = await response.json();
    if (data.ok) {
      isDebateEnded.value = true;
      fetchAnalysis();
    } else {
      error.value = data.error || "投降失败";
    }
  } catch (err: any) {
    error.value = err.message || "投降失败";
  }
};

const fetchAnalysis = async () => {
  if (!debateId.value) return;

  isAnalyzing.value = true;
  analysisPhase.value = "开始分析...";

  if (analysisWsRef.value) analysisWsRef.value.close();
  const analysisWs = new WebSocket(wsUrl("/ws/debate/analyze", { debateId: debateId.value || "" }));

  analysisWs.onmessage = (event) => {
    const data = JSON.parse(event.data);
    switch (data.type) {
      case "phase":
        analysisPhase.value = data.value;
        break;
      case "complete":
        analysis.value = data.analysis;
        session.value = data.session;
        isAnalyzing.value = false;
        analysisPhase.value = "";
        analysisWs.close();
        break;
      case "error":
        error.value = data.error;
        isAnalyzing.value = false;
        analysisPhase.value = "";
        analysisWs.close();
        break;
    }
  };

  analysisWs.onerror = () => {
    error.value = "分析连接错误";
    isAnalyzing.value = false;
    analysisPhase.value = "";
  };

  analysisWsRef.value = analysisWs;

  try {
    const response = await fetch(`${backendBase}/debate/${debateId.value}/analyze`, {
      method: "POST",
      headers: authHeaders(),
    });

    const data = await response.json();
    if (!data.ok && data.error) {
      error.value = data.error;
      isAnalyzing.value = false;
      analysisPhase.value = "";
      analysisWs.close();
    }
  } catch (err: any) {
    error.value = err.message || "开始分析失败";
    isAnalyzing.value = false;
    analysisPhase.value = "";
    analysisWs.close();
  }
};

const resetDebate = () => {
  debateId.value = null;
  session.value = null;
  messages.value = [];
  isDebateEnded.value = false;
  analysis.value = null;
  router.push("/debate");
};

onMounted(scrollToBottom);

onBeforeUnmount(() => {
  if (wsRef.value) wsRef.value.close();
  if (analysisWsRef.value) analysisWsRef.value.close();
});
</script>
