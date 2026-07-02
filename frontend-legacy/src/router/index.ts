import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { pinia } from "../stores";
import EduMindHome from "../pages/EduMindHome.vue";
import AuthPortal from "../pages/AuthPortal.vue";
import TeacherIntro from "../pages/TeacherIntro.vue";
import StudentIntro from "../pages/StudentIntro.vue";
import Landing from "../pages/Landing.vue";
import Chat from "../pages/Chat.vue";
import Quiz from "../pages/Quiz.vue";
import NotFound from "../pages/NotFound.vue";
import Tools from "../pages/Tools.vue";
import Exam from "../pages/Exam.vue";
import LearningRecords from "../pages/LearningRecords.vue";
import TeachingRecords from "../pages/TeachingRecords.vue";
import WrongBook from "../pages/WrongBook.vue";
import WrongBookPractice from "../pages/WrongBookPractice.vue";
import FlashCards from "../pages/FlashCards.vue";
import LessonPlan from "../pages/LessonPlan.vue";
import Paper from "../pages/Paper.vue";
import Slides from "../pages/Slides.vue";
import TeachingVideo from "../pages/TeachingVideo.vue";
import SmartNotes from "../pages/SmartNotes.vue";
import Podcast from "../pages/Podcast.vue";
import EnglishSpeaking from "../pages/EnglishSpeaking.vue";
import FileLibrary from "../pages/FileLibrary.vue";
import KnowledgeCards from "../pages/KnowledgeCards.vue";
import BiliLearning from "../views/BiliLearning.vue";
import BiliLessonPrep from "../views/BiliLessonPrep.vue";

const routes = [
  { path: "/", name: "home", component: EduMindHome, meta: { hideSidebar: true, public: true } },
  { path: "/auth", name: "auth", component: AuthPortal, meta: { hideSidebar: true, public: true } },
  { path: "/intro/teacher", name: "teacher-intro", component: TeacherIntro, meta: { hideSidebar: true, public: true } },
  { path: "/intro/student", name: "student-intro", component: StudentIntro, meta: { hideSidebar: true, public: true } },
  { path: "/landing", name: "landing", component: Landing, meta: { requiresAuth: true } },
  { path: "/chat", name: "chat", component: Chat, meta: { requiresAuth: true } },
  { path: "/teacher/chat", name: "teacher-chat", component: Chat, meta: { requiresAuth: true } },
  { path: "/teacher/file-library", name: "teacher-file-library", component: FileLibrary, meta: { requiresAuth: true } },
  { path: "/teacher/quiz", name: "teacher-quiz", component: Quiz, meta: { requiresAuth: true } },
  { path: "/teacher/paper", name: "teacher-paper", component: Paper, meta: { requiresAuth: true } },
  { path: "/quiz", name: "quiz", component: Quiz, meta: { requiresAuth: true } },
  { path: "/tools", name: "tools", component: Tools, meta: { requiresAuth: true } },
  { path: "/wrong-book", name: "wrong-book", component: WrongBook, meta: { requiresAuth: true } },
  { path: "/wrong-book/practice", name: "wrong-book-practice", component: WrongBookPractice, meta: { requiresAuth: true } },
  { path: "/learning-records", name: "learning-records", component: LearningRecords, meta: { requiresAuth: true } },
  { path: "/teaching-records", name: "teaching-records", component: TeachingRecords, meta: { requiresAuth: true } },
  { path: "/cards", name: "cards", component: FlashCards, meta: { requiresAuth: true } },
  { path: "/exam", name: "exam", component: Exam, meta: { requiresAuth: true } },
  { path: "/lesson-plan", name: "lesson-plan", component: LessonPlan, meta: { requiresAuth: true } },
  { path: "/slides", name: "slides", component: Slides, meta: { requiresAuth: true } },
  { path: "/teaching-video", name: "teaching-video", component: TeachingVideo, meta: { requiresAuth: true } },
  { path: "/smart-notes", name: "smart-notes", component: SmartNotes, meta: { requiresAuth: true } },
  { path: "/podcast", name: "podcast", component: Podcast, meta: { requiresAuth: true } },
  { path: "/english-speaking", name: "english-speaking", component: EnglishSpeaking, meta: { requiresAuth: true } },
  { path: "/file-library", name: "file-library", component: FileLibrary, meta: { requiresAuth: true } },
  { path: "/knowledge-cards", name: "knowledge-cards", component: KnowledgeCards, meta: { requiresAuth: true } },
  { path: "/bili-learning", name: "bili-learning", component: BiliLearning, meta: { requiresAuth: true } },
  { path: "/teacher/bili-learning", name: "teacher-bili-learning", component: BiliLessonPrep, meta: { requiresAuth: true } },
  { path: "/:pathMatch(.*)*", name: "not-found", component: NotFound, meta: { public: true } },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 };
  },
});

const inferRole = (path: string) => {
  if (
    path.startsWith("/teacher/")
    || ["/lesson-plan", "/slides", "/teaching-video", "/teaching-records"].includes(path)
  ) {
    return "teacher";
  }
  return "student";
};

router.beforeEach(async (to) => {
  const auth = useAuthStore(pinia);
  await auth.hydrate();

  if (to.name === "auth" && auth.isAuthenticated) {
    const redirect = typeof to.query.redirect === "string" ? to.query.redirect : "";
    const requestedRole = to.query.role === "teacher" ? "teacher" : "student";
    return redirect || (requestedRole === "teacher" ? "/intro/teacher" : "/intro/student");
  }

  if (to.meta?.requiresAuth && !auth.isAuthenticated) {
    return {
      path: "/auth",
      query: {
        role: inferRole(to.path),
        redirect: to.fullPath,
      },
    };
  }

  return true;
});

export default router;
