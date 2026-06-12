import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import Badge from '@mui/material/Badge';
import Box from '@mui/material/Box';
import MenuIcon from '@mui/icons-material/Menu';
import NotificationsIcon from '@mui/icons-material/Notifications';
import SearchIcon from '@mui/icons-material/Search';
import InputBase from '@mui/material/InputBase';
import { useSidebarStore } from '@/stores';

interface AppHeaderProps {
  drawerWidth: number;
}

export function AppHeader({ drawerWidth }: AppHeaderProps) {
  const toggle = useSidebarStore((s) => s.toggle);

  return (
    <AppBar
      position="fixed"
      elevation={0}
      sx={{
        width: '100%',
        bgcolor: '#111827',
        borderBottom: '1px solid #2a3a52',
        zIndex: (theme) => theme.zIndex.drawer + 1,
      }}
    >
      <Toolbar sx={{ gap: 2 }}>
        <IconButton color="inherit" edge="start" onClick={toggle} sx={{ mr: 1 }}>
          <MenuIcon />
        </IconButton>

        <Typography variant="h6" sx={{ fontWeight: 700, color: '#3b82f6', mr: 3, letterSpacing: '-0.5px' }}>
          FreightHero
        </Typography>

        <Box sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          bgcolor: '#1a2235', 
          borderRadius: 1, 
          px: 2, 
          py: 0.5, 
          flex: 1, 
          maxWidth: { xs: '100%', sm: 300, md: 480 },
          ml: { xs: 1, sm: 2 }
        }}>
          <SearchIcon sx={{ color: '#64748b', mr: 1, fontSize: 20 }} />
          <InputBase
            placeholder="Search loads, agents, events..."
            sx={{ color: '#94a3b8', flex: 1, fontSize: '0.875rem', minWidth: 0 }}
            inputProps={{ 'aria-label': 'search' }}
          />
        </Box>

        <Box sx={{ flexGrow: 1 }} />

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <IconButton color="inherit" size="small">
            <Badge badgeContent={3} color="error">
              <NotificationsIcon fontSize="small" />
            </Badge>
          </IconButton>
        </Box>
      </Toolbar>
    </AppBar>
  );
}