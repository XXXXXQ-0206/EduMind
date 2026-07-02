import { Suspense, lazy, type ReactNode } from "react";
import { createBrowserRouter, Navigate } from "react-router-dom";
import { AppShell } from "@/components/layout/app-shell";

const AuthPage = lazy(() => import("@/pages/auth-page").then((module) => ({ default: module.AuthPage })));
const DashboardPage = lazy(() => import("@/pages/dashboard-page").then((module) => ({ default: module.DashboardPage })));
const FileLibraryPage = lazy(() => import("@/pages/file-library-page").then((module) => ({ default: module.FileLibraryPage })));
const FeatureHubPage = lazy(() => import("@/pages/feature-hub-page").then((module) => ({ default: module.FeatureHubPage })));
const RecordsPage = lazy(() => import("@/pages/records-page").then((module) => ({ default: module.RecordsPage })));
const WorkspacePage = lazy(() => import("@/pages/workspace-page").then((module) => ({ default: module.WorkspacePage })));
const NotFoundPage = lazy(() => import("@/pages/not-found-page").then((module) => ({ default: module.NotFoundPage })));

function routePage(node: ReactNode) {
  return (
    <Suspense
      fallback={
        <div className="grid min-h-[40dvh] place-items-center text-sm text-muted-foreground">
          正在载入工作区...
        </div>
      }
    >
      {node}
    </Suspense>
  );
}

export const router = createBrowserRouter([
  { path: "/auth", element: routePage(<AuthPage />) },
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: routePage(<DashboardPage />) },
      { path: "files", element: routePage(<FileLibraryPage />) },
      { path: "records", element: routePage(<RecordsPage />) },
      { path: "workspace/:kind", element: routePage(<WorkspacePage />) },
      { path: "tools", element: routePage(<FeatureHubPage />) },
      { path: "wrong-book", element: routePage(<FeatureHubPage />) },
      { path: "wrong-book/practice", element: routePage(<FeatureHubPage />) },
      { path: "learning-records", element: routePage(<FeatureHubPage />) },
      { path: "teaching-records", element: routePage(<FeatureHubPage />) },
      { path: "cards", element: routePage(<FeatureHubPage />) },
      { path: "knowledge-cards", element: routePage(<FeatureHubPage />) },
      { path: "exam", element: routePage(<FeatureHubPage />) },
      { path: "teaching-video", element: routePage(<FeatureHubPage />) },
      { path: "english-speaking", element: routePage(<FeatureHubPage />) },
      { path: "bili-learning", element: routePage(<FeatureHubPage />) },
      { path: "teacher/bili-learning", element: routePage(<FeatureHubPage />) },
      { path: "planner", element: routePage(<FeatureHubPage />) },
      { path: "intro/teacher", element: <Navigate to="/?role=teacher" replace /> },
      { path: "intro/student", element: <Navigate to="/?role=student" replace /> },
      { path: "landing", element: <Navigate to="/" replace /> },
      { path: "chat", element: <Navigate to="/workspace/chat" replace /> },
      { path: "quiz", element: <Navigate to="/workspace/quiz" replace /> },
      { path: "file-library", element: <Navigate to="/files" replace /> },
      { path: "teacher/file-library", element: <Navigate to="/files?role=teacher" replace /> },
      { path: "teacher/chat", element: <Navigate to="/workspace/chat?role=teacher" replace /> },
      { path: "teacher/quiz", element: <Navigate to="/workspace/quiz?role=teacher" replace /> },
      { path: "teacher/paper", element: <Navigate to="/workspace/paper" replace /> },
      { path: "paper", element: <Navigate to="/workspace/paper" replace /> },
      { path: "lesson-plan", element: <Navigate to="/workspace/lesson-plan" replace /> },
      { path: "slides", element: <Navigate to="/workspace/slides" replace /> },
      { path: "smart-notes", element: <Navigate to="/workspace/smartnotes" replace /> },
      { path: "podcast", element: <Navigate to="/workspace/podcast" replace /> },
      { path: "*", element: routePage(<NotFoundPage />) },
    ],
  },
]);
