<template>
  <div class="feature-shell">
    <div class="feature-frame">
      <div class="feature-grid">
        <div class="feature-side">
          <aside class="w-full lg:w-64 min-w-[220px] flex-1 rounded-3xl border border-sky-200/60 dark:border-sky-800/50 bg-gradient-to-br from-sky-50 to-blue-50/90 dark:from-sky-950/50 dark:to-blue-950/40 p-4 shadow-[0_8px_30px_rgba(0,0,0,0.08)] flex flex-col min-h-0 lg:overflow-y-auto overflow-x-hidden custom-scroll lg:pr-1">
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center gap-2 text-sm font-semibold text-[color:var(--app-text)]">
                <span class="inline-flex size-6 items-center justify-center rounded-full bg-violet-500/20 text-violet-400">
                  <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 6.5h15" />
                    <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12h15" />
                    <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 17.5h10.5" />
                  </svg>
                </span>
                教学记录概览
              </div>
              <div class="text-xs text-[color:var(--nav-text-muted)]">共 {{ totalCount }} 条</div>
            </div>
            <div class="grid grid-cols-2 gap-2">
              <div class="rounded-xl border border-[color:var(--glass-border)] bg-[color:var(--app-bg-2)]/60 p-2.5">
                <div class="text-[10px] text-[color:var(--nav-text-muted)]">对话</div>
                <div class="text-base font-semibold text-[color:var(--app-text)]">{{ chats.length }}</div>
              </div>
              <div class="rounded-xl border border-[color:var(--glass-border)] bg-[color:var(--app-bg-2)]/60 p-2.5">
                <div class="text-[10px] text-[color:var(--nav-text-muted)]">教案</div>
                <div class="text-base font-semibold text-[color:var(--app-text)]">{{ lessonPlans.length }}</div>
              </div>
              <div class="rounded-xl border border-[color:var(--glass-border)] bg-[color:var(--app-bg-2)]/60 p-2.5">
                <div class="text-[10px] text-[color:var(--nav-text-muted)]">幻灯片</div>
                <div class="text-base font-semibold text-[color:var(--app-text)]">{{ slides.length }}</div>
              </div>
              <div class="rounded-xl border border-[color:var(--glass-border)] bg-[color:var(--app-bg-2)]/60 p-2.5">
                <div class="text-[10px] text-[color:var(--nav-text-muted)]">视频</div>
                <div class="text-base font-semibold text-[color:var(--app-text)]">{{ videos.length }}</div>
              </div>
              <div class="rounded-xl border border-[color:var(--glass-border)] bg-[color:var(--app-bg-2)]/60 p-2.5">
                <div class="text-[10px] text-[color:var(--nav-text-muted)]">测验</div>
                <div class="text-base font-semibold text-[color:var(--app-text)]">{{ quizzes.length }}</div>
              </div>
              <div class="rounded-xl border border-[color:var(--glass-border)] bg-[color:var(--app-bg-2)]/60 p-2.5">
                <div class="text-[10px] text-[color:var(--nav-text-muted)]">试卷</div>
                <div class="text-base font-semibold text-[color:var(--app-text)]">{{ papers.length }}</div>
              </div>
            </div>
            <div class="mt-3 space-y-3">
              <div class="text-xs text-[color:var(--nav-text-muted)]">
                最常用：<span class="text-[color:var(--app-text)]">{{ mostUsed.label }}</span>
              </div>
              <div class="rounded-xl border border-[color:var(--glass-border)] bg-[color:var(--app-bg-2)]/60 p-3">
                <div class="text-[10px] font-semibold text-[color:var(--app-text)]">使用占比</div>
                <div class="mt-2 flex items-center gap-2">
                  <div class="relative size-20 shrink-0">
                    <svg viewBox="0 0 80 80" class="size-20 -rotate-90" role="img" aria-label="教学方式使用占比">
                      <circle cx="40" cy="40" r="28" fill="none" stroke="rgba(148,163,184,0.2)" stroke-width="8" />
                      <template v-if="usageTotal">
                        <circle
                          v-for="seg in donutSegments"
                          :key="seg.label"
                          cx="40"
                          cy="40"
                          r="28"
                          fill="none"
                          stroke-width="8"
                          stroke-linecap="round"
                          :stroke="seg.color"
                          :stroke-dasharray="seg.dashArray"
                          :stroke-dashoffset="seg.dashOffset"
                        />
                      </template>
                    </svg>
                    <div class="absolute inset-0 flex flex-col items-center justify-center text-[color:var(--app-text)]">
                      <div class="text-sm font-semibold">{{ usageTotal }}</div>
                      <div class="text-[9px] text-[color:var(--nav-text-muted)]">总条数</div>
                    </div>
                  </div>
                  <div class="flex-1 min-w-0 space-y-1">
                    <div v-for="item in usageItems" :key="item.label" class="flex items-center justify-between text-[10px]">
                      <span class="truncate text-[color:var(--app-text)]">{{ item.label }}</span>
                      <span class="text-[color:var(--nav-text-muted)] shrink-0 ml-1">{{ item.percent }}%</span>
                    </div>
                  </div>
                </div>
              </div>
              <div class="rounded-xl border border-[color:var(--glass-border)] bg-[color:var(--app-bg-2)]/60 p-3">
                <div class="text-[10px] font-semibold text-[color:var(--app-text)]">使用次数对比</div>
                <div class="mt-2 space-y-1.5">
                  <div v-for="item in usageItems" :key="item.label" class="flex items-center gap-2">
                    <div class="w-8 text-[9px] text-[color:var(--nav-text-muted)] truncate">{{ item.label }}</div>
                    <div class="flex-1 h-1.5 rounded-full bg-[color:var(--glass-border)] overflow-hidden">
                      <div class="h-full rounded-full transition-[width] duration-300" :style="{ width: item.barWidth, backgroundColor: item.color }" />
                    </div>
                    <div class="w-6 text-right text-[9px] text-[color:var(--nav-text-muted)]">{{ item.count }}</div>
                  </div>
                </div>
              </div>
            </div>
            <div class="mt-2 text-[10px] text-[color:var(--nav-text-muted)]">更新于 {{ lastUpdated }}</div>
          </aside>
        </div>

        <div class="feature-main custom-scroll space-y-6">
          <div class="flex flex-col gap-2">
            <h1 class="text-2xl font-semibold text-[color:var(--app-text)]">教学记录汇</h1>
            <p class="text-sm text-[color:var(--nav-text-muted)]">集中查看对话、教案、幻灯片、教学视频、测验与试卷历史，并用词云洞察教学主题。</p>
          </div>

          <section class="rounded-3xl border border-sky-200/60 dark:border-sky-800/50 bg-gradient-to-br from-sky-50 to-blue-50/90 dark:from-sky-950/50 dark:to-blue-950/40 px-5 py-3.5 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
            <div class="flex items-center justify-between">
              <div>
                <div class="text-sm font-semibold text-[color:var(--app-text)]">主题词云</div>
                <div class="text-xs text-[color:var(--nav-text-muted)]">基于历史记录的标题与主题生成</div>
              </div>
              <button type="button" class="text-xs px-3 py-1.5 rounded-full border border-[color:var(--nav-border)] text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors duration-200 cursor-pointer" @click="refresh">刷新统计</button>
            </div>
            <div v-if="loading" class="mt-6 text-xs text-[color:var(--nav-text-muted)]">正在统计主题…</div>
            <div v-else-if="cloudWords.length" class="mt-6 flex flex-wrap gap-2">
              <button
                v-for="word in cloudWords"
                :key="word.term"
                type="button"
                class="px-2.5 py-1 rounded-full border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors duration-200 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-400/60"
                :style="{ fontSize: word.size, color: word.color }"
                :title="`${word.term} · ${word.count} 次`"
              >
                {{ word.term }}
              </button>
            </div>
            <div v-else class="mt-6 text-xs text-[color:var(--nav-text-muted)]">暂无可统计的主题，先去生成一些教学内容吧。</div>
          </section>

          <section class="rounded-3xl border border-sky-200/60 dark:border-sky-800/50 bg-gradient-to-br from-sky-50 to-blue-50/90 dark:from-sky-950/50 dark:to-blue-950/40 p-5 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
            <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <div class="text-sm font-semibold text-[color:var(--app-text)]">教学趋势</div>
                <div class="text-xs text-[color:var(--nav-text-muted)]">真实历史数据，支持近 7 天 / 30 天切换，并在页面停留期间自动刷新</div>
              </div>
              <div class="flex flex-wrap items-center gap-2">
                <div class="flex items-center rounded-full border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 p-1 text-xs">
                  <button type="button" class="px-3 py-1 rounded-full transition-colors duration-200 cursor-pointer" :class="trendRange === 7 ? 'bg-[color:var(--nav-hover-bg-strong)] text-[color:var(--app-text)]' : 'text-[color:var(--nav-text-muted)]'" @click="setTrendRange(7)">近7天</button>
                  <button type="button" class="px-3 py-1 rounded-full transition-colors duration-200 cursor-pointer" :class="trendRange === 30 ? 'bg-[color:var(--nav-hover-bg-strong)] text-[color:var(--app-text)]' : 'text-[color:var(--nav-text-muted)]'" @click="setTrendRange(30)">近30天</button>
                </div>
                <button type="button" class="text-xs px-3 py-1.5 rounded-full border border-[color:var(--nav-border)] text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors duration-200 cursor-pointer" @click="refresh">更新数据</button>
              </div>
            </div>
            <div class="mt-5 grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div class="rounded-2xl border border-[color:var(--glass-border)] bg-[color:var(--app-bg-2)]/60 p-4">
                <div class="text-xs font-semibold text-[color:var(--app-text)]">教学趋势折线图</div>
                <div class="relative mt-3">
                  <div ref="trendLineChartRef" class="h-44 w-full" role="img" aria-label="教学趋势折线图" />
                  <div
                    v-if="!trendHasData"
                    class="pointer-events-none absolute inset-0 flex flex-col items-center justify-center rounded-2xl border border-dashed border-[color:var(--glass-border)] bg-white/20 px-6 text-center"
                  >
                    <div class="text-sm font-medium text-[color:var(--app-text)]">暂无可视化数据</div>
                    <div class="mt-1 text-xs text-[color:var(--nav-text-muted)]">{{ trendEmptyMessage }}</div>
                  </div>
                </div>
              </div>
              <div class="rounded-2xl border border-[color:var(--glass-border)] bg-[color:var(--app-bg-2)]/60 p-4">
                <div class="text-xs font-semibold text-[color:var(--app-text)]">累计教学量堆叠图</div>
                <div class="relative mt-3">
                  <div ref="stackedChartRef" class="h-44 w-full" role="img" aria-label="教学量堆叠面积图" />
                  <div
                    v-if="!trendHasData"
                    class="pointer-events-none absolute inset-0 flex flex-col items-center justify-center rounded-2xl border border-dashed border-[color:var(--glass-border)] bg-white/20 px-6 text-center"
                  >
                    <div class="text-sm font-medium text-[color:var(--app-text)]">暂无累计趋势</div>
                    <div class="mt-1 text-xs text-[color:var(--nav-text-muted)]">{{ trendEmptyMessage }}</div>
                  </div>
                </div>
                <div class="mt-3 flex flex-wrap gap-2 text-[10px] text-[color:var(--nav-text-muted)]">
                  <div v-for="item in trendLegend" :key="item.label" class="flex items-center gap-1.5">
                    <span class="size-2 rounded-full shrink-0" :style="{ backgroundColor: item.color }" />
                    <span>{{ item.label }}</span>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <section class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2 text-sm font-semibold text-[color:var(--app-text)]">
                  <span class="inline-flex size-6 items-center justify-center rounded-full bg-violet-500/20 text-violet-400">
                    <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.7"><path stroke-linecap="round" stroke-linejoin="round" d="M7 4.5h10a3.5 3.5 0 0 1 3.5 3.5v5a3.5 3.5 0 0 1-3.5 3.5H10l-3.5 3v-3H7A3.5 3.5 0 0 1 3.5 13V8A3.5 3.5 0 0 1 7 4.5Z" /></svg>
                  </span>
                  历史对话
                </div>
                <div class="flex items-center gap-2">
                  <button type="button" class="text-xs px-3 py-1 rounded-full border border-[color:var(--nav-border)] text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors duration-200 cursor-pointer" @click="goTo('/teacher/chat')">查看全部</button>
                  <button type="button" class="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full border border-[color:var(--nav-border)] text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors duration-200 cursor-pointer" @click="toggleSection('chat')">
                    <span>{{ expandedSections.chat ? "收起" : "展开" }}</span>
                    <svg viewBox="0 0 24 24" class="size-3.5" :class="expandedSections.chat ? 'rotate-180' : ''" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 9l6 6 6-6" /></svg>
                  </button>
                </div>
              </div>
              <div v-if="expandedSections.chat" class="mt-3">
                <div v-if="loading" class="text-xs text-[color:var(--nav-text-muted)]">加载中...</div>
                <ul v-else-if="sortedChats.length" class="space-y-2 max-h-64 overflow-y-auto custom-scroll pr-1">
                  <li v-for="item in sortedChats" :key="item.id" class="min-w-0">
                    <button type="button" class="w-full text-left rounded-2xl px-3 py-2 text-sm text-[color:var(--app-text)] bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] border border-[color:var(--nav-border)] transition-colors duration-200 cursor-pointer" @click="openChat(item.id)">
                      <div class="truncate">{{ item.title || "未命名对话" }}</div>
                      <div class="mt-1 text-[10px] text-[color:var(--nav-text-muted)]">{{ formatTime(getItemTime(item)) }}</div>
                    </button>
                  </li>
                </ul>
                <div v-else class="text-xs text-[color:var(--nav-text-muted)]">暂无历史对话</div>
              </div>
            </section>

            <section class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2 text-sm font-semibold text-[color:var(--app-text)]">
                  <span class="inline-flex size-6 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-400">
                    <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.7"><path stroke-linecap="round" stroke-linejoin="round" d="M7 3.5h7l3.5 3.5V18a2.5 2.5 0 0 1-2.5 2.5H7A2.5 2.5 0 0 1 4.5 18V6A2.5 2.5 0 0 1 7 3.5Z" /><path d="M14 3.5V7h3.5" /><path d="m8.5 12 2 2 4-4" /></svg>
                  </span>
                  历史教案
                </div>
                <div class="flex items-center gap-2">
                  <button type="button" class="text-xs px-3 py-1 rounded-full border border-[color:var(--nav-border)] text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors duration-200 cursor-pointer" @click="goTo('/lesson-plan')">查看全部</button>
                  <button type="button" class="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full border border-[color:var(--nav-border)] text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors duration-200 cursor-pointer" @click="toggleSection('lessonPlans')">
                    <span>{{ expandedSections.lessonPlans ? "收起" : "展开" }}</span>
                    <svg viewBox="0 0 24 24" class="size-3.5" :class="expandedSections.lessonPlans ? 'rotate-180' : ''" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 9l6 6 6-6" /></svg>
                  </button>
                </div>
              </div>
              <div v-if="expandedSections.lessonPlans" class="mt-3">
                <div v-if="loading" class="text-xs text-[color:var(--nav-text-muted)]">加载中...</div>
                <ul v-else-if="sortedLessonPlans.length" class="space-y-2 max-h-64 overflow-y-auto custom-scroll pr-1">
                  <li v-for="item in sortedLessonPlans" :key="item.id" class="min-w-0">
                    <button type="button" class="w-full text-left rounded-2xl px-3 py-2 text-sm text-[color:var(--app-text)] bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] border border-[color:var(--nav-border)] transition-colors duration-200 cursor-pointer" @click="openLessonPlan(item.id)">
                      <div class="truncate">{{ item.title || "未命名教案" }}</div>
                      <div class="mt-1 text-[10px] text-[color:var(--nav-text-muted)]">{{ formatTime(getItemTime(item)) }}</div>
                    </button>
                  </li>
                </ul>
                <div v-else class="text-xs text-[color:var(--nav-text-muted)]">暂无历史教案</div>
              </div>
            </section>

            <section class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2 text-sm font-semibold text-[color:var(--app-text)]">
                  <span class="inline-flex size-6 items-center justify-center rounded-full bg-amber-500/20 text-amber-400">
                    <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.7"><path stroke-linecap="round" stroke-linejoin="round" d="M5 4.5h14A2.5 2.5 0 0 1 21.5 7v7A2.5 2.5 0 0 1 19 16.5H5A2.5 2.5 0 0 1 2.5 14V7A2.5 2.5 0 0 1 5 4.5Z" /><path d="M8 19.5h8M10 16.5v3M14 16.5v3" /></svg>
                  </span>
                  历史幻灯片
                </div>
                <div class="flex items-center gap-2">
                  <button type="button" class="text-xs px-3 py-1 rounded-full border border-[color:var(--nav-border)] text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors duration-200 cursor-pointer" @click="goTo('/slides')">查看全部</button>
                  <button type="button" class="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full border border-[color:var(--nav-border)] text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors duration-200 cursor-pointer" @click="toggleSection('slides')">
                    <span>{{ expandedSections.slides ? "收起" : "展开" }}</span>
                    <svg viewBox="0 0 24 24" class="size-3.5" :class="expandedSections.slides ? 'rotate-180' : ''" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 9l6 6 6-6" /></svg>
                  </button>
                </div>
              </div>
              <div v-if="expandedSections.slides" class="mt-3">
                <div v-if="loading" class="text-xs text-[color:var(--nav-text-muted)]">加载中...</div>
                <ul v-else-if="sortedSlides.length" class="space-y-2 max-h-64 overflow-y-auto custom-scroll pr-1">
                  <li v-for="item in sortedSlides" :key="item.id" class="min-w-0">
                    <button type="button" class="w-full text-left rounded-2xl px-3 py-2 text-sm text-[color:var(--app-text)] bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] border border-[color:var(--nav-border)] transition-colors duration-200 cursor-pointer" @click="openSlides(item.id)">
                      <div class="truncate">{{ item.title || "未命名幻灯片" }}</div>
                      <div class="mt-1 text-[10px] text-[color:var(--nav-text-muted)]">页数：{{ item.pageCount ?? 10 }}</div>
                    </button>
                  </li>
                </ul>
                <div v-else class="text-xs text-[color:var(--nav-text-muted)]">暂无历史幻灯片</div>
              </div>
            </section>

            <section class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2 text-sm font-semibold text-[color:var(--app-text)]">
                  <span class="inline-flex size-6 items-center justify-center rounded-full bg-pink-500/20 text-pink-400">
                    <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.7"><path stroke-linecap="round" stroke-linejoin="round" d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z" /></svg>
                  </span>
                  历史教学视频
                </div>
                <div class="flex items-center gap-2">
                  <button type="button" class="text-xs px-3 py-1 rounded-full border border-[color:var(--nav-border)] text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors duration-200 cursor-pointer" @click="goTo('/teaching-video')">查看全部</button>
                  <button type="button" class="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full border border-[color:var(--nav-border)] text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors duration-200 cursor-pointer" @click="toggleSection('videos')">
                    <span>{{ expandedSections.videos ? "收起" : "展开" }}</span>
                    <svg viewBox="0 0 24 24" class="size-3.5" :class="expandedSections.videos ? 'rotate-180' : ''" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 9l6 6 6-6" /></svg>
                  </button>
                </div>
              </div>
              <div v-if="expandedSections.videos" class="mt-3">
                <div v-if="loading" class="text-xs text-[color:var(--nav-text-muted)]">加载中...</div>
                <ul v-else-if="sortedVideos.length" class="space-y-2 max-h-64 overflow-y-auto custom-scroll pr-1">
                  <li v-for="item in sortedVideos" :key="item.id" class="min-w-0">
                    <button type="button" class="w-full text-left rounded-2xl px-3 py-2 text-sm text-[color:var(--app-text)] bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] border border-[color:var(--nav-border)] transition-colors duration-200 cursor-pointer" @click="openVideo(item.id)">
                      <div class="truncate">{{ item.title || "未命名视频" }}</div>
                      <div class="mt-1 text-[10px] text-[color:var(--nav-text-muted)]">{{ formatTime(item.at || 0) }}</div>
                    </button>
                  </li>
                </ul>
                <div v-else class="text-xs text-[color:var(--nav-text-muted)]">暂无历史教学视频</div>
              </div>
            </section>

            <section class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2 text-sm font-semibold text-[color:var(--app-text)]">
                  <span class="inline-flex size-6 items-center justify-center rounded-full bg-blue-500/20 text-blue-400">
                    <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.7"><path stroke-linecap="round" stroke-linejoin="round" d="M12 3.5a6.5 6.5 0 0 0-3.5 11.98V17.5h7v-2.02A6.5 6.5 0 0 0 12 3.5Z" /><path d="M9.5 20.5h5" /></svg>
                  </span>
                  历史测验
                </div>
                <div class="flex items-center gap-2">
                  <button type="button" class="text-xs px-3 py-1 rounded-full border border-[color:var(--nav-border)] text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors duration-200 cursor-pointer" @click="goTo('/teacher/quiz')">查看全部</button>
                  <button type="button" class="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full border border-[color:var(--nav-border)] text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors duration-200 cursor-pointer" @click="toggleSection('quizzes')">
                    <span>{{ expandedSections.quizzes ? "收起" : "展开" }}</span>
                    <svg viewBox="0 0 24 24" class="size-3.5" :class="expandedSections.quizzes ? 'rotate-180' : ''" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 9l6 6 6-6" /></svg>
                  </button>
                </div>
              </div>
              <div v-if="expandedSections.quizzes" class="mt-3">
                <div v-if="loading" class="text-xs text-[color:var(--nav-text-muted)]">加载中...</div>
                <ul v-else-if="sortedQuizzes.length" class="space-y-2 max-h-64 overflow-y-auto custom-scroll pr-1">
                  <li v-for="item in sortedQuizzes" :key="item.id" class="min-w-0">
                    <button type="button" class="w-full text-left rounded-2xl px-3 py-2 text-sm text-[color:var(--app-text)] bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] border border-[color:var(--nav-border)] transition-colors duration-200 cursor-pointer" @click="openQuiz(item.id)">
                      <div class="truncate">{{ item.title || "未命名测验" }}</div>
                      <div class="mt-1 text-[10px] text-[color:var(--nav-text-muted)]">题目数：{{ item.count ?? 5 }}</div>
                    </button>
                  </li>
                </ul>
                <div v-else class="text-xs text-[color:var(--nav-text-muted)]">暂无历史测验</div>
              </div>
            </section>

            <section class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2 text-sm font-semibold text-[color:var(--app-text)]">
                  <span class="inline-flex size-6 items-center justify-center rounded-full bg-teal-500/20 text-teal-400">
                    <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.7"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5v-7.5H8.25v7.5Z" /></svg>
                  </span>
                  历史试卷
                </div>
                <div class="flex items-center gap-2">
                  <button type="button" class="text-xs px-3 py-1 rounded-full border border-[color:var(--nav-border)] text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors duration-200 cursor-pointer" @click="goTo('/teacher/paper')">查看全部</button>
                  <button type="button" class="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full border border-[color:var(--nav-border)] text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors duration-200 cursor-pointer" @click="toggleSection('papers')">
                    <span>{{ expandedSections.papers ? "收起" : "展开" }}</span>
                    <svg viewBox="0 0 24 24" class="size-3.5" :class="expandedSections.papers ? 'rotate-180' : ''" fill="none" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 9l6 6 6-6" /></svg>
                  </button>
                </div>
              </div>
              <div v-if="expandedSections.papers" class="mt-3">
                <div v-if="loading" class="text-xs text-[color:var(--nav-text-muted)]">加载中...</div>
                <ul v-else-if="sortedPapers.length" class="space-y-2 max-h-64 overflow-y-auto custom-scroll pr-1">
                  <li v-for="item in sortedPapers" :key="item.id" class="min-w-0">
                    <button type="button" class="w-full text-left rounded-2xl px-3 py-2 text-sm text-[color:var(--app-text)] bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] border border-[color:var(--nav-border)] transition-colors duration-200 cursor-pointer" @click="openPaper(item.id)">
                      <div class="truncate">{{ item.title || "未命名试卷" }}</div>
                      <div class="mt-1 text-[10px] text-[color:var(--nav-text-muted)]">{{ formatTime(item.at || 0) }}</div>
                    </button>
                  </li>
                </ul>
                <div v-else class="text-xs text-[color:var(--nav-text-muted)]">暂无历史试卷</div>
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import * as echarts from "echarts/core";
import { LineChart } from "echarts/charts";
import { GridComponent, TooltipComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import {
  getChats,
  listLessonPlans,
  listPapers,
  listQuizzes,
  listTeachingVideos,
  type ChatInfo,
  type LessonPlanMeta,
} from "../lib/api";
import { getUserScopedStorageKey } from "../lib/userStorage";

echarts.use([LineChart, GridComponent, TooltipComponent, CanvasRenderer]);

const SLIDES_STORAGE_KEY = "pagelm-slides-history";
const scopedSlidesStorageKey = () => getUserScopedStorageKey(SLIDES_STORAGE_KEY);

type SlideRecord = { id: string; title?: string; pageCount?: number; at?: number };
type TrendData = { days: string[]; values: number[] };
type StackedData = { days: string[]; series: Record<string, number[]> };

const router = useRouter();

const loading = ref(true);
const chats = ref<(ChatInfo & { at?: number })[]>([]);
const lessonPlans = ref<LessonPlanMeta[]>([]);
const slides = ref<SlideRecord[]>([]);
const videos = ref<{ id: string; title?: string; at?: number }[]>([]);
const quizzes = ref<{ id: string; title?: string; count?: number; at?: number }[]>([]);
const papers = ref<{ id: string; title?: string; at?: number }[]>([]);
const lastUpdatedAt = ref<number | null>(null);
const trendRange = ref<7 | 30>(7);
const trendData = ref<TrendData>({ days: [], values: [] });
const stackedData = ref<StackedData>({
  days: [],
  series: { chat: [], lessonPlans: [], slides: [], videos: [], quizzes: [], papers: [] },
});
const trendLineChartRef = ref<HTMLElement | null>(null);
const stackedChartRef = ref<HTMLElement | null>(null);

let trendLineChart: echarts.ECharts | null = null;
let stackedChart: echarts.ECharts | null = null;
let trendRefreshTimer: number | null = null;

const trendPalette = [
  { label: "对话", key: "chat", color: "#8B5CF6" },
  { label: "教案", key: "lessonPlans", color: "#34D399" },
  { label: "幻灯片", key: "slides", color: "#F59E0B" },
  { label: "视频", key: "videos", color: "#EC4899" },
  { label: "测验", key: "quizzes", color: "#3B82F6" },
  { label: "试卷", key: "papers", color: "#10B981" },
];

const trendLegend = computed(() => trendPalette.map((item) => ({ label: item.label, color: item.color })));
const totalCount = computed(
  () =>
    chats.value.length +
    lessonPlans.value.length +
    slides.value.length +
    videos.value.length +
    quizzes.value.length +
    papers.value.length,
);
const usageTotal = computed(() => totalCount.value);
const trendHasData = computed(() => trendData.value.values.some((value) => value > 0));
const trendEmptyMessage = computed(() => {
  if (loading.value) return "正在加载真实历史数据…";
  if (totalCount.value === 0) return "暂无历史记录，生成教学内容后会自动出现在这里。";
  return `近 ${trendRange.value} 天暂无记录，切换周期或新增内容后会自动刷新。`;
});

const usageItems = computed(() => {
  const total = usageTotal.value || 1;
  const counts = [
    chats.value.length,
    lessonPlans.value.length,
    slides.value.length,
    videos.value.length,
    quizzes.value.length,
    papers.value.length,
  ];
  const max = Math.max(...counts, 1);
  return trendPalette.map((item, i) => {
    const count = counts[i];
    const percent = Math.round((count / total) * 100);
    const barWidth = `${Math.round((count / max) * 100)}%`;
    return { ...item, count, percent, barWidth };
  });
});

const expandedSections = ref({
  chat: false,
  lessonPlans: false,
  slides: false,
  videos: false,
  quizzes: false,
  papers: false,
});

const toggleSection = (key: keyof typeof expandedSections.value) => {
  expandedSections.value = { ...expandedSections.value, [key]: !expandedSections.value[key] };
};

const mostUsed = computed(() => {
  const sorted = [...usageItems.value].sort((a, b) => b.count - a.count);
  return sorted[0] || { label: "--", count: 0 };
});

const donutSegments = computed(() => {
  const total = usageTotal.value;
  if (!total) return [] as { label: string; color: string; dashArray: string; dashOffset: string }[];
  const radius = 28;
  const circumference = 2 * Math.PI * radius;
  let offset = 0;
  return usageItems.value.map((item) => {
    const length = (item.count / total) * circumference;
    const dashArray = `${length.toFixed(2)} ${(circumference - length).toFixed(2)}`;
    const dashOffset = (-offset).toFixed(2);
    offset += length;
    return { label: item.label, color: item.color, dashArray, dashOffset };
  });
});

const lastUpdated = computed(() => {
  if (!lastUpdatedAt.value) return "--";
  const d = new Date(lastUpdatedAt.value);
  return Number.isNaN(d.getTime()) ? "--" : d.toLocaleString();
});

function buildDateKeys(range: number) {
  const now = new Date();
  const start = new Date(now);
  start.setHours(0, 0, 0, 0);
  start.setDate(start.getDate() - (range - 1));
  const labels: string[] = [];
  for (let i = 0; i < range; i++) {
    const d = new Date(start);
    d.setDate(start.getDate() + i);
    labels.push(`${String(d.getMonth() + 1).padStart(2, "0")}/${String(d.getDate()).padStart(2, "0")}`);
  }
  return { labels, start };
}

const updateTrendData = () => {
  const range = trendRange.value;
  const { labels, start } = buildDateKeys(range);
  const series: Record<string, number[]> = {
    chat: Array.from({ length: range }, () => 0),
    lessonPlans: Array.from({ length: range }, () => 0),
    slides: Array.from({ length: range }, () => 0),
    videos: Array.from({ length: range }, () => 0),
    quizzes: Array.from({ length: range }, () => 0),
    papers: Array.from({ length: range }, () => 0),
  };
  const startTime = start.getTime();
  const endTime = startTime + range * 24 * 60 * 60 * 1000;
  const toIndex = (ts: number) => {
    if (ts < startTime || ts >= endTime) return -1;
    const offset = Math.floor((ts - startTime) / (24 * 60 * 60 * 1000));
    return offset >= 0 && offset < range ? offset : -1;
  };

  chats.value.forEach((item) => {
    const idx = toIndex(getItemTime(item));
    if (idx >= 0) series.chat[idx] += 1;
  });
  lessonPlans.value.forEach((item) => {
    const idx = toIndex(getItemTime(item));
    if (idx >= 0) series.lessonPlans[idx] += 1;
  });
  slides.value.forEach((item) => {
    const idx = toIndex(item.at || 0);
    if (idx >= 0) series.slides[idx] += 1;
  });
  videos.value.forEach((item) => {
    const idx = toIndex(item.at || 0);
    if (idx >= 0) series.videos[idx] += 1;
  });
  quizzes.value.forEach((item) => {
    const idx = toIndex(item.at || 0);
    if (idx >= 0) series.quizzes[idx] += 1;
  });
  papers.value.forEach((item) => {
    const idx = toIndex(item.at || 0);
    if (idx >= 0) series.papers[idx] += 1;
  });

  trendData.value = {
    days: labels,
    values: Array.from({ length: range }, (_, index) =>
      trendPalette.reduce((sum, paletteItem) => sum + (series[paletteItem.key]?.[index] || 0), 0),
    ),
  };
  stackedData.value = { days: labels, series };
};

const buildLineOption = () => {
  const hasData = trendHasData.value;
  const fallback = trendData.value.days.map(() => 0);
  return {
    animationDuration: 320,
    grid: { left: 28, right: 12, top: 18, bottom: 22 },
    tooltip: {
      trigger: "axis" as const,
      backgroundColor: "rgba(15,23,42,0.88)",
      borderColor: "rgba(139,92,246,0.25)",
      textStyle: { color: "#e5eefc", fontSize: 12 },
    },
    xAxis: {
      type: "category" as const,
      data: trendData.value.days,
      boundaryGap: false,
      axisLine: { lineStyle: { color: "rgba(148,163,184,0.25)" } },
      axisTick: { show: false },
      axisLabel: { color: "#64748b", fontSize: 10 },
    },
    yAxis: {
      type: "value" as const,
      minInterval: 1,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: "#64748b", fontSize: 10 },
      splitLine: { lineStyle: { color: "rgba(148,163,184,0.14)", type: "dashed" as const } },
    },
    series: [
      {
        type: "line" as const,
        smooth: true,
        showSymbol: hasData,
        symbolSize: 7,
        data: hasData ? trendData.value.values : fallback,
        lineStyle: {
          width: 3,
          color: "#8B5CF6",
          opacity: hasData ? 1 : 0.22,
        },
        itemStyle: {
          color: "#8B5CF6",
          borderWidth: 2,
          borderColor: "#F5F3FF",
        },
        areaStyle: {
          opacity: hasData ? 1 : 0,
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(139,92,246,0.35)" },
            { offset: 1, color: "rgba(167,139,250,0.02)" },
          ]),
        },
      },
    ],
  };
};

const buildStackedOption = () => {
  const hasData = trendHasData.value;
  const zeroSeries = trendData.value.days.map(() => 0);
  return {
    animationDuration: 320,
    grid: { left: 28, right: 12, top: 18, bottom: 22 },
    tooltip: {
      trigger: "axis" as const,
      backgroundColor: "rgba(15,23,42,0.88)",
      borderColor: "rgba(59,130,246,0.25)",
      textStyle: { color: "#e5eefc", fontSize: 12 },
    },
    xAxis: {
      type: "category" as const,
      data: stackedData.value.days,
      boundaryGap: false,
      axisLine: { lineStyle: { color: "rgba(148,163,184,0.25)" } },
      axisTick: { show: false },
      axisLabel: { color: "#64748b", fontSize: 10 },
    },
    yAxis: {
      type: "value" as const,
      minInterval: 1,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: "#64748b", fontSize: 10 },
      splitLine: { lineStyle: { color: "rgba(148,163,184,0.14)", type: "dashed" as const } },
    },
    series: trendPalette.map((item) => ({
      name: item.label,
      type: "line" as const,
      stack: "teaching-total",
      smooth: true,
      showSymbol: false,
      data: hasData ? stackedData.value.series[item.key] || zeroSeries : zeroSeries,
      lineStyle: {
        width: 1.8,
        color: item.color,
        opacity: hasData ? 0.95 : 0,
      },
      areaStyle: {
        opacity: hasData ? 0.3 : 0,
        color: item.color,
      },
    })),
  };
};

const ensureTrendCharts = () => {
  if (trendLineChartRef.value && !trendLineChart) {
    trendLineChart = echarts.init(trendLineChartRef.value);
  }
  if (stackedChartRef.value && !stackedChart) {
    stackedChart = echarts.init(stackedChartRef.value);
  }
};

const renderTrendCharts = () => {
  ensureTrendCharts();
  trendLineChart?.setOption(buildLineOption(), true);
  stackedChart?.setOption(buildStackedOption(), true);
  trendLineChart?.resize();
  stackedChart?.resize();
};

const getItemTime = (item: { at?: number; created_at?: string }) => {
  if (item.at) return item.at;
  if (item.created_at) {
    const t = new Date(item.created_at).getTime();
    return Number.isNaN(t) ? 0 : t;
  }
  return 0;
};

const sortedChats = computed(() => [...chats.value].sort((a, b) => getItemTime(b) - getItemTime(a)).slice(0, 8));
const sortedLessonPlans = computed(() => [...lessonPlans.value].sort((a, b) => getItemTime(b) - getItemTime(a)).slice(0, 8));
const sortedSlides = computed(() => [...slides.value].sort((a, b) => (b.at || 0) - (a.at || 0)).slice(0, 8));
const sortedVideos = computed(() => [...videos.value].sort((a, b) => (b.at || 0) - (a.at || 0)).slice(0, 8));
const sortedQuizzes = computed(() => [...quizzes.value].sort((a, b) => (b.at || 0) - (a.at || 0)).slice(0, 8));
const sortedPapers = computed(() => [...papers.value].sort((a, b) => (b.at || 0) - (a.at || 0)).slice(0, 8));

const cloudWords = computed(() => {
  const seeds = [
    ...chats.value.map((c) => c.title || ""),
    ...lessonPlans.value.map((p) => p.title || ""),
    ...slides.value.map((s) => s.title || ""),
    ...videos.value.map((v) => v.title || ""),
    ...quizzes.value.map((q) => q.title || ""),
    ...papers.value.map((p) => p.title || ""),
  ].join(" ");
  const stopWords = new Set(["教学", "教案", "课程", "测验", "试卷", "对话", "主题", "未命名", "幻灯片", "视频", "历史"]);
  const tokens = seeds.match(/[\p{Script=Han}]{2,}|[A-Za-z0-9]{2,}/gu) || [];
  const freq = new Map<string, number>();
  for (const raw of tokens) {
    const t = raw.trim();
    if (!t || stopWords.has(t)) continue;
    const normalized = /[A-Za-z]/.test(t) ? t.toLowerCase() : t;
    freq.set(normalized, (freq.get(normalized) || 0) + 1);
  }
  const sorted = Array.from(freq.entries()).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  const top = sorted.slice(0, 32);
  if (!top.length) return [] as { term: string; count: number; size: string; color: string }[];
  const max = Math.max(...top.map(([, count]) => count));
  const min = Math.min(...top.map(([, count]) => count));
  const palette = ["#8B5CF6", "#F59E0B", "#34D399", "#EC4899", "#3B82F6", "#10B981"];
  return top.map(([term, count], index) => {
    const ratio = max === min ? 0.5 : (count - min) / (max - min);
    return { term, count, size: `${12 + ratio * 16}px`, color: palette[index % palette.length] };
  });
});

const setTrendRange = (range: 7 | 30) => {
  trendRange.value = range;
};

const refresh = () => void loadAll();
const goTo = (path: string) => router.push({ path });

const openChat = (id: string) => router.push({ path: "/teacher/chat", query: { chatId: id }, state: { chatId: id } });
const openLessonPlan = (id: string) => router.push({ path: "/lesson-plan", query: { lessonPlanId: id }, state: { lessonPlanId: id } });
const openSlides = (id: string) => router.push({ path: "/slides", query: { slideId: id }, state: { slideId: id } });
const openVideo = (id: string) => router.push({ path: "/teaching-video", query: { videoId: id }, state: { videoId: id } });
const openQuiz = (id: string) => router.push({ path: "/teacher/quiz", query: { quizId: id }, state: { quizId: id } });
const openPaper = (id: string) => router.push({ path: "/teacher/paper", query: { paperId: id }, state: { paperId: id } });

const loadSlidesFromStorage = () => {
  try {
    const raw = localStorage.getItem(scopedSlidesStorageKey());
    const parsed = raw ? (JSON.parse(raw) as SlideRecord[]) : [];
    slides.value = Array.isArray(parsed) ? parsed : [];
  } catch {
    slides.value = [];
  }
};

const loadAll = async () => {
  loading.value = true;
  loadSlidesFromStorage();
  const [chatRes, lessonPlanRes, videoRes, quizRes, paperRes] = await Promise.allSettled([
    getChats(undefined, "teacher"),
    listLessonPlans(),
    listTeachingVideos("teacher"),
    listQuizzes("teacher"),
    listPapers(),
  ]);

  if (chatRes.status === "fulfilled") {
    chats.value = Array.isArray(chatRes.value?.chats) ? (chatRes.value.chats as (ChatInfo & { at?: number })[]) : [];
  }
  if (lessonPlanRes.status === "fulfilled") {
    lessonPlans.value = Array.isArray(lessonPlanRes.value?.lessonPlans) ? lessonPlanRes.value.lessonPlans : [];
  }
  if (videoRes.status === "fulfilled") {
    videos.value = Array.isArray(videoRes.value?.videos) ? videoRes.value.videos : [];
  }
  if (quizRes.status === "fulfilled") {
    quizzes.value = Array.isArray(quizRes.value?.quizzes) ? quizRes.value.quizzes : [];
  }
  if (paperRes.status === "fulfilled") {
    papers.value = Array.isArray(paperRes.value?.papers) ? paperRes.value.papers : [];
  }

  updateTrendData();
  lastUpdatedAt.value = Date.now();
  loading.value = false;
  await nextTick();
  renderTrendCharts();
};

const formatTime = (value?: number) => {
  if (!value) return "";
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? "" : d.toLocaleString();
};

const handleTrendResize = () => {
  trendLineChart?.resize();
  stackedChart?.resize();
};

const handleWindowFocus = () => {
  void loadAll();
};

onMounted(() => {
  void loadAll();
  window.addEventListener("resize", handleTrendResize);
  window.addEventListener("focus", handleWindowFocus);
  trendRefreshTimer = window.setInterval(() => {
    void loadAll();
  }, 30000);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", handleTrendResize);
  window.removeEventListener("focus", handleWindowFocus);
  if (trendRefreshTimer !== null) {
    window.clearInterval(trendRefreshTimer);
    trendRefreshTimer = null;
  }
  trendLineChart?.dispose();
  stackedChart?.dispose();
  trendLineChart = null;
  stackedChart = null;
});

watch(trendRange, async () => {
  updateTrendData();
  await nextTick();
  renderTrendCharts();
});
</script>
