<template>
  <div>
    <div v-if="showSiriUI" class="fixed inset-0 z-50 backdrop-blur-3xl flex items-center justify-center bg-black/70">
      <div class="absolute top-0 left-0 w-96 h-96 bg-gradient-to-br from-blue-600/20 to-transparent rounded-full blur-3xl"></div>
      <div class="absolute bottom-0 right-0 w-80 h-80 bg-gradient-to-tl from-purple-600/15 to-transparent rounded-full blur-3xl"></div>
      <div class="absolute top-1/3 right-1/4 w-64 h-64 bg-gradient-to-b from-pink-500/10 to-transparent rounded-full blur-2xl"></div>

      <div class="relative w-full h-full flex flex-col items-center justify-center px-6">
        <div class="relative" :style="{ width: `${orbSize}px`, height: `${orbSize}px` }">
          <video
            autoplay
            loop
            muted
            playsinline
            class="w-full h-full object-cover rounded-full"
            :style="{
              transform: `scale(${1 + audioIntensity * 0.1 + idleWave * 0.03})`,
              filter: `blur(${processing ? '1px' : '0px'}) brightness(${0.8 + audioIntensity * 0.3})`,
              opacity: 0.9 + audioIntensity * 0.1
            }"
          >
            <source src="/voice/orb.mp4" type="video/mp4" />
          </video>
        </div>

        <div class="absolute bottom-16 sm:bottom-20 flex items-center gap-6 sm:gap-8">
          <button
            type="button"
            @click="cancelRecording"
            class="w-12 h-12 sm:w-14 sm:h-14 rounded-full border border-white/10 text-white/60 hover:text-white/90 hover:border-white/20 transition-all duration-300 flex items-center justify-center"
            :style="glassButtonStyle"
          >
            <svg class="w-5 h-5 sm:w-6 sm:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>

          <button
            type="button"
            @click="recording ? stopRecording() : undefined"
            class="w-16 h-16 sm:w-18 sm:h-18 rounded-full border border-white/15 text-white/80 hover:text-white hover:border-white/25 transition-all duration-300 flex items-center justify-center"
            :style="glassButtonStyle"
          >
            <svg class="w-6 h-6 sm:w-7 sm:h-7" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 14c1.66 0 2.99-1.34 2.99-3L15 5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.3-3c0 3-2.54 5.1-5.3 5.1S6.7 14 6.7 11H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c3.28-.48 6-3.3 6-6.72h-1.7z" />
            </svg>
          </button>
        </div>

        <div v-if="processing" class="absolute bottom-4 sm:bottom-6 text-center">
          <div class="text-white/90 text-base sm:text-lg font-light tracking-wide">处理中</div>
          <div class="text-white/60 text-xs sm:text-sm mt-1">正在将语音转换为文字</div>
        </div>
      </div>
    </div>

    <div v-else class="group rounded-2xl bg-stone-950 border border-zinc-800 p-4 hover:border-orange-500/50 transition-all duration-300 hover:shadow-lg hover:shadow-orange-500/10">
      <div class="flex items-start justify-between gap-3">
        <div class="flex-1">
          <div class="flex items-center gap-2 mb-1">
            <div class="text-xs uppercase tracking-wide text-orange-400 font-semibold">语音转录器</div>
            <div class="w-2 h-2 rounded-full bg-gradient-to-r from-orange-400 to-red-400 animate-pulse"></div>
          </div>
          <div class="text-white font-semibold text-xl mb-2">语音转文字</div>
          <div class="text-stone-300 text-sm leading-relaxed">
            将讲座录音和语音笔记瞬间转化为有条理、可搜索的学习材料。
          </div>
        </div>
      </div>

      <div class="mt-6 space-y-3">
        <div class="flex gap-2">
          <button
            type="button"
            @click="startRecording"
            :disabled="busy"
            class="flex-1 px-4 py-3 rounded-xl bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium transition-all duration-300 flex items-center justify-center gap-2"
          >
            <template v-if="busy">
              <div class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
              处理中...
            </template>
            <template v-else>
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M7 4a3 3 0 616 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 715 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z" clip-rule="evenodd" />
              </svg>
              录制语音
            </template>
          </button>

          <input
            ref="fileInputRef"
            type="file"
            accept="audio/*,video/*"
            class="hidden"
            :disabled="busy"
            @change="onFileChange"
          />

          <button
            type="button"
            @click="fileInputRef?.click()"
            :disabled="busy"
            class="px-6 py-3 rounded-xl bg-stone-800 hover:bg-stone-700 disabled:opacity-50 disabled:cursor-not-allowed text-stone-300 hover:text-white font-medium transition-all duration-300 flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            上传
          </button>
        </div>

        <div v-if="status" :class="['p-4 rounded-xl font-medium', status.startsWith('Error') ? 'bg-red-950/40 border border-red-800/40 text-red-200' : 'bg-orange-950/40 border border-orange-800/40 text-orange-200']">
          {{ status }}
          <span v-if="confidence" class="block text-sm mt-1 opacity-75">置信度: {{ Math.round(confidence * 100) }}%</span>
        </div>

        <div v-if="transcription" class="space-y-4">
          <div v-if="studyMaterials" class="space-y-4">
            <div class="p-4 rounded-xl bg-gradient-to-br from-orange-950/40 to-red-950/40 border border-orange-800/40">
              <div class="flex items-center gap-2 mb-3">
                <svg class="w-5 h-5 text-orange-400" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <h3 class="text-orange-400 font-semibold">学习材料已生成</h3>
              </div>
              <p class="text-orange-200 text-sm">{{ studyMaterials.summary }}</p>
            </div>

            <div class="grid gap-4 md:grid-cols-2">
              <div class="p-4 rounded-xl bg-stone-900/50 border border-zinc-700">
                <h4 class="text-white font-medium mb-3 flex items-center gap-2">
                  <svg class="w-4 h-4 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd" />
                  </svg>
                  关键要点
                </h4>
                <ul class="space-y-2">
                  <li v-for="(point, i) in studyMaterials.keyPoints" :key="i" class="text-stone-300 text-sm flex items-start gap-2">
                    <span class="text-blue-400 mt-1">•</span>
                    {{ point }}
                  </li>
                </ul>
              </div>

              <div class="p-4 rounded-xl bg-stone-900/50 border border-zinc-700">
                <h4 class="text-white font-medium mb-3 flex items-center gap-2">
                  <svg class="w-4 h-4 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M17.707 9.293a1 1 0 010 1.414l-7 7a1 1 0 01-1.414 0l-7-7A.997.997 0 012 10V5a3 3 0 013-3h5c.256 0 .512.098.707.293l7 7zM5 6a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd" />
                  </svg>
                  主题与分类
                </h4>
                <div class="space-y-3">
                  <div>
                    <span class="text-xs text-stone-400 uppercase tracking-wider">主题</span>
                    <div class="flex flex-wrap gap-1 mt-1">
                      <span v-for="(topic, i) in studyMaterials.topics" :key="`topic-${i}`" class="px-2 py-1 bg-green-900/30 text-green-300 text-xs rounded-md">
                        {{ topic }}
                      </span>
                    </div>
                  </div>
                  <div>
                    <span class="text-xs text-stone-400 uppercase tracking-wider">分类</span>
                    <div class="flex flex-wrap gap-1 mt-1">
                      <span v-for="(cat, i) in studyMaterials.categories" :key="`cat-${i}`" class="px-2 py-1 bg-purple-900/30 text-purple-300 text-xs rounded-md">
                        {{ cat }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="studyMaterials.studyGuide.mainConcepts.length > 0" class="p-4 rounded-xl bg-stone-900/50 border border-zinc-700">
              <h4 class="text-white font-medium mb-3 flex items-center gap-2">
                <svg class="w-4 h-4 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
                学习指南
              </h4>
              <div class="grid gap-4 md:grid-cols-2">
                <div>
                  <h5 class="text-stone-300 font-medium mb-2">主要概念</h5>
                  <ul class="space-y-1">
                    <li v-for="(concept, i) in studyMaterials.studyGuide.mainConcepts" :key="`concept-${i}`" class="text-stone-400 text-sm">• {{ concept }}</li>
                  </ul>
                </div>
                <div v-if="studyMaterials.studyGuide.questions.length > 0">
                  <h5 class="text-stone-300 font-medium mb-2">复习问题</h5>
                  <ul class="space-y-1">
                    <li v-for="(question, i) in studyMaterials.studyGuide.questions" :key="`q-${i}`" class="text-stone-400 text-sm">• {{ question }}</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          <div class="p-4 rounded-xl bg-stone-900/50 border border-zinc-700">
            <div class="flex items-center justify-between mb-3">
              <h4 class="text-white font-medium">完整转录</h4>
              <button type="button" @click="copyToClipboard" class="text-xs px-3 py-1 rounded-lg bg-zinc-800 text-zinc-200 hover:bg-zinc-700">复制</button>
            </div>
            <div class="text-stone-300 text-sm whitespace-pre-wrap max-h-60 overflow-y-auto custom-scroll">
              {{ transcription }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from "vue";
import { transcribeAudio, type StudyMaterials } from "../../lib/api";

const busy = ref(false);
const recording = ref(false);
const showSiriUI = ref(false);
const transcription = ref<string | null>(null);
const studyMaterials = ref<StudyMaterials | null>(null);
const status = ref("");
const confidence = ref<number | null>(null);
const audioLevel = ref(0);
const processing = ref(false);

const fileInputRef = ref<HTMLInputElement | null>(null);
const mediaRecorderRef = ref<MediaRecorder | null>(null);
const audioContextRef = ref<AudioContext | null>(null);
const analyserRef = ref<AnalyserNode | null>(null);
const animationFrameRef = ref<number | null>(null);
const chunksRef = ref<Blob[]>([]);

const glassButtonStyle = {
  background: "rgba(255, 255, 255, 0.05)",
  backdropFilter: "blur(20px)",
  WebkitBackdropFilter: "blur(20px)",
};

const handleFileUpload = async (file: File) => {
  if (!file) return;

  busy.value = true;
  processing.value = true;
  status.value = "正在转录音频...";
  transcription.value = null;
  studyMaterials.value = null;
  confidence.value = null;

  try {
    const result = await transcribeAudio(file);
    if (result.ok && result.transcription) {
      transcription.value = result.transcription;
      studyMaterials.value = result.studyMaterials || null;
      confidence.value = result.confidence || null;
      status.value = "学习材料已就绪!";
    } else {
      status.value = `错误: ${result.error || "转录失败"}`;
    }
  } catch (error: any) {
    status.value = `错误: ${error?.message || "音频转录失败"}`;
  } finally {
    busy.value = false;
    processing.value = false;
  }
};

const onFileChange = (e: Event) => {
  const target = e.target as HTMLInputElement;
  const file = target.files?.[0];
  if (file) handleFileUpload(file);
};

const startRecording = async () => {
  try {
    showSiriUI.value = true;
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    const audioContext = new AudioContext();
    const analyser = audioContext.createAnalyser();
    const source = audioContext.createMediaStreamSource(stream);

    analyser.fftSize = 512;
    source.connect(analyser);

    audioContextRef.value = audioContext;
    analyserRef.value = analyser;

    const monitorAudioLevel = () => {
      if (!analyserRef.value) return;
      const bufferLength = analyserRef.value.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      analyserRef.value.getByteFrequencyData(dataArray);
      const average = dataArray.reduce((a, b) => a + b, 0) / bufferLength;
      audioLevel.value = Math.min(1, average / 128);
      animationFrameRef.value = requestAnimationFrame(monitorAudioLevel);
    };

    monitorAudioLevel();

    const mediaRecorder = new MediaRecorder(stream);
    mediaRecorderRef.value = mediaRecorder;
    chunksRef.value = [];

    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.value.push(e.data);
    };

    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(chunksRef.value, { type: "audio/webm" });
      const audioFile = new File([audioBlob], "recording.webm", { type: "audio/webm" });

      if (animationFrameRef.value) cancelAnimationFrame(animationFrameRef.value);
      if (audioContextRef.value) audioContextRef.value.close();

      stream.getTracks().forEach((track) => track.stop());

      await handleFileUpload(audioFile);
      showSiriUI.value = false;
    };

    mediaRecorder.start();
    recording.value = true;
    status.value = "正在听...";
  } catch {
    status.value = "错误: 无法访问麦克风";
    showSiriUI.value = false;
  }
};

const stopRecording = () => {
  if (mediaRecorderRef.value && recording.value) {
    mediaRecorderRef.value.stop();
    recording.value = false;
    audioLevel.value = 0;
    processing.value = true;
    status.value = "处理中...";
  }
};

const cancelRecording = () => {
  if (mediaRecorderRef.value && recording.value) {
    mediaRecorderRef.value.stop();
    recording.value = false;
    audioLevel.value = 0;

    if (animationFrameRef.value) cancelAnimationFrame(animationFrameRef.value);
    if (audioContextRef.value) audioContextRef.value.close();

    if (mediaRecorderRef.value?.stream) {
      mediaRecorderRef.value.stream.getTracks().forEach((track) => track.stop());
    }
  }
  showSiriUI.value = false;
  status.value = "录音已取消";
};

const copyToClipboard = () => {
  if (!transcription.value) return;
  navigator.clipboard.writeText(transcription.value);
  status.value = "已复制到剪贴板!";
};

onBeforeUnmount(() => {
  if (animationFrameRef.value) cancelAnimationFrame(animationFrameRef.value);
  if (audioContextRef.value) audioContextRef.value.close();
});

const orbSize = computed(() => {
  const w = window.innerWidth;
  return w < 768 ? Math.min(w * 0.8, 500) : Math.min(w * 0.6, 600);
});

const audioIntensity = computed(() => Math.max(0.08, audioLevel.value));
const idleWave = computed(() => Math.sin(performance.now() * 0.0006) * 0.4 + Math.cos(performance.now() * 0.0009) * 0.3);
</script>
