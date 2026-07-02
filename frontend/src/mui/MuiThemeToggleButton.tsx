import { Fab, Tooltip } from "@mui/material";
import DarkModeRoundedIcon from "@mui/icons-material/DarkModeRounded";
import LightModeRoundedIcon from "@mui/icons-material/LightModeRounded";
import { MuiSurface, type MuiThemeMode } from "./MuiSurface";

export type MuiThemeToggleButtonProps = {
  mode: MuiThemeMode;
  onToggle: () => void;
};

export function MuiThemeToggleButton({ mode, onToggle }: MuiThemeToggleButtonProps) {
  const isDark = mode === "dark";
  const label = isDark ? "切换到浅色模式" : "切换到深色模式";

  return (
    <MuiSurface mode={mode}>
      {/* 替换：原自定义主题按钮 → MUI Fab/Tooltip，功能已保留 */}
      <Tooltip title={label} placement="left">
        <Fab
          color="primary"
          size="medium"
          aria-label={label}
          onClick={onToggle}
          sx={{
            position: "fixed",
            right: 20,
            bottom: 20,
            zIndex: 50,
            boxShadow: "0 18px 40px rgba(2, 8, 23, 0.22)",
          }}
        >
          {isDark ? <LightModeRoundedIcon /> : <DarkModeRoundedIcon />}
        </Fab>
      </Tooltip>
    </MuiSurface>
  );
}
