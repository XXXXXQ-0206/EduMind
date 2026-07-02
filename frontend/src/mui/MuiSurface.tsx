import { useMemo, type ReactNode } from "react";
import { createTheme, ThemeProvider } from "@mui/material/styles";

export type MuiThemeMode = "dark" | "light";

type MuiSurfaceProps = {
  mode?: MuiThemeMode;
  children: ReactNode;
};

export function MuiSurface({ mode = "dark", children }: MuiSurfaceProps) {
  const theme = useMemo(
    () =>
      createTheme({
        palette: {
          mode,
          primary: { main: "#2563eb" },
          secondary: { main: "#f97316" },
          success: { main: "#059669" },
          warning: { main: "#d97706" },
          background: {
            default: mode === "dark" ? "#0f172a" : "#f8fafc",
            paper: mode === "dark" ? "rgba(15, 23, 42, 0.92)" : "rgba(255, 255, 255, 0.94)",
          },
          text: {
            primary: mode === "dark" ? "#f8fafc" : "#0f172a",
            secondary: mode === "dark" ? "#cbd5e1" : "#475569",
          },
        },
        shape: { borderRadius: 8 },
        typography: {
          fontFamily:
            'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
          button: {
            textTransform: "none",
            fontWeight: 700,
          },
        },
        components: {
          MuiButton: {
            styleOverrides: {
              root: {
                minHeight: 40,
              },
            },
          },
          MuiPaper: {
            styleOverrides: {
              root: {
                backdropFilter: "blur(18px)",
              },
            },
          },
          MuiTooltip: {
            defaultProps: {
              arrow: true,
            },
          },
        },
      }),
    [mode],
  );

  return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
}
