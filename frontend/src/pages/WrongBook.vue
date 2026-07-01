<template>
  <div class="feature-shell">
    <div class="feature-frame">
      <div class="feature-stack custom-scroll space-y-8">
        <header class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div class="space-y-2">
            <div class="inline-flex items-center gap-2 rounded-full border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 px-3 py-1 text-xs text-[color:var(--nav-text-muted)]">
              <span class="size-2 rounded-full bg-emerald-400"></span>
              错题本 · 复习与掌握中心
            </div>
            <h1 class="text-2xl md:text-3xl font-semibold text-[color:var(--app-text)]">错题集中复盘与知识掌握仪表板</h1>
            <p class="text-sm md:text-base text-[color:var(--nav-text-muted)] max-w-2xl">
              汇总测验错题与已掌握题目，快速定位薄弱知识点，生成个性化提升报告，持续优化你的复习路径。
            </p>
          </div>
          <div class="flex flex-wrap items-center gap-3">
            <button
              type="button"
              class="px-4 py-2 rounded-2xl border border-rose-400/40 bg-rose-500/10 text-black text-sm font-semibold hover:bg-rose-500/20 transition-colors cursor-pointer"
              @click="openPractice('wrong')"
            >
              错题复习 · {{ wrongQuestions.length }} 题
            </button>
            <button
              type="button"
              class="px-4 py-2 rounded-2xl border border-emerald-400/40 bg-emerald-500/10 text-black text-sm font-semibold hover:bg-emerald-500/20 transition-colors cursor-pointer"
              @click="openPractice('mastered')"
            >
              已掌握 · {{ masteredQuestions.length }} 题
            </button>
          </div>
        </header>

        <section class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          <div
            v-for="card in statCards"
            :key="card.title"
            class="glass-card rounded-3xl p-4 border border-[color:var(--glass-border)] shadow-[0_14px_32px_rgba(0,0,0,0.25)]"
          >
            <div class="flex items-start justify-between">
              <div>
                <div class="text-xs uppercase tracking-wide text-[color:var(--nav-text-muted)]">{{ card.title }}</div>
                <div class="mt-2 text-2xl font-semibold text-[color:var(--app-text)]">{{ card.value }}</div>
                <div class="mt-2 text-xs text-[color:var(--nav-text-muted)]">{{ card.note }}</div>
              </div>
              <span :class="card.tone" class="size-10 rounded-2xl flex items-center justify-center">
                <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                  <path stroke-linecap="round" stroke-linejoin="round" :d="card.icon" />
                </svg>
              </span>
            </div>
          </div>
        </section>

        <section class="grid grid-cols-1 xl:grid-cols-[1.15fr_0.85fr] gap-6">
          <div class="glass-card rounded-3xl p-6 border border-[color:var(--glass-border)] shadow-[0_16px_40px_rgba(15,23,42,0.35)]">
            <div class="flex items-center justify-between">
              <div>
                <h2 class="text-lg font-semibold text-[color:var(--app-text)]">知识掌握仪表板</h2>
                <p class="text-xs text-[color:var(--nav-text-muted)]">对错题占比 + 知识点掌握走势</p>
              </div>
              <button class="text-xs px-3 py-1.5 rounded-full border border-[color:var(--glass-border)] text-[color:var(--nav-text-muted)] hover:bg-white/5 transition-colors cursor-pointer">
                查看历史
              </button>
            </div>

            <div class="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2">
              <div class="relative h-full overflow-hidden rounded-[28px] border border-[color:var(--glass-border)] bg-gradient-to-br from-white/10 via-[color:var(--glass-bg)]/70 to-[color:var(--glass-bg)]/45 p-5">
                <div class="absolute -right-8 -top-10 h-28 w-28 rounded-full bg-rose-400/12 blur-3xl"></div>
                <div class="relative">
                  <div class="flex items-start justify-between gap-4">
                    <div>
                      <div class="text-[11px] uppercase tracking-[0.22em] text-[color:var(--nav-text-muted)]">错题类型占比</div>
                      <div class="mt-1 text-sm font-semibold text-[color:var(--app-text)]">高频失分点分布</div>
                    </div>
                    <span
                      v-if="mistakeBreakdown.length"
                      class="inline-flex items-center rounded-full border border-white/10 bg-white/10 px-2.5 py-1 text-[11px] text-[color:var(--nav-text-muted)]"
                    >
                      TOP {{ mistakeBreakdown[0].name }}
                    </span>
                  </div>

                  <div v-if="mistakeBreakdown.length" class="mt-4 space-y-3">
                    <div
                      v-for="item in mistakeBreakdown"
                      :key="item.name"
                      class="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 backdrop-blur-sm"
                    >
                      <div class="flex items-center justify-between gap-3 text-sm">
                        <div class="flex items-center gap-2">
                          <span class="size-2.5 rounded-full" :class="item.tone"></span>
                          <span class="font-medium text-[color:var(--app-text)]">{{ item.name }}</span>
                        </div>
                        <span class="text-[color:var(--nav-text-muted)]">{{ item.value }}%</span>
                      </div>
                      <div class="mt-2 h-2 rounded-full bg-black/10 overflow-hidden">
                        <div class="h-full rounded-full shadow-[0_0_18px_rgba(255,255,255,0.12)]" :class="item.tone" :style="{ width: item.value + '%' }"></div>
                      </div>
                    </div>
                  </div>

                  <div
                    v-else
                    class="mt-4 rounded-2xl border border-dashed border-white/12 bg-white/5 px-4 py-6 text-center text-sm text-[color:var(--nav-text-muted)]"
                  >
                    暂无错题类型数据
                  </div>
                </div>
              </div>

              <div class="rounded-2xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/60 p-4">
                <div class="text-xs uppercase tracking-wide text-[color:var(--nav-text-muted)]">掌握度</div>
                <div class="mt-4 flex items-center gap-4">
                  <div class="relative size-24">
                    <div
                      class="absolute inset-0 rounded-full"
                      :style="{ background: `conic-gradient(#22c55e ${masteryRate}%, rgba(255,255,255,0.1) 0)` }"
                    ></div>
                    <div class="absolute inset-2 rounded-full bg-[color:var(--app-bg-2)] flex items-center justify-center text-base font-semibold text-[color:var(--app-text)]">
                      {{ masteryRate }}%
                    </div>
                  </div>
                  <div class="space-y-2 text-sm">
                    <div class="text-[color:var(--nav-text-muted)]">最近 14 天正确率趋势</div>
                    <div class="flex items-end gap-1 h-16">
                      <span
                        v-for="(point, idx) in masteryTrend"
                        :key="idx"
                        class="w-3 rounded-full bg-emerald-400/50"
                        :style="{ height: point + '%' }"
                      ></span>
                    </div>
                    <div class="text-xs text-[color:var(--nav-text-muted)]">持续上升 · 建议加入困难题</div>
                  </div>
                </div>
              </div>
            </div>

            <div class="mt-6 rounded-2xl border border-[color:var(--glass-border)] bg-gradient-to-br from-[color:var(--glass-bg)]/80 to-[color:var(--glass-bg)]/40 px-5 pt-4 pb-2">
              <div class="flex items-center justify-between">
                <div>
                  <div class="text-sm font-semibold text-[color:var(--app-text)]">能力雷达图</div>
                  <div class="text-xs text-[color:var(--nav-text-muted)] mt-0.5">基于已掌握题目在 6 个维度的掌握程度</div>
                </div>
                <span class="text-xs px-2 py-1 rounded-full bg-sky-500/15 text-sky-300">满分 100</span>
              </div>
              <div class="mt-2 grid grid-cols-1 md:grid-cols-[1fr_1fr] gap-2 items-center">
                <div ref="radarChartRef" class="w-full" style="height: 220px"></div>
                <div class="grid grid-cols-3 gap-2">
                  <div
                    v-for="item in radarLegend"
                    :key="item.label"
                    class="rounded-xl border border-[color:var(--glass-border)] bg-white/5 px-3 py-2 flex flex-col gap-0.5"
                  >
                    <div class="flex items-center gap-1.5">
                      <span class="size-2 rounded-full" :style="{ backgroundColor: item.color }"></span>
                      <span class="text-xs text-[color:var(--nav-text-muted)]">{{ item.label }}</span>
                    </div>
                    <div class="flex items-end gap-1">
                      <span class="text-base font-bold text-[color:var(--app-text)] leading-none">{{ item.value }}</span>
                      <span class="text-xs text-[color:var(--nav-text-muted)] mb-px">/ 100</span>
                    </div>
                    <div class="h-1.5 rounded-full bg-white/5 overflow-hidden">
                      <div class="h-full rounded-full transition-all" :style="{ width: item.value + '%', backgroundColor: item.color }"></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="mt-6">
              <div class="flex items-center justify-between">
                <div class="text-sm font-semibold text-[color:var(--app-text)]">薄弱知识点热力</div>
                <div class="flex items-center gap-2">
                  <button
                    v-if="!weakPointsLoading && weakPoints.length === 0"
                    type="button"
                    class="text-xs px-3 py-1 rounded-full border border-amber-400/40 bg-amber-500/10 text-black font-semibold hover:bg-amber-500/20 transition-colors cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
                    :disabled="weakPointsLoading || wrongQuestions.length === 0"
                    @click="onAnalyzeWeakPoints"
                  >
                    AI 分析薄弱知识点
                  </button>
                  <button
                    v-else-if="!weakPointsLoading && weakPoints.length > 0"
                    type="button"
                    class="text-xs px-3 py-1 rounded-full border border-[color:var(--glass-border)] text-[color:var(--nav-text-muted)] hover:bg-white/5 transition-colors cursor-pointer"
                    @click="onAnalyzeWeakPoints"
                  >
                    重新分析
                  </button>
                  <button
                    v-if="weakPoints.length > 4"
                    type="button"
                    class="text-xs px-3 py-1 rounded-full border border-[color:var(--glass-border)] text-[color:var(--nav-text-muted)] hover:bg-white/5 transition-colors cursor-pointer"
                    @click="toggleWeakPoints"
                  >
                    {{ weakPointsExpanded ? "收起" : "展开全部" }}
                  </button>
                </div>
              </div>

              <!-- 加载中 -->
              <div v-if="weakPointsLoading" class="mt-4 flex flex-col items-center justify-center py-8 gap-3">
                <div class="size-8 rounded-full border-2 border-amber-400/40 border-t-amber-400 animate-spin"></div>
                <div class="text-sm text-[color:var(--nav-text-muted)]">正在使用 AI 分析错题中的薄弱知识点…</div>
              </div>

              <!-- 无错题提示 -->
              <div v-else-if="wrongQuestions.length === 0" class="mt-4 rounded-2xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/60 p-6 text-center">
                <div class="text-sm text-[color:var(--nav-text-muted)]">暂无错题数据，完成测验后即可分析薄弱知识点。</div>
              </div>

              <!-- 未分析提示 -->
              <div v-else-if="weakPoints.length === 0" class="mt-4 rounded-2xl border border-dashed border-amber-400/30 bg-amber-500/5 p-6 text-center">
                <div class="text-sm text-[color:var(--nav-text-muted)]">
                  当前有 <span class="text-amber-300 font-semibold">{{ wrongQuestions.length }}</span> 道错题待分析，点击上方按钮使用 AI 提取具体薄弱知识点。
                </div>
              </div>

              <!-- 知识点列表 -->
              <div v-else class="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                <div
                  v-for="point in visibleWeakPoints"
                  :key="point.name"
                  class="rounded-2xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/60 p-4"
                >
                  <div class="flex items-start justify-between gap-2">
                    <div class="flex-1 min-w-0">
                      <div class="text-sm font-semibold text-[color:var(--app-text)] leading-snug">{{ point.name }}</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)] mt-0.5">{{ point.category }}</div>
                    </div>
                    <span
                      class="shrink-0 text-xs px-2 py-1 rounded-full font-bold text-black"
                      :class="severityBadgeBg(point.severity)"
                    >
                      {{ severityLabel(point.severity) }}
                    </span>
                  </div>
                  <div class="mt-2 text-xs text-[color:var(--nav-text-muted)] leading-relaxed">{{ point.description }}</div>
                  <div class="mt-3 h-2 rounded-full bg-white/5 overflow-hidden">
                    <div
                      class="h-full rounded-full"
                      :class="severityBar(point.severity)"
                      :style="{ width: Math.min(100, point.wrongCount * 25) + '%' }"
                    ></div>
                  </div>
                  <div class="mt-2 flex items-center justify-between text-xs text-[color:var(--nav-text-muted)]">
                    <span>涉及错题 {{ point.wrongCount }} 道</span>
                  </div>
                  <div class="mt-2 text-xs text-amber-400 font-bold leading-relaxed">💡 {{ point.suggestion }}</div>
                </div>
              </div>
            </div>
          </div>

          <div class="space-y-4">
            <div class="glass-card rounded-3xl p-6 border border-[color:var(--glass-border)] shadow-[0_14px_32px_rgba(0,0,0,0.3)]">
              <div class="flex items-center justify-between">
                <h3 class="text-lg font-semibold text-[color:var(--app-text)]">错题分析提升报告</h3>
                <span class="text-xs px-2 py-1 rounded-full bg-sky-500/15 text-sky-200">Agent</span>
              </div>
              <p class="mt-2 text-sm text-[color:var(--nav-text-muted)]">
                基于每道错题的具体内容与知识点，深入分析薄弱环节并给出针对性提升措施。
              </p>
              <div class="mt-4 space-y-3">
                <div v-for="item in reportHighlights" :key="item.title" class="rounded-2xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/60 p-3">
                  <div class="text-sm font-semibold text-[color:var(--app-text)]">{{ item.title }}</div>
                  <div class="text-xs text-[color:var(--nav-text-muted)]">{{ item.desc }}</div>
                </div>
              </div>
              <button
                class="mt-5 w-full px-4 py-2 rounded-2xl bg-gradient-to-r from-sky-400/80 to-cyan-400/80 text-slate-900 text-sm font-semibold shadow-[0_12px_30px_rgba(56,189,248,0.35)] hover:from-sky-300 hover:to-cyan-300 transition-colors cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
                :disabled="reportLoading"
                @click="onGenerateReport"
              >
                {{ reportLoading ? "正在生成报告…" : "生成分析提升报告" }}
              </button>

              <div v-if="reportHistory.length" class="mt-4 space-y-2">
                <div class="text-xs text-[color:var(--nav-text-muted)]">历史报告</div>
                <div v-for="item in reportHistory" :key="item.id" class="flex items-center justify-between rounded-2xl border-2 border-[color:var(--glass-border)] bg-white/5 px-3 py-2">
                  <div class="text-xs text-[color:var(--nav-text-muted)]">{{ formatTime(item.createdAt) }}</div>
                  <div class="flex items-center gap-2">
                    <button
                      type="button"
                      class="text-xs px-2 py-1 rounded-full border border-[color:var(--glass-border)] text-[color:var(--nav-text)] hover:bg-white/5 transition-colors cursor-pointer"
                      @click="openHistoryReport(item.id)"
                    >
                      查看
                    </button>
                    <button
                      type="button"
                      class="text-xs px-2 py-1 rounded-full border border-[color:var(--glass-border)] text-[color:var(--nav-text)] hover:bg-white/5 transition-colors cursor-pointer"
                      @click="downloadReportPdf(item.id)"
                    >
                      下载PDF
                    </button>
                    <button
                      type="button"
                      class="text-xs px-2 py-1 rounded-full border border-rose-400/40 text-rose-300 hover:bg-rose-500/10 transition-colors cursor-pointer"
                      @click="deleteHistoryReport(item.id)"
                    >
                      删除
                    </button>
                  </div>
                </div>
              </div>
            </div>
            <div class="glass-card rounded-3xl p-6 border border-[color:var(--glass-border)] shadow-[0_14px_32px_rgba(0,0,0,0.3)]">
              <h3 class="text-lg font-semibold text-[color:var(--app-text)]">复习节奏建议</h3>
              <ul class="mt-3 space-y-3 text-sm text-[color:var(--nav-text-muted)]">
                <li class="flex items-start gap-2">
                  <span class="mt-1 size-2 rounded-full bg-amber-400"></span>
                  每日安排 15 分钟错题快刷，优先复习高频知识点。
                </li>
                <li class="flex items-start gap-2">
                  <span class="mt-1 size-2 rounded-full bg-emerald-400"></span>
                  每周加入 2 组综合题，巩固已掌握内容。
                </li>
                <li class="flex items-start gap-2">
                  <span class="mt-1 size-2 rounded-full bg-sky-400"></span>
                  错题复习完成后，立刻生成新的测验进行迁移练习。
                </li>
              </ul>
            </div>
          </div>
        </section>

        <section
          v-if="report"
          class="glass-card rounded-3xl p-6 border border-[color:var(--glass-border)] shadow-[0_16px_40px_rgba(0,0,0,0.35)]"
        >
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-semibold text-[color:var(--app-text)]">错题分析提升报告</h3>
            <span class="text-xs px-2 py-1 rounded-full bg-emerald-500/15 text-black font-bold">已生成</span>
          </div>
          <p class="mt-2 text-sm text-[color:var(--nav-text-muted)]">{{ report.overview }}</p>

          <div class="mt-4 grid grid-cols-1 gap-3">
            <div
              v-for="item in report.highlights"
              :key="item.title"
              class="rounded-2xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/60 p-3"
            >
              <div class="text-sm font-semibold text-[color:var(--app-text)]">{{ item.title }}</div>
              <div class="text-xs text-[color:var(--nav-text-muted)]">{{ item.desc }}</div>
            </div>
          </div>

          <div class="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
            <div class="rounded-2xl border border-[color:var(--glass-border)] bg-white/5 p-3">
              <div class="text-xs uppercase tracking-wide text-[color:var(--nav-text-muted)]">优势</div>
              <ul class="mt-2 space-y-1 text-sm text-[color:var(--nav-text-muted)]">
                <li v-for="item in report.strengths" :key="item">{{ item }}</li>
              </ul>
            </div>
            <div class="rounded-2xl border border-[color:var(--glass-border)] bg-white/5 p-3">
              <div class="text-xs uppercase tracking-wide text-[color:var(--nav-text-muted)]">薄弱点</div>
              <ul class="mt-2 space-y-1 text-sm text-[color:var(--nav-text-muted)]">
                <li v-for="item in report.weaknesses" :key="item">{{ item }}</li>
              </ul>
            </div>
          </div>

          <div class="mt-4 rounded-2xl border border-[color:var(--glass-border)] bg-white/5 p-3">
            <div class="text-xs uppercase tracking-wide text-[color:var(--nav-text-muted)]">提升动作</div>
            <ul class="mt-2 space-y-1 text-sm text-[color:var(--nav-text-muted)]">
              <li v-for="item in report.actions" :key="item">{{ item }}</li>
            </ul>
          </div>

          <div class="mt-4 rounded-2xl border border-[color:var(--glass-border)] bg-white/5 p-3">
            <div class="text-xs uppercase tracking-wide text-[color:var(--nav-text-muted)]">每周复习计划</div>
            <ul class="mt-2 space-y-1 text-sm text-[color:var(--nav-text-muted)]">
              <li v-for="item in report.weeklyPlan" :key="item">{{ item }}</li>
            </ul>
          </div>

          <div class="mt-4 grid grid-cols-3 gap-3">
            <div class="rounded-2xl border border-[color:var(--glass-border)] bg-white/5 p-3">
              <div class="text-xs text-[color:var(--nav-text-muted)]">当前正确率</div>
              <div class="mt-1 text-sm font-semibold text-[color:var(--app-text)]">{{ report.metrics.currentAccuracy }}%</div>
            </div>
            <div class="rounded-2xl border border-[color:var(--glass-border)] bg-white/5 p-3">
              <div class="text-xs text-[color:var(--nav-text-muted)]">目标正确率</div>
              <div class="mt-1 text-sm font-semibold text-[color:var(--app-text)]">{{ report.metrics.targetAccuracy }}%</div>
            </div>
            <div class="rounded-2xl border border-[color:var(--glass-border)] bg-white/5 p-3">
              <div class="text-xs text-[color:var(--nav-text-muted)]">建议复习间隔</div>
              <div class="mt-1 text-sm font-semibold text-[color:var(--app-text)]">{{ report.metrics.reviewIntervalDays }} 天</div>
            </div>
          </div>
        </section>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount, ref, watch, nextTick } from "vue";
import { useRouter } from "vue-router";
import * as echarts from "echarts/core";
import { RadarChart } from "echarts/charts";
import { TooltipComponent, LegendComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
echarts.use([RadarChart, TooltipComponent, LegendComponent, CanvasRenderer]);
import {
  analyzeWeakPoints,
  generateWrongBookReport,
  getWrongBookSummary,
  saveQuizAttempts,
  type QuizAttempt,
  type WeakPoint,
  type WrongBookReport,
  type WrongBookSummary,
} from "../lib/api";
import { getUserScopedStorageKey } from "../lib/userStorage";
const router = useRouter();
const loading = ref(true);
const error = ref("");
const summary = ref<WrongBookSummary | null>(null);
const report = ref<WrongBookReport | null>(null);
const reportLoading = ref(false);
const reportHistory = ref<{ id: string; createdAt: number; report: WrongBookReport }[]>([]);
const weakPoints = ref<WeakPoint[]>([]);
const weakPointsLoading = ref(false);
const weakPointsExpanded = ref(false);

const wrongQuestions = computed(() => summary.value?.wrongQuestions || []);
const masteredQuestions = computed(() => summary.value?.masteredQuestions || []);

const masteryRate = computed(() => summary.value?.stats?.masteryRate ?? 0);
const masteryTrend = computed(() => {
  const trend = summary.value?.masteryTrend || [];
  return trend.length ? trend : Array(14).fill(0);
});

const visibleWeakPoints = computed(() =>
  weakPointsExpanded.value ? weakPoints.value : weakPoints.value.slice(0, 4)
);

const radarChartRef = ref<HTMLElement | null>(null);
let radarChart: echarts.ECharts | null = null;

const radarCategories = ["基础知识", "逻辑推演", "计算/实现", "审题分析", "综合应用", "策略/心理"];
const radarColors = ["#38bdf8", "#a78bfa", "#fbbf24", "#34d399", "#fb7185", "#22d3ee"];
const radarDefaults = [35, 30, 28, 32, 25, 20];

const classifyQuestion = (q: { title?: string; explanation?: string; hint?: string; note?: string }) => {
  const text = [q.title || "", q.explanation || "", q.hint || "", q.note || ""].join(" ");
  const rules: Array<[string, string[]]> = [
    ["基础知识", ["概念", "定义", "性质", "原理", "含义", "特征", "规则", "定律", "公理", "基础", "常识", "记忆", "背诵"]],
    ["逻辑推演", ["推理", "因果", "条件", "充分", "必要", "假设", "证明", "结论", "论证", "逻辑", "演绎", "归纳", "反证", "矛盾"]],
    ["计算/实现", ["计算", "数值", "公式", "代入", "求值", "速度", "加速度", "电阻", "压强", "浓度", "方程", "解方程", "运算", "比值"]],
    ["审题分析", ["审题", "题意", "关键词", "条件", "分析", "读题", "理解", "信息", "已知", "求解", "陷阱"]],
    ["综合应用", ["综合", "应用", "实际", "场景", "建模", "转化", "迁移", "跨学科", "实验", "设计", "方案"]],
    ["策略/心理", ["策略", "方法", "技巧", "心理", "粗心", "时间", "取舍", "优先", "检查", "复查", "马虎", "紧张"]],
  ];
  const hits: string[] = [];
  for (const [name, keywords] of rules) {
    if (keywords.some((k) => text.includes(k))) hits.push(name);
  }
  return hits.length > 0 ? hits : ["基础知识"];
};

const radarData = computed(() => {
  const totals: Record<string, number> = {};
  const correct: Record<string, number> = {};
  radarCategories.forEach((c) => { totals[c] = 0; correct[c] = 0; });

  const all = [...wrongQuestions.value, ...masteredQuestions.value];
  all.forEach((q) => {
    const cats = classifyQuestion(q);
    cats.forEach((c) => { totals[c] = (totals[c] || 0) + 1; });
  });
  masteredQuestions.value.forEach((q) => {
    const cats = classifyQuestion(q);
    cats.forEach((c) => { correct[c] = (correct[c] || 0) + 1; });
  });

  const raw = radarCategories.map((c) => {
    const total = totals[c] || 0;
    if (total <= 0) return 0;
    return Math.round((correct[c] / total) * 100);
  });

  // 如果有维度为 0 则使用默认值让图形更好看
  const values = raw.map((v, i) => (v <= 0 ? radarDefaults[i] : v));
  return { labels: radarCategories, values };
});

const radarLegend = computed(() =>
  radarData.value.labels.map((label, idx) => ({
    label,
    value: radarData.value.values[idx] ?? 0,
    color: radarColors[idx % radarColors.length],
  }))
);

const buildRadarOption = () => {
  const values = radarData.value.values;
  return {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "item" as const,
      backgroundColor: "rgba(15,23,42,0.85)",
      borderColor: "rgba(56,189,248,0.3)",
      textStyle: { color: "#e2e8f0", fontSize: 12 },
    },
    radar: {
      indicator: radarCategories.map((name) => ({ name, max: 100 })),
      shape: "polygon" as const,
      radius: "68%",
      center: ["50%", "52%"],
      axisName: {
        color: "rgba(255,255,255,0.85)",
        fontSize: 11,
        fontWeight: 600,
      },
      splitNumber: 5,
      axisLine: { lineStyle: { color: "rgba(255,255,255,0.12)" } },
      splitLine: { lineStyle: { color: "rgba(56,189,248,0.18)", type: "dashed" as const } },
      splitArea: {
        areaStyle: {
          color: [
            "rgba(56,189,248,0.03)",
            "rgba(56,189,248,0.07)",
            "rgba(56,189,248,0.11)",
            "rgba(56,189,248,0.15)",
            "rgba(56,189,248,0.20)",
          ],
        },
      },
    },
    series: [
      {
        type: "radar" as const,
        data: [
          {
            value: values,
            name: "能力值",
            symbol: "circle",
            symbolSize: 6,
            lineStyle: {
              width: 2,
              color: "rgba(56,189,248,0.85)",
              shadowColor: "rgba(56,189,248,0.5)",
              shadowBlur: 8,
            },
            areaStyle: {
              color: {
                type: "radial" as const,
                x: 0.5, y: 0.5, r: 0.5,
                colorStops: [
                  { offset: 0, color: "rgba(56,189,248,0.45)" },
                  { offset: 1, color: "rgba(56,189,248,0.05)" },
                ],
              },
            },
            itemStyle: {
              color: "#38bdf8",
              borderColor: "rgba(56,189,248,0.4)",
              borderWidth: 3,
            },
          },
        ],
        animationDuration: 800,
        animationEasing: "cubicOut" as const,
      },
    ],
  };
};

const initRadarChart = () => {
  if (!radarChartRef.value) return;
  if (radarChart) radarChart.dispose();
  radarChart = echarts.init(radarChartRef.value);
  radarChart.setOption(buildRadarOption());
};

const updateRadarChart = () => {
  if (!radarChart) return;
  radarChart.setOption(buildRadarOption(), true);
};

watch(radarData, () => {
  if (radarChart) updateRadarChart();
});

const breakdownTones = ["bg-rose-400", "bg-amber-400", "bg-sky-400", "bg-emerald-400"];
const mistakeBreakdown = computed(() =>
  (summary.value?.breakdown || []).map((item, idx) => ({
    ...item,
    tone: breakdownTones[idx % breakdownTones.length],
  }))
);

const statCards = computed(() => {
  const stats = summary.value?.stats;
  const wrongCount = stats?.wrongCount ?? 0;
  const masteredCount = stats?.masteredCount ?? 0;
  const mastery = stats?.masteryRate ?? 0;
  const newWrong = stats?.newWrongCount ?? 0;
  const reviewInterval = stats?.reviewIntervalDays ?? 0;
  const weakCount = weakPoints.value.length;
  const intervalLabel = Number.isFinite(reviewInterval) ? reviewInterval.toFixed(1) : "0";

  return [
    {
      title: "待复习错题",
      value: String(wrongCount),
      note: `近 7 天新增 ${newWrong} 题`,
      tone: "bg-rose-500/15 text-rose-200",
      icon: "M12 6v6l4 2",
    },
    {
      title: "已掌握题目",
      value: String(masteredCount),
      note: `掌握率 ${mastery}%`,
      tone: "bg-emerald-500/15 text-emerald-200",
      icon: "M9 12.75 11.25 15 15 9.75",
    },
    {
      title: "薄弱知识点",
      value: String(weakCount),
      note: "高频错题聚焦",
      tone: "bg-amber-500/15 text-amber-200",
      icon: "M12 3.75v16.5m7.5-7.5h-15",
    },
    {
      title: "错题复习节奏",
      value: intervalLabel,
      note: "平均复习间隔/天",
      tone: "bg-sky-500/15 text-sky-200",
      icon: "M6.75 5.25h10.5v13.5H6.75z",
    },
  ];
});

const defaultReportHighlights = [
  {
    title: "最易失分知识点",
    desc: "请先完成错题复盘，系统将自动生成针对性建议。",
  },
  {
    title: "复习策略",
    desc: "建议将错题按知识点分类，进行二刷和变式练习。",
  },
  {
    title: "提升目标",
    desc: "先把高频错题模块提升到 80% 以上正确率。",
  },
];

const reportHighlights = computed(() => report.value?.highlights?.length ? report.value.highlights : defaultReportHighlights);

const quizAttemptsStorageKey = () => getUserScopedStorageKey("quiz:attempts");
const wrongbookSyncStorageKey = () => getUserScopedStorageKey("wrongbook:sync:v1");
const weakPointsCacheStorageKey = () => getUserScopedStorageKey("wrongbook:weak-points:v1");
const reportHistoryStorageKey = () => getUserScopedStorageKey("wrongbook:reports:v1");


const loadSummary = async () => {
  loading.value = true;
  error.value = "";
  try {
    const res = await getWrongBookSummary();
    if (!res || !(res as any).ok) {
      throw new Error((res as any)?.error || "错题数据加载失败");
    }
    summary.value = res;
  } catch (err) {
    error.value = err instanceof Error ? err.message : "错题数据加载失败";
  } finally {
    loading.value = false;
  }
};

const syncLocalAttempts = async () => {
  if (typeof window === "undefined") return;
  const syncKey = wrongbookSyncStorageKey();
  if (localStorage.getItem(syncKey)) return;
  try {
    const raw = localStorage.getItem(quizAttemptsStorageKey());
    if (!raw) return;
    const parsed = JSON.parse(raw) as Record<string, QuizAttempt[]>;
    const entries = Object.entries(parsed || {}).filter(([id, list]) => id && Array.isArray(list) && list.length > 0);
    if (!entries.length) return;
    await Promise.all(entries.map(([id, list]) => saveQuizAttempts(id, list)));
    localStorage.setItem(syncKey, String(Date.now()));
  } catch {
    return;
  }
};

const loadCachedWeakPoints = () => {
  if (typeof window === "undefined") return;
  try {
    const raw = localStorage.getItem(weakPointsCacheStorageKey());
    if (!raw) return;
    const cached = JSON.parse(raw) as { ts: number; points: WeakPoint[] };
    if (cached && Array.isArray(cached.points) && cached.points.length > 0) {
      weakPoints.value = cached.points;
    }
  } catch {
    return;
  }
};

const persistWeakPoints = (points: WeakPoint[]) => {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(weakPointsCacheStorageKey(), JSON.stringify({ ts: Date.now(), points }));
  } catch {
    return;
  }
};

const onAnalyzeWeakPoints = async () => {
  weakPointsLoading.value = true;
  try {
    const res = await analyzeWeakPoints();
    if (!res || !(res as any).ok) {
      throw new Error("分析失败");
    }
    weakPoints.value = res.points || [];
    persistWeakPoints(weakPoints.value);
  } catch {
    weakPoints.value = [];
  } finally {
    weakPointsLoading.value = false;
  }
};

const severityLabel = (s: string) => s === "high" ? "严重" : s === "medium" ? "中等" : "轻微";
const severityBadgeBg = (s: string) => s === "high" ? "bg-rose-500/20" : s === "medium" ? "bg-amber-500/20" : "bg-emerald-500/20";
const severityBar = (s: string) => s === "high" ? "bg-rose-400" : s === "medium" ? "bg-amber-400" : "bg-emerald-400";

const onGenerateReport = async () => {
  reportLoading.value = true;
  try {
    const res = await generateWrongBookReport();
    if (!res || !(res as any).ok) {
      throw new Error("报告生成失败");
    }
    report.value = res.report;
    const item = { id: cryptoRandomId(), createdAt: Date.now(), report: res.report };
    reportHistory.value = [item, ...reportHistory.value].slice(0, 20);
    persistReportHistory();
  } catch {
    report.value = null;
  } finally {
    reportLoading.value = false;
  }
};

const toggleWeakPoints = () => {
  weakPointsExpanded.value = !weakPointsExpanded.value;
};

const loadReportHistory = () => {
  if (typeof window === "undefined") return;
  try {
    const raw = localStorage.getItem(reportHistoryStorageKey());
    const parsed = raw ? (JSON.parse(raw) as { id: string; createdAt: number; report: WrongBookReport }[]) : [];
    reportHistory.value = Array.isArray(parsed) ? parsed : [];
  } catch {
    reportHistory.value = [];
  }
};

const persistReportHistory = () => {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(reportHistoryStorageKey(), JSON.stringify(reportHistory.value));
  } catch {
    return;
  }
};

const openHistoryReport = (id: string) => {
  const found = reportHistory.value.find((item) => item.id === id);
  if (found) report.value = found.report;
};

const deleteHistoryReport = (id: string) => {
  reportHistory.value = reportHistory.value.filter((item) => item.id !== id);
  persistReportHistory();
};

const downloadReportPdf = (id: string) => {
  const found = reportHistory.value.find((item) => item.id === id) || (report.value ? { report: report.value } : null);
  if (!found) return;
  const html = buildReportHtml(found.report);
  const win = window.open("", "_blank");
  if (!win) return;
  win.document.open();
  win.document.write(html);
  win.document.close();
  win.focus();
  win.print();
};

const buildReportHtml = (data: WrongBookReport) => {
  const list = (items: string[]) => items.map((i) => `<li>${escapeHtml(i)}</li>`).join("");
  const highlight = data.highlights.map((h) => `<li><strong>${escapeHtml(h.title)}</strong>：${escapeHtml(h.desc)}</li>`).join("");
  return `<!doctype html>
<html lang="zh">
<head>
  <meta charset="utf-8" />
  <title>错题分析与提升报告</title>
  <style>
    body { font-family: "Microsoft YaHei", Arial, sans-serif; padding: 24px; color: #111827; }
    h1 { font-size: 20px; margin-bottom: 12px; }
    h2 { font-size: 14px; margin-top: 18px; }
    ul { padding-left: 18px; }
    .meta { color: #6b7280; font-size: 12px; }
  </style>
</head>
<body>
  <h1>错题分析与提升报告</h1>
  <div class="meta">生成时间：${new Date().toLocaleString()}</div>
  <p>${escapeHtml(data.overview)}</p>
  <h2>重点摘要</h2>
  <ul>${highlight}</ul>
  <h2>优势</h2>
  <ul>${list(data.strengths)}</ul>
  <h2>薄弱点</h2>
  <ul>${list(data.weaknesses)}</ul>
  <h2>提升动作</h2>
  <ul>${list(data.actions)}</ul>
  <h2>每周复习计划</h2>
  <ul>${list(data.weeklyPlan)}</ul>
  <h2>关键指标</h2>
  <ul>
    <li>当前正确率：${data.metrics.currentAccuracy}%</li>
    <li>目标正确率：${data.metrics.targetAccuracy}%</li>
    <li>建议复习间隔：${data.metrics.reviewIntervalDays} 天</li>
  </ul>
</body>
</html>`;
};

const escapeHtml = (value: string) =>
  (value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");

const cryptoRandomId = () => {
  if (typeof crypto !== "undefined" && crypto.randomUUID) return crypto.randomUUID();
  return `rpt_${Math.random().toString(36).slice(2, 10)}`;
};

const formatTime = (value?: number) => {
  if (!value) return "--";
  return new Date(value).toLocaleString();
};

const openPractice = (mode: "wrong" | "mastered") => {
  router.push({ path: "/wrong-book/practice", query: { mode } });
};

const onResize = () => { radarChart?.resize(); };

onMounted(() => {
  loadReportHistory();
  loadCachedWeakPoints();
  void syncLocalAttempts().finally(() => {
    loadSummary().then(() => nextTick(initRadarChart));
  });
  window.addEventListener("resize", onResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", onResize);
  radarChart?.dispose();
  radarChart = null;
});
</script>
