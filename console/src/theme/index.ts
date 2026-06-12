import { createTheme } from '@mui/material/styles';

export const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#3b82f6' },
    secondary: { main: '#a855f7' },
    error: { main: '#ef4444' },
    warning: { main: '#f59e0b' },
    success: { main: '#22c55e' },
    info: { main: '#06b6d4' },
    background: {
      default: '#0a0e17',
      paper: '#1a2235',
    },
    text: {
      primary: '#e2e8f0',
      secondary: '#94a3b8',
    },
    divider: '#2a3a52',
  },
  typography: {
    fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    h1: { fontSize: '2rem', fontWeight: 700 },
    h2: { fontSize: '1.5rem', fontWeight: 600 },
    h3: { fontSize: '1.25rem', fontWeight: 600 },
    h4: { fontSize: '1.1rem', fontWeight: 600 },
    h5: { fontSize: '1rem', fontWeight: 600 },
    h6: { fontSize: '0.875rem', fontWeight: 600 },
    body2: { fontSize: '0.8125rem' },
    caption: { fontSize: '0.75rem' },
  },
  shape: { borderRadius: 8 },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          border: '1px solid #2a3a52',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: { textTransform: 'none', fontWeight: 500 },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: { fontWeight: 500 },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: { borderBottomColor: '#2a3a52' },
      },
    },
  },
});

export const stateColors: Record<string, string> = {
  dispatched: '#94a3b8',
  on_route_to_delivery: '#3b82f6',
  at_delivery: '#f59e0b',
  confirm_delivery: '#a855f7',
  delivered: '#22c55e',
};

export const statusColors: Record<string, string> = {
  pending: '#94a3b8',
  running: '#3b82f6',
  completed: '#22c55e',
  failed: '#ef4444',
};

export const memoryTypeColors: Record<string, string> = {
  episodic: '#3b82f6',
  semantic: '#a855f7',
  procedural: '#06b6d4',
  STM: '#06b6d4',
  LTM: '#3b82f6',
};

export const workflowColors: Record<string, string> = {
  event: '#f59e0b',
  workflow: '#3b82f6',
  agent: '#a855f7',
  memory: '#06b6d4',
  tool: '#22c55e',
  decision: '#ef4444',
};