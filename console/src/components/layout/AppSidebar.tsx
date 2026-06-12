import Drawer from '@mui/material/Drawer';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Divider from '@mui/material/Divider';
import { useLocation, useNavigate } from 'react-router-dom';
import DashboardIcon from '@mui/icons-material/Dashboard';
import LocalShippingIcon from '@mui/icons-material/LocalShipping';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import AddIcon from '@mui/icons-material/Add';
import ScienceIcon from '@mui/icons-material/Science';
import PsychologyIcon from '@mui/icons-material/Psychology';
import BuildIcon from '@mui/icons-material/Build';
import TimelineIcon from '@mui/icons-material/Timeline';
import BugReportIcon from '@mui/icons-material/BugReport';
import MonitorHeartIcon from '@mui/icons-material/MonitorHeart';
import MemoryIcon from '@mui/icons-material/Memory';
import { useSidebarStore } from '@/stores';

const NAV_ITEMS = [
  { label: 'Dashboard', icon: <DashboardIcon />, path: '/' },
  { label: 'Loads', icon: <LocalShippingIcon />, path: '/loads' },
  { label: 'New Load', icon: <AddIcon />, path: '/loads/new' },
  { label: 'Simulation', icon: <ScienceIcon />, path: '/simulation' },
  { label: 'Agent Viewer', icon: <SmartToyIcon />, path: '/agent' },
  { label: 'Workflows', icon: <AccountTreeIcon />, path: '/workflow' },
  { label: 'Memory', icon: <MemoryIcon />, path: '/memory' },
  { label: 'Tool Calls', icon: <BuildIcon />, path: '/tools' },
  { label: 'Traces', icon: <TimelineIcon />, path: '/traces' },
  { label: 'Debugger', icon: <BugReportIcon />, path: '/debugger' },
  { label: 'Monitoring', icon: <MonitorHeartIcon />, path: '/monitoring' },
];

interface AppSidebarProps {
  drawerWidth: number;
}

export function AppSidebar({ drawerWidth }: AppSidebarProps) {
  const open = useSidebarStore((s) => s.open);
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <Drawer
      variant="persistent"
      anchor="left"
      open={open}
      sx={{
        width: open ? drawerWidth : 0,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          bgcolor: '#111827',
          borderRight: '1px solid #2a3a52',
          boxSizing: 'border-box',
          top: '64px',
          height: 'calc(100vh - 64px)',
        },
      }}
    >
      <Box sx={{ px: 2, py: 1.5 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <PsychologyIcon sx={{ color: '#3b82f6', fontSize: 24 }} />
          <Typography variant="subtitle2" sx={{ color: '#94a3b8', fontWeight: 600, letterSpacing: '0.5px' }}>
            WATCHTOWER
          </Typography>
        </Box>
      </Box>
      <Divider sx={{ borderColor: '#2a3a52' }} />
      <List sx={{ px: 1, pt: 1 }}>
        {NAV_ITEMS.map((item) => {
          const isActive = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path));
          return (
            <ListItem key={item.label} disablePadding sx={{ mb: 0.5 }}>
              <ListItemButton
                onClick={() => navigate(item.path)}
                sx={{
                  borderRadius: 1.5,
                  py: 0.75,
                  px: 1.5,
                  bgcolor: isActive ? 'rgba(59, 130, 246, 0.12)' : 'transparent',
                  '&:hover': { bgcolor: isActive ? 'rgba(59, 130, 246, 0.18)' : 'rgba(255,255,255,0.04)' },
                }}
              >
                <ListItemIcon sx={{ minWidth: 36, color: isActive ? '#3b82f6' : '#64748b' }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Typography
                      variant="body2"
                      sx={{
                        fontSize: '0.8125rem',
                        fontWeight: isActive ? 600 : 400,
                        color: isActive ? '#3b82f6' : '#94a3b8',
                      }}
                    >
                      {item.label}
                    </Typography>
                  }
                />
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>
      <Box sx={{ mt: 'auto', p: 2 }}>
        <Divider sx={{ borderColor: '#2a3a52', mb: 2 }} />
        <Typography variant="caption" sx={{ color: '#475569', display: 'block' }}>
          FreightHero Watchtower v0.1.0
        </Typography>
        <Typography variant="caption" sx={{ color: '#475569' }}>
          Agent Operations Console
        </Typography>
      </Box>
    </Drawer>
  );
}