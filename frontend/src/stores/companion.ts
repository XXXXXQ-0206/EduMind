import { defineStore } from "pinia";
import { computed, ref } from "vue";

export type CompanionDocument = {
  id: string;
  title?: string;
  filePath?: string;
  text?: string;
};

export const useCompanionStore = defineStore("companion", () => {
  const document = ref<CompanionDocument | null>(null);
  const open = ref(false);

  const hasDocument = computed(() => !!document.value);

  const setDocument = (doc: CompanionDocument | null) => {
    const prev = document.value;
    document.value = doc;
    if (!doc) {
      open.value = false;
      return;
    }
    const changed =
      !prev ||
      prev.id !== doc.id ||
      prev.text !== doc.text ||
      prev.title !== doc.title ||
      prev.filePath !== doc.filePath;
    if (changed) open.value = true;
  };

  return { document, open, hasDocument, setDocument };
});
