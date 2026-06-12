import Box from '@mui/material/Box';
import CssBaseline from '@mui/material/CssBaseline';
import { ThemeProvider } from '@mui/material/styles';
import { Outlet } from 'react-router-dom';
import { darkTheme } from '@/theme';
import { AppSidebar } from './AppSidebar';
import { AppHeader } from './AppHeader';
import { useSidebarStore } from '@/stores';

const DRAWER_WIDTH = 260;

export function AppLayout() {
  const sidebarOpen = useSidebarStore((s) => s.open);

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
        <AppHeader drawerWidth={DRAWER_WIDTH} />
        <AppSidebar drawerWidth={DRAWER_WIDTH} />
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            ml: sidebarOpen ? `${DRAWER_WIDTH}px` : 0,
            mt: '64px',
            transition: 'margin-left 0.2s',
            minHeight: 'calc(100vh - 64px)',
            p: 3,
          }}
        >
          <Outlet />
        </Box>
      </Box>
    </ThemeProvider>
  );
}