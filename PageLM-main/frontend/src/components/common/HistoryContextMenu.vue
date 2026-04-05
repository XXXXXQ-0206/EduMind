<template>
  <Teleport to="body">
    <div v-if="visible" class="fixed inset-0 z-[120]" @click="emit('close')" @contextmenu.prevent="emit('close')">
      <div
        class="fixed min-w-[170px] rounded-xl border border-[color:var(--nav-border)] bg-[color:var(--nav-bg)] backdrop-blur-xl shadow-[0_12px_30px_rgba(0,0,0,0.35)] p-1"
        :style="menuStyle"
        @click.stop
      >
        <button
          type="button"
          class="w-full text-left rounded-lg px-3 py-2 text-sm text-[color:var(--app-text)] hover:bg-[color:var(--nav-hover-bg-strong)] transition-colors"
          @click="onAdd"
        >
          添加到学习袋
        </button>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted } from "vue";

const props = defineProps<{
  visible: boolean;
  x: number;
  y: number;
}>();

const emit = defineEmits<{
  (e: "select"): void;
  (e: "close"): void;
}>();

const onAdd = () => {
  emit("select");
  emit("close");
};

const menuStyle = computed(() => {
  const menuWidth = 180;
  const menuHeight = 44;
  const padding = 8;
  const maxX = Math.max(padding, window.innerWidth - menuWidth - padding);
  const maxY = Math.max(padding, window.innerHeight - menuHeight - padding);
  const left = Math.min(Math.max(props.x, padding), maxX);
  const top = Math.min(Math.max(props.y, padding), maxY);
  return {
    left: `${left}px`,
    top: `${top}px`,
  };
});

const onEscape = (event: KeyboardEvent) => {
  if (event.key === "Escape") emit("close");
};

const onScroll = () => emit("close");

onMounted(() => {
  window.addEventListener("keydown", onEscape);
  window.addEventListener("scroll", onScroll, true);
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", onEscape);
  window.removeEventListener("scroll", onScroll, true);
});
</script>
