<template>
  <aside class="w-full lg:w-64 min-w-[220px] flex-1 glass-card rounded-3xl p-4 border border-[color:var(--glass-border)] shadow-[0_12px_28px_rgba(0,0,0,0.2)] flex flex-col">
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center gap-2 text-sm font-semibold text-[color:var(--app-text)]">
        <span class="inline-flex size-6 items-center justify-center rounded-full bg-[color:var(--nav-hover-bg-strong)] text-amber-300">
          <svg viewBox="0 0 24 24" class="size-4" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
          </svg>
        </span>
        历史教案
      </div>
      <button
        type="button"
        class="rounded-xl bg-gradient-to-br from-[color:var(--primary-blue)] to-[color:var(--primary-purple)] px-3 py-1.5 text-[11px] font-semibold text-white shadow-[0_10px_18px_rgba(59,130,246,0.25)] hover:brightness-110 transition-colors inline-flex items-center gap-1.5 cursor-pointer"
        @click="startNew"
      >
        <svg viewBox="0 0 24 24" class="size-3.5" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 5v14M5 12h14" />
        </svg>
        新建教案
      </button>
    </div>
    <div v-if="loading" class="text-xs text-[color:var(--nav-text-muted)]">加载中...</div>
    <ul v-else-if="plans.length" class="space-y-2 flex-1 overflow-y-auto overflow-x-hidden custom-scroll pr-1">
      <li v-for="plan in plans" :key="plan.id" class="min-w-0">
        <div class="flex items-stretch gap-2">
          <button
            type="button"
            class="flex-1 min-w-0 text-left rounded-2xl px-3 py-2 text-sm text-[color:var(--app-text)] bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] border border-[color:var(--nav-border)] transition-colors cursor-pointer"
            @click="openPlan(plan.id)"
            :title="plan.title || '未命名教案'"
          >
            <div class="truncate">{{ plan.title || "未命名教案" }}</div>
            <div class="mt-1 text-[10px] text-[color:var(--nav-text-muted)]">教案</div>
          </button>
          <button
            type="button"
            class="w-9 shrink-0 rounded-2xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors inline-flex items-center justify-center cursor-pointer"
            @click.stop="togglePreview(plan.id)"
            aria-label="预览教案"
            :title="expandedId === plan.id ? '收起预览' : '预览教案'"
          >
            <svg viewBox="0 0 24 24" class="size-4 text-amber-300" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12c1.8-4.2 6-7.5 9.75-7.5s7.95 3.3 9.75 7.5c-1.8 4.2-6 7.5-9.75 7.5S4.05 16.2 2.25 12Z" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
            </svg>
          </button>
          <button
            type="button"
            class="w-9 shrink-0 rounded-2xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors inline-flex items-center justify-center cursor-pointer"
            @click.stop="removePlan(plan.id)"
            aria-label="删除教案"
            title="删除教案"
          >
            <svg viewBox="0 0 24 24" class="size-4 text-rose-300" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 7h12M9 7V5.5h6V7m-7 0v11.5A1.5 1.5 0 0 0 9.5 20h5A1.5 1.5 0 0 0 16 18.5V7" />
              <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 11v5m3-5v5" />
            </svg>
          </button>
        </div>
        <div v-if="expandedId === plan.id" class="mt-3 rounded-2xl border border-[color:var(--glass-border)] bg-[color:var(--glass-bg)]/70 p-3">
          <div v-if="details[plan.id]" class="space-y-2 max-h-64 overflow-y-auto overflow-x-hidden custom-scroll pr-1 text-xs text-[color:var(--app-text)]">
            <div v-if="details[plan.id].teaching_goals?.knowledge" class="rounded-xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 p-2">
              <span class="text-[color:var(--nav-text-muted)]">知识与技能：</span>{{ (details[plan.id].teaching_goals?.knowledge || "").slice(0, 80) }}{{ (details[plan.id].teaching_goals?.knowledge || "").length > 80 ? "…" : "" }}
            </div>
            <div v-if="(details[plan.id].key_points?.length ?? 0) > 0" class="rounded-xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 p-2">
              <span class="text-[color:var(--nav-text-muted)]">重点：</span>{{ (details[plan.id].key_points || []).join("；").slice(0, 60) }}{{ (details[plan.id].key_points || []).join("；").length > 60 ? "…" : "" }}
            </div>
            <div v-if="(details[plan.id].process?.length ?? 0) > 0" class="rounded-xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 p-2">
              <span class="text-[color:var(--nav-text-muted)]">过程：</span>{{ (details[plan.id].process?.[0]?.title || "") }} {{ (details[plan.id].process?.[0]?.content || "").slice(0, 40) }}{{ (details[plan.id].process?.[0]?.content || "").length > 40 ? "…" : "" }}
            </div>
            <div v-if="details[plan.id].homework" class="rounded-xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)]/40 p-2">
              <span class="text-[color:var(--nav-text-muted)]">作业：</span>{{ (details[plan.id].homework || "").slice(0, 50) }}{{ (details[plan.id].homework || "").length > 50 ? "…" : "" }}
            </div>
          </div>
          <div v-else class="text-xs text-[color:var(--nav-text-muted)]">加载中…</div>
        </div>
      </li>
    </ul>
    <div v-else class="text-xs text-[color:var(--nav-text-muted)]">暂无历史教案</div>
  </aside>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { deleteLessonPlan, getLessonPlanDetail, listLessonPlans, type LessonPlanMeta, type LessonPlanData } from "../../lib/api";

const router = useRouter();
const route = useRoute();
const loading = ref(false);
const plans = ref<LessonPlanMeta[]>([]);
const expandedId = ref<string | null>(null);
const details = ref<Record<string, LessonPlanData>>({});

const loadPlans = async () => {
  loading.value = true;
  try {
    const res = await listLessonPlans();
    plans.value = Array.isArray(res?.lessonPlans) ? res.lessonPlans : [];
  } catch {
    plans.value = [];
  } finally {
    loading.value = false;
  }
};

const openPlan = (id: string) => {
  if (!id) return;
  router.push({ path: "/lesson-plan", query: { lessonPlanId: id }, state: { lessonPlanId: id } });
};

const togglePreview = async (id: string) => {
  if (!id) return;
  if (expandedId.value === id) {
    expandedId.value = null;
    return;
  }
  expandedId.value = id;
  if (!details.value[id]) {
    try {
      const res = await getLessonPlanDetail(id);
      if (res?.ok && res.plan) {
        details.value = { ...details.value, [id]: res.plan };
      }
    } catch {
      return;
    }
  }
};

const startNew = () => {
  router.push({ path: "/lesson-plan", query: { new: String(Date.now()) } });
};

const removePlan = async (id: string) => {
  if (!id) return;
  if (!window.confirm("确定删除该教案吗？")) return;
  const prev = plans.value;
  plans.value = prev.filter((p) => p.id !== id);
  try {
    await deleteLessonPlan(id);
    if ((route.query.lessonPlanId as string) === id) {
      router.push({ path: "/lesson-plan" });
    }
    await loadPlans();
  } catch {
    plans.value = prev;
  }
};

onMounted(loadPlans);
defineExpose({ loadPlans });
</script>
