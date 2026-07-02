import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  IconButton,
  Paper,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import CloseRoundedIcon from "@mui/icons-material/CloseRounded";
import DeleteRoundedIcon from "@mui/icons-material/DeleteRounded";
import LockRoundedIcon from "@mui/icons-material/LockRounded";
import VisibilityOffRoundedIcon from "@mui/icons-material/VisibilityOffRounded";
import VisibilityRoundedIcon from "@mui/icons-material/VisibilityRounded";
import WarningRoundedIcon from "@mui/icons-material/WarningRounded";
import { MuiSurface, type MuiThemeMode } from "./MuiSurface";

export type MuiAccountSettingsDialogProps = {
  open: boolean;
  username: string;
  oldPassword: string;
  newPassword: string;
  confirmPassword: string;
  deletePassword: string;
  showOldPassword: boolean;
  showNewPassword: boolean;
  showConfirmPassword: boolean;
  showDeletePassword: boolean;
  passwordError?: string;
  deleteError?: string;
  passwordSubmitting?: boolean;
  deleteSubmitting?: boolean;
  confirmingDeletion?: boolean;
  mode?: MuiThemeMode;
  onClose: () => void;
  onOldPasswordChange: (value: string) => void;
  onNewPasswordChange: (value: string) => void;
  onConfirmPasswordChange: (value: string) => void;
  onDeletePasswordChange: (value: string) => void;
  onToggleOldPassword: () => void;
  onToggleNewPassword: () => void;
  onToggleConfirmPassword: () => void;
  onToggleDeletePassword: () => void;
  onSubmitPasswordChange: () => void;
  onOpenDeleteConfirm: () => void;
  onCloseDeleteConfirm: () => void;
  onSubmitDeleteAccount: () => void;
};

type PasswordFieldProps = {
  label: string;
  value: string;
  shown: boolean;
  autocomplete: string;
  danger?: boolean;
  onChange: (value: string) => void;
  onToggle: () => void;
};

function PasswordField({
  label,
  value,
  shown,
  autocomplete,
  danger,
  onChange,
  onToggle,
}: PasswordFieldProps) {
  const visibilityLabel = shown ? `隐藏${label}` : `显示${label}`;

  return (
    <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
      <TextField
        fullWidth
        size="small"
        label={label}
        type={shown ? "text" : "password"}
        value={value}
        autoComplete={autocomplete}
        error={Boolean(danger)}
        onChange={(event) => onChange(event.target.value)}
      />
      <Tooltip title={visibilityLabel}>
        <IconButton aria-label={visibilityLabel} color={danger ? "error" : "default"} onClick={onToggle}>
          {shown ? <VisibilityOffRoundedIcon /> : <VisibilityRoundedIcon />}
        </IconButton>
      </Tooltip>
    </Stack>
  );
}

export function MuiAccountSettingsDialog({
  open,
  username,
  oldPassword,
  newPassword,
  confirmPassword,
  deletePassword,
  showOldPassword,
  showNewPassword,
  showConfirmPassword,
  showDeletePassword,
  passwordError,
  deleteError,
  passwordSubmitting,
  deleteSubmitting,
  confirmingDeletion,
  mode,
  onClose,
  onOldPasswordChange,
  onNewPasswordChange,
  onConfirmPasswordChange,
  onDeletePasswordChange,
  onToggleOldPassword,
  onToggleNewPassword,
  onToggleConfirmPassword,
  onToggleDeletePassword,
  onSubmitPasswordChange,
  onOpenDeleteConfirm,
  onCloseDeleteConfirm,
  onSubmitDeleteAccount,
}: MuiAccountSettingsDialogProps) {
  return (
    <MuiSurface mode={mode}>
      {/* 替换：原自定义账户设置 Modal/表单 → MUI Dialog/TextField/Button/Alert，功能已保留 */}
      <Dialog
        open={open}
        fullWidth
        maxWidth="md"
        onClose={(_event, reason) => {
          if (reason === "backdropClick") onClose();
        }}
        slotProps={{
          paper: {
            sx: {
              border: "1px solid",
              borderColor: "divider",
              bgcolor: "background.paper",
            },
          },
        }}
      >
        <DialogTitle sx={{ pr: 7 }}>
          <Typography variant="overline" color="text.secondary" sx={{ fontWeight: 900 }}>
            Account Settings
          </Typography>
          <Typography variant="h5" sx={{ fontWeight: 900 }}>
            账户设置
          </Typography>
          <Typography variant="body2" color="text.secondary">
            当前账户：
            <Box component="span" sx={{ color: "text.primary", fontWeight: 800 }}>
              {username}
            </Box>
          </Typography>
          <IconButton
            aria-label="关闭设置"
            onClick={onClose}
            sx={{ position: "absolute", top: 14, right: 14 }}
          >
            <CloseRoundedIcon />
          </IconButton>
        </DialogTitle>

        <DialogContent>
          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: { xs: "1fr", lg: "1.15fr 0.85fr" },
              gap: 2,
              py: 1,
            }}
          >
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Stack direction="row" spacing={1.5} sx={{ alignItems: "center" }}>
                <LockRoundedIcon color="primary" />
                <Box>
                  <Typography variant="subtitle1" sx={{ fontWeight: 850 }}>
                    修改密码
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    修改成功后将退出当前登录，需要重新登录。
                  </Typography>
                </Box>
              </Stack>

              <Box
                component="form"
                sx={{ mt: 2.5 }}
                onSubmit={(event) => {
                  event.preventDefault();
                  onSubmitPasswordChange();
                }}
              >
                <Stack spacing={2}>
                  <PasswordField
                    label="旧密码"
                    value={oldPassword}
                    shown={showOldPassword}
                    autocomplete="current-password"
                    onChange={onOldPasswordChange}
                    onToggle={onToggleOldPassword}
                  />
                  <PasswordField
                    label="新密码"
                    value={newPassword}
                    shown={showNewPassword}
                    autocomplete="new-password"
                    onChange={onNewPasswordChange}
                    onToggle={onToggleNewPassword}
                  />
                  <PasswordField
                    label="确认新密码"
                    value={confirmPassword}
                    shown={showConfirmPassword}
                    autocomplete="new-password"
                    onChange={onConfirmPasswordChange}
                    onToggle={onToggleConfirmPassword}
                  />
                  {passwordError ? <Alert severity="error">{passwordError}</Alert> : null}
                  <Button type="submit" variant="contained" disabled={Boolean(passwordSubmitting)}>
                    {passwordSubmitting ? "提交中..." : "保存新密码"}
                  </Button>
                </Stack>
              </Box>
            </Paper>

            <Paper variant="outlined" sx={{ p: 2, borderColor: "error.main" }}>
              <Stack direction="row" spacing={1.5} sx={{ alignItems: "center" }}>
                <DeleteRoundedIcon color="error" />
                <Box>
                  <Typography variant="subtitle1" sx={{ fontWeight: 850 }}>
                    注销账户
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    只会注销当前正在使用的账户，删除后不可恢复。
                  </Typography>
                </Box>
              </Stack>

              <Stack spacing={2} sx={{ mt: 2.5 }}>
                <PasswordField
                  label="账户密码"
                  value={deletePassword}
                  shown={showDeletePassword}
                  autocomplete="current-password"
                  danger={Boolean(deleteError)}
                  onChange={onDeletePasswordChange}
                  onToggle={onToggleDeletePassword}
                />
                {deleteError ? <Alert severity="error">{deleteError}</Alert> : null}
                <Button color="error" variant="outlined" startIcon={<DeleteRoundedIcon />} onClick={onOpenDeleteConfirm}>
                  注销当前账户
                </Button>
              </Stack>
            </Paper>
          </Box>
        </DialogContent>
      </Dialog>

      <Dialog
        open={Boolean(confirmingDeletion)}
        fullWidth
        maxWidth="xs"
        onClose={(_event, reason) => {
          if (reason === "backdropClick") onCloseDeleteConfirm();
        }}
      >
        <DialogTitle>
          <Stack direction="row" spacing={1.25} sx={{ alignItems: "center" }}>
            <WarningRoundedIcon color="error" />
            <Typography variant="h6" sx={{ fontWeight: 850 }}>
              确认注销账户
            </Typography>
          </Stack>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary">
            该操作会删除当前账户及其对应历史数据，且无法恢复。
          </Typography>
          <Divider sx={{ my: 2 }} />
          <Typography variant="body2">
            账户：
            <Box component="span" sx={{ fontWeight: 850 }}>
              {username}
            </Box>
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={onCloseDeleteConfirm}>取消</Button>
          <Button color="error" variant="contained" disabled={Boolean(deleteSubmitting)} onClick={onSubmitDeleteAccount}>
            {deleteSubmitting ? "注销中..." : "确认注销"}
          </Button>
        </DialogActions>
      </Dialog>
    </MuiSurface>
  );
}
