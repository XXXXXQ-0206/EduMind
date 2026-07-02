import { Box, Paper, ToggleButton, ToggleButtonGroup, Tooltip } from "@mui/material";
import AutoAwesomeRoundedIcon from "@mui/icons-material/AutoAwesomeRounded";
import SchoolRoundedIcon from "@mui/icons-material/SchoolRounded";
import LocalLibraryRoundedIcon from "@mui/icons-material/LocalLibraryRounded";
import { MuiSurface, type MuiThemeMode } from "./MuiSurface";

export type MuiUserRole = "teacher" | "student";

export type MuiRoleSwitcherPanelProps = {
  role: MuiUserRole;
  mode?: MuiThemeMode;
  onRoleChange: (role: MuiUserRole) => void;
};

export function MuiRoleSwitcherPanel({ role, mode, onRoleChange }: MuiRoleSwitcherPanelProps) {
  return (
    <MuiSurface mode={mode}>
      <Box
        sx={{
          position: "fixed",
          top: 64,
          left: { xs: 16, md: "auto" },
          right: 16,
          zIndex: 50,
          display: "flex",
          justifyContent: { xs: "center", md: "flex-end" },
          pointerEvents: "none",
        }}
      >
        <Paper
          elevation={8}
          sx={{
            width: "min(100%, 232px)",
            p: 0.5,
            borderRadius: 999,
            border: "1px solid",
            borderColor: "divider",
            bgcolor: "background.paper",
            pointerEvents: "auto",
          }}
        >
          {/* 替换：原自定义角色切换器 → MUI ToggleButtonGroup，功能已保留 */}
          <ToggleButtonGroup
            exclusive
            fullWidth
            value={role}
            aria-label="切换用户角色"
            sx={{
              "& .MuiToggleButton-root": {
                gap: 0.75,
                border: 0,
                borderRadius: "999px !important",
                py: 0.75,
                color: "text.secondary",
              },
              "& .Mui-selected": {
                color: "primary.contrastText !important",
                bgcolor: "primary.main !important",
                boxShadow: "0 8px 18px rgba(37, 99, 235, 0.28)",
              },
            }}
          >
            <ToggleButton value="teacher" aria-label="教师" onClick={() => onRoleChange("teacher")}>
              <Tooltip title="教师端">
                <SchoolRoundedIcon fontSize="small" />
              </Tooltip>
              教师
            </ToggleButton>
            <ToggleButton value="student" aria-label="学生" onClick={() => onRoleChange("student")}>
              <Tooltip title="学生端">
                <LocalLibraryRoundedIcon fontSize="small" />
              </Tooltip>
              学生
            </ToggleButton>
          </ToggleButtonGroup>
          <Box
            aria-hidden="true"
            sx={{
              position: "absolute",
              mt: "-34px",
              ml: "-8px",
              color: "primary.main",
              opacity: 0.72,
              pointerEvents: "none",
            }}
          >
            <AutoAwesomeRoundedIcon sx={{ fontSize: 16 }} />
          </Box>
        </Paper>
      </Box>
    </MuiSurface>
  );
}
