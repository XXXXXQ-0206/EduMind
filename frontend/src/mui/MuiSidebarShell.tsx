import type { ReactElement, ReactNode } from "react";
import {
  Avatar,
  Box,
  Button,
  Divider,
  List,
  ListItemButton,
  ListItemIcon,
  Paper,
  Stack,
  Tooltip,
  Typography,
} from "@mui/material";
import AccountCircleRoundedIcon from "@mui/icons-material/AccountCircleRounded";
import ArticleRoundedIcon from "@mui/icons-material/ArticleRounded";
import ChatRoundedIcon from "@mui/icons-material/ChatRounded";
import ChecklistRoundedIcon from "@mui/icons-material/ChecklistRounded";
import DescriptionRoundedIcon from "@mui/icons-material/DescriptionRounded";
import FactCheckRoundedIcon from "@mui/icons-material/FactCheckRounded";
import FolderRoundedIcon from "@mui/icons-material/FolderRounded";
import HomeRoundedIcon from "@mui/icons-material/HomeRounded";
import LoginRoundedIcon from "@mui/icons-material/LoginRounded";
import LogoutRoundedIcon from "@mui/icons-material/LogoutRounded";
import ManageAccountsRoundedIcon from "@mui/icons-material/ManageAccountsRounded";
import MenuBookRoundedIcon from "@mui/icons-material/MenuBookRounded";
import MicRoundedIcon from "@mui/icons-material/MicRounded";
import OndemandVideoRoundedIcon from "@mui/icons-material/OndemandVideoRounded";
import PodcastsRoundedIcon from "@mui/icons-material/PodcastsRounded";
import SchoolRoundedIcon from "@mui/icons-material/SchoolRounded";
import SettingsRoundedIcon from "@mui/icons-material/SettingsRounded";
import SlideshowRoundedIcon from "@mui/icons-material/SlideshowRounded";
import SmartDisplayRoundedIcon from "@mui/icons-material/SmartDisplayRounded";
import StickyNote2RoundedIcon from "@mui/icons-material/StickyNote2Rounded";
import StyleRoundedIcon from "@mui/icons-material/StyleRounded";
import { MuiSurface, type MuiThemeMode } from "./MuiSurface";

export type MuiSidebarRole = "teacher" | "student";

export type MuiSidebarChat = {
  id: string;
  title?: string;
};

export type MuiSidebarShellProps = {
  activePath: string;
  role: MuiSidebarRole;
  username?: string;
  isAuthenticated: boolean;
  chats: MuiSidebarChat[];
  mode?: MuiThemeMode;
  onNavigate: (path: string) => void;
  onAccountAction: () => void;
  onLogout: () => void;
  onAuth: () => void;
};

type NavItem = {
  label: string;
  path: string;
  icon: ReactElement;
};

const studentItems: NavItem[] = [
  { label: "智能笔记", path: "/smart-notes", icon: <StickyNote2RoundedIcon /> },
  { label: "AI播客", path: "/podcast", icon: <PodcastsRoundedIcon /> },
  { label: "测验", path: "/quiz", icon: <FactCheckRoundedIcon /> },
  { label: "知识卡片", path: "/knowledge-cards", icon: <StyleRoundedIcon /> },
  { label: "bilibili视频学习", path: "/bili-learning", icon: <SmartDisplayRoundedIcon /> },
  { label: "错题本", path: "/wrong-book", icon: <ArticleRoundedIcon /> },
  { label: "学习记录汇", path: "/learning-records", icon: <ChecklistRoundedIcon /> },
  { label: "英语口语", path: "/english-speaking", icon: <MicRoundedIcon /> },
  { label: "学习袋", path: "/cards", icon: <SchoolRoundedIcon /> },
];

const teacherItems: NavItem[] = [
  { label: "教案", path: "/lesson-plan", icon: <DescriptionRoundedIcon /> },
  { label: "教学幻灯片", path: "/slides", icon: <SlideshowRoundedIcon /> },
  { label: "教学视频", path: "/teaching-video", icon: <OndemandVideoRoundedIcon /> },
  { label: "bilibili视频备课", path: "/teacher/bili-learning", icon: <SmartDisplayRoundedIcon /> },
  { label: "测验", path: "/teacher/quiz", icon: <FactCheckRoundedIcon /> },
  { label: "试卷", path: "/teacher/paper", icon: <DescriptionRoundedIcon /> },
  { label: "教学记录汇", path: "/teaching-records", icon: <ChecklistRoundedIcon /> },
];

function navigateWith(event: React.MouseEvent<HTMLAnchorElement>, path: string, onNavigate: (path: string) => void) {
  event.preventDefault();
  onNavigate(path);
}

function SidebarLink({
  item,
  activePath,
  onNavigate,
}: {
  item: NavItem;
  activePath: string;
  onNavigate: (path: string) => void;
}) {
  const selected = activePath === item.path;

  return (
    <Tooltip title={item.label} placement="right">
      <ListItemButton
        component="a"
        href={item.path}
        selected={selected}
        onClick={(event) => navigateWith(event, item.path, onNavigate)}
        sx={{
          minHeight: 42,
          borderRadius: 2,
          px: 1.25,
          gap: 1,
          "&.Mui-selected": {
            bgcolor: "primary.main",
            color: "primary.contrastText",
            boxShadow: "0 10px 24px rgba(37, 99, 235, 0.24)",
            "&:hover": { bgcolor: "primary.dark" },
            "& .MuiListItemIcon-root": { color: "primary.contrastText" },
          },
        }}
      >
        <ListItemIcon sx={{ minWidth: 30, color: selected ? "inherit" : "text.secondary" }}>
          {item.icon}
        </ListItemIcon>
        <Typography
          variant="body2"
          noWrap
          sx={{ display: { xs: "none", md: "block" }, fontSize: 14, fontWeight: selected ? 800 : 650 }}
        >
          {item.label}
        </Typography>
      </ListItemButton>
    </Tooltip>
  );
}

function AccountButton({
  icon,
  label,
  onClick,
  color = "inherit",
}: {
  icon: ReactNode;
  label: string;
  onClick: () => void;
  color?: "inherit" | "primary" | "error";
}) {
  return (
    <Button
      fullWidth
      size="small"
      variant="outlined"
      color={color}
      startIcon={icon}
      onClick={onClick}
      sx={{ justifyContent: "flex-start" }}
    >
      {label}
    </Button>
  );
}

export function MuiSidebarShell({
  activePath,
  role,
  username,
  isAuthenticated,
  chats,
  mode,
  onNavigate,
  onAccountAction,
  onLogout,
  onAuth,
}: MuiSidebarShellProps) {
  const chatPath = role === "teacher" ? "/teacher/chat" : "/chat";
  const filePath = role === "teacher" ? "/teacher/file-library" : "/file-library";
  const commonItems: NavItem[] = [
    { label: "项目首页", path: "/", icon: <HomeRoundedIcon /> },
    { label: "对话", path: chatPath, icon: <ChatRoundedIcon /> },
    { label: "文件库", path: filePath, icon: <FolderRoundedIcon /> },
  ];
  const roleItems = role === "teacher" ? teacherItems : studentItems;
  const displayName = username || "未登录";

  return (
    <MuiSurface mode={mode}>
      {/* 替换：原自定义侧边栏/导航按钮 → MUI Paper/List/ListItemButton/Button，功能已保留 */}
      <Box
        component="aside"
        sx={{
          position: "fixed",
          left: 0,
          bottom: 0,
          zIndex: 50,
          width: { xs: "100vw", md: "auto" },
          height: { xs: "auto", md: "100vh" },
          p: 2,
          display: "flex",
          alignItems: { xs: "flex-end", md: "stretch" },
          gap: 1.5,
          pointerEvents: "none",
        }}
      >
        <Paper
          elevation={12}
          sx={{
            width: { xs: "100%", md: 232 },
            maxHeight: { xs: 96, md: "calc(100vh - 32px)" },
            borderRadius: 3,
            border: "1px solid",
            borderColor: "divider",
            overflow: "hidden",
            display: "flex",
            flexDirection: "column",
            pointerEvents: "auto",
          }}
        >
          <Box sx={{ display: { xs: "none", md: "block" }, px: 2, pt: 2, pb: 1 }}>
            <Typography variant="overline" color="text.secondary" sx={{ fontWeight: 900 }}>
              功能
            </Typography>
          </Box>

          <List
            disablePadding
            sx={{
              display: "flex",
              flexDirection: { xs: "row", md: "column" },
              gap: 0.75,
              px: 1,
              py: 1,
              overflowX: { xs: "auto", md: "hidden" },
              overflowY: { xs: "hidden", md: "auto" },
              flex: 1,
            }}
          >
            {[...commonItems, ...roleItems].map((item) => (
              <SidebarLink key={item.path} item={item} activePath={activePath} onNavigate={onNavigate} />
            ))}

            <Tooltip title="账户设置" placement="right">
              <ListItemButton
                onClick={onAccountAction}
                sx={{
                  minHeight: 42,
                  borderRadius: 2,
                  px: 1.25,
                  gap: 1,
                }}
              >
                <ListItemIcon sx={{ minWidth: 30, color: "text.secondary" }}>
                  <SettingsRoundedIcon />
                </ListItemIcon>
                <Typography
                  variant="body2"
                  noWrap
                  sx={{ display: { xs: "none", md: "block" }, fontSize: 14, fontWeight: 650 }}
                >
                  设置
                </Typography>
              </ListItemButton>
            </Tooltip>
          </List>

          <Box sx={{ display: { xs: "none", md: "block" }, px: 1.5, pb: 1.5 }}>
            <Divider sx={{ mb: 1.5 }} />
            <Stack spacing={1.25}>
              <Stack direction="row" spacing={1.25} sx={{ alignItems: "center" }}>
                <Avatar sx={{ width: 34, height: 34, bgcolor: "primary.main" }}>
                  <AccountCircleRoundedIcon fontSize="small" />
                </Avatar>
                <Box sx={{ minWidth: 0 }}>
                  <Typography variant="caption" color="text.secondary">
                    账户
                  </Typography>
                  <Typography variant="body2" noWrap sx={{ fontWeight: 850 }}>
                    {displayName}
                  </Typography>
                </Box>
              </Stack>

              {isAuthenticated ? (
                <>
                  <AccountButton icon={<ManageAccountsRoundedIcon />} label="账户设置" onClick={onAccountAction} />
                  <AccountButton icon={<LogoutRoundedIcon />} label="退出登录" color="error" onClick={onLogout} />
                </>
              ) : (
                <AccountButton icon={<LoginRoundedIcon />} label="登录 / 注册" color="primary" onClick={onAuth} />
              )}
            </Stack>
          </Box>
        </Paper>

        <Paper
          elevation={10}
          sx={{
            width: 256,
            maxHeight: "calc(100vh - 32px)",
            p: 1.5,
            borderRadius: 3,
            border: "1px solid",
            borderColor: "divider",
            display: { xs: "none", xl: "flex" },
            flexDirection: "column",
            pointerEvents: "auto",
          }}
        >
          <Typography variant="overline" color="text.secondary" sx={{ px: 0.5, fontWeight: 900 }}>
            最近文件
          </Typography>
          <List dense disablePadding sx={{ mt: 0.5, overflowY: "auto" }}>
            {chats.length ? (
              chats.map((chat) => {
                const path = `${chatPath}?chatId=${encodeURIComponent(chat.id)}`;
                return (
                  <ListItemButton
                    key={chat.id}
                    component="a"
                    href={path}
                    onClick={(event) => navigateWith(event, path, onNavigate)}
                    sx={{ borderRadius: 2 }}
                  >
                    <ListItemIcon sx={{ minWidth: 30, color: "text.secondary" }}>
                      <MenuBookRoundedIcon fontSize="small" />
                    </ListItemIcon>
                    <Typography variant="body2" noWrap sx={{ fontSize: 13 }}>
                      {chat.title || "未命名对话"}
                    </Typography>
                  </ListItemButton>
                );
              })
            ) : (
              <Typography variant="caption" color="text.secondary" sx={{ px: 1, py: 1.5 }}>
                暂无最近文件
              </Typography>
            )}
          </List>
        </Paper>
      </Box>
    </MuiSurface>
  );
}
