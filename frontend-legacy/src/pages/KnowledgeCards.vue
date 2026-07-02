<template>
  <div class="knowledge-cards feature-shell">
    <div class="feature-frame">
      <div class="feature-grid">
        <div class="feature-side">
          <LearningFolderPanel class="shrink-0" />
          <KnowledgeCardsHistoryPanel class="min-h-0" />
        </div>
        <div class="feature-main custom-scroll">
          <div class="flex items-center justify-between mb-6">
            <div class="flex items-center gap-3">
              <h1 class="text-2xl font-semibold text-[color:var(--app-text)] flex items-center gap-3">知识卡片</h1>
            </div>
          </div>

          <div
            v-if="!deckReady && !connecting"
            class="min-h-[62vh] flex flex-col items-center justify-center"
          >
            <div class="w-full max-w-3xl mx-auto">
              <div class="flex flex-col items-center text-center gap-3">
                <div class="size-16 rounded-3xl bg-gradient-to-br from-amber-500/20 to-orange-400/30 border border-amber-400/30 shadow-[0_18px_40px_rgba(251,146,60,0.25)] flex items-center justify-center">
                  <svg viewBox="0 0 24 24" class="size-8 text-amber-400" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M6 4.5h9.75A2.25 2.25 0 0 1 18 6.75v12A2.25 2.25 0 0 1 15.75 21H6A2.25 2.25 0 0 1 3.75 18.75V6.75A2.25 2.25 0 0 1 6 4.5Z" />
                    <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 3h9.75A2.25 2.25 0 0 1 20.25 5.25V17.25" />
                  </svg>
                </div>
                <h2 class="text-2xl md:text-3xl font-semibold text-[color:var(--app-text)]">把知识变成可记忆的卡片</h2>
                <p class="text-sm md:text-base text-[color:var(--nav-text-muted)] max-w-2xl">
                  输入主题生成 AI 提取的知识卡片，包含线索提示、助记词与应用场景，适合快速回忆与巩固。
                </p>
              </div>

              <div class="mt-6 flex flex-wrap items-center justify-center gap-2">
                <button
                  v-for="item in quickTopics"
                  :key="item"
                  type="button"
                  class="px-4 py-2 rounded-full border border-amber-400/30 bg-white/80 text-sm text-slate-800 shadow-[0_8px_16px_rgba(15,23,42,0.08)] hover:bg-white transition-colors cursor-pointer"
                  @click="onQuickTopic(item)"
                >
                  {{ item }}
                </button>
              </div>

              <div class="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                  <div class="flex items-center gap-3">
                    <span class="size-10 rounded-2xl bg-amber-500/15 text-amber-500 flex items-center justify-center">
                      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 6.75h15M4.5 12h10.5M4.5 17.25h7.5" />
                      </svg>
                    </span>
                    <div>
                      <div class="text-sm font-semibold text-[color:var(--app-text)]">全局聚合复习</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)]">按掌握度聚合所有历史卡片。</div>
                    </div>
                  </div>
                </div>
                <div class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                  <div class="flex items-center gap-3">
                    <span class="size-10 rounded-2xl bg-emerald-500/15 text-emerald-500 flex items-center justify-center">
                      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M7.5 12l3 3 6-6" />
                        <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 5.25h15a1.5 1.5 0 0 1 1.5 1.5v10.5a1.5 1.5 0 0 1-1.5 1.5h-15a1.5 1.5 0 0 1-1.5-1.5V6.75a1.5 1.5 0 0 1 1.5-1.5Z" />
                      </svg>
                    </span>
                    <div>
                      <div class="text-sm font-semibold text-[color:var(--app-text)]">掌握度标记</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)]">标记掌握 / 待确认 / 待复习。</div>
                    </div>
                  </div>
                </div>
                <div class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                  <div class="flex items-center gap-3">
                    <span class="size-10 rounded-2xl bg-sky-500/15 text-sky-500 flex items-center justify-center">
                      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 7.5h15M4.5 12h15M4.5 16.5h15" />
                      </svg>
                    </span>
                    <div>
                      <div class="text-sm font-semibold text-[color:var(--app-text)]">多张同步复习</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)]">批量导航，快速定位重点。</div>
                    </div>
                  </div>
                </div>
                <div class="rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-4 shadow-[0_12px_26px_rgba(15,23,42,0.12)]">
                  <div class="flex items-center gap-3">
                    <span class="size-10 rounded-2xl bg-fuchsia-500/15 text-fuchsia-500 flex items-center justify-center">
                      <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.75v10.5m5.25-5.25H6.75" />
                        <circle cx="12" cy="12" r="9" />
                      </svg>
                    </span>
                    <div>
                      <div class="text-sm font-semibold text-[color:var(--app-text)]">资料融合生成</div>
                      <div class="text-xs text-[color:var(--nav-text-muted)]">可选学习资料辅助提炼。</div>
                    </div>
                  </div>
                </div>
              </div>

              <div class="mt-10">
                <KnowledgeCardsTopicBar
                  :key="topicBarKey"
                  :value="topic"
                  :onChange="setTopic"
                  :onStart="() => start(topic)"
                  :onSelectInclude="setIncludeMaterials"
                  :onSelectCount="setCount"
                  :countValue="cardCount"
                  :countOptions="[5, 10, 15]"
                  :isLoading="connecting"
                />
              </div>
            </div>
          </div>

          <div v-if="connecting" class="mt-10">
            <GenerationStatusCard
              emoji="🗂️"
              tone="amber"
              title="知识卡片正在生成"
              description="系统正在提炼知识点、提示词和应用场景，请稍候。"
              phase="generating"
              :steps="knowledgeCardSteps"
            />
          </div>

          <div v-if="deckReady" class="space-y-6">
            <div class="rounded-3xl bg-[color:var(--glass-bg)] border border-[color:var(--glass-border)] p-6 shadow-[0_16px_36px_rgba(0,0,0,0.3)]">
              <div class="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div class="text-xs text-[color:var(--nav-text-muted)]">AI 知识卡片</div>
                  <div class="text-lg font-semibold text-[color:var(--app-text)] flex items-center gap-2">
                    {{ deck?.title || topic || "未命名卡组" }}
                    <span v-if="globalMode" class="text-[10px] px-2 py-0.5 rounded-full bg-slate-900 text-white">全局汇总</span>
                  </div>
                  <div class="text-xs text-[color:var(--nav-text-muted)] mt-1">{{ displayCount }} 张卡片</div>
                </div>
                <div class="flex flex-wrap items-center gap-2">
                  <button
                    type="button"
                    class="inline-flex items-center gap-2 rounded-full bg-[color:var(--nav-bg)] border border-[color:var(--nav-border)] px-4 py-2 text-xs font-semibold text-[color:var(--app-text)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors"
                    @click="toggleReviewMode"
                  >
                    {{ reviewMode ? "列表模式" : "复习模式" }}
                  </button>
                  <button
                    type="button"
                    class="inline-flex items-center gap-2 rounded-full bg-emerald-400/20 border border-emerald-300/40 px-4 py-2 text-xs font-semibold text-slate-950 hover:bg-emerald-400/30 transition-colors disabled:opacity-50"
                    :disabled="savingToBag || !cards.length"
                    @click="saveToLearningBag"
                  >
                    保存到学习袋
                  </button>
                  <button
                    type="button"
                    class="inline-flex items-center gap-2 rounded-full bg-[color:var(--nav-bg)] border border-[color:var(--nav-border)] px-4 py-2 text-xs font-semibold text-[color:var(--app-text)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors"
                    @click="newTopic"
                  >
                    新主题
                  </button>
                  <button
                    type="button"
                    class="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-amber-400 to-orange-400 border border-amber-300/60 px-4 py-2 text-xs font-semibold text-amber-950 shadow-[0_12px_24px_rgba(251,146,60,0.35)] hover:brightness-110 transition-all"
                    @click="start(topic)"
                    :disabled="connecting || !topic"
                  >
                    重新生成
                  </button>
                </div>
              </div>
            </div>

            <div v-if="reviewMode" class="rounded-[32px] border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/80 p-6 shadow-[0_18px_40px_rgba(15,23,42,0.15)]">
              <div class="flex items-center justify-between">
                <div class="text-sm text-[color:var(--nav-text-muted)]">复习进度</div>
                <div class="text-sm text-[color:var(--nav-text-muted)]">{{ displayedCards.length ? activeIndex + 1 : 0 }} / {{ displayedCards.length }}</div>
              </div>
              <div class="mt-3 flex flex-wrap items-center gap-2">
                <button
                  v-for="(card, idx) in displayedCards"
                  :key="card.id"
                  type="button"
                  class="size-10 rounded-full border-2 transition-colors"
                  :class="circleClass(card.id, idx)"
                  @click="jumpToCard(idx)"
                  :aria-label="`跳转到第 ${idx + 1} 张卡片`"
                >
                  <span class="text-sm font-semibold">{{ idx + 1 }}</span>
                </button>
              </div>
              <div v-if="activeCard" class="mt-4 rounded-[28px] border border-[color:var(--glass-border)] bg-[color:var(--app-bg-2)]/70 p-6 shadow-[0_14px_30px_rgba(15,23,42,0.15)] relative">
                <div class="absolute inset-0 pointer-events-none rounded-[24px] bg-[radial-gradient(circle_at_15%_20%,rgba(251,146,60,0.18),transparent_45%),radial-gradient(circle_at_85%_25%,rgba(56,189,248,0.18),transparent_40%),radial-gradient(circle_at_30%_85%,rgba(244,114,182,0.14),transparent_50%)]"></div>
                <div class="relative z-10 aspect-square w-full max-w-[520px] mx-auto">
                  <div class="kc-flip" :class="{ 'is-flipped': flipped[activeCard.id] }">
                    <div class="kc-flip-inner">
                      <div class="kc-face kc-face--front">
                        <div class="kc-face__content">
                <div class="absolute left-1/2 -top-2 -translate-x-1/2">
                  <span class="inline-flex items-center justify-center size-6 rounded-full bg-amber-400/20 text-amber-300 border border-amber-300/40 shadow-[0_6px_12px_rgba(251,146,60,0.35)]">
                    <svg viewBox="0 0 24 24" class="size-3.5" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M12 3l2.25 4.5L19 8.25l-3.5 3.75.75 5.25L12 15.75 7.75 17.25 8.5 12 5 8.25l4.75-.75L12 3z" />
                    </svg>
                  </span>
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-[10px] uppercase tracking-wider text-[color:var(--nav-text-muted)]">{{ flipped[activeCard.id] ? 'Back' : 'Front' }}</span>
                  <div class="flex items-center gap-2">
                    <span v-if="cardStatus[activeCard.id] === 'mastered'" class="text-[10px] px-2 py-0.5 rounded-full bg-emerald-400/20 text-emerald-200">已掌握</span>
                    <span v-else-if="cardStatus[activeCard.id] === 'review'" class="text-[10px] px-2 py-0.5 rounded-full bg-amber-400/20 text-amber-200">待复习</span>
                    <span v-else class="text-[10px] px-2 py-0.5 rounded-full bg-white text-slate-950 border border-slate-300">待确认</span>
                    <button
                      type="button"
                      class="text-lg text-slate-950 hover:text-slate-900 transition-colors border border-sky-300/70 rounded-full px-4 py-1.5 bg-sky-400/10"
                      @click="toggleFlip(activeCard.id)"
                    >
                      翻转卡片
                    </button>
                  </div>
                </div>

                <div class="mt-5 space-y-4">
                  <div class="text-xl font-semibold text-[color:var(--app-text)] kc-fancy">{{ activeCard.concept }}</div>
                  <div class="text-lg text-[color:var(--nav-text)] leading-relaxed kc-fancy">
                    {{ activeCard.question || activeCard.fill_blank }}
                  </div>
                  <button
                    type="button"
                    class="kc-strong inline-flex items-center gap-2 text-base text-slate-950 hover:text-slate-900 transition-colors border border-amber-300/70 rounded-full px-4 py-2 bg-amber-400/15 mt-2"
                    @click="toggleHint(activeCard.id)"
                  >
                    <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M12 3.75a6 6 0 0 1 3 11.25v2.25H9v-2.25a6 6 0 0 1 3-11.25Z" />
                      <path stroke-linecap="round" stroke-linejoin="round" d="M9 20.25h6" />
                    </svg>
                    提示
                  </button>
                  <div v-if="hintShown[activeCard.id]" class="text-sm font-semibold text-[color:var(--nav-text)] bg-emerald-400/10 border-2 border-emerald-400/70 rounded-2xl p-4">
                    {{ activeCard.hint }}
                  </div>
                </div>
                        </div>
                      </div>
                      <div class="kc-face kc-face--back">
                        <div class="kc-face__content">
                <div class="absolute left-1/2 -top-2 -translate-x-1/2">
                  <span class="inline-flex items-center justify-center size-6 rounded-full bg-amber-400/20 text-amber-300 border border-amber-300/40 shadow-[0_6px_12px_rgba(251,146,60,0.35)]">
                    <svg viewBox="0 0 24 24" class="size-3.5" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M12 3l2.25 4.5L19 8.25l-3.5 3.75.75 5.25L12 15.75 7.75 17.25 8.5 12 5 8.25l4.75-.75L12 3z" />
                    </svg>
                  </span>
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-[10px] uppercase tracking-wider text-[color:var(--nav-text-muted)]">{{ flipped[activeCard.id] ? 'Back' : 'Front' }}</span>
                  <div class="flex items-center gap-2">
                    <span v-if="cardStatus[activeCard.id] === 'mastered'" class="text-[10px] px-2 py-0.5 rounded-full bg-emerald-400/20 text-emerald-200">已掌握</span>
                    <span v-else-if="cardStatus[activeCard.id] === 'review'" class="text-[10px] px-2 py-0.5 rounded-full bg-amber-400/20 text-amber-200">待复习</span>
                    <span v-else class="text-[10px] px-2 py-0.5 rounded-full bg-white text-slate-950 border border-slate-300">待确认</span>
                    <button
                      type="button"
                      class="text-lg text-slate-950 hover:text-slate-900 transition-colors border border-sky-300/70 rounded-full px-4 py-1.5 bg-sky-400/10"
                      @click="toggleFlip(activeCard.id)"
                    >
                      翻转卡片
                    </button>
                  </div>
                </div>

                <div class="mt-5 space-y-4">
                  <div>
                    <div class="text-sm text-[color:var(--nav-text-muted)]">参考答案</div>
                    <div class="text-lg text-[color:var(--app-text)] mt-1 leading-relaxed kc-fancy">{{ activeCard.answer }}</div>
                  </div>
                  <div class="rounded-2xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 p-4">
                    <div class="text-sm text-[color:var(--nav-text-muted)]">助记词</div>
                    <div class="text-base text-[color:var(--app-text)] mt-1">{{ activeCard.mnemonic }}</div>
                  </div>
                  <div class="rounded-2xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 p-4">
                    <div class="text-sm text-[color:var(--nav-text-muted)]">应用案例</div>
                    <div class="text-base text-[color:var(--app-text)] mt-1">{{ activeCard.application }}</div>
                  </div>
                </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div class="mt-4 flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  class="inline-flex items-center gap-2 rounded-full bg-white border border-slate-300 px-4 py-2 text-xs font-semibold text-slate-950 hover:bg-slate-100 transition-colors"
                  @click="setStatus(activeCard?.id, 'pending')"
                  :disabled="!activeCard"
                >
                  待确认
                </button>
                <button
                  type="button"
                  class="inline-flex items-center gap-2 rounded-full bg-emerald-400/20 border border-emerald-300/40 px-4 py-2 text-xs font-semibold text-slate-950 hover:bg-emerald-400/30 transition-colors"
                  @click="setStatus(activeCard?.id, 'mastered')"
                  :disabled="!activeCard"
                >
                  标记掌握
                </button>
                <button
                  type="button"
                  class="inline-flex items-center gap-2 rounded-full bg-amber-400/20 border border-amber-300/40 px-4 py-2 text-xs font-semibold text-slate-950 hover:bg-amber-400/30 transition-colors"
                  @click="setStatus(activeCard?.id, 'review')"
                  :disabled="!activeCard"
                >
                  待复习
                </button>
                <div class="flex-1"></div>
                <button
                  type="button"
                  class="inline-flex items-center gap-2 rounded-full bg-[color:var(--nav-bg)] border border-[color:var(--nav-border)] px-4 py-2 text-xs font-semibold text-[color:var(--app-text)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors"
                  @click="prevCard"
                  :disabled="activeIndex === 0"
                >
                  上一张
                </button>
                <button
                  type="button"
                  class="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-amber-400 to-orange-400 border border-amber-300/60 px-4 py-2 text-xs font-semibold text-amber-950 shadow-[0_12px_24px_rgba(251,146,60,0.35)] hover:brightness-110 transition-all"
                  @click="nextCard"
                  :disabled="!activeCard"
                >
                  下一张
                </button>
              </div>
            </div>

            <div v-else class="grid gap-5 sm:grid-cols-2">
              <div
                v-for="card in displayedCards"
                :key="card.id"
                class="rounded-[28px] border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/80 p-6 shadow-[0_14px_30px_rgba(15,23,42,0.15)] relative overflow-hidden aspect-square"
              >
                <div class="absolute inset-0 pointer-events-none rounded-[24px] bg-[radial-gradient(circle_at_15%_20%,rgba(251,146,60,0.16),transparent_45%),radial-gradient(circle_at_85%_25%,rgba(56,189,248,0.16),transparent_40%),radial-gradient(circle_at_30%_85%,rgba(244,114,182,0.12),transparent_50%)]"></div>
                <div class="relative z-10 h-full">
                  <div class="kc-flip" :class="{ 'is-flipped': flipped[card.id] }">
                    <div class="kc-flip-inner">
                      <div class="kc-face kc-face--front">
                        <div class="kc-face__content">
                <div class="absolute left-1/2 -top-2 -translate-x-1/2">
                  <span class="inline-flex items-center justify-center size-6 rounded-full bg-amber-400/20 text-amber-300 border border-amber-300/40 shadow-[0_6px_12px_rgba(251,146,60,0.35)]">
                    <svg viewBox="0 0 24 24" class="size-3.5" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M12 3l2.25 4.5L19 8.25l-3.5 3.75.75 5.25L12 15.75 7.75 17.25 8.5 12 5 8.25l4.75-.75L12 3z" />
                    </svg>
                  </span>
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-[10px] uppercase tracking-wider text-[color:var(--nav-text-muted)]">{{ flipped[card.id] ? 'Back' : 'Front' }}</span>
                  <div class="flex items-center gap-2">
                    <span v-if="cardStatus[card.id] === 'mastered'" class="text-[10px] px-2 py-0.5 rounded-full bg-emerald-400/20 text-emerald-200">已掌握</span>
                    <span v-else-if="cardStatus[card.id] === 'review'" class="text-[10px] px-2 py-0.5 rounded-full bg-amber-400/20 text-amber-200">待复习</span>
                    <span v-else class="text-[10px] px-2 py-0.5 rounded-full bg-white text-slate-950 border border-slate-300">待确认</span>
                    <button
                      type="button"
                      class="text-lg text-slate-950 hover:text-slate-900 transition-colors border border-sky-300/70 rounded-full px-4 py-1.5 bg-sky-400/10"
                      @click="toggleFlip(card.id)"
                    >
                      翻转卡片
                    </button>
                  </div>
                </div>

                <div class="mt-5 space-y-4">
                  <div class="text-xl font-semibold text-[color:var(--app-text)] kc-fancy">{{ card.concept }}</div>
                  <div class="text-lg text-[color:var(--nav-text)] leading-relaxed kc-fancy">
                    {{ card.question || card.fill_blank }}
                  </div>
                  <button
                    type="button"
                    class="kc-strong inline-flex items-center gap-2 text-base text-slate-950 hover:text-slate-900 transition-colors border border-amber-300/70 rounded-full px-4 py-2 bg-amber-400/15 mt-2"
                    @click="toggleHint(card.id)"
                  >
                    <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M12 3.75a6 6 0 0 1 3 11.25v2.25H9v-2.25a6 6 0 0 1 3-11.25Z" />
                      <path stroke-linecap="round" stroke-linejoin="round" d="M9 20.25h6" />
                    </svg>
                    提示
                  </button>
                  <div v-if="hintShown[card.id]" class="text-sm font-semibold text-[color:var(--nav-text)] bg-emerald-400/10 border-2 border-emerald-400/70 rounded-2xl p-4">
                    {{ card.hint }}
                  </div>
                </div>
                        </div>
                      </div>
                      <div class="kc-face kc-face--back">
                        <div class="kc-face__content">
                <div class="absolute left-1/2 -top-2 -translate-x-1/2">
                  <span class="inline-flex items-center justify-center size-6 rounded-full bg-amber-400/20 text-amber-300 border border-amber-300/40 shadow-[0_6px_12px_rgba(251,146,60,0.35)]">
                    <svg viewBox="0 0 24 24" class="size-3.5" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M12 3l2.25 4.5L19 8.25l-3.5 3.75.75 5.25L12 15.75 7.75 17.25 8.5 12 5 8.25l4.75-.75L12 3z" />
                    </svg>
                  </span>
                </div>
                <div class="flex items-center justify-between">
                  <span class="text-[10px] uppercase tracking-wider text-[color:var(--nav-text-muted)]">{{ flipped[card.id] ? 'Back' : 'Front' }}</span>
                  <div class="flex items-center gap-2">
                    <span v-if="cardStatus[card.id] === 'mastered'" class="text-[10px] px-2 py-0.5 rounded-full bg-emerald-400/20 text-emerald-200">已掌握</span>
                    <span v-else-if="cardStatus[card.id] === 'review'" class="text-[10px] px-2 py-0.5 rounded-full bg-amber-400/20 text-amber-200">待复习</span>
                    <span v-else class="text-[10px] px-2 py-0.5 rounded-full bg-white text-slate-950 border border-slate-300">待确认</span>
                    <button
                      type="button"
                      class="text-lg text-slate-950 hover:text-slate-900 transition-colors border border-sky-300/70 rounded-full px-4 py-1.5 bg-sky-400/10"
                      @click="toggleFlip(card.id)"
                    >
                      翻转卡片
                    </button>
                  </div>
                </div>

                <div class="mt-5 space-y-4">
                  <div>
                    <div class="text-sm text-[color:var(--nav-text-muted)]">参考答案</div>
                    <div class="text-lg text-[color:var(--app-text)] mt-1 leading-relaxed kc-fancy">{{ card.answer }}</div>
                  </div>
                  <div class="rounded-2xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 p-4">
                    <div class="text-sm text-[color:var(--nav-text-muted)]">助记词</div>
                    <div class="text-base text-[color:var(--app-text)] mt-1">{{ card.mnemonic }}</div>
                  </div>
                  <div class="rounded-2xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 p-4">
                    <div class="text-sm text-[color:var(--nav-text-muted)]">应用案例</div>
                    <div class="text-base text-[color:var(--app-text)] mt-1">{{ card.application }}</div>
                  </div>
                  <div class="flex items-center gap-2">
                    <button
                      type="button"
                      class="inline-flex items-center gap-2 rounded-full bg-white border border-slate-300 px-3 py-1.5 text-[10px] font-semibold text-slate-950 hover:bg-slate-100 transition-colors"
                      @click="setStatus(card.id, 'pending')"
                    >
                      待确认
                    </button>
                    <button
                      type="button"
                      class="inline-flex items-center gap-2 rounded-full bg-emerald-400/20 border border-emerald-300/40 px-3 py-1.5 text-[10px] font-semibold text-slate-950 hover:bg-emerald-400/30 transition-colors"
                      @click="setStatus(card.id, 'mastered')"
                    >
                      标记掌握
                    </button>
                    <button
                      type="button"
                      class="inline-flex items-center gap-2 rounded-full bg-amber-400/20 border border-amber-300/40 px-3 py-1.5 text-[10px] font-semibold text-slate-950 hover:bg-amber-400/30 transition-colors"
                      @click="setStatus(card.id, 'review')"
                    >
                      待复习
                    </button>
                  </div>
                </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-if="summaryOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div class="w-full max-w-xl rounded-3xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/95 p-6 shadow-[0_18px_40px_rgba(0,0,0,0.35)]">
              <div class="flex items-center justify-between">
                <div class="text-lg font-semibold text-[color:var(--app-text)]">复习汇总</div>
                <button
                  type="button"
                  class="text-sm text-slate-950 border border-[color:var(--nav-border)] rounded-full px-3 py-1 hover:bg-[color:var(--nav-hover-bg-strong)]"
                  @click="summaryOpen = false"
                >
                  关闭
                </button>
              </div>
              <div class="mt-4 flex flex-wrap items-center gap-3">
                <div
                  v-for="(card, idx) in displayedCards"
                  :key="card.id"
                  class="flex items-center gap-2"
                >
                  <span
                    class="size-9 rounded-full border-2 inline-flex items-center justify-center text-sm font-semibold"
                    :class="circleClass(card.id, idx)"
                  >
                    {{ idx + 1 }}
                  </span>
                  <span class="text-sm text-[color:var(--app-text)]">{{ card.concept }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  createFlashcard,
  generateKnowledgeDeck,
  getKnowledgeDeck,
  listKnowledgeDecks,
  type KnowledgeCard,
  type KnowledgeDeck,
} from "../lib/api";
import { getUserScopedStorageKey, readScopedStorage } from "../lib/userStorage";
import LearningFolderPanel from "../components/LearningFolderPanel.vue";
import KnowledgeCardsHistoryPanel from "../components/KnowledgeCards/KnowledgeCardsHistoryPanel.vue";
import KnowledgeCardsTopicBar from "../components/KnowledgeCards/KnowledgeCardsTopicBar.vue";
import GenerationStatusCard from "../components/common/GenerationStatusCard.vue";

const route = useRoute();
const router = useRouter();

const passedDeckId = (route as any)?.state?.deckId || "";
const initialDeckId = (route.query.deckId as string) || passedDeckId || "";

const topic = ref("");
const deckId = ref(initialDeckId);
const cards = ref<KnowledgeCard[]>([]);
const deck = ref<KnowledgeDeck | null>(null);
const connecting = ref(false);
const includeMaterials = ref(false);
const cardCount = ref(5);
const topicBarKey = ref(0);
const reviewMode = ref(true);
const activeIndex = ref(0);
const cardStatus = ref<Record<string, "mastered" | "review" | "pending" | "">>({});
const cardDeckMap = ref<Record<string, string>>({});
const savingToBag = ref(false);
const quickTopics = ["软件工程", "计算机网络分层", "数据结构时间复杂度", "概率论条件概率", "极限的概念", "英语时态"];
const knowledgeCardSteps = [
  { key: "generating", label: "正在提炼知识点" },
  { key: "done", label: "正在整理卡片结构" },
];

const hintShown = ref<Record<string, boolean>>({});
const flipped = ref<Record<string, boolean>>({});

const LEARNING_FOLDER_KEY = computed(() => getUserScopedStorageKey("edumind-learning-folder"));
const closeRef = ref<null | (() => void)>(null);

const deckReady = computed(() => Boolean(deck.value && cards.value.length));
const filterStatus = computed(() => {
  const raw = String(route.query.status || "");
  if (raw === "mastered" || raw === "review" || raw === "pending") return raw;
  return "";
});
const globalMode = computed(() => Boolean(filterStatus.value && !deckId.value));
const displayedCards = computed(() => {
  if (!filterStatus.value) return cards.value;
  return cards.value.filter((card) => (cardStatus.value[card.id] || "pending") === filterStatus.value);
});
const displayCount = computed(() => displayedCards.value.length);
const activeCard = computed(() => displayedCards.value[activeIndex.value] || null);

const setTopic = (value: string) => {
  topic.value = value;
};

const onQuickTopic = (value: string) => {
  if (connecting.value) return;
  topic.value = value;
  start(value);
};

const setIncludeMaterials = (next: boolean) => {
  includeMaterials.value = next;
};

const setCount = (next: number) => {
  cardCount.value = next;
};

const loadLearningFolderIds = () => {
  try {
    const raw = readScopedStorage(LEARNING_FOLDER_KEY.value);
    const parsed = raw ? (JSON.parse(raw) as string[]) : [];
    return Array.isArray(parsed) ? parsed.filter(Boolean) : [];
  } catch {
    return [] as string[];
  }
};

const resetState = () => {
  cards.value = [];
  deck.value = null;
  deckId.value = "";
  topic.value = "";
  includeMaterials.value = false;
  cardCount.value = 5;
  hintShown.value = {};
  flipped.value = {};
  cardStatus.value = {};
  cardDeckMap.value = {};
  activeIndex.value = 0;
  reviewMode.value = true;
  summaryOpen.value = false;
  topicBarKey.value += 1;
};

const toggleHint = (id: string) => {
  hintShown.value = { ...hintShown.value, [id]: !hintShown.value[id] };
};

const toggleFlip = (id: string) => {
  flipped.value = { ...flipped.value, [id]: !flipped.value[id] };
};

const toggleReviewMode = () => {
  reviewMode.value = !reviewMode.value;
};

const jumpToCard = (idx: number) => {
  if (idx < 0 || idx >= displayedCards.value.length) return;
  activeIndex.value = idx;
};

const circleClass = (id: string, idx: number) => {
  const status = cardStatus.value[id];
  const isActive = idx === activeIndex.value;
  if (status === "mastered") return `border-2 border-emerald-400 bg-emerald-300/70 text-slate-950 ${isActive ? "ring-2 ring-emerald-300/80" : ""}`;
  if (status === "review") return `border-2 border-amber-400 bg-amber-300/70 text-slate-950 ${isActive ? "ring-2 ring-amber-300/80" : ""}`;
  return `border-2 border-slate-400/70 bg-white text-slate-950 ${isActive ? "ring-2 ring-sky-300/80" : ""}`;
};

const readStatusMap = (targetDeckId: string) => {
  if (!targetDeckId) return {} as Record<string, "mastered" | "review" | "pending" | "">;
  try {
    const raw = localStorage.getItem(getUserScopedStorageKey(`knowledge-cards:status:${targetDeckId}`));
    const parsed = raw ? JSON.parse(raw) : {};
    return parsed || {};
  } catch {
    return {} as Record<string, "mastered" | "review" | "pending" | "">;
  }
};

const persistStatusMap = (targetDeckId: string, nextMap: Record<string, "mastered" | "review" | "pending" | "">) => {
  if (!targetDeckId) return;
  try {
    localStorage.setItem(getUserScopedStorageKey(`knowledge-cards:status:${targetDeckId}`), JSON.stringify(nextMap));
  } catch {
    return;
  }
};

const loadCardStatus = (nextDeckId: string) => {
  if (!nextDeckId) return;
  cardStatus.value = readStatusMap(nextDeckId);
};

const statusLabelMap: Record<string, string> = {
  mastered: "标记掌握",
  pending: "待确认",
  review: "待复习",
};

const loadGlobalStatusDeck = async (status: "mastered" | "review" | "pending") => {
  connecting.value = true;
  cards.value = [];
  deck.value = null;
  deckId.value = "";
  cardStatus.value = {};
  cardDeckMap.value = {};
  hintShown.value = {};
  flipped.value = {};
  activeIndex.value = 0;
  reviewMode.value = true;
  summaryOpen.value = false;

  try {
    const res = await listKnowledgeDecks();
    const metas = Array.isArray(res?.decks) ? res.decks : [];
    const nextCards: KnowledgeCard[] = [];
    const nextStatusMap: Record<string, "mastered" | "review" | "pending"> = {};
    const nextDeckMap: Record<string, string> = {};

    await Promise.all(
      metas.map(async (meta) => {
        const detail = await getKnowledgeDeck(meta.id).catch(() => undefined);
        if (!detail?.ok || !detail.deck) return;
        const stored = readStatusMap(meta.id);
        detail.deck.cards.forEach((card) => {
          const currentStatus = (stored[card.id] || "pending") as "mastered" | "review" | "pending";
          nextStatusMap[card.id] = currentStatus;
          nextDeckMap[card.id] = meta.id;
          if (currentStatus === status) nextCards.push(card);
        });
      })
    );

    cards.value = nextCards;
    cardStatus.value = nextStatusMap;
    cardDeckMap.value = nextDeckMap;
    deck.value = {
      id: "global",
      title: `全局复习 · ${statusLabelMap[status]}`,
      count: nextCards.length,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      cards: nextCards,
    } as KnowledgeDeck;
  } finally {
    connecting.value = false;
  }
};

const setStatus = (id: string | null | undefined, status: "mastered" | "review" | "pending") => {
  if (!id) return;
  const targetDeckId = deckId.value || cardDeckMap.value[id];
  if (!targetDeckId) return;
  const existingMap = targetDeckId === deckId.value ? cardStatus.value : readStatusMap(targetDeckId);
  const nextMap = { ...existingMap, [id]: status };
  cardStatus.value = { ...cardStatus.value, [id]: status };
  persistStatusMap(targetDeckId, nextMap);
  notifyHistoryUpdated(targetDeckId);
};

const summaryOpen = ref(false);

const nextCard = () => {
  if (!activeCard.value) return;
  const isLast = activeIndex.value >= displayedCards.value.length - 1;
  if (isLast) {
    summaryOpen.value = true;
    return;
  }
  activeIndex.value = Math.min(displayedCards.value.length - 1, activeIndex.value + 1);
};

const prevCard = () => {
  activeIndex.value = Math.max(0, activeIndex.value - 1);
};

const notifyHistoryUpdated = (nextDeckId?: string) => {
  try {
    window.dispatchEvent(new CustomEvent("knowledge-cards:updated", { detail: { deckId: nextDeckId || deckId.value } }));
  } catch {
    return;
  }
};

const start = async (input: string) => {
  const trimmed = input.trim();
  if (!trimmed) return;
  if (closeRef.value) closeRef.value();

  connecting.value = true;
  cards.value = [];
  deck.value = null;

  try {
    const materialIds = includeMaterials.value ? loadLearningFolderIds() : [];
    const useMaterials = includeMaterials.value && materialIds.length > 0;
    const res = await generateKnowledgeDeck({
      topic: trimmed,
      includeMaterials: useMaterials,
      materialIds: useMaterials ? materialIds : [],
      count: cardCount.value,
    });
    if (!res?.deck?.id) throw new Error("deck id missing");

    deck.value = res.deck;
    cards.value = res.deck.cards || [];
    deckId.value = res.deck.id;
    topic.value = res.deck.title || trimmed;
    cardCount.value = res.deck.count || cardCount.value;
    cardDeckMap.value = Object.fromEntries((res.deck.cards || []).map((card) => [card.id, res.deck.id]));
    hintShown.value = {};
    flipped.value = {};
    activeIndex.value = 0;
    reviewMode.value = true;
    summaryOpen.value = false;
    loadCardStatus(res.deck.id);

    notifyHistoryUpdated(res.deck.id);
    router.replace({ path: "/knowledge-cards", query: { deckId: res.deck.id }, state: { deckId: res.deck.id } });
  } catch {
    connecting.value = false;
    return;
  } finally {
    connecting.value = false;
  }
};

const loadDeck = async (nextDeckId: string) => {
  if (!nextDeckId) return;
  connecting.value = false;
  try {
    const res = await getKnowledgeDeck(nextDeckId);
    if (res?.ok && res.deck) {
      deck.value = res.deck;
      cards.value = res.deck.cards || [];
      topic.value = res.deck.title || topic.value;
      cardCount.value = res.deck.count || cardCount.value;
      deckId.value = nextDeckId;
      cardDeckMap.value = Object.fromEntries((res.deck.cards || []).map((card) => [card.id, nextDeckId]));
      hintShown.value = {};
      flipped.value = {};
      activeIndex.value = 0;
      reviewMode.value = true;
      summaryOpen.value = false;
      loadCardStatus(nextDeckId);
      notifyHistoryUpdated(nextDeckId);
    }
  } catch {
    return;
  }
};

const saveToLearningBag = async () => {
  if (!cards.value.length) return;
  savingToBag.value = true;
  try {
    await Promise.all(
      cards.value.map((card) =>
        createFlashcard({
          question: `${card.concept}：${card.question || card.fill_blank || ""}`.trim(),
          answer: `${card.answer}\n助记词：${card.mnemonic}\n应用：${card.application}`.trim(),
          tag: "knowledge",
        }).catch(() => undefined)
      )
    );
  } finally {
    savingToBag.value = false;
  }
};


const newTopic = () => {
  if (closeRef.value) closeRef.value();
  resetState();
  router.push({ path: "/knowledge-cards", query: { new: String(Date.now()) } });
};

onMounted(() => {
  if (initialDeckId) {
    loadDeck(initialDeckId);
    return;
  }
  if (filterStatus.value) {
    loadGlobalStatusDeck(filterStatus.value as "mastered" | "review" | "pending");
  }
});

watch(
  () => route.query.deckId,
  async (next, prev) => {
    if (connecting.value) return;
    const nextId = (next as string) || (route as any)?.state?.deckId || "";
    if (!nextId) {
      if (filterStatus.value) {
        await loadGlobalStatusDeck(filterStatus.value as "mastered" | "review" | "pending");
        return;
      }
      resetState();
      return;
    }
    if (nextId === deckId.value && prev === next) return;
    await loadDeck(nextId);
  }
);

watch(
  () => route.query.status,
  async (next) => {
    if (!next) return;
    if (deckId.value) return;
    if (filterStatus.value) {
      await loadGlobalStatusDeck(filterStatus.value as "mastered" | "review" | "pending");
    }
  }
);

watch(
  () => [displayedCards.value.length, filterStatus.value],
  () => {
    if (!displayedCards.value.length) {
      activeIndex.value = 0;
      summaryOpen.value = false;
      return;
    }
    if (activeIndex.value >= displayedCards.value.length) {
      activeIndex.value = 0;
      summaryOpen.value = false;
    }
  }
);

watch(
  () => route.query.t,
  async (next, prev) => {
    if (!next || next === prev) return;
    const nextId = (route.query.deckId as string) || "";
    if (nextId && route.path === "/knowledge-cards") {
      await loadDeck(nextId);
    }
  }
);

watch(
  () => route.query.new,
  (next) => {
    if (connecting.value) return;
    if (route.query.deckId) return;
    if (!next) return;
    if (route.path === "/knowledge-cards") {
      resetState();
    }
  }
);

onBeforeUnmount(() => {
  if (closeRef.value) closeRef.value();
});
</script>

<style scoped>
@import url("https://fonts.googleapis.com/css2?family=Baloo+2:wght@500;700&display=swap");

.kc-fancy {
  font-family: "Baloo 2", "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", sans-serif;
}

.kc-strong {
  font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", sans-serif;
  font-weight: 700;
}

:deep(.knowledge-cards .text-xs),
:deep(.knowledge-cards .text-sm),
:deep(.knowledge-cards .text-\[10px\]) {
  font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", sans-serif;
  color: var(--app-text);
  font-weight: 600;
}

.kc-flip {
  position: relative;
  width: 100%;
  height: 100%;
  perspective: 1200px;
}

.kc-flip-inner {
  position: relative;
  width: 100%;
  height: 100%;
  transform-style: preserve-3d;
  transition: transform 0.7s cubic-bezier(0.22, 0.61, 0.36, 1);
}

.kc-flip.is-flipped .kc-flip-inner {
  transform: rotateY(180deg);
}

.kc-face {
  position: absolute;
  inset: 0;
  backface-visibility: hidden;
  transform: translateZ(1px);
}

.kc-face--back {
  transform: rotateY(180deg) translateZ(1px);
}

.kc-face__content {
  position: relative;
  height: 100%;
  display: flex;
  flex-direction: column;
}

@media (prefers-reduced-motion: reduce) {
  .kc-flip-inner {
    transition: none;
  }
}
</style>
