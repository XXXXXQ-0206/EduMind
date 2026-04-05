<template>
  <div class="auth-shell min-h-screen relative overflow-hidden" :class="roleClass">
    <div class="auth-ambient auth-ambient-a"></div>
    <div class="auth-ambient auth-ambient-b"></div>
    <div class="auth-grid"></div>

    <nav class="relative z-10 flex items-center justify-between px-5 py-5 md:px-8">
      <RouterLink to="/" class="inline-flex items-center gap-2 text-sm font-medium text-slate-700 transition hover:text-slate-950">
        <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        返回首页
      </RouterLink>
      <div class="rounded-full border border-white/50 bg-white/70 px-3 py-1 text-xs font-semibold text-slate-700 shadow-[0_8px_24px_rgba(15,23,42,0.08)] backdrop-blur">
        {{ roleLabel }}入口认证
      </div>
    </nav>

    <main class="relative z-10 px-4 pb-10 md:px-8">
      <div class="mx-auto grid max-w-6xl gap-8 lg:grid-cols-[1.1fr_0.9fr]">
        <section class="rounded-[32px] border border-white/55 bg-white/72 p-6 shadow-[0_24px_80px_rgba(15,23,42,0.10)] backdrop-blur-xl md:p-8">
          <div class="inline-flex items-center gap-2 rounded-full border border-[color:var(--auth-accent-soft)] bg-[color:var(--auth-chip-bg)] px-3 py-1 text-xs font-semibold text-[color:var(--auth-accent-strong)]">
            <span class="h-2 w-2 rounded-full bg-[color:var(--auth-accent)]"></span>
            {{ portalCopy.badge }}
          </div>

          <h1 class="mt-5 max-w-xl text-4xl font-black tracking-tight text-slate-950 md:text-5xl">
            {{ portalCopy.heroTitle }}
          </h1>
          <p class="mt-4 max-w-2xl text-base leading-7 text-slate-600 md:text-lg">
            {{ portalCopy.heroDesc }}
          </p>

          <div class="mt-8 grid gap-4 md:grid-cols-3">
            <article v-for="item in highlights" :key="item.title" class="rounded-3xl border border-slate-200/70 bg-white/80 p-4 shadow-[0_12px_32px_rgba(15,23,42,0.06)]">
              <div class="text-sm font-semibold text-slate-950">{{ item.title }}</div>
              <p class="mt-2 text-sm leading-6 text-slate-600">{{ item.desc }}</p>
            </article>
          </div>

          <div class="mt-8 min-h-[220px] rounded-[28px] border p-6 shadow-[0_18px_42px_rgba(15,23,42,0.12)]" :class="summaryCardClass">
            <div class="text-lg font-bold text-slate-950">{{ portalCopy.summaryTitle }}</div>
            <p class="mt-4 text-base leading-8 text-slate-700">
              {{ portalCopy.summaryDesc }}
            </p>
            <div class="mt-5 grid gap-3 sm:grid-cols-2">
              <div
                v-for="point in portalCopy.summaryPoints"
                :key="point.title"
                class="rounded-2xl border border-white/55 bg-white/55 px-4 py-3 shadow-[0_8px_18px_rgba(15,23,42,0.06)]"
              >
                <div class="text-sm font-semibold text-slate-900">{{ point.title }}</div>
                <p class="mt-1 text-sm leading-6 text-slate-600">{{ point.desc }}</p>
              </div>
            </div>
          </div>

          <p v-if="notice" class="mt-6 rounded-2xl border border-emerald-300/50 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-700">
            {{ notice }}
          </p>
        </section>

        <section class="rounded-[32px] border border-white/55 bg-white/84 p-6 shadow-[0_24px_80px_rgba(15,23,42,0.12)] backdrop-blur-xl md:p-8">
          <div class="inline-flex rounded-full border border-slate-200 bg-slate-100 p-1">
            <button
              type="button"
              class="auth-tab"
              :class="{ active: mode === 'login' }"
              @click="mode = 'login'"
            >
              登录
            </button>
            <button
              type="button"
              class="auth-tab"
              :class="{ active: mode === 'register' }"
              @click="mode = 'register'"
            >
              注册
            </button>
          </div>

          <div class="mt-6">
            <h2 class="text-2xl font-black text-slate-950">{{ mode === "login" ? `${roleLabel}登录` : `注册${roleLabel}账号` }}</h2>
            <p class="mt-2 text-sm leading-6 text-slate-500">
              {{ mode === "login" ? portalCopy.loginDesc : portalCopy.registerDesc }}
            </p>
          </div>

          <form class="mt-8 space-y-4" @submit.prevent="submit">
            <label class="block">
              <span class="mb-2 block text-sm font-semibold text-slate-700">用户名</span>
              <input
                v-model.trim="username"
                type="text"
                autocomplete="username"
                class="auth-input"
                maxlength="32"
                placeholder="请输入用户名"
              />
            </label>

            <label class="block">
              <span class="mb-2 block text-sm font-semibold text-slate-700">密码</span>
              <input
                v-model="password"
                type="password"
                :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
                class="auth-input"
                maxlength="64"
                placeholder="请输入密码"
              />
            </label>

            <p v-if="error" class="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
              {{ error }}
            </p>

            <button type="submit" class="auth-submit" :disabled="submitting">
              <span>{{ submitting ? "处理中..." : mode === "login" ? `登录${roleLabel}` : "注册并进入" }}</span>
            </button>
          </form>

          <div class="mt-6 rounded-3xl border border-slate-200/70 bg-slate-50 px-4 py-4 text-sm leading-6 text-slate-600">
            <div class="font-semibold text-slate-800">登录说明</div>
            <ul class="mt-2 space-y-1">
              <li v-for="rule in portalCopy.rules" :key="rule">{{ rule }}</li>
            </ul>
          </div>
        </section>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { useRoleStore } from "../stores/role";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const roleStore = useRoleStore();

const resolveMode = () => (route.query.mode === "register" ? "register" : "login");

const mode = ref<"login" | "register">(resolveMode());
const username = ref("");
const password = ref("");
const error = ref("");
const submitting = ref(false);

const role = computed<"teacher" | "student">(() => (route.query.role === "teacher" ? "teacher" : "student"));
const roleLabel = computed(() => (role.value === "teacher" ? "教师端" : "学生端"));
const roleClass = computed(() => (role.value === "teacher" ? "auth-teacher" : "auth-student"));
const summaryCardClass = computed(() =>
  role.value === "teacher"
    ? "border-sky-200/80 bg-gradient-to-br from-sky-50 via-cyan-50 to-blue-100/80"
    : "border-emerald-200/80 bg-gradient-to-br from-emerald-50 via-lime-50 to-cyan-100/80"
);
const portalCopy = computed(() =>
  role.value === "teacher"
    ? {
        badge: "教师备课空间",
        heroTitle: "进入你的专属备课工作台",
        heroDesc:
          "登录教师端后，你可以围绕教学资料生成教案、测验、课堂提纲与教学内容，持续保存个人备课记录，方便反复打磨课程设计。",
        summaryTitle: "开始你的备课流程",
        summaryDesc:
          "登录后即可进入教师备课空间，围绕课程资料持续整理教案、教学设计与课堂内容。系统会按账户独立保存你的备课记录，方便后续继续完善和复用。",
        summaryPoints: [
          {
            title: "备课内容持续保存",
            desc: "每次生成的教案、提纲与资料问答都会沉淀到当前教师账户下。",
          },
          {
            title: "围绕课程反复打磨",
            desc: "你可以随时回来继续修改课堂设计、补充测验和完善教学流程。",
          },
        ],
        loginDesc: "登录后进入教师备课空间，继续教案编写、课堂设计与资料问答。",
        registerDesc: "注册新账号后将直接进入教师备课空间，开始建立自己的备课记录。",
        rules: [
          "登录后可查看并管理自己的备课对话与资料记录。",
          "新注册账号默认是空白备课空间，不会看到其他人的历史内容。",
          "退出后重新登录，即可继续之前的备课进度。",
        ],
      }
    : {
        badge: "学生学习空间",
        heroTitle: "开启你的专属学习空间",
        heroDesc:
          "登录学生端后，你可以围绕学习资料进行提问、总结、练习与复习，系统会保存个人学习记录，让每一次学习都能接着上一次继续。",
        summaryTitle: "开始你的学习流程",
        summaryDesc:
          "登录后即可进入学生学习空间，围绕自己的学习资料进行提问、总结、练习和复习。系统会按账户独立保存你的学习记录，方便你随时回来继续学习。",
        summaryPoints: [
          {
            title: "学习记录独立保存",
            desc: "你的提问、总结、练习和复习内容都会只保存在当前学生账户中。",
          },
          {
            title: "学习进度随时续接",
            desc: "下次登录后可以继续之前的学习主题，不需要重复从头开始整理。",
          },
        ],
        loginDesc: "登录后进入学生学习空间，继续提问、练习、整理笔记与复习。",
        registerDesc: "注册新账号后将直接进入学生学习空间，开始建立自己的学习记录。",
        rules: [
          "登录后可查看并管理自己的学习对话与个人记录。",
          "新注册账号默认是空白学习空间，不会看到其他人的历史内容。",
          "退出后重新登录，即可继续之前的学习进度。",
        ],
      }
);
const notice = computed(() => {
  if (route.query.reason === "password-changed") return "密码修改成功，请使用新密码重新登录。";
  if (route.query.reason === "account-deleted") return "账户已注销，如需继续使用请重新注册。";
  return "";
});

watch(
  () => route.query.mode,
  () => {
    mode.value = resolveMode();
    error.value = "";
  }
);

const highlights = computed(() =>
  role.value === "teacher"
    ? [
        {
          title: "资料备课",
          desc: "围绕教学资料生成教案、教学目标、课堂提纲与讲解内容。",
        },
        {
          title: "课堂设计",
          desc: "快速整理测验、板书思路、互动提问与课件结构。",
        },
        {
          title: "持续沉淀",
          desc: "个人备课对话独立保存，便于反复修改和长期积累。",
        },
      ]
    : [
        {
          title: "资料问答",
          desc: "围绕学习资料提问、总结重点，快速理解章节内容。",
        },
        {
          title: "练习巩固",
          desc: "生成测验、知识卡片和错题整理，帮助查漏补缺。",
        },
        {
          title: "学习积累",
          desc: "个人学习对话独立保存，复习时可以持续接着学。",
        },
      ]
);

const resolveNextPath = () => {
  const redirect = typeof route.query.redirect === "string" ? route.query.redirect : "";
  if (redirect) return redirect;
  return role.value === "teacher" ? "/intro/teacher" : "/intro/student";
};

const submit = async () => {
  error.value = "";
  if (!username.value) {
    error.value = "请输入用户名";
    return;
  }
  if (username.value.length < 2) {
    error.value = "用户名至少 2 个字符";
    return;
  }
  if (!password.value) {
    error.value = "请输入密码";
    return;
  }
  if (password.value.length < 6) {
    error.value = "密码至少 6 位";
    return;
  }

  submitting.value = true;
  try {
    if (mode.value === "login") {
      await authStore.login(username.value, password.value);
    } else {
      await authStore.register(username.value, password.value);
    }
    roleStore.setRole(role.value);
    await router.replace(resolveNextPath());
  } catch (err) {
    const message = err instanceof Error ? err.message : "认证失败，请稍后重试";
    error.value = message.replace(/^http \d+:\s*/, "") || "认证失败，请稍后重试";
  } finally {
    submitting.value = false;
  }
};
</script>

<style scoped>
.auth-shell {
  --auth-accent: #10b981;
  --auth-accent-strong: #047857;
  --auth-accent-soft: rgba(16, 185, 129, 0.2);
  --auth-chip-bg: rgba(16, 185, 129, 0.12);
  background:
    radial-gradient(circle at top left, rgba(255, 255, 255, 0.95), transparent 40%),
    linear-gradient(140deg, #f8fafc 0%, #f0fdf4 45%, #ecfeff 100%);
}

.auth-teacher {
  --auth-accent: #0ea5e9;
  --auth-accent-strong: #0369a1;
  --auth-accent-soft: rgba(14, 165, 233, 0.22);
  --auth-chip-bg: rgba(14, 165, 233, 0.12);
  background:
    radial-gradient(circle at top left, rgba(255, 255, 255, 0.95), transparent 40%),
    linear-gradient(140deg, #f8fafc 0%, #f0f9ff 48%, #ecfeff 100%);
}

.auth-student {
  background:
    radial-gradient(circle at top left, rgba(255, 255, 255, 0.95), transparent 40%),
    linear-gradient(140deg, #f8fafc 0%, #f0fdf4 48%, #ecfeff 100%);
}

.auth-ambient {
  position: absolute;
  border-radius: 9999px;
  filter: blur(80px);
  opacity: 0.55;
  pointer-events: none;
}

.auth-ambient-a {
  top: -8%;
  right: -8%;
  width: min(34rem, 45vw);
  height: min(34rem, 45vw);
  background: color-mix(in srgb, var(--auth-accent) 32%, white);
}

.auth-ambient-b {
  bottom: -12%;
  left: -8%;
  width: min(28rem, 36vw);
  height: min(28rem, 36vw);
  background: rgba(249, 115, 22, 0.18);
}

.auth-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(148, 163, 184, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, 0.08) 1px, transparent 1px);
  background-size: 32px 32px;
  mask-image: linear-gradient(to bottom, rgba(0, 0, 0, 0.5), transparent 88%);
  pointer-events: none;
}

.auth-tab {
  min-width: 104px;
  border-radius: 9999px;
  padding: 0.65rem 1rem;
  font-size: 0.875rem;
  font-weight: 700;
  color: #475569;
  transition: all 180ms ease;
  cursor: pointer;
}

.auth-tab.active {
  background: linear-gradient(135deg, var(--auth-accent) 0%, color-mix(in srgb, var(--auth-accent) 58%, #f97316) 100%);
  color: white;
  box-shadow: 0 14px 26px color-mix(in srgb, var(--auth-accent) 32%, transparent);
}

.auth-input {
  width: 100%;
  min-height: 52px;
  border-radius: 20px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  background: rgba(255, 255, 255, 0.88);
  padding: 0.95rem 1rem;
  font-size: 1rem;
  color: #0f172a;
  outline: none;
  transition: border-color 180ms ease, box-shadow 180ms ease, transform 180ms ease;
}

.auth-input:focus {
  border-color: var(--auth-accent);
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--auth-accent) 16%, transparent);
  transform: translateY(-1px);
}

.auth-submit {
  width: 100%;
  min-height: 54px;
  border-radius: 22px;
  background: linear-gradient(135deg, var(--auth-accent) 0%, color-mix(in srgb, var(--auth-accent) 58%, #f97316) 100%);
  color: white;
  font-size: 1rem;
  font-weight: 800;
  letter-spacing: 0.01em;
  box-shadow: 0 20px 34px color-mix(in srgb, var(--auth-accent) 26%, transparent);
  transition: transform 180ms ease, box-shadow 180ms ease, opacity 180ms ease;
  cursor: pointer;
}

.auth-submit:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 24px 42px color-mix(in srgb, var(--auth-accent) 32%, transparent);
}

.auth-submit:focus-visible,
.auth-tab:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--auth-accent) 30%, white);
  outline-offset: 2px;
}

.auth-submit:disabled {
  cursor: not-allowed;
  opacity: 0.75;
}

@media (prefers-reduced-motion: reduce) {
  .auth-input,
  .auth-submit,
  .auth-tab {
    transition: none;
  }
}
</style>
