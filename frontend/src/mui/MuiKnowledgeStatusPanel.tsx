import { Box, Button, LinearProgress, Paper, Stack, Typography } from "@mui/material";
import type { ReactElement } from "react";
import CheckCircleRoundedIcon from "@mui/icons-material/CheckCircleRounded";
import HelpOutlineRoundedIcon from "@mui/icons-material/HelpOutlineRounded";
import RefreshRoundedIcon from "@mui/icons-material/RefreshRounded";
import ScheduleRoundedIcon from "@mui/icons-material/ScheduleRounded";
import { MuiSurface, type MuiThemeMode } from "./MuiSurface";

type KnowledgeStatus = "mastered" | "pending" | "review";

export type MuiKnowledgeStatusPanelProps = {
  counts: Record<KnowledgeStatus, number>;
  loading?: boolean;
  mode?: MuiThemeMode;
  onRefresh: () => void;
  onStatusClick: (status: KnowledgeStatus) => void;
};

const statusItems: Array<{
  key: KnowledgeStatus;
  label: string;
  color: "success" | "inherit" | "warning";
  icon: ReactElement;
}> = [
  { key: "mastered", label: "标记掌握", color: "success", icon: <CheckCircleRoundedIcon /> },
  { key: "pending", label: "待确认", color: "inherit", icon: <HelpOutlineRoundedIcon /> },
  { key: "review", label: "待复习", color: "warning", icon: <ScheduleRoundedIcon /> },
];

export function MuiKnowledgeStatusPanel({
  counts,
  loading,
  mode,
  onRefresh,
  onStatusClick,
}: MuiKnowledgeStatusPanelProps) {
  return (
    <MuiSurface mode={mode}>
      {/* 替换：原自定义知识卡片快捷区 → MUI Paper/Button/LinearProgress，功能已保留 */}
      <Paper
        elevation={8}
        sx={{
          mt: 3,
          p: 2.5,
          border: "1px solid",
          borderColor: "divider",
          bgcolor: "background.paper",
        }}
      >
        <Stack
          direction="row"
          sx={{ alignItems: "center", justifyContent: "space-between", gap: 2 }}
        >
          <Box>
            <Typography variant="caption" color="text.secondary">
              知识卡片
            </Typography>
            <Typography variant="subtitle1" sx={{ fontWeight: 800 }}>
              掌握度快捷复习
            </Typography>
          </Box>
          <Button
            size="small"
            variant="outlined"
            startIcon={<RefreshRoundedIcon />}
            onClick={onRefresh}
            disabled={Boolean(loading)}
          >
            刷新统计
          </Button>
        </Stack>

        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: { xs: "1fr", sm: "repeat(3, minmax(0, 1fr))" },
            gap: 1.25,
            mt: 2,
          }}
        >
          {statusItems.map((item) => (
            <Button
              key={item.key}
              variant="outlined"
              color={item.color}
              startIcon={item.icon}
              onClick={() => onStatusClick(item.key)}
              sx={{
                minHeight: 54,
                justifyContent: "space-between",
                px: 1.5,
                "& .MuiButton-endIcon": { ml: "auto" },
              }}
              endIcon={
                <Typography component="span" variant="body2" sx={{ fontWeight: 900 }}>
                  {counts[item.key] ?? 0}
                </Typography>
              }
            >
              {item.label}
            </Button>
          ))}
        </Box>

        {loading ? (
          <Box sx={{ mt: 1.5 }}>
            <LinearProgress />
            <Typography variant="caption" color="text.secondary">
              统计更新中...
            </Typography>
          </Box>
        ) : null}
      </Paper>
    </MuiSurface>
  );
}
