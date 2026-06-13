import Box from '@mui/material/Box';
import CssBaseline from '@mui/material/CssBaseline';
import { ThemeProvider, useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';
import { Outlet } from 'react-router-dom';
import { darkTheme } from '@/theme';
import { AppSidebar } from './AppSidebar';
import { AppHeader } from './AppHeader';
import { useSidebarStore } from '@/stores';

const DRAWER_WIDTH = 260;

export function AppLayout() {
  const sidebarOpen = useSidebarStore((s) => s.open);
  const setOpen = useSidebarStore((s) => s.setOpen);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
        <AppHeader drawerWidth={DRAWER_WIDTH} />
        <AppSidebar
          drawerWidth={DRAWER_WIDTH}
          isMobile={isMobile}
          onClose={() => setOpen(false)}
        />
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            ml: !isMobile && sidebarOpen ? `${DRAWER_WIDTH}px` : 0,
            mt: '64px',
            transition: 'margin-left 0.2s',
            minHeight: 'calc(100vh - 64px)',
            p: { xs: 2, md: 3 },
          }}
        >
          <Outlet />
        </Box>
      </Box>
    </ThemeProvider>
  );
}
