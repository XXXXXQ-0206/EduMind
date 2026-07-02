<template>
  <div class="mt-8">
    <div class="flex items-center gap-3 mb-6">
      <h2 class="text-xl font-semibold text-white">更多工具即将推出</h2>
      <div class="flex-1 h-px bg-gradient-to-r from-zinc-700 to-transparent"></div>
      <div class="px-3 py-1 rounded-full bg-gradient-to-r from-amber-500/20 to-orange-500/20 border border-amber-500/30 text-amber-300 text-xs font-medium">
        开发中
      </div>
    </div>

    <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div class="group rounded-2xl bg-stone-950/50 border border-zinc-800 p-4 hover:border-blue-500/50 transition-all duration-300 hover:shadow-lg hover:shadow-blue-500/10 opacity-70 hover:opacity-90">
        <div class="flex items-start justify-between gap-3">
          <div class="flex-1">
            <div class="flex items-center gap-2 mb-1">
              <div class="text-xs uppercase tracking-wide text-blue-400 font-semibold">学习计划</div>
            </div>
            <div class="text-white font-semibold text-lg mb-2">AI学习计划</div>
            <div class="text-stone-400 text-sm leading-relaxed">
              创建个性化学习计划，使用AI优化的间隔重复和截止日期管理。
            </div>
          </div>
          <div class="p-3 rounded-xl bg-gradient-to-br from-blue-500/20 to-cyan-500/20 border border-blue-500/30">
            <svg class="size-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
        </div>
      </div>

      <div class="group rounded-2xl bg-stone-950/50 border border-zinc-800 p-4 hover:border-rose-500/50 transition-all duration-300 hover:shadow-lg hover:shadow-rose-500/10 opacity-70 hover:opacity-90">
        <div class="flex items-start justify-between gap-3">
          <div class="flex-1">
            <div class="flex items-center gap-2 mb-1">
              <div class="text-xs uppercase tracking-wide text-rose-400 font-semibold">视觉学习</div>
            </div>
            <div class="text-white font-semibold text-lg mb-2">思维导图生成器</div>
            <div class="text-stone-400 text-sm leading-relaxed">
              将复杂主题转换为交互式视觉思维导图，包含AI生成的连接和见解。
            </div>
          </div>
          <div class="p-3 rounded-xl bg-gradient-to-br from-rose-500/20 to-pink-500/20 border border-rose-500/30">
            <svg class="size-5 text-rose-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>
        </div>
      </div>

      <div class="group rounded-2xl bg-stone-950/50 border border-zinc-800 p-4 hover:border-amber-500/50 transition-all duration-300 hover:shadow-lg hover:shadow-amber-500/10 opacity-70 hover:opacity-90">
        <div class="flex items-start justify-between gap-3">
          <div class="flex-1">
            <div class="flex items-center gap-2 mb-1">
              <div class="text-xs uppercase tracking-wide text-amber-400 font-semibold">演示制作</div>
            </div>
            <div class="text-white font-semibold text-lg mb-2">幻灯片制作专家</div>
            <div class="text-stone-400 text-sm leading-relaxed">
              生成专业演示文稿，包含AI设计的幻灯片、动画和演讲者备注。
            </div>
          </div>
          <div class="p-3 rounded-xl bg-gradient-to-br from-amber-500/20 to-yellow-500/20 border border-amber-500/30">
            <svg class="size-5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 3v11.25A2.25 2.25 0 0 0 6 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0 1 18 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3 1 3m0 0 .5 1.5m-.5-1.5h-9.5m0 0-.5 1.5m.75-9 3-3 2.148 2.148A12.061 12.061 0 0 1 16.5 7.605" />
            </svg>
          </div>
        </div>
      </div>
    </div>

    <div class="mt-6 text-center">
      <div class="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-zinc-800/50 to-zinc-700/50 border border-zinc-600/50">
        <div class="w-2 h-2 rounded-full bg-gradient-to-r from-blue-400 to-sky-400 animate-pulse"></div>
        <span class="text-stone-300 text-sm font-medium">每周推出新工具</span>
      </div>
    </div>
  </div>
</template>
