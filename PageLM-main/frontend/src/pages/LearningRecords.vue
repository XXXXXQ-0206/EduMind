<template>
  <div class="feature-shell">
    <div class="feature-frame">
      <div class="feature-grid">
        <div class="feature-side">
          <aside class="w-full lg:w-64 min-w-[220px] flex-1 glass-card rounded-3xl p-4 border border-[color:var(--glass-border)] shadow-[0_12px_28px_rgba(0,0,0,0.2)] flex flex-col min-h-0 lg:overflow-y-auto overflow-x-hidden custom-scroll lg:pr-1">
            <div class="flex items-center justify-between mb-3">
              <div class="flex items-center gap-2 text-sm font-semibold text-[color:var(--app-text)]">
                <span class="inline-flex size-6 items-center justify-center rounded-full bg-[color:var(--nav-hover-bg-strong)] text-sky-300">
                  <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 6.5h15" />
                    <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12h15" />
                    <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 17.5h10.5" />
                  </svg>
                </span>
                学习记录概览
              </div>
              <div class="text-xs text-[color:var(--nav-text-muted)]">共 {{ totalCount }} 条</div>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div class="rounded-2xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/60 p-3">
                <div class="text-xs text-[color:var(--nav-text-muted)]">对话</div>
                <div class="text-lg font-semibold text-[color:var(--app-text)]">{{ chats.length }}</div>
              </div>
              <div class="rounded-2xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/60 p-3">
                <div class="text-xs text-[color:var(--nav-text-muted)]">笔记</div>
                <div class="text-lg font-semibold text-[color:var(--app-text)]">{{ notes.length }}</div>
              </div>
              <div class="rounded-2xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/60 p-3">
                <div class="text-xs text-[color:var(--nav-text-muted)]">播客</div>
                <div class="text-lg font-semibold text-[color:var(--app-text)]">{{ podcasts.length }}</div>
              </div>
              <div class="rounded-2xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/60 p-3">
                <div class="text-xs text-[color:var(--nav-text-muted)]">测验</div>
                <div class="text-lg font-semibold text-[color:var(--app-text)]">{{ quizzes.length }}</div>
              </div>
              <div class="rounded-2xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/60 p-3 col-span-2">
                <div class="text-xs text-[color:var(--nav-text-muted)]">卡片</div>
                <div class="text-lg font-semibold text-[color:var(--app-text)]">{{ decks.length }}</div>
              </div>
            </div>
            <div class="mt-4 space-y-3">
              <div class="text-xs text-[color:var(--nav-text-muted)]">
                最常用：<span class="text-[color:var(--app-text)]">{{ mostUsed.label }}</span>
              </div>
              <div class="grid grid-cols-1 gap-3">
                <div class="rounded-2xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/60 p-3">
                  <div class="text-xs font-semibold text-[color:var(--app-text)]">使用占比</div>
                  <div class="mt-3 flex items-center gap-3">
                    <div class="relative size-[120px]">
                      <svg viewBox="0 0 120 120" class="size-[120px] -rotate-90" role="img" aria-label="学习方式使用占比">
                        <circle cx="60" cy="60" r="42" fill="none" stroke="rgba(148,163,184,0.2)" stroke-width="12" />
                        <template v-if="usageTotal">
                          <circle
                            v-for="seg in donutSegments"
                            :key="seg.label"
                            cx="60"
                            cy="60"
                            r="42"
                            fill="none"
                            stroke-width="12"
                            stroke-linecap="round"
                            :stroke="seg.color"
                            :stroke-dasharray="seg.dashArray"
                            :stroke-dashoffset="seg.dashOffset"
                          />
                        </template>
                      </svg>
                      <div class="absolute inset-0 flex flex-col items-center justify-center text-[color:var(--app-text)]">
                        <div class="text-lg font-semibold">{{ usageTotal }}</div>
                        <div class="text-[10px] text-[color:var(--nav-text-muted)]">总次数</div>
                      </div>
                    </div>
                    <div class="flex-1 space-y-2">
                      <div v-for="item in usageItems" :key="item.label" class="flex items-center justify-between text-[11px]">
                        <div class="flex items-center gap-2">
                          <span class="size-2 rounded-full" :style="{ backgroundColor: item.color }" />
                          <span class="text-[color:var(--app-text)]">{{ item.label }}</span>
                        </div>
                        <div class="text-[color:var(--nav-text-muted)]">{{ item.percent }}%</div>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="rounded-2xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/60 p-3">
                  <div class="text-xs font-semibold text-[color:var(--app-text)]">使用次数对比</div>
                  <div class="mt-3 space-y-2">
                    <div v-for="item in usageItems" :key="item.label" class="flex items-center gap-2">
                      <div class="w-10 text-[10px] text-[color:var(--nav-text-muted)]">{{ item.label }}</div>
                      <div class="flex-1 h-2 rounded-full bg-white/10 overflow-hidden">
                        <div
                          class="h-full rounded-full"
                          :style="{ width: item.barWidth, backgroundColor: item.color }"
                        />
                      </div>
                      <div class="w-8 text-right text-[10px] text-[color:var(--nav-text-muted)]">{{ item.count }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="mt-3 text-xs text-[color:var(--nav-text-muted)]">更新于 {{ lastUpdated }}</div>
          </aside>
        </div>

        <div class="feature-main custom-scroll space-y-6">
          <div class="flex flex-col gap-2">
            <h1 class="text-2xl font-semibold text-[color:var(--app-text)]">学习记录汇</h1>
            <p class="text-sm text-[color:var(--nav-text-muted)]">集中查看对话、笔记、播客、测验与卡片历史，并用词云洞察主题热度。</p>
          </div>

          <section class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 px-5 py-3.5 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
            <div class="flex items-center justify-between">
              <div>
                <div class="text-sm font-semibold text-[color:var(--app-text)]">主题词云</div>
                <div class="text-xs text-[color:var(--nav-text-muted)]">基于历史记录的标题与主题生成</div>
              </div>
              <button
                type="button"
                class="text-xs px-3 py-1.5 rounded-full border border-[color:var(--nav-border)] text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors cursor-pointer"
                @click="refresh"
              >
                刷新统计
              </button>
            </div>
            <div v-if="loading" class="mt-6 text-xs text-[color:var(--nav-text-muted)]">正在统计主题…</div>
            <div v-else-if="cloudWords.length" class="mt-6 flex flex-wrap gap-2 animate-[fadeIn_0.4s_ease-out] motion-reduce:animate-none">
              <button
                v-for="word in cloudWords"
                :key="word.term"
                type="button"
                class="px-2.5 py-1 rounded-full border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400/60"
                :style="{ fontSize: word.size, color: word.color }"
                :title="`${word.term} · ${word.count} 次`"
              >
                {{ word.term }}
              </button>
            </div>
            <div v-else class="mt-6 text-xs text-[color:var(--nav-text-muted)]">暂无可统计的主题，先去生成一些学习内容吧。</div>
          </section>

          <section class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-5 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
            <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <div class="text-sm font-semibold text-[color:var(--app-text)]">学习趋势</div>
                <div class="text-xs text-[color:var(--nav-text-muted)]">真实历史数据，支持近 7 天 / 30 天切换，并在页面停留期间自动刷新</div>
              </div>
              <div class="flex flex-wrap items-center gap-2">
                <div class="flex items-center rounded-full border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 p-1 text-xs">
                  <button
                    type="button"
                    class="px-3 py-1 rounded-full transition-colors cursor-pointer"
                    :class="trendRange === 7 ? 'bg-[color:var(--nav-hover-bg-strong)] text-[color:var(--app-text)]' : 'text-[color:var(--nav-text-muted)]'"
                    @click="setTrendRange(7)"
                  >
                    近7天
                  </button>
                  <button
                    type="button"
                    class="px-3 py-1 rounded-full transition-colors cursor-pointer"
                    :class="trendRange === 30 ? 'bg-[color:var(--nav-hover-bg-strong)] text-[color:var(--app-text)]' : 'text-[color:var(--nav-text-muted)]'"
                    @click="setTrendRange(30)"
                  >
                    近30天
                  </button>
                </div>
                <button
                  type="button"
                  class="text-xs px-3 py-1.5 rounded-full border border-[color:var(--nav-border)] text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors cursor-pointer"
                  @click="refresh"
                >
                  更新数据
                </button>
              </div>
            </div>
            <div class="mt-5 grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div class="rounded-2xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/60 p-4">
                <div class="flex items-center justify-between">
                  <div class="text-xs font-semibold text-[color:var(--app-text)]">学习趋势折线图</div>
                  <div class="text-[10px] text-[color:var(--nav-text-muted)]">活跃度变化</div>
                </div>
                <div class="relative mt-3">
                  <div ref="trendLineChartRef" class="h-44 w-full" role="img" aria-label="学习趋势折线图" />
                  <div
                    v-if="!trendHasData"
                    class="pointer-events-none absolute inset-0 flex flex-col items-center justify-center rounded-2xl border border-dashed border-[color:var(--glass-border)] bg-white/20 px-6 text-center"
                  >
                    <div class="text-sm font-medium text-[color:var(--app-text)]">暂无可视化数据</div>
                    <div class="mt-1 text-xs text-[color:var(--nav-text-muted)]">{{ trendEmptyMessage }}</div>
                  </div>
                </div>
              </div>

              <div class="rounded-2xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/60 p-4">
                <div class="flex items-center justify-between">
                  <div class="text-xs font-semibold text-[color:var(--app-text)]">累计学习量堆叠面积图</div>
                  <div class="text-[10px] text-[color:var(--nav-text-muted)]">构成与总量</div>
                </div>
                <div class="relative mt-3">
                  <div ref="stackedChartRef" class="h-44 w-full" role="img" aria-label="学习量堆叠面积图" />
                  <div
                    v-if="!trendHasData"
                    class="pointer-events-none absolute inset-0 flex flex-col items-center justify-center rounded-2xl border border-dashed border-[color:var(--glass-border)] bg-white/20 px-6 text-center"
                  >
                    <div class="text-sm font-medium text-[color:var(--app-text)]">暂无累计趋势</div>
                    <div class="mt-1 text-xs text-[color:var(--nav-text-muted)]">{{ trendEmptyMessage }}</div>
                  </div>
                </div>
                  <div class="mt-3 flex flex-wrap gap-3 text-[10px] text-[color:var(--nav-text-muted)]">
                    <div v-for="item in trendLegend" :key="item.label" class="flex items-center gap-1.5">
                      <span class="size-2 rounded-full" :style="{ backgroundColor: item.color }" />
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
                  <span class="inline-flex size-6 items-center justify-center rounded-full bg-[color:var(--nav-hover-bg-strong)] text-sky-300">
                    <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M7 4.5h10a3.5 3.5 0 0 1 3.5 3.5v5a3.5 3.5 0 0 1-3.5 3.5H10l-3.5 3v-3H7A3.5 3.5 0 0 1 3.5 13V8A3.5 3.5 0 0 1 7 4.5Z" />
                    </svg>
                  </span>
                  历史对话
                </div>
                <div class="flex items-center gap-2">
                  <button
                    type="button"
                    class="text-xs px-3 py-1 rounded-full border border-[color:var(--nav-border)] text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors cursor-pointer"
                    @click="goTo('/chat')"
                  >
                    查看全部
                  </button>
                  <button
                    type="button"
                    class="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full border border-[color:var(--nav-border)] text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors cursor-pointer"
                    @click="toggleSection('chat')"
                  >
                    <span>{{ expandedSections.chat ? "收起" : "展开" }}</span>
                    <svg
                      viewBox="0 0 24 24"
                      class="size-3.5"
                      :class="expandedSections.chat ? 'rotate-180' : ''"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      aria-hidden="true"
                    >
                      <path stroke-linecap="round" stroke-linejoin="round" d="M6 9l6 6 6-6" />
                    </svg>
                  </button>
                </div>
              </div>
              <div v-if="expandedSections.chat" class="mt-3">
                <div v-if="loading" class="text-xs text-[color:var(--nav-text-muted)]">加载中...</div>
                <ul v-else-if="sortedChats.length" class="space-y-2 max-h-64 overflow-y-auto custom-scroll pr-1">
                  <li v-for="item in sortedChats" :key="item.id" class="min-w-0">
                    <button
                      type="button"
                      class="w-full text-left rounded-2xl px-3 py-2 text-sm text-[color:var(--app-text)] bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] border border-[color:var(--nav-border)] transition-colors cursor-pointer"
                      @click="openChat(item.id)"
                    >
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
                  <span class="inline-flex size-6 items-center justify-center rounded-full bg-[color:var(--nav-hover-bg-strong)] text-emerald-300">
                    <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M5.25 6.75h13.5v10.5H5.25z" />
                      <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 6.75v-1.5h7.5v1.5" />
                    </svg>
                  </span>
                  历史笔记
                </div>
                <div class="flex items-center gap-2">
                  <button
                    type="button"
                    class="text-xs px-3 py-1 rounded-full border border-[color:var(--nav-border)] text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors cursor-pointer"
                    @click="goTo('/smart-notes')"
                  >
                    查看全部
                  </button>
                  <button
                    type="button"
                    class="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full border border-[color:var(--nav-border)] text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors cursor-pointer"
                    @click="toggleSection('notes')"
                  >
                    <span>{{ expandedSections.notes ? "收起" : "展开" }}</span>
                    <svg
                      viewBox="0 0 24 24"
                      class="size-3.5"
                      :class="expandedSections.notes ? 'rotate-180' : ''"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      aria-hidden="true"
                    >
                      <path stroke-linecap="round" stroke-linejoin="round" d="M6 9l6 6 6-6" />
                    </svg>
                  </button>
                </div>
              </div>
              <div v-if="expandedSections.notes" class="mt-3">
                <div v-if="loading" class="text-xs text-[color:var(--nav-text-muted)]">加载中...</div>
                <ul v-else-if="sortedNotes.length" class="space-y-2 max-h-64 overflow-y-auto custom-scroll pr-1">
                  <li v-for="item in sortedNotes" :key="item.id" class="min-w-0">
                    <button
                      type="button"
                      class="w-full text-left rounded-2xl px-3 py-2 text-sm text-[color:var(--app-text)] bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] border border-[color:var(--nav-border)] transition-colors cursor-pointer"
                      @click="openNote(item.id)"
                    >
                      <div class="truncate">{{ item.title || "未命名笔记" }}</div>
                      <div class="mt-1 text-[10px] text-[color:var(--nav-text-muted)]">
                        {{ formatTime(getItemTime(item)) }} · {{ lengthLabel(item.length) }}
                      </div>
                    </button>
                  </li>
                </ul>
                <div v-else class="text-xs text-[color:var(--nav-text-muted)]">暂无历史笔记</div>
              </div>
            </section>

            <section class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2 text-sm font-semibold text-[color:var(--app-text)]">
                  <span class="inline-flex size-6 items-center justify-center rounded-full bg-[color:var(--nav-hover-bg-strong)] text-sky-300">
                    <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 8.25h15v7.5h-15z" />
                      <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v12" />
                    </svg>
                  </span>
                  历史播客
                </div>
                <div class="flex items-center gap-2">
                  <button
                    type="button"
                    class="text-xs px-3 py-1 rounded-full border border-[color:var(--nav-border)] text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors cursor-pointer"
                    @click="goTo('/podcast')"
                  >
                    查看全部
                  </button>
                  <button
                    type="button"
                    class="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full border border-[color:var(--nav-border)] text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors cursor-pointer"
                    @click="toggleSection('podcasts')"
                  >
                    <span>{{ expandedSections.podcasts ? "收起" : "展开" }}</span>
                    <svg
                      viewBox="0 0 24 24"
                      class="size-3.5"
                      :class="expandedSections.podcasts ? 'rotate-180' : ''"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      aria-hidden="true"
                    >
                      <path stroke-linecap="round" stroke-linejoin="round" d="M6 9l6 6 6-6" />
                    </svg>
                  </button>
                </div>
              </div>
              <div v-if="expandedSections.podcasts" class="mt-3">
                <div v-if="loading" class="text-xs text-[color:var(--nav-text-muted)]">加载中...</div>
                <ul v-else-if="sortedPodcasts.length" class="space-y-2 max-h-64 overflow-y-auto custom-scroll pr-1">
                  <li v-for="item in sortedPodcasts" :key="item.id" class="min-w-0">
                    <button
                      type="button"
                      class="w-full text-left rounded-2xl px-3 py-2 text-sm text-[color:var(--app-text)] bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] border border-[color:var(--nav-border)] transition-colors cursor-pointer"
                      @click="openPodcast(item.id)"
                    >
                      <div class="truncate">{{ item.title || "未命名播客" }}</div>
                      <div class="mt-1 text-[10px] text-[color:var(--nav-text-muted)]">
                        {{ formatTime(getItemTime(item)) }} · {{ podcastLength(item.length) }}
                      </div>
                    </button>
                  </li>
                </ul>
                <div v-else class="text-xs text-[color:var(--nav-text-muted)]">暂无历史播客</div>
              </div>
            </section>

            <section class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2 text-sm font-semibold text-[color:var(--app-text)]">
                  <span class="inline-flex size-6 items-center justify-center rounded-full bg-[color:var(--nav-hover-bg-strong)] text-amber-300">
                    <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6l4 2" />
                      <circle cx="12" cy="12" r="9" />
                    </svg>
                  </span>
                  历史测验
                </div>
                <div class="flex items-center gap-2">
                  <button
                    type="button"
                    class="text-xs px-3 py-1 rounded-full border border-[color:var(--nav-border)] text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors cursor-pointer"
                    @click="goTo('/quiz')"
                  >
                    查看全部
                  </button>
                  <button
                    type="button"
                    class="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full border border-[color:var(--nav-border)] text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors cursor-pointer"
                    @click="toggleSection('quizzes')"
                  >
                    <span>{{ expandedSections.quizzes ? "收起" : "展开" }}</span>
                    <svg
                      viewBox="0 0 24 24"
                      class="size-3.5"
                      :class="expandedSections.quizzes ? 'rotate-180' : ''"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      aria-hidden="true"
                    >
                      <path stroke-linecap="round" stroke-linejoin="round" d="M6 9l6 6 6-6" />
                    </svg>
                  </button>
                </div>
              </div>
              <div v-if="expandedSections.quizzes" class="mt-3">
                <div v-if="loading" class="text-xs text-[color:var(--nav-text-muted)]">加载中...</div>
                <ul v-else-if="sortedQuizzes.length" class="space-y-2 max-h-64 overflow-y-auto custom-scroll pr-1">
                  <li v-for="item in sortedQuizzes" :key="item.id" class="min-w-0">
                    <button
                      type="button"
                      class="w-full text-left rounded-2xl px-3 py-2 text-sm text-[color:var(--app-text)] bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] border border-[color:var(--nav-border)] transition-colors cursor-pointer"
                      @click="openQuiz(item.id)"
                    >
                      <div class="truncate">{{ item.title || "未命名测验" }}</div>
                      <div class="mt-1 text-[10px] text-[color:var(--nav-text-muted)]">题目数量：{{ item.count || 5 }}</div>
                    </button>
                  </li>
                </ul>
                <div v-else class="text-xs text-[color:var(--nav-text-muted)]">暂无历史测验</div>
              </div>
            </section>

            <section class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)] lg:col-span-2">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2 text-sm font-semibold text-[color:var(--app-text)]">
                  <span class="inline-flex size-6 items-center justify-center rounded-full bg-[color:var(--nav-hover-bg-strong)] text-fuchsia-300">
                    <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M6 5.25h9.75A2.25 2.25 0 0 1 18 7.5v11.25A2.25 2.25 0 0 1 15.75 21H6A2.25 2.25 0 0 1 3.75 18.75V7.5A2.25 2.25 0 0 1 6 5.25Z" />
                      <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 3.75h9.75A2.25 2.25 0 0 1 20.25 6v11.25" />
                    </svg>
                  </span>
                  历史卡片
                </div>
                <div class="flex items-center gap-2">
                  <button
                    type="button"
                    class="text-xs px-3 py-1 rounded-full border border-[color:var(--nav-border)] text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors cursor-pointer"
                    @click="goTo('/knowledge-cards')"
                  >
                    查看全部
                  </button>
                  <button
                    type="button"
                    class="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full border border-[color:var(--nav-border)] text-[color:var(--nav-text)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors cursor-pointer"
                    @click="toggleSection('decks')"
                  >
                    <span>{{ expandedSections.decks ? "收起" : "展开" }}</span>
                    <svg
                      viewBox="0 0 24 24"
                      class="size-3.5"
                      :class="expandedSections.decks ? 'rotate-180' : ''"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      aria-hidden="true"
                    >
                      <path stroke-linecap="round" stroke-linejoin="round" d="M6 9l6 6 6-6" />
                    </svg>
                  </button>
                </div>
              </div>
              <div v-if="expandedSections.decks" class="mt-3">
                <div v-if="loading" class="text-xs text-[color:var(--nav-text-muted)]">加载中...</div>
                <ul v-else-if="sortedDecks.length" class="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-64 overflow-y-auto custom-scroll pr-1">
                  <li v-for="item in sortedDecks" :key="item.id" class="min-w-0">
                    <button
                      type="button"
                      class="w-full text-left rounded-2xl px-3 py-2 text-sm text-[color:var(--app-text)] bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] border border-[color:var(--nav-border)] transition-colors cursor-pointer"
                      @click="openDeck(item.id)"
                    >
                      <div class="truncate">{{ item.title || "未命名卡组" }}</div>
                      <div class="mt-1 text-[10px] text-[color:var(--nav-text-muted)]">卡片数量：{{ item.count || 5 }}</div>
                    </button>
                  </li>
                </ul>
                <div v-else class="text-xs text-[color:var(--nav-text-muted)]">暂无历史卡片</div>
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
  listKnowledgeDecks,
  listPodcasts,
  listQuizzes,
  listSmartNotes,
  type ChatInfo,
  type KnowledgeDeckMeta,
  type PodcastMeta,
  type QuizMeta,
  type SmartNoteMeta,
} from "../lib/api";

echarts.use([LineChart, GridComponent, TooltipComponent, CanvasRenderer]);

type TrendData = { days: string[]; values: number[] };
type StackedData = { days: string[]; series: Record<string, number[]> };
type TimeAwareRecord = {
  at?: number;
  createdAt?: number;
  created_at?: string;
  updated_at?: string;
};

const router = useRouter();
const loading = ref(true);
const chats = ref<(ChatInfo & { at?: number })[]>([]);
const notes = ref<SmartNoteMeta[]>([]);
const podcasts = ref<PodcastMeta[]>([]);
const quizzes = ref<QuizMeta[]>([]);
const decks = ref<KnowledgeDeckMeta[]>([]);
const lastUpdatedAt = ref<number | null>(null);
const trendRange = ref<7 | 30>(7);
const trendData = ref<TrendData>({ days: [], values: [] });
const stackedData = ref<StackedData>({
  days: [],
  series: { chat: [], notes: [], podcasts: [], quizzes: [], decks: [] },
});
const trendLineChartRef = ref<HTMLElement | null>(null);
const stackedChartRef = ref<HTMLElement | null>(null);

let trendLineChart: echarts.ECharts | null = null;
let stackedChart: echarts.ECharts | null = null;
let trendRefreshTimer: number | null = null;

const trendPalette = [
  { label: "对话", key: "chat", color: "#38BDF8" },
  { label: "笔记", key: "notes", color: "#34D399" },
  { label: "播客", key: "podcasts", color: "#A5B4FC" },
  { label: "测验", key: "quizzes", color: "#FBBF24" },
  { label: "卡片", key: "decks", color: "#F472B6" },
];

const trendLegend = computed(() => trendPalette.map((item) => ({ label: item.label, color: item.color })));
const totalCount = computed(() => chats.value.length + notes.value.length + podcasts.value.length + quizzes.value.length + decks.value.length);
const usageTotal = computed(() => totalCount.value);
const trendHasData = computed(() => trendData.value.values.some((value) => value > 0));
const trendEmptyMessage = computed(() => {
  if (loading.value) return "正在加载真实历史数据…";
  if (totalCount.value === 0) return "暂无历史记录，生成学习内容后会自动出现在这里。";
  return `近 ${trendRange.value} 天暂无记录，切换周期或新增内容后会自动刷新。`;
});

const usageItems = computed(() => {
  const total = usageTotal.value || 1;
  const counts = [chats.value.length, notes.value.length, podcasts.value.length, quizzes.value.length, decks.value.length];
  const max = Math.max(...counts, 1);
  return trendPalette.map((item, index) => {
    const count = counts[index];
    const percent = Math.round((count / total) * 100);
    const barWidth = `${Math.round((count / max) * 100)}%`;
    return { ...item, count, percent, barWidth };
  });
});

const expandedSections = ref({
  chat: false,
  notes: false,
  podcasts: false,
  quizzes: false,
  decks: false,
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
  const radius = 42;
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

const getItemTime = (item: TimeAwareRecord | null | undefined) => {
  if (!item) return 0;
  if (typeof item.at === "number" && item.at > 0) return item.at;
  if (typeof item.createdAt === "number" && item.createdAt > 0) return item.createdAt;
  if (item.created_at) {
    const createdAt = new Date(item.created_at).getTime();
    if (!Number.isNaN(createdAt)) return createdAt;
  }
  if (item.updated_at) {
    const updatedAt = new Date(item.updated_at).getTime();
    if (!Number.isNaN(updatedAt)) return updatedAt;
  }
  return 0;
};

const sortedChats = computed(() => [...chats.value].sort((a, b) => getItemTime(b) - getItemTime(a)).slice(0, 8));
const sortedNotes = computed(() => [...notes.value].sort((a, b) => getItemTime(b) - getItemTime(a)).slice(0, 8));
const sortedPodcasts = computed(() => [...podcasts.value].sort((a, b) => getItemTime(b) - getItemTime(a)).slice(0, 8));
const sortedQuizzes = computed(() => [...quizzes.value].sort((a, b) => getItemTime(b) - getItemTime(a)).slice(0, 8));
const sortedDecks = computed(() => [...decks.value].sort((a, b) => getItemTime(b) - getItemTime(a)).slice(0, 8));

const cloudWords = computed(() => buildCloud());

const setTrendRange = (range: 7 | 30) => {
  trendRange.value = range;
};

function buildDateKeys(range: number) {
  const now = new Date();
  const start = new Date(now);
  start.setHours(0, 0, 0, 0);
  start.setDate(start.getDate() - (range - 1));
  const labels: string[] = [];
  for (let index = 0; index < range; index += 1) {
    const d = new Date(start);
    d.setDate(start.getDate() + index);
    labels.push(`${String(d.getMonth() + 1).padStart(2, "0")}/${String(d.getDate()).padStart(2, "0")}`);
  }
  return { labels, start };
}

const updateTrendData = () => {
  const range = trendRange.value;
  const { labels, start } = buildDateKeys(range);
  const series: Record<string, number[]> = {
    chat: Array.from({ length: range }, () => 0),
    notes: Array.from({ length: range }, () => 0),
    podcasts: Array.from({ length: range }, () => 0),
    quizzes: Array.from({ length: range }, () => 0),
    decks: Array.from({ length: range }, () => 0),
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
  notes.value.forEach((item) => {
    const idx = toIndex(getItemTime(item));
    if (idx >= 0) series.notes[idx] += 1;
  });
  podcasts.value.forEach((item) => {
    const idx = toIndex(getItemTime(item));
    if (idx >= 0) series.podcasts[idx] += 1;
  });
  quizzes.value.forEach((item) => {
    const idx = toIndex(getItemTime(item));
    if (idx >= 0) series.quizzes[idx] += 1;
  });
  decks.value.forEach((item) => {
    const idx = toIndex(getItemTime(item));
    if (idx >= 0) series.decks[idx] += 1;
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
      borderColor: "rgba(56,189,248,0.25)",
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
          color: "#38BDF8",
          opacity: hasData ? 1 : 0.22,
        },
        itemStyle: {
          color: "#38BDF8",
          borderWidth: 2,
          borderColor: "#E0F2FE",
        },
        areaStyle: {
          opacity: hasData ? 1 : 0,
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(56,189,248,0.35)" },
            { offset: 1, color: "rgba(52,211,153,0.03)" },
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
      borderColor: "rgba(56,189,248,0.25)",
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
      stack: "learning-total",
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

const refresh = () => void loadAll();
const goTo = (path: string) => router.push({ path });

const openChat = (id: string) => {
  if (!id) return;
  router.push({ path: "/chat", query: { chatId: id }, state: { chatId: id } });
};

const openNote = (id: string) => {
  if (!id) return;
  router.push({ path: "/smart-notes", query: { noteId: id }, state: { noteId: id } });
};

const openPodcast = (id: string) => {
  if (!id) return;
  router.push({ path: "/podcast", query: { pid: id, t: String(Date.now()) }, state: { pid: id } });
};

const openQuiz = (id: string) => {
  if (!id) return;
  router.push({ path: "/quiz", query: { quizId: id }, state: { quizId: id } });
};

const openDeck = (id: string) => {
  if (!id) return;
  router.push({ path: "/knowledge-cards", query: { deckId: id, t: String(Date.now()) }, state: { deckId: id } });
};

const formatTime = (value?: number) => {
  if (!value) return "";
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? "" : d.toLocaleString();
};

const lengthLabel = (value?: string) => {
  if (value === "rough") return "粗略";
  if (value === "detailed") return "详细";
  return "中等";
};

const podcastLength = (value?: string) => {
  if (value === "short") return "短";
  if (value === "long") return "长";
  return "中";
};

const buildCloud = () => {
  const seeds = [
    ...chats.value.map((item) => item.title || ""),
    ...notes.value.map((item) => item.title || ""),
    ...podcasts.value.map((item) => item.title || ""),
    ...quizzes.value.map((item) => item.title || ""),
    ...decks.value.map((item) => item.title || ""),
  ].join(" ");

  const stopWords = new Set([
    "学习",
    "知识",
    "课程",
    "笔记",
    "测验",
    "播客",
    "对话",
    "历史",
    "主题",
    "未命名",
    "复习",
    "卡片",
  ]);

  const tokens = seeds.match(/[\p{Script=Han}]{2,}|[A-Za-z0-9]{2,}/gu) || [];
  const freq = new Map<string, number>();
  for (const raw of tokens) {
    const trimmed = raw.trim();
    if (!trimmed) continue;
    const normalized = /[A-Za-z]/.test(trimmed) ? trimmed.toLowerCase() : trimmed;
    if (stopWords.has(normalized)) continue;
    freq.set(normalized, (freq.get(normalized) || 0) + 1);
  }

  const sorted = Array.from(freq.entries()).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  const top = sorted.slice(0, 32);
  if (!top.length) return [] as { term: string; count: number; size: string; color: string }[];

  const max = Math.max(...top.map(([, count]) => count));
  const min = Math.min(...top.map(([, count]) => count));
  const palette = ["#38BDF8", "#A5B4FC", "#FBBF24", "#34D399", "#F472B6", "#F97316"];

  return top.map(([term, count], index) => {
    const ratio = max === min ? 0.5 : (count - min) / (max - min);
    return {
      term,
      count,
      size: `${(12 + ratio * 16).toFixed(1)}px`,
      color: palette[index % palette.length],
    };
  });
};

const loadAll = async () => {
  loading.value = true;
  const [chatRes, noteRes, podcastRes, quizRes, deckRes] = await Promise.allSettled([
    getChats(undefined, "student"),
    listSmartNotes(),
    listPodcasts(),
    listQuizzes("student"),
    listKnowledgeDecks(),
  ]);

  if (chatRes.status === "fulfilled") {
    chats.value = Array.isArray(chatRes.value?.chats) ? (chatRes.value.chats as (ChatInfo & { at?: number })[]) : [];
  }
  if (noteRes.status === "fulfilled") {
    notes.value = Array.isArray(noteRes.value?.notes) ? noteRes.value.notes : [];
  }
  if (podcastRes.status === "fulfilled") {
    podcasts.value = Array.isArray(podcastRes.value?.podcasts) ? podcastRes.value.podcasts : [];
  }
  if (quizRes.status === "fulfilled") {
    quizzes.value = Array.isArray(quizRes.value?.quizzes) ? quizRes.value.quizzes : [];
  }
  if (deckRes.status === "fulfilled") {
    decks.value = Array.isArray(deckRes.value?.decks) ? deckRes.value.decks : [];
  }

  updateTrendData();
  lastUpdatedAt.value = Date.now();
  loading.value = false;
  await nextTick();
  renderTrendCharts();
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
