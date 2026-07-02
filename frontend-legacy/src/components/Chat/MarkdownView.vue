<template>
  <div class="prose prose-invert max-w-3xl leading-relaxed text-stone-200" v-html="rendered"></div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import DOMPurify from "dompurify";
import { marked } from "marked";
import markedKatex from "marked-katex-extension";
import hljs from "highlight.js";

type Props = { md: string };

const props = defineProps<Props>();

marked.setOptions({
  gfm: true,
  breaks: true,
  highlight(code: string, lang: string) {
    if (lang && hljs.getLanguage(lang)) {
      return hljs.highlight(code, { language: lang }).value;
    }
    return hljs.highlightAuto(code).value;
  },
} as any);

marked.use(
  markedKatex({
    throwOnError: false,
    output: "html",
  })
);

const rendered = computed(() => {
  const raw = props.md || "";
  const html = marked.parse(raw) as string;
  return DOMPurify.sanitize(html);
});
</script>
