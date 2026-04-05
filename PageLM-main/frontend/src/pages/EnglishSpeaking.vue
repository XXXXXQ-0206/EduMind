<template>
  <div class="speaking-page speaking-body relative min-h-screen overflow-hidden px-4 md:pl-60 md:pr-6 lg:pl-64 lg:pr-12">
    <div class="absolute inset-0 bg-grid-pattern opacity-20 pointer-events-none"></div>
    <div class="speaking-orb speaking-orb--one"></div>
    <div class="speaking-orb speaking-orb--two"></div>
    <div class="speaking-orb speaking-orb--three"></div>

    <div class="relative z-10 mx-auto flex w-full max-w-6xl flex-col gap-10 py-16">
      <template v-if="!showPractice">
        <header class="flex flex-col gap-6">
        <div class="speaking-badge">
          <span class="speaking-dot"></span>
          AI 智能生成 · 真人级发音 · 实时语音评测
        </div>
        <div class="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div class="max-w-2xl">
            <h1 class="speaking-heading speaking-title text-3xl md:text-4xl lg:text-5xl font-semibold">
              英语口语跟读 · 智能纠音训练
            </h1>
            <p class="speaking-muted speaking-muted-light mt-3 text-base md:text-lg">
              AI 按需生成单词、短语或句子，听标准英/美音发音后跟读录音，系统实时评测准确度、流利度与标准度，精准标注每个发音薄弱点。
            </p>
          </div>
          <div class="flex flex-wrap items-center gap-3">
            <button
              type="button"
              class="speaking-pill speaking-pill--primary"
              :disabled="isGenerating"
              @click="onGenerate"
            >
              {{ isGenerating ? "生成中..." : "生成练习清单" }}
            </button>
          </div>
        </div>
      </header>

      <section class="grid grid-cols-1 gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <div class="clay-card speaking-fade setup-card">
          <div class="flex flex-col gap-6">
            <div class="flex flex-wrap items-start justify-between gap-4">
              <div>
                <div class="speaking-muted text-xs font-semibold">生成设置</div>
                <div class="speaking-heading speaking-title mt-2 text-xl font-semibold">自定义练习内容</div>
              </div>
              <div class="speaking-chip">
                默认：5 个单词 · 英音
              </div>
            </div>

            <div class="grid grid-cols-1 gap-5 sm:grid-cols-2">
              <div>
                <div class="speaking-label text-sm font-semibold mb-2 flex items-center gap-2">
                  <span class="label-icon label-icon--count">
                    <svg class="icon-sm" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <path d="M9 6h11M9 12h11M9 18h11M4 6h.01M4 12h.01M4 18h.01" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
                    </svg>
                  </span>
                  生成数量
                </div>
                <div class="flex flex-wrap gap-2">
                  <button
                    v-for="count in countOptions"
                    :key="count"
                    type="button"
                    class="clay-chip chip-count"
                    :class="selectedCount === count ? 'clay-chip--active' : ''"
                    @click="selectedCount = count"
                  >
                    {{ count }} 个
                  </button>
                </div>
              </div>
              <div>
                <div class="speaking-label text-sm font-semibold mb-2 flex items-center gap-2">
                  <span class="label-icon label-icon--difficulty">
                    <svg class="icon-sm" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <path d="M4 14a8 8 0 1 1 16 0" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
                    <path d="M12 14l4-4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
                    </svg>
                  </span>
                  难度等级
                </div>
                <div class="flex flex-wrap gap-2">
                  <button
                    v-for="option in difficultyOptions"
                    :key="option.key"
                    type="button"
                    class="clay-chip chip-difficulty"
                    :class="selectedDifficulty === option.key ? 'clay-chip--active' : ''"
                    @click="selectedDifficulty = option.key"
                  >
                    {{ option.label }}
                  </button>
                </div>
              </div>
            </div>

            <div class="flex flex-wrap gap-3">
              <div class="speaking-label w-full text-sm font-semibold flex items-center gap-2">
                <span class="label-icon label-icon--type">
                  <svg class="icon-sm" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <path d="M6 6h12M9 12h6M11 18h2" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
                  </svg>
                </span>
                生成类型
              </div>
              <button
                v-for="option in typeOptions"
                :key="option.key"
                type="button"
                class="clay-chip"
                :class="selectedType === option.key ? 'clay-chip--active' : ''"
                @click="selectedType = option.key"
              >
                {{ option.label }}
              </button>
            </div>

            <div class="flex flex-wrap gap-3">
              <div class="speaking-label w-full text-sm font-semibold flex items-center gap-2">
                <span class="label-icon label-icon--voice">
                  <svg class="icon-sm" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <path d="M5 10v4h4l5 4V6l-5 4H5Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>
                    <path d="M17 9a5 5 0 0 1 0 6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
                  </svg>
                </span>
                示范口音
              </div>
              <button
                type="button"
                class="clay-chip"
                :class="selectedVoice === 'british' ? 'clay-chip--active' : ''"
                @click="selectedVoice = 'british'"
              >
                英音
              </button>
              <button
                type="button"
                class="clay-chip"
                :class="selectedVoice === 'american' ? 'clay-chip--active' : ''"
                @click="selectedVoice = 'american'"
              >
                美音
              </button>
            </div>

            <div class="speaking-panel">
              <div class="speaking-muted text-xs font-semibold flex items-center gap-2">
                <svg class="icon-sm" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <path d="M21 12a9 9 0 0 1-15.5 6.36M3 12A9 9 0 0 1 18.5 5.64" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
                  <path d="M3 4v4h4M21 20v-4h-4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                智能学习流程
              </div>
              <div class="mt-3 grid gap-3 sm:grid-cols-2">
                <div class="clay-step">
                  <span class="clay-step__dot clay-step__dot--ai">
                    <svg class="icon-xs" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                      <rect x="6" y="8" width="12" height="10" rx="3" stroke="currentColor" stroke-width="1.8"/>
                      <path d="M12 4v4M9 12h.01M15 12h.01" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
                    </svg>
                  </span>
                  <div>
                    <div class="speaking-label text-sm font-semibold">AI 智能生成</div>
                    <div class="speaking-muted text-xs">大模型按难度自动生成练习内容</div>
                  </div>
                </div>
                <div class="clay-step">
                  <span class="clay-step__dot clay-step__dot--tts">
                    <svg class="icon-xs" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                      <path d="M5 10v4h4l5 4V6l-5 4H5Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>
                      <path d="M17 9a5 5 0 0 1 0 6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
                    </svg>
                  </span>
                  <div>
                    <div class="speaking-label text-sm font-semibold">真人级发音</div>
                    <div class="speaking-muted text-xs">英音 / 美音标准示范朗读</div>
                  </div>
                </div>
                <div class="clay-step">
                  <span class="clay-step__dot clay-step__dot--mic">
                    <svg class="icon-xs" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                      <rect x="9" y="4" width="6" height="11" rx="3" stroke="currentColor" stroke-width="1.8"/>
                      <path d="M6 11a6 6 0 0 0 12 0M12 17v3M9 20h6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
                    </svg>
                  </span>
                  <div>
                    <div class="speaking-label text-sm font-semibold">跟读录音</div>
                    <div class="speaking-muted text-xs">浏览器一键录音 · 实时波形反馈</div>
                  </div>
                </div>
                <div class="clay-step">
                  <span class="clay-step__dot clay-step__dot--score">
                    <svg class="icon-xs" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                      <path d="M4 19h16M7 16V9M12 16V6M17 16v-4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
                    </svg>
                  </span>
                  <div>
                    <div class="speaking-label text-sm font-semibold">智能评测打分</div>
                    <div class="speaking-muted text-xs">准确度 · 流利度 · 标准度三维评估</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="flex flex-col gap-6">
          <div class="clay-card speaking-fade compact-panel dashboard-card" style="animation-delay: 120ms;">
            <div class="flex items-center justify-between gap-3">
              <div>
                <div class="speaking-muted text-xs font-semibold flex items-center gap-2">
                  <svg class="icon-sm" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <path d="M4 19h16M7 16V9M12 16V6M17 16v-4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
                  </svg>
                  口语能力仪表盘
                </div>
                <div class="speaking-heading speaking-title text-2xl font-semibold">
                  {{ dashboardMetrics.total.toFixed(1) }} / 100
                </div>
              </div>
              <button
                type="button"
                class="speaking-pill speaking-pill--ghost text-xs"
                @click="syncDashboardFromHistory"
              >
                更新
              </button>
            </div>

            <div class="mt-3 grid gap-3 md:grid-cols-[1fr_160px] md:items-center">
              <div class="space-y-3">
                <div class="score-row">
                  <span class="score-metric-label">准确度
                    <strong class="score-metric-value" :style="{ color: scoreColor(dashboardMetrics.accuracy) }">{{ dashboardMetrics.accuracy.toFixed(1) }}</strong>
                  </span>
                  <div class="score-bar"><div class="score-fill" :style="{ width: dashboardMetrics.accuracy + '%' }"></div></div>
                </div>
                <div class="score-row">
                  <span class="score-metric-label">流利度
                    <strong class="score-metric-value" :style="{ color: scoreColor(dashboardMetrics.fluency) }">{{ dashboardMetrics.fluency.toFixed(1) }}</strong>
                  </span>
                  <div class="score-bar"><div class="score-fill" :style="{ width: dashboardMetrics.fluency + '%' }"></div></div>
                </div>
                <div class="score-row">
                  <span class="score-metric-label">标准度
                    <strong class="score-metric-value" :style="{ color: scoreColor(dashboardMetrics.standard) }">{{ dashboardMetrics.standard.toFixed(1) }}</strong>
                  </span>
                  <div class="score-bar"><div class="score-fill" :style="{ width: dashboardMetrics.standard + '%' }"></div></div>
                </div>
              </div>

              <div class="radar-wrap" aria-label="三维雷达图">
                <div ref="dashboardRadarRef" class="dashboard-radar"></div>
              </div>
            </div>
          </div>

          <div class="clay-card speaking-fade compact-panel" style="animation-delay: 200ms;">
            <div class="speaking-muted text-xs font-semibold flex items-center gap-2">
              <svg class="icon-sm" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <rect x="9" y="4" width="6" height="11" rx="3" stroke="currentColor" stroke-width="1.8"/>
                <path d="M6 11a6 6 0 0 0 12 0M12 17v3M9 20h6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
              </svg>
              实时录音
            </div>
            <div class="speaking-heading speaking-title mt-2 text-xl font-semibold">一键跟读录音</div>
            <p class="speaking-muted mt-2 text-sm">点击录音后显示实时波形，结束后自动上传评测，无需手动操作。</p>
            <div class="mt-3 flex items-center gap-3">
              <div class="waveform">
                <span v-for="bar in 10" :key="bar" class="waveform__bar"></span>
              </div>
              <div class="speaking-muted text-xs font-semibold">00:12</div>
            </div>
            <div class="speaking-muted mt-3 flex flex-wrap gap-2 text-xs">
              <span class="clay-tag">浏览器录音</span>
              <span class="clay-tag">16kHz 高清</span>
              <span class="clay-tag">自动评测</span>
            </div>
          </div>

          <div class="clay-card speaking-fade" style="animation-delay: 260ms;">
            <div class="speaking-muted text-xs font-semibold flex items-center gap-2">
              <svg class="icon-sm" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <circle cx="12" cy="12" r="8" stroke="currentColor" stroke-width="1.8"/>
                <path d="m12 8 3 4-3 4-3-4 3-4Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>
              </svg>
              智能纠音
            </div>
            <div class="speaking-muted mt-2 text-sm">
              每个词逐一评分，<b>绿色</b>表示标准、<b>橙色</b>需注意、<b>红色</b>需纠正，助你精准提升。
            </div>
            <div class="mt-3 flex flex-wrap gap-2">
              <span class="feedback-pill feedback-pill--good">excellent ✓</span>
              <span class="feedback-pill feedback-pill--warn">attention</span>
              <span class="feedback-pill feedback-pill--bad">practice ✗</span>
            </div>
          </div>
        </div>
      </section>

      <!-- History section -->
      <section class="speaking-fade" style="animation-delay: 320ms;">
        <div class="flex items-center justify-between mb-4">
          <h2 class="speaking-heading speaking-title text-xl font-semibold flex items-center gap-2">
            <svg class="icon-sm" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M8 4h8M7 7h10M7 12h10M7 17h6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
              <rect x="4" y="3" width="16" height="18" rx="3" stroke="currentColor" stroke-width="1.8"/>
            </svg>
            练习历史
          </h2>
          <button
            v-if="historyList.length > 0"
            type="button"
            class="speaking-pill speaking-pill--ghost text-xs"
            @click="loadHistory"
          >
            刷新
          </button>
        </div>
        <div v-if="historyLoading" class="speaking-muted text-sm py-6 text-center">加载中...</div>
        <div v-else-if="historyList.length === 0" class="clay-card">
          <p class="speaking-muted text-sm text-center py-4">暂无练习记录，完成一次评测后将自动保存。</p>
        </div>
        <div v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div
            v-for="record in historyList"
            :key="record.id"
            class="clay-card transition-transform history-card cursor-pointer"
            @click="previewHistory(record)"
          >
            <div class="flex items-center justify-between mb-2">
              <span class="speaking-muted text-xs">{{ record.date }}</span>
              <span
                class="text-xs font-bold px-2 py-0.5 rounded-full"
                :style="{ color: '#fff', background: scoreColor(record.avgScore) }"
              >
                {{ record.avgScore.toFixed(0) }}分
              </span>
            </div>
            <div class="speaking-label text-sm font-semibold">
              {{ record.itemType === 'word' ? '单词' : record.itemType === 'phrase' ? '短语' : '句子' }}
              · {{ record.difficulty === 'easy' ? '简单' : record.difficulty === 'medium' ? '中等' : '困难' }}
              · {{ record.count }}题
            </div>
            <div class="mt-2 flex gap-3 text-xs">
              <span class="speaking-muted">准确 <b :style="{ color: scoreColor(record.avgAccuracy) }">{{ record.avgAccuracy.toFixed(0) }}</b></span>
              <span class="speaking-muted">流利 <b :style="{ color: scoreColor(record.avgFluency) }">{{ record.avgFluency.toFixed(0) }}</b></span>
              <span class="speaking-muted">标准 <b :style="{ color: scoreColor(record.avgStandard) }">{{ record.avgStandard.toFixed(0) }}</b></span>
            </div>
            <div class="mt-2 flex flex-wrap gap-1">
              <span
                v-for="(item, i) in record.items.slice(0, 4)"
                :key="i"
                class="text-xs speaking-muted truncate max-w-[100px]"
              >
                {{ item.text }}{{ i < Math.min(record.items.length, 4) - 1 ? ',' : '' }}
              </span>
              <span v-if="record.items.length > 4" class="text-xs speaking-muted">...</span>
            </div>
            <div class="mt-4 flex items-center justify-end gap-2">
              <button
                type="button"
                class="speaking-pill speaking-pill--ghost text-xs"
                @click.stop="previewHistoryScores(record)"
              >
                预览
              </button>
              <button
                type="button"
                class="speaking-pill speaking-pill--ghost text-xs"
                @click.stop="deleteHistory(record.id)"
              >
                删除
              </button>
            </div>
          </div>
        </div>
        <div v-if="historyPreview" class="speaking-panel mt-4">
          <div class="speaking-muted text-xs font-semibold mb-2">历史分数预览 · {{ historyPreview.date }}</div>
          <div class="space-y-2 text-sm">
            <div v-for="(item, idx) in historyPreview.items" :key="`${historyPreview.id}-${idx}`" class="flex items-center gap-3">
              <span class="w-5 text-center speaking-muted">{{ idx + 1 }}</span>
              <span class="flex-1 truncate speaking-label">{{ item.text }}</span>
              <span class="font-bold" :style="{ color: scoreColor(item.score) }">{{ Number(item.score || 0).toFixed(1) }}</span>
            </div>
          </div>
        </div>
      </section>

      </template>

      <template v-else>
        <header class="flex flex-col gap-6">
          <div class="flex flex-wrap items-center justify-between gap-4">
            <div>
              <div class="speaking-muted text-xs font-semibold">英语口语跟读</div>
              <div class="speaking-heading speaking-title mt-2 text-2xl font-semibold">逐题跟读练习</div>
            </div>
            <div class="flex flex-wrap gap-2">
              <button type="button" class="speaking-pill speaking-pill--ghost" @click="exitPractice">
                返回设置
              </button>
              <button type="button" class="speaking-pill speaking-pill--primary" @click="onGenerate">
                重新生成
              </button>
            </div>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <button
              v-for="(item, idx) in practiceItems"
              :key="item.id"
              type="button"
              class="clay-chip"
              :class="currentStep === idx ? 'clay-chip--active' : ''"
              @click="goToStep(idx)"
            >
              {{ idx + 1 }}
            </button>
            <button
              type="button"
              class="clay-chip"
              :class="currentStep === practiceItems.length ? 'clay-chip--active' : ''"
              @click="goToStep(practiceItems.length)"
            >
              评分
            </button>
          </div>
        </header>

        <section class="clay-card speaking-fade">
          <div v-if="currentItem" class="flex flex-col gap-6">
            <div class="flex flex-wrap items-start justify-between gap-4">
              <div>
                <div class="speaking-muted text-xs font-semibold">第 {{ currentStep + 1 }} 题 / {{ practiceItems.length }}</div>
                <div class="speaking-title mt-3 text-3xl font-semibold">{{ currentItem.text }}</div>
                <div class="speaking-phonetic mt-2 text-base">{{ currentItem.phonetic }}</div>
                <div class="speaking-muted mt-2 text-sm">{{ currentItem.translation || "释义待生成" }}</div>
              </div>
              <!-- Per-item score ring -->
              <div v-if="currentItem.score && currentItem.score !== '--'" class="score-ring-wrapper">
                <div class="score-ring" :style="{ borderColor: scoreColor(parseFloat(currentItem.score)) + '55', background: `conic-gradient(${scoreColor(parseFloat(currentItem.score))} ${parseFloat(currentItem.score) * 3.6}deg, rgba(148,163,184,0.15) 0deg)` }">
                  <span class="score-ring__value" :style="{ color: scoreColor(parseFloat(currentItem.score)) }">{{ currentItem.score }}</span>
                </div>
                <div class="score-ring__grade" :style="{ color: scoreColor(parseFloat(currentItem.score)) }">{{ scoreGrade(parseFloat(currentItem.score)) }}</div>
              </div>
            </div>

            <!-- Score breakdown: accuracy / fluency / standard -->
            <div v-if="currentItem.score && currentItem.score !== '--'" class="mt-2 grid gap-3 sm:grid-cols-3">
              <div class="speaking-panel">
                <div class="speaking-muted text-xs font-semibold">准确度</div>
                <div class="mt-2 text-xl font-bold" :style="{ color: scoreColor(currentItem.accuracy_score) }">
                  {{ typeof currentItem.accuracy_score === 'number' ? currentItem.accuracy_score.toFixed(1) : '--' }}
                </div>
                <div class="score-bar mt-2">
                  <div class="score-fill" :style="{ width: (currentItem.accuracy_score ?? 0) + '%', background: scoreBarGradient(currentItem.accuracy_score) }"></div>
                </div>
              </div>
              <div class="speaking-panel">
                <div class="speaking-muted text-xs font-semibold">流利度</div>
                <div class="mt-2 text-xl font-bold" :style="{ color: scoreColor(currentItem.fluency_score) }">
                  {{ typeof currentItem.fluency_score === 'number' ? currentItem.fluency_score.toFixed(1) : '--' }}
                </div>
                <div class="score-bar mt-2">
                  <div class="score-fill" :style="{ width: (currentItem.fluency_score ?? 0) + '%', background: scoreBarGradient(currentItem.fluency_score) }"></div>
                </div>
              </div>
              <div class="speaking-panel">
                <div class="speaking-muted text-xs font-semibold">标准度</div>
                <div class="mt-2 text-xl font-bold" :style="{ color: scoreColor(currentItem.standard_score) }">
                  {{ typeof currentItem.standard_score === 'number' ? currentItem.standard_score.toFixed(1) : '--' }}
                </div>
                <div class="score-bar mt-2">
                  <div class="score-fill" :style="{ width: (currentItem.standard_score ?? 0) + '%', background: scoreBarGradient(currentItem.standard_score) }"></div>
                </div>
              </div>
            </div>
            <div class="flex flex-wrap items-center gap-3">
              <button type="button" class="speaking-pill speaking-pill--primary" @click="playAudio(currentItem.audioUrl)">
                播放示范
              </button>
              <button
                v-if="!isRecording"
                type="button"
                class="speaking-pill speaking-pill--accent"
                @click="startRecording"
              >
                开始录音
              </button>
              <button
                v-else
                type="button"
                class="speaking-pill speaking-pill--accent"
                @click="stopRecording"
              >
                结束录音
              </button>
              <button
                type="button"
                class="speaking-pill speaking-pill--ghost"
                @click="resetRecording"
              >
                重新录音
              </button>
              <button
                v-if="recordedUrl"
                type="button"
                class="speaking-pill speaking-pill--ghost"
                @click="playAudio(recordedUrl)"
              >
                播放录音
              </button>
            </div>
            <div class="mt-4 flex flex-wrap items-center gap-3">
              <div class="waveform" :class="isRecording ? '' : 'waveform--idle'">
                <span v-for="bar in 10" :key="bar" class="waveform__bar"></span>
              </div>
              <div class="speaking-muted text-xs font-semibold">
                {{ recordingTimerText }}
              </div>
              <div v-if="recordingStatus" class="recording-status">
                {{ recordingStatus }}
              </div>
              <div v-if="recordingError" class="text-xs font-semibold text-red-500">
                {{ recordingError }}
              </div>
            </div>
            <div class="speaking-panel">
              <div class="speaking-muted text-xs font-semibold">纠音提示</div>
              <div class="mt-3 flex flex-wrap gap-2">
                <span
                  v-for="token in currentItem.feedback || []"
                  :key="token.text"
                  class="feedback-pill"
                  :class="feedbackClass(token.status)"
                >
                  {{ token.text }}
                </span>
                <span v-if="!currentItem.feedback || currentItem.feedback.length === 0" class="feedback-pill feedback-pill--warn">
                  暂无评分结果
                </span>
              </div>
            </div>
          </div>

          <div v-else class="flex flex-col gap-6">
            <!-- Summary header -->
            <div class="flex flex-wrap items-center justify-between gap-4">
              <div>
                <div class="speaking-muted text-xs font-semibold">综合评分</div>
                <div class="speaking-heading speaking-title text-3xl font-semibold" :style="{ color: avgTotal != null ? scoreColor(avgTotal) : undefined }">
                  {{ avgTotal != null ? avgTotal.toFixed(1) : '待评测' }}
                  <span v-if="avgTotal != null" class="text-lg opacity-60">/ 100</span>
                </div>
                <div v-if="evaluatedItems.length > 0" class="speaking-muted mt-1 text-sm">
                  已评测 {{ evaluatedItems.length }} / {{ practiceItems.length }} 题
                </div>
              </div>
              <div v-if="avgTotal != null" class="score-ring" :style="{ borderColor: scoreColor(avgTotal) + '55', background: `conic-gradient(${scoreColor(avgTotal)} ${avgTotal * 3.6}deg, rgba(148,163,184,0.15) 0deg)` }">
                <span class="score-ring__value score-ring__value--summary">{{ avgTotal.toFixed(0) }}</span>
              </div>
            </div>

            <!-- Summary: avg accuracy / fluency / standard -->
            <div class="mt-2 grid gap-3 sm:grid-cols-3">
              <div class="speaking-panel">
                <div class="speaking-muted text-xs font-semibold">平均准确度</div>
                <div class="mt-2 text-xl font-bold" :style="{ color: scoreColor(avgAccuracy) }">
                  {{ avgAccuracy != null ? avgAccuracy.toFixed(1) : '--' }}
                </div>
                <div class="score-bar mt-2">
                  <div class="score-fill" :style="{ width: (avgAccuracy ?? 0) + '%', background: scoreBarGradient(avgAccuracy) }"></div>
                </div>
              </div>
              <div class="speaking-panel">
                <div class="speaking-muted text-xs font-semibold">平均流利度</div>
                <div class="mt-2 text-xl font-bold" :style="{ color: scoreColor(avgFluency) }">
                  {{ avgFluency != null ? avgFluency.toFixed(1) : '--' }}
                </div>
                <div class="score-bar mt-2">
                  <div class="score-fill" :style="{ width: (avgFluency ?? 0) + '%', background: scoreBarGradient(avgFluency) }"></div>
                </div>
              </div>
              <div class="speaking-panel">
                <div class="speaking-muted text-xs font-semibold">平均标准度</div>
                <div class="mt-2 text-xl font-bold" :style="{ color: scoreColor(avgStandard) }">
                  {{ avgStandard != null ? avgStandard.toFixed(1) : '--' }}
                </div>
                <div class="score-bar mt-2">
                  <div class="score-fill" :style="{ width: (avgStandard ?? 0) + '%', background: scoreBarGradient(avgStandard) }"></div>
                </div>
              </div>
            </div>

            <!-- Per-item score list -->
            <div v-if="evaluatedItems.length > 0" class="speaking-panel">
              <div class="speaking-muted text-xs font-semibold mb-3">各题得分</div>
              <div class="space-y-2">
                <div v-for="(item, idx) in practiceItems" :key="item.id" class="flex items-center gap-3 text-sm">
                  <span class="font-semibold speaking-muted w-5 text-center">{{ idx + 1 }}</span>
                  <span class="flex-1 truncate speaking-label">{{ item.text }}</span>
                  <div class="flex items-center gap-2">
                    <span class="font-bold" :style="{ color: item.score && item.score !== '--' ? scoreColor(parseFloat(item.score)) : '#94a3b8' }">
                      {{ item.score || '--' }}
                    </span>
                    <span v-if="item.score && item.score !== '--'" class="score-dot" :style="{ background: scoreColor(parseFloat(item.score)) }"></span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Error words list -->
            <div v-if="allErrorWords.length > 0" class="speaking-panel">
              <div class="speaking-muted text-xs font-semibold mb-3">发音问题词汇</div>
              <div class="flex flex-wrap gap-2">
                <span
                  v-for="(ew, idx) in allErrorWords"
                  :key="idx"
                  class="error-word-tag"
                  :title="`来源: ${ew.itemText} | ${dpLabel(ew.dp)}${ew.wordScore != null ? ' | 得分: ' + ew.wordScore.toFixed(1) : ''}`"
                >
                  {{ ew.word }}
                  <span class="error-word-tag__label">{{ dpLabel(ew.dp) }}</span>
                </span>
              </div>
            </div>

            <p v-if="evaluatedItems.length === 0" class="speaking-muted text-sm">完成语音评测后，将展示整体发音、流利度与标准度得分。</p>
          </div>

          <div class="mt-6 flex flex-wrap items-center justify-between gap-3">
            <button type="button" class="speaking-pill speaking-pill--ghost" :disabled="currentStep === 0" @click="prevStep">
              上一题
            </button>
            <button
              type="button"
              class="speaking-pill speaking-pill--primary"
              :disabled="currentStep >= practiceItems.length"
              @click="nextStep"
            >
              下一题
            </button>
          </div>
        </section>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import * as echarts from "echarts";
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import {
  evaluateSpeaking,
  generateSpeakingItems,
  uploadSpeakingRecording,
  type SpeakingItem,
} from "../lib/api";
import { getAuthToken } from "../lib/auth";

const env = {
  backend: import.meta.env.VITE_BACKEND_URL || "http://localhost:5000",
};

const authHeaders = (json = false) => {
  const token = getAuthToken();
  const headers: Record<string, string> = {};
  if (json) headers["Content-Type"] = "application/json";
  if (token) headers.authorization = `Bearer ${token}`;
  return headers;
};

const countOptions = [5, 10, 15];
const difficultyOptions = [
  { key: "easy", label: "简单", desc: "基础高频词" },
  { key: "medium", label: "中等", desc: "场景核心词" },
  { key: "hard", label: "困难", desc: "学术与抽象" },
];
const typeOptions = [
  { key: "word", label: "单词" },
  { key: "phrase", label: "短语" },
  { key: "sentence", label: "句子" },
];

const selectedCount = ref(5);
const selectedDifficulty = ref("easy");
const selectedType = ref("word");
const selectedVoice = ref("british");

type WordDetail = {
  content: string;
  dp_message: number;
  total_score?: number | null;
  sylls?: { content: string; serr_msg: number; syll_score?: number | null }[];
};

type SpeakingItemWithFeedback = SpeakingItem & {
  score?: string;
  accuracy_score?: number | null;
  fluency_score?: number | null;
  standard_score?: number | null;
  integrity_score?: number | null;
  words?: WordDetail[];
  feedback?: { text: string; status: "good" | "warn" | "bad" }[];
};

const defaultItems: SpeakingItemWithFeedback[] = [
  {
    id: 1,
    tag: "高频词",
    text: "adapt",
    phonetic: "/uh-DAPT/",
    translation: "适应",
    level: "简单",
    score: "92",
    feedback: [
      { text: "a-", status: "good" },
      { text: "-dapt", status: "warn" },
      { text: "t", status: "good" },
    ],
    audioUrl: "",
  },
  {
    id: 2,
    tag: "场景短语",
    text: "on time",
    phonetic: "/on TIME/",
    translation: "准时",
    level: "简单",
    score: "88",
    feedback: [
      { text: "on", status: "good" },
      { text: "time", status: "warn" },
    ],
    audioUrl: "",
  },
  {
    id: 3,
    tag: "课堂表达",
    text: "I would like to ask a question.",
    phonetic: "/eye wood like tuh ask uh KWEH-stuhn/",
    translation: "我想提一个问题。",
    level: "中等",
    score: "80",
    feedback: [
      { text: "would", status: "good" },
      { text: "ask", status: "warn" },
      { text: "question", status: "bad" },
    ],
    audioUrl: "",
  },
  {
    id: 4,
    tag: "校园对话",
    text: "Could you please repeat that?",
    phonetic: "/kood yoo pleez rih-PEAT that/",
    translation: "可以再说一遍吗？",
    level: "中等",
    score: "84",
    feedback: [
      { text: "repeat", status: "warn" },
      { text: "that", status: "good" },
    ],
    audioUrl: "",
  },
  {
    id: 5,
    tag: "学术表达",
    text: "The data suggests a significant trend.",
    phonetic: "/thuh DAY-tuh suh-JESTS uh sig-NIF-i-kuhnt trend/",
    translation: "数据显示出显著趋势。",
    level: "困难",
    score: "76",
    feedback: [
      { text: "data", status: "warn" },
      { text: "significant", status: "bad" },
      { text: "trend", status: "good" },
    ],
    audioUrl: "",
  },
];

const practiceItems = ref<SpeakingItemWithFeedback[]>(defaultItems);
const isGenerating = ref(false);
const generateError = ref("");
const audioPlayer = ref<HTMLAudioElement | null>(null);
const showPractice = ref(false);
const currentStep = ref(0);
const speakingSessionId = ref<string | null>(null);

const isRecording = ref(false);
const recordingStatus = ref("");
const recordingError = ref("");
const recordedUrl = ref("");
const recordingTimer = ref(0);
const recorder = ref<MediaRecorder | null>(null);
const recorderStream = ref<MediaStream | null>(null);
const recordChunks = ref<Blob[]>([]);
let timerHandle: number | null = null;

const currentItem = computed(() => {
  if (currentStep.value >= practiceItems.value.length) return null;
  return practiceItems.value[currentStep.value] || null;
});

const recordingTimerText = computed(() => {
  const total = recordingTimer.value;
  const mins = Math.floor(total / 60)
    .toString()
    .padStart(2, "0");
  const secs = (total % 60).toString().padStart(2, "0");
  return `${mins}:${secs}`;
});

const goToStep = (index: number) => {
  const maxStep = practiceItems.value.length;
  if (index < 0) {
    currentStep.value = 0;
    return;
  }
  if (index > maxStep) {
    currentStep.value = maxStep;
    return;
  }
  currentStep.value = index;
};

const nextStep = () => {
  goToStep(currentStep.value + 1);
};

const prevStep = () => {
  goToStep(currentStep.value - 1);
};

const exitPractice = () => {
  showPractice.value = false;
};

const onGenerate = async () => {
  if (isGenerating.value) return;
  isGenerating.value = true;
  generateError.value = "";
  try {
    const response = await generateSpeakingItems({
      count: selectedCount.value,
      difficulty: selectedDifficulty.value as "easy" | "medium" | "hard",
      itemType: selectedType.value as "word" | "phrase" | "sentence",
      voice: selectedVoice.value as "american" | "british",
    });
    if (!response || !response.items) {
      throw new Error("生成失败，请稍后重试");
    }
    practiceItems.value = response.items.map((item) => ({
      ...item,
      score: "--",
      feedback: [],
    }));
    speakingSessionId.value = response.sessionId || null;
    showPractice.value = true;
    currentStep.value = 0;
  } catch (err) {
    generateError.value = err instanceof Error ? err.message : "生成失败，请稍后重试";
  } finally {
    isGenerating.value = false;
  }
};

const playAudio = (url: string) => {
  if (!url) return;
  if (audioPlayer.value) {
    audioPlayer.value.pause();
  }
  const audio = new Audio(url);
  audioPlayer.value = audio;
  audio.play().catch(() => {
    generateError.value = "音频播放失败，请检查浏览器权限";
  });
};

const startRecording = async () => {
  if (isRecording.value || !currentItem.value) return;
  recordingError.value = "";
  recordedUrl.value = "";
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    recorderStream.value = stream;

    const mimeTypes = [
      "audio/webm;codecs=opus",
      "audio/webm",
      "audio/mp4",
    ];
    const supported = mimeTypes.find((type) => MediaRecorder.isTypeSupported(type));
    const mediaRecorder = new MediaRecorder(stream, supported ? { mimeType: supported } : undefined);
    recorder.value = mediaRecorder;
    recordChunks.value = [];
    mediaRecorder.ondataavailable = (event) => {
      if (event.data && event.data.size > 0) recordChunks.value.push(event.data);
    };
    mediaRecorder.onstop = handleRecordingStop;

    mediaRecorder.start();
    isRecording.value = true;
    recordingStatus.value = "录音中...";
    recordingTimer.value = 0;
    if (timerHandle) window.clearInterval(timerHandle);
    timerHandle = window.setInterval(() => {
      recordingTimer.value += 1;
    }, 1000);
  } catch (err) {
    recordingError.value = err instanceof Error ? err.message : "无法开启麦克风";
  }
};

const stopRecording = () => {
  if (!recorder.value) return;
  recorder.value.stop();
  recorder.value = null;
  isRecording.value = false;
  if (timerHandle) {
    window.clearInterval(timerHandle);
    timerHandle = null;
  }
  if (recorderStream.value) {
    recorderStream.value.getTracks().forEach((track) => track.stop());
    recorderStream.value = null;
  }
};

const resetRecording = () => {
  recordedUrl.value = "";
  recordingStatus.value = "";
  recordingError.value = "";
  recordingTimer.value = 0;
};

const handleRecordingStop = async () => {
  recordingStatus.value = "降噪处理中...";
  await new Promise((resolve) => setTimeout(resolve, 300));
  recordingStatus.value = "上传中...";
  try {
    const blob = new Blob(recordChunks.value, { type: recordChunks.value[0]?.type || "audio/webm" });
    const file = new File([blob], "recording.webm", { type: blob.type });
    const response = await uploadSpeakingRecording(
      file,
      speakingSessionId.value || undefined,
      currentItem.value?.id
    );
    recordedUrl.value = response.staticUrl;
    recordingStatus.value = "评测中...";

    const evalResponse = await evaluateSpeaking({
      sessionId: response.sessionId,
      filename: response.filename,
      text: currentItem.value?.text || "",
      itemType: selectedType.value as "word" | "phrase" | "sentence",
    });
    const sc = evalResponse.scores;
    const totalScore = sc?.total_score;
    const evalWords = evalResponse.words || [];
    if (currentItem.value) {
      // build feedback from per-word details (scores are already 0-100 from backend)
      const feedback: { text: string; status: "good" | "warn" | "bad" }[] = evalWords.map((w) => {
        let status: "good" | "warn" | "bad" = "good";
        // Serious dp errors: 16=漏读, 128=替换 → bad; 32=增读, 64=回读 → warn
        const dp = w.dp_message ?? 0;
        if (dp & (16 | 128)) {
          status = "bad";
        } else if (dp & (32 | 64)) {
          status = "warn";
        } else if (typeof w.total_score === "number" && w.total_score < 50) {
          status = "bad";
        } else if (typeof w.total_score === "number" && w.total_score < 70) {
          status = "warn";
        }
        return { text: w.content, status };
      });
      const updated = practiceItems.value.map((item) =>
        item.id === currentItem.value?.id
          ? {
              ...item,
              score: typeof totalScore === "number" ? totalScore.toFixed(1) : "--",
              accuracy_score: sc?.accuracy_score ?? null,
              fluency_score: sc?.fluency_score ?? null,
              standard_score: sc?.standard_score ?? null,
              integrity_score: sc?.integrity_score ?? null,
              words: evalWords,
              feedback,
            }
          : item
      );
      practiceItems.value = updated;
    }
    recordingStatus.value = "评测完成";
    // Auto-save history after each evaluation
    setTimeout(() => saveHistory(), 500);
  } catch (err) {
    recordingStatus.value = "";
    recordingError.value = err instanceof Error ? err.message : "上传失败";
  }
};

onBeforeUnmount(() => {
  if (timerHandle) window.clearInterval(timerHandle);
  if (recorderStream.value) {
    recorderStream.value.getTracks().forEach((track) => track.stop());
  }
  window.removeEventListener("resize", handleWindowResize);
  if (dashboardChart) {
    dashboardChart.dispose();
    dashboardChart = null;
  }
});

// ── History ──
type HistoryRecord = {
  id: string;
  date: string;
  count: number;
  difficulty: string;
  itemType: string;
  voice: string;
  avgScore: number;
  avgAccuracy: number;
  avgFluency: number;
  avgStandard: number;
  items: { text: string; score: number }[];
};

const historyList = ref<HistoryRecord[]>([]);
const historyLoading = ref(false);
const historyPreview = ref<HistoryRecord | null>(null);
const dashboardUseHistory = ref(false);
const dashboardRadarRef = ref<HTMLElement | null>(null);
let dashboardChart: echarts.ECharts | null = null;
const defaultDashboard = {
  total: 84.4,
  accuracy: 89.5,
  fluency: 91.9,
  standard: 71.8,
};

const dashboardMetrics = computed(() => {
  if (!dashboardUseHistory.value || historyList.value.length === 0) {
    return defaultDashboard;
  }
  const records = historyList.value;
  const avg = (getter: (r: HistoryRecord) => number) =>
    records.reduce((sum, item) => sum + getter(item), 0) / records.length;
  return {
    total: Number(avg((r) => r.avgScore).toFixed(1)),
    accuracy: Number(avg((r) => r.avgAccuracy).toFixed(1)),
    fluency: Number(avg((r) => r.avgFluency).toFixed(1)),
    standard: Number(avg((r) => r.avgStandard).toFixed(1)),
  };
});

const renderDashboardRadar = () => {
  if (!dashboardRadarRef.value) return;
  if (!dashboardChart) {
    dashboardChart = echarts.init(dashboardRadarRef.value);
  }
  const m = dashboardMetrics.value;
  dashboardChart.setOption({
    animationDuration: 350,
    radar: {
      center: ["50%", "56%"],
      radius: 32,
      splitNumber: 4,
      axisName: {
        color: "#475569",
        fontSize: 11,
        fontWeight: 700,
      },
      nameGap: 12,
      splitLine: {
        lineStyle: { color: "rgba(148,163,184,0.45)" },
      },
      splitArea: {
        areaStyle: { color: ["rgba(59,130,246,0.05)", "rgba(59,130,246,0.08)"] },
      },
      indicator: [
        { name: "准确度", max: 100 },
        { name: "流利度", max: 100 },
        { name: "标准度", max: 100 },
      ],
    },
    series: [
      {
        type: "radar",
        symbol: "circle",
        symbolSize: 5,
        lineStyle: { color: "#22d3ee", width: 2 },
        itemStyle: { color: "#3b82f6" },
        areaStyle: { color: "rgba(34,211,238,0.25)" },
        data: [
          {
            value: [m.accuracy, m.fluency, m.standard],
            name: "能力",
          },
        ],
      },
    ],
  });
  dashboardChart.resize();
};

const handleWindowResize = () => {
  dashboardChart?.resize();
};

const loadHistory = async () => {
  historyLoading.value = true;
  try {
    const res = await fetch(`${env.backend}/speaking/history`, { headers: authHeaders() });
    if (res.ok) {
      const data = await res.json();
      historyList.value = data.records || [];
    }
  } catch { /* ignore */ }
  historyLoading.value = false;
};

const syncDashboardFromHistory = async () => {
  await loadHistory();
  dashboardUseHistory.value = true;
  await nextTick();
  requestAnimationFrame(() => {
    renderDashboardRadar();
  });
};

const saveHistory = async () => {
  const evaluated = evaluatedItems.value;
  if (evaluated.length === 0) return;
  try {
    await fetch(`${env.backend}/speaking/history`, {
      method: "POST",
      headers: authHeaders(true),
      body: JSON.stringify({
        sessionId: speakingSessionId.value,
        count: practiceItems.value.length,
        difficulty: selectedDifficulty.value,
        itemType: selectedType.value,
        voice: selectedVoice.value,
        avgScore: avgTotal.value ?? 0,
        avgAccuracy: avgAccuracy.value ?? 0,
        avgFluency: avgFluency.value ?? 0,
        avgStandard: avgStandard.value ?? 0,
        items: practiceItems.value.map((i) => ({
          text: i.text,
          score: i.score && i.score !== "--" ? parseFloat(i.score) : 0,
        })),
      }),
    });
  } catch { /* ignore */ }
};

const previewHistory = (record: HistoryRecord) => {
  practiceItems.value = record.items.map((item, idx) => ({
    id: idx + 1,
    text: item.text,
    translation: "历史记录",
    phonetic: "",
    level: record.difficulty,
    tag: "历史练习",
    audioUrl: "",
    score: Number(item.score || 0).toFixed(1),
    accuracy_score: null,
    fluency_score: null,
    standard_score: null,
    integrity_score: null,
    words: [],
    feedback: [],
  }));
  selectedDifficulty.value = record.difficulty;
  selectedType.value = record.itemType;
  selectedVoice.value = record.voice;
  showPractice.value = true;
  currentStep.value = 0;
};

const previewHistoryScores = (record: HistoryRecord) => {
  historyPreview.value = record;
};

const deleteHistory = async (id: string) => {
  try {
    await fetch(`${env.backend}/speaking/history/${id}`, { method: "DELETE", headers: authHeaders() });
    if (historyPreview.value?.id === id) {
      historyPreview.value = null;
    }
    await loadHistory();
  } catch { /* ignore */ }
};

onMounted(() => {
  loadHistory();
  nextTick(() => {
    requestAnimationFrame(() => {
      renderDashboardRadar();
    });
  });
  window.addEventListener("resize", handleWindowResize);
});

watch(dashboardMetrics, () => {
  nextTick(() => {
    requestAnimationFrame(() => {
      renderDashboardRadar();
    });
  });
});

watch(showPractice, (val) => {
  if (!val) {
    nextTick(() => {
      requestAnimationFrame(() => {
        renderDashboardRadar();
      });
    });
  }
});

const feedbackClass = (status: "good" | "warn" | "bad") => {
  if (status === "good") return "feedback-pill--good";
  if (status === "warn") return "feedback-pill--warn";
  return "feedback-pill--bad";
};

const scoreColor = (score: number | null | undefined): string => {
  if (score == null) return "#94a3b8";
  if (score >= 80) return "#22c55e";
  if (score >= 60) return "#f59e0b";
  return "#ef4444";
};

const scoreGrade = (score: number | null | undefined): string => {
  if (score == null) return "--";
  if (score >= 90) return "A";
  if (score >= 80) return "B";
  if (score >= 70) return "C";
  if (score >= 60) return "D";
  return "F";
};

const scoreBarGradient = (score: number | null | undefined): string => {
  const c = scoreColor(score);
  return `linear-gradient(90deg, ${c}, ${c}dd)`;
};

// Summary page computed values
const evaluatedItems = computed(() => {
  return practiceItems.value.filter((item) => item.score && item.score !== "--");
});

const avgTotal = computed(() => {
  const items = evaluatedItems.value;
  if (items.length === 0) return null;
  const sum = items.reduce((acc, item) => acc + parseFloat(item.score || "0"), 0);
  return sum / items.length;
});

const avgAccuracy = computed(() => {
  const items = evaluatedItems.value.filter((i) => typeof i.accuracy_score === "number");
  if (items.length === 0) return null;
  return items.reduce((acc, i) => acc + (i.accuracy_score || 0), 0) / items.length;
});

const avgFluency = computed(() => {
  const items = evaluatedItems.value.filter((i) => typeof i.fluency_score === "number");
  if (items.length === 0) return null;
  return items.reduce((acc, i) => acc + (i.fluency_score || 0), 0) / items.length;
});

const avgStandard = computed(() => {
  const items = evaluatedItems.value.filter((i) => typeof i.standard_score === "number");
  if (items.length === 0) return null;
  return items.reduce((acc, i) => acc + (i.standard_score || 0), 0) / items.length;
});

const allErrorWords = computed(() => {
  const result: { word: string; itemText: string; dp: number; wordScore: number | null }[] = [];
  for (const item of practiceItems.value) {
    if (!item.words) continue;
    for (const w of item.words) {
      const dp = w.dp_message ?? 0;
      // Only flag truly problematic words: serious dp error OR very low score
      const hasSeriousDp = !!(dp & (16 | 128));  // 漏读 or 替换
      const hasLowScore = typeof w.total_score === "number" && w.total_score < 50;
      if (hasSeriousDp || hasLowScore) {
        result.push({
          word: w.content,
          itemText: item.text,
          dp: w.dp_message,
          wordScore: w.total_score ?? null,
        });
      }
    }
  }
  return result;
});

const dpLabel = (dp: number): string => {
  if (dp === 16) return "漏读";
  if (dp === 32) return "增读";
  if (dp === 64) return "回读";
  if (dp === 128) return "替换";
  if (dp !== 0) return "错误";
  return "发音差";
};
</script>

<style scoped>
.speaking-page {
  color: var(--app-text);
}

.speaking-body {
  font-family: var(--font-body);
}

.speaking-heading {
  font-family: var(--font-heading);
}

.speaking-title {
  color: var(--app-text);
}

.speaking-muted {
  color: #0f172a;
  font-weight: 600;
}

.speaking-muted-light {
  color: #64748b;
}

.icon-sm {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

.icon-xs {
  width: 12px;
  height: 12px;
  flex-shrink: 0;
}

.speaking-label {
  color: #0f172a;
  font-weight: 600;
}

.speaking-phonetic {
  color: #0f172a;
  font-weight: 700;
}

.speaking-badge {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  border-radius: 9999px;
  border: 1px solid var(--nav-border);
  background: var(--glass-bg);
  padding: 8px 16px;
  font-size: 12px;
  font-weight: 600;
  color: var(--nav-text);
  box-shadow: var(--glass-shadow);
}

.speaking-dot {
  width: 10px;
  height: 10px;
  border-radius: 9999px;
  background: linear-gradient(135deg, #22d3ee, #a855f7);
  box-shadow: 0 0 10px rgba(34, 211, 238, 0.5);
}

.speaking-orb {
  position: absolute;
  border-radius: 44%;
  filter: blur(48px);
  opacity: 0.35;
  pointer-events: none;
}

.speaking-orb--one {
  top: -80px;
  left: 40px;
  width: 280px;
  height: 280px;
  background: radial-gradient(circle at top, rgba(59, 130, 246, 0.35), transparent 70%);
}

.speaking-orb--two {
  top: 32%;
  right: 40px;
  width: 320px;
  height: 320px;
  background: radial-gradient(circle at top, rgba(139, 92, 246, 0.3), transparent 70%);
}

.speaking-orb--three {
  bottom: 0;
  left: 33%;
  width: 360px;
  height: 360px;
  background: radial-gradient(circle at top, rgba(34, 211, 238, 0.25), transparent 70%);
}

.clay-card {
  border-radius: 28px;
  border: 1px solid var(--glass-border);
  background: var(--glass-bg);
  box-shadow: var(--glass-shadow);
  padding: 26px;
}

.setup-card {
  background: linear-gradient(180deg, rgba(59, 130, 246, 0.08), rgba(255, 255, 255, 0.08));
}

.compact-panel {
  padding-top: 18px;
  padding-bottom: 18px;
}

.dashboard-card .score-row {
  gap: 8px;
}

.dashboard-card .score-row span {
  min-width: 108px;
}

.score-metric-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.score-metric-value {
  font-weight: 800;
}

.speaking-pill {
  border-radius: 9999px;
  padding: 10px 18px;
  font-size: 13px;
  font-weight: 700;
  transition: transform 200ms ease, box-shadow 200ms ease, background-color 200ms ease;
  cursor: pointer;
}

.speaking-pill:hover {
  transform: translateY(-1px);
}

.speaking-pill--primary {
  background: linear-gradient(135deg, #22d3ee, #3b82f6);
  color: #0f172a;
  box-shadow: 0 12px 24px rgba(34, 211, 238, 0.25);
}

.speaking-pill--accent {
  background: linear-gradient(135deg, #a855f7, #8b5cf6);
  color: #ffffff;
  box-shadow: 0 12px 24px rgba(139, 92, 246, 0.25);
}

.speaking-pill--ghost {
  background: rgba(255, 255, 255, 0.08);
  color: var(--nav-text);
  border: 1px solid var(--nav-border);
}

.clay-input {
  border-radius: 16px;
  border: 1px solid var(--glass-border);
  background: rgba(255, 255, 255, 0.08);
  padding: 10px 12px;
  font-size: 14px;
  color: var(--app-text);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.clay-input:focus {
  outline: 2px solid rgba(59, 130, 246, 0.45);
  outline-offset: 2px;
}

.clay-chip {
  border-radius: 999px;
  padding: 8px 14px;
  border: 1px solid var(--glass-border);
  background: rgba(255, 255, 255, 0.08);
  font-size: 12px;
  font-weight: 700;
  color: var(--nav-text);
  transition: background-color 200ms ease, box-shadow 200ms ease;
  cursor: pointer;
}

.chip-count {
  background: rgba(34, 211, 238, 0.12);
}

.chip-difficulty {
  background: rgba(139, 92, 246, 0.12);
}

.clay-chip--active {
  background: var(--nav-active-bg);
  color: var(--nav-active-text);
  box-shadow: var(--nav-active-shadow);
}

.speaking-chip {
  border-radius: 16px;
  border: 1px solid var(--glass-border);
  background: rgba(255, 255, 255, 0.08);
  padding: 8px 16px;
  font-size: 12px;
  font-weight: 600;
  color: var(--nav-text);
}

.speaking-panel {
  border-radius: 24px;
  border: 1px solid var(--glass-border);
  background: rgba(255, 255, 255, 0.08);
  padding: 16px;
}

.clay-step {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid var(--glass-border);
  padding: 14px;
}

.step-card {
  min-height: 84px;
}

.step-card--ai {
  background: linear-gradient(140deg, rgba(59, 130, 246, 0.14), rgba(255, 255, 255, 0.08));
}

.step-card--tts {
  background: linear-gradient(140deg, rgba(99, 102, 241, 0.14), rgba(255, 255, 255, 0.08));
}

.step-card--mic {
  background: linear-gradient(140deg, rgba(16, 185, 129, 0.14), rgba(255, 255, 255, 0.08));
}

.step-card--score {
  background: linear-gradient(140deg, rgba(245, 158, 11, 0.14), rgba(255, 255, 255, 0.08));
}

.clay-step__dot {
  width: 20px;
  height: 20px;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid var(--glass-border);
  margin-top: 2px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--nav-text);
}

.step-icon-wrap {
  width: 28px;
  height: 28px;
  border-radius: 10px;
  margin-top: 0;
}

.clay-step__dot--ai {
  background: rgba(59, 130, 246, 0.2);
  color: #1d4ed8;
}

.clay-step__dot--tts {
  background: rgba(99, 102, 241, 0.2);
  color: #4338ca;
}

.clay-step__dot--mic {
  background: rgba(16, 185, 129, 0.2);
  color: #047857;
}

.clay-step__dot--score {
  background: rgba(245, 158, 11, 0.2);
  color: #b45309;
}

.step-title {
  font-size: 14px;
  letter-spacing: 0.2px;
}

.step-desc {
  margin-top: 4px;
  color: #334155;
  font-weight: 500;
  line-height: 1.35;
}

.label-icon {
  width: 20px;
  height: 20px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--glass-border);
}

.label-icon--count {
  background: rgba(34, 211, 238, 0.16);
}

.label-icon--difficulty {
  background: rgba(139, 92, 246, 0.16);
}

.label-icon--type {
  background: rgba(59, 130, 246, 0.16);
}

.label-icon--voice {
  background: rgba(14, 165, 233, 0.16);
}

.radar-wrap {
  border-radius: 16px;
  border: 1px solid var(--glass-border);
  background: rgba(255, 255, 255, 0.08);
  padding: 8px;
}

.dashboard-radar {
  width: 100%;
  height: 116px;
}

.history-card:hover {
  border-color: rgba(59, 130, 246, 0.4);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.12);
}

.score-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  font-size: 12px;
  font-weight: 700;
  color: var(--nav-text);
}

.score-bar {
  flex: 1;
  height: 8px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.25);
  overflow: hidden;
}

.score-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #22d3ee, #8b5cf6);
}

.clay-ring {
  height: 60px;
  width: 60px;
  border-radius: 50%;
  border: 6px solid rgba(59, 130, 246, 0.35);
  background: conic-gradient(#22d3ee 300deg, rgba(59, 130, 246, 0.2) 0deg);
  display: grid;
  place-items: center;
  box-shadow: inset 0 2px 0 rgba(255, 255, 255, 0.8);
}

.waveform {
  display: flex;
  align-items: center;
  gap: 4px;
  height: 32px;
}

.waveform__bar {
  width: 4px;
  height: 60%;
  border-radius: 999px;
  background: linear-gradient(180deg, #22d3ee, #8b5cf6);
  animation: wave 1.4s ease-in-out infinite;
}

.waveform--idle .waveform__bar {
  animation-play-state: paused;
  opacity: 0.4;
}

.recording-status {
  border-radius: 999px;
  border: 1px solid var(--glass-border);
  background: rgba(255, 255, 255, 0.08);
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 700;
  color: #0f172a;
}

.waveform__bar:nth-child(2) { animation-delay: 0.2s; }
.waveform__bar:nth-child(3) { animation-delay: 0.4s; }
.waveform__bar:nth-child(4) { animation-delay: 0.6s; }
.waveform__bar:nth-child(5) { animation-delay: 0.8s; }
.waveform__bar:nth-child(6) { animation-delay: 1s; }
.waveform__bar:nth-child(7) { animation-delay: 1.2s; }
.waveform__bar:nth-child(8) { animation-delay: 1.4s; }
.waveform__bar:nth-child(9) { animation-delay: 1.6s; }
.waveform__bar:nth-child(10) { animation-delay: 1.8s; }

.clay-tag {
  border-radius: 999px;
  border: 1px solid var(--glass-border);
  background: rgba(255, 255, 255, 0.08);
  padding: 4px 10px;
  font-weight: 700;
  color: var(--nav-text);
}

.practice-card {
  border-radius: 24px;
  border: 1px solid var(--glass-border);
  background: rgba(255, 255, 255, 0.08);
  padding: 18px;
  box-shadow: 0 12px 26px rgba(15, 23, 42, 0.18);
}

.clay-icon-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 38px;
  width: 38px;
  border-radius: 14px;
  border: 1px solid var(--glass-border);
  background: rgba(255, 255, 255, 0.08);
  color: var(--nav-text);
  transition: background-color 200ms ease, transform 200ms ease;
  cursor: pointer;
}

.clay-icon-button:hover {
  background: rgba(255, 255, 255, 0.14);
  transform: translateY(-1px);
}

.feedback-pill {
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 700;
  border: 2px solid transparent;
  color: #0f172a;
}

.feedback-pill--good {
  background: rgba(34, 197, 94, 0.2);
  border-color: rgba(34, 197, 94, 0.35);
}

.feedback-pill--warn {
  background: rgba(245, 158, 11, 0.2);
  border-color: rgba(245, 158, 11, 0.35);
}

.feedback-pill--bad {
  background: rgba(239, 68, 68, 0.2);
  border-color: rgba(239, 68, 68, 0.35);
}

/* ── Score ring ── */
.score-ring-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
.score-ring {
  width: 68px;
  height: 68px;
  border-radius: 50%;
  border: 3px solid rgba(148,163,184,0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.score-ring__value {
  font-size: 1.15rem;
  font-weight: 800;
  letter-spacing: -0.5px;
}

.score-ring__value--summary {
  color: #0f172a;
  font-weight: 900;
}
.score-ring__grade {
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.5px;
}

/* ── Score dot (per-item list) ── */
.score-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

/* ── Error word tags ── */
.error-word-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 0.82rem;
  font-weight: 600;
  background: rgba(239, 68, 68, 0.12);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #f87171;
  cursor: default;
}
.error-word-tag__label {
  font-size: 0.68rem;
  font-weight: 500;
  opacity: 0.75;
  padding-left: 2px;
}

.speaking-fade {
  animation: fadeUp 600ms ease both;
}

@keyframes fadeUp {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes wave {
  0%,
  100% {
    height: 30%;
  }
  50% {
    height: 100%;
  }
}

@media (prefers-reduced-motion: reduce) {
  .speaking-fade,
  .waveform__bar {
    animation: none;
  }
}
</style>
