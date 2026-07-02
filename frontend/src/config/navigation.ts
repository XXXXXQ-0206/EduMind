import {
  BookOpenCheck,
  BrainCircuit,
  BookMarked,
  FileQuestion,
  Files,
  Home,
  Layers3,
  Mic,
  MessageSquareText,
  NotebookText,
  Package,
  Presentation,
  Radio,
  ScrollText,
  Video,
  Youtube,
  type LucideIcon,
} from "lucide-react";

export type Role = "student" | "teacher";
export type FeatureKind = "chat" | "quiz" | "paper" | "lesson-plan" | "slides" | "smartnotes" | "podcast";

export type NavItem = {
  label: string;
  href: string;
  icon: LucideIcon;
  activeHrefs?: string[];
};

export type NavSection = {
  title: string;
  role?: Role;
  items: NavItem[];
};

export const navSections: NavSection[] = [
  {
    title: "项目",
    items: [
      { label: "项目首页", href: "/", icon: Home },
    ],
  },
  {
    title: "学生功能",
    role: "student" as Role,
    items: [
      { label: "对话", href: "/workspace/chat", icon: MessageSquareText, activeHrefs: ["/chat"] },
      { label: "文件库", href: "/files", icon: Files, activeHrefs: ["/file-library"] },
      { label: "智能笔记", href: "/workspace/smartnotes", icon: NotebookText, activeHrefs: ["/smart-notes"] },
      { label: "AI播客", href: "/workspace/podcast", icon: Radio, activeHrefs: ["/podcast"] },
      { label: "测验", href: "/workspace/quiz", icon: BookOpenCheck, activeHrefs: ["/quiz"] },
      { label: "知识卡片", href: "/knowledge-cards", icon: BookMarked },
      { label: "bilibili视频学习", href: "/bili-learning", icon: Youtube },
      { label: "错题本", href: "/wrong-book", icon: FileQuestion },
      { label: "学习记录汇", href: "/learning-records", icon: ScrollText },
      { label: "英语口语", href: "/english-speaking", icon: Mic },
      { label: "学习袋", href: "/cards", icon: Package },
    ],
  },
  {
    title: "教师功能",
    role: "teacher" as Role,
    items: [
      { label: "对话", href: "/workspace/chat?role=teacher", icon: BrainCircuit, activeHrefs: ["/teacher/chat"] },
      { label: "文件库", href: "/files?role=teacher", icon: Files, activeHrefs: ["/teacher/file-library"] },
      { label: "教案", href: "/workspace/lesson-plan", icon: Layers3, activeHrefs: ["/lesson-plan"] },
      { label: "教学幻灯片", href: "/workspace/slides", icon: Presentation, activeHrefs: ["/slides"] },
      { label: "教学视频", href: "/teaching-video", icon: Video },
      { label: "bilibili视频备课", href: "/teacher/bili-learning", icon: Youtube },
      { label: "测验", href: "/workspace/quiz?role=teacher", icon: BookOpenCheck, activeHrefs: ["/teacher/quiz"] },
      { label: "试卷", href: "/workspace/paper", icon: FileQuestion, activeHrefs: ["/teacher/paper", "/paper"] },
      { label: "教学记录汇", href: "/teaching-records", icon: ScrollText },
    ],
  },
];

export const workflowDefinitions = [
  {
    kind: "chat" as FeatureKind,
    title: "资料问答",
    description: "基于多文件 RAG 上下文进行连续对话。",
    endpoint: "chat",
    role: "student" as Role,
    icon: MessageSquareText,
    promptLabel: "问题",
    promptPlaceholder: "例如：根据这些 PDF，总结本章的三条关键结论",
  },
  {
    kind: "quiz" as FeatureKind,
    title: "自测练习",
    description: "按主题、难度和资料范围生成题目。",
    endpoint: "quiz",
    role: "student" as Role,
    icon: BookOpenCheck,
    promptLabel: "测验主题",
    promptPlaceholder: "例如：函数极限与连续性",
  },
  {
    kind: "paper" as FeatureKind,
    title: "试卷生成",
    description: "为教师生成选择、填空和应用题组合。",
    endpoint: "paper",
    role: "teacher" as Role,
    icon: FileQuestion,
    promptLabel: "试卷主题",
    promptPlaceholder: "例如：初二物理浮力专题测验",
  },
  {
    kind: "lesson-plan" as FeatureKind,
    title: "教案生成",
    description: "结合资料生成教学目标、重难点和课堂流程。",
    endpoint: "lesson-plan",
    role: "teacher" as Role,
    icon: Layers3,
    promptLabel: "教案主题",
    promptPlaceholder: "例如：一元二次方程的实际应用",
  },
  {
    kind: "slides" as FeatureKind,
    title: "课件生成",
    description: "生成课件大纲和配图预览。",
    endpoint: "slides",
    role: "teacher" as Role,
    icon: Presentation,
    promptLabel: "课件主题",
    promptPlaceholder: "例如：古诗词中的意象分析",
  },
  {
    kind: "smartnotes" as FeatureKind,
    title: "智能笔记",
    description: "整理资料重点、摘要和复习问题。",
    endpoint: "smartnotes",
    role: "student" as Role,
    icon: NotebookText,
    promptLabel: "笔记主题",
    promptPlaceholder: "例如：整理上传材料中的核心公式",
  },
  {
    kind: "podcast" as FeatureKind,
    title: "播客复习",
    description: "把知识点改写为双人播客脚本或音频。",
    endpoint: "podcast",
    role: "student" as Role,
    icon: Radio,
    promptLabel: "播客主题",
    promptPlaceholder: "例如：用轻松对话讲解牛顿三定律",
  },
];

export function workflowByKind(kind: string | undefined) {
  return workflowDefinitions.find((item) => item.kind === kind) ?? workflowDefinitions[0];
}
