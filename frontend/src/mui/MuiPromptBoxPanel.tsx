import { useEffect, useState, type KeyboardEvent, type MouseEvent } from "react";
import {
  Box,
  Button,
  IconButton,
  Menu,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import FolderSpecialRoundedIcon from "@mui/icons-material/FolderSpecialRounded";
import FormatAlignLeftRoundedIcon from "@mui/icons-material/FormatAlignLeftRounded";
import SendRoundedIcon from "@mui/icons-material/SendRounded";
import { MuiSurface, type MuiThemeMode } from "./MuiSurface";

type MenuOption = { key: string; label: string };

export type MuiPromptBoxPanelProps = {
  value: string;
  busy?: boolean;
  responseLengthText?: string;
  showLength?: boolean;
  lengths?: readonly MenuOption[];
  mode?: MuiThemeMode;
  onChange: (value: string) => void;
  onSend: () => void;
  onToggleLength?: () => void;
  onSelectLength?: (key: string, label: string) => void;
  onSelectInclude?: (include: boolean) => void;
};

export function MuiPromptBoxPanel({
  value,
  busy,
  responseLengthText,
  showLength,
  lengths,
  mode,
  onChange,
  onSend,
  onToggleLength,
  onSelectLength,
  onSelectInclude,
}: MuiPromptBoxPanelProps) {
  const [includeMaterials, setIncludeMaterials] = useState(false);
  const [includeAnchor, setIncludeAnchor] = useState<HTMLElement | null>(null);
  const [lengthAnchor, setLengthAnchor] = useState<HTMLElement | null>(null);

  useEffect(() => {
    if (!showLength) setLengthAnchor(null);
  }, [showLength]);

  const handleSendKey = (event: KeyboardEvent<HTMLDivElement>) => {
    if (
      event.key === "Enter" &&
      !event.shiftKey &&
      !event.ctrlKey &&
      !event.altKey &&
      !event.metaKey
    ) {
      event.preventDefault();
      onSend();
    }
  };

  const chooseInclude = (next: boolean) => {
    setIncludeMaterials(next);
    setIncludeAnchor(null);
    onSelectInclude?.(next);
  };

  const openLengthMenu = (event: MouseEvent<HTMLButtonElement>) => {
    if (showLength) {
      setLengthAnchor(null);
      onToggleLength?.();
      return;
    }
    setLengthAnchor(event.currentTarget);
    onToggleLength?.();
  };

  const closeLengthMenu = () => {
    setLengthAnchor(null);
    if (showLength) onToggleLength?.();
  };

  return (
    <MuiSurface mode={mode}>
      {/* 替换：原自定义 PromptBox/textarea/下拉菜单 → MUI Paper/TextField/Button/Menu，功能已保留 */}
      <Paper
        elevation={10}
        sx={{
          border: "1px solid",
          borderColor: "divider",
          bgcolor: "background.paper",
          overflow: "hidden",
          position: "relative",
        }}
      >
        <Box sx={{ p: 1.5 }}>
          <TextField
            fullWidth
            multiline
            minRows={1}
            maxRows={6}
            placeholder="教我任何东西..."
            value={value}
            onChange={(event) => onChange(event.target.value)}
            onKeyDown={handleSendKey}
            aria-label="主要提示"
            variant="outlined"
            sx={{
              "& .MuiInputBase-root": {
                alignItems: "flex-start",
                px: 1,
                py: 0.5,
                color: "text.primary",
              },
              "& fieldset": {
                borderColor: "transparent",
              },
            }}
          />
        </Box>

        <Stack
          direction="row"
          spacing={1.25}
          sx={{
            px: 1.5,
            pb: 1.5,
            justifyContent: "flex-end",
            alignItems: "center",
            flexWrap: "wrap",
          }}
        >
          <Button
            variant="outlined"
            size="small"
            startIcon={<FolderSpecialRoundedIcon />}
            aria-label="学习资料"
            title={includeMaterials ? "学习资料：是" : "学习资料：否"}
            onClick={(event) => setIncludeAnchor(event.currentTarget)}
          >
            学习资料：{includeMaterials ? "是" : "否"}
          </Button>
          <Menu
            anchorEl={includeAnchor}
            open={Boolean(includeAnchor)}
            onClose={() => setIncludeAnchor(null)}
            anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
            transformOrigin={{ vertical: "top", horizontal: "right" }}
          >
            <MenuItem selected={includeMaterials} onClick={() => chooseInclude(true)}>
              是
            </MenuItem>
            <MenuItem selected={!includeMaterials} onClick={() => chooseInclude(false)}>
              否
            </MenuItem>
          </Menu>

          <Button
            variant="outlined"
            size="small"
            startIcon={<FormatAlignLeftRoundedIcon />}
            aria-label="选择回复长度"
            title={responseLengthText ? `回复长度：${responseLengthText}` : "选择回复长度"}
            onClick={openLengthMenu}
          >
            {responseLengthText ? `回复：${responseLengthText}` : "选择回复长度"}
          </Button>
          <Menu
            anchorEl={lengthAnchor}
            open={Boolean(lengthAnchor) && Boolean(showLength) && Boolean(lengths?.length)}
            onClose={closeLengthMenu}
            anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
            transformOrigin={{ vertical: "top", horizontal: "right" }}
          >
            {(lengths || []).map((option) => (
              <MenuItem
                key={option.key}
                selected={option.label === responseLengthText}
                onClick={() => {
                  setLengthAnchor(null);
                  onSelectLength?.(option.key, option.label);
                }}
              >
                {option.label}
              </MenuItem>
            ))}
          </Menu>

          <Tooltip title={busy ? "请稍候..." : "发送"}>
            <span>
              <IconButton
                color="primary"
                aria-label="发送"
                title={busy ? "请稍候..." : "发送"}
                disabled={Boolean(busy) || !value.trim()}
                onClick={onSend}
                sx={{
                  width: 44,
                  height: 44,
                  bgcolor: "primary.main",
                  color: "primary.contrastText",
                  "&:hover": { bgcolor: "primary.dark" },
                  "&.Mui-disabled": {
                    bgcolor: "action.disabledBackground",
                    color: "action.disabled",
                  },
                }}
              >
                <SendRoundedIcon />
              </IconButton>
            </span>
          </Tooltip>
        </Stack>

        {busy ? (
          <Typography
            variant="caption"
            sx={{
              position: "absolute",
              left: 16,
              bottom: 14,
              color: "text.secondary",
            }}
          >
            正在准备回答...
          </Typography>
        ) : null}
      </Paper>
    </MuiSurface>
  );
}
