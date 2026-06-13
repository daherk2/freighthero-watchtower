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

const NAV_GROUPS = [
  {
    label: 'Operations',
    items: [
      { label: 'Dashboard', icon: <DashboardIcon />, path: '/' },
      { label: 'Loads', icon: <LocalShippingIcon />, path: '/loads' },
      { label: 'New Load', icon: <AddIcon />, path: '/loads/new' },
      { label: 'Simulation', icon: <ScienceIcon />, path: '/simulation' },
    ],
  },
  {
    label: 'Agent Intelligence',
    items: [
      { label: 'Agent Viewer', icon: <SmartToyIcon />, path: '/agent' },
      { label: 'Workflows', icon: <AccountTreeIcon />, path: '/workflow' },
      { label: 'Memory', icon: <MemoryIcon />, path: '/memory' },
      { label: 'Tool Calls', icon: <BuildIcon />, path: '/tools' },
      { label: 'Traces', icon: <TimelineIcon />, path: '/traces' },
    ],
  },
  {
    label: 'System',
    items: [
      { label: 'Debugger', icon: <BugReportIcon />, path: '/debugger' },
      { label: 'Monitoring', icon: <MonitorHeartIcon />, path: '/monitoring' },
    ],
  },
];

interface AppSidebarProps {
  drawerWidth: number;
  isMobile: boolean;
  onClose: () => void;
}

export function AppSidebar({ drawerWidth, isMobile, onClose }: AppSidebarProps) {
  const open = useSidebarStore((s) => s.open);
  const location = useLocation();
  const navigate = useNavigate();

  const handleNav = (path: string) => {
    navigate(path);
    if (isMobile) onClose();
  };

  const drawerContent = (
    <>
      <Box sx={{ px: 2, py: 1.5 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <PsychologyIcon sx={{ color: '#3b82f6', fontSize: 22 }} />
          <Typography variant="subtitle2" sx={{ color: '#94a3b8', fontWeight: 600, letterSpacing: '0.5px', fontSize: '0.7rem' }}>
            WATCHTOWER
          </Typography>
        </Box>
      </Box>
      <Divider sx={{ borderColor: '#2a3a52' }} />

      <Box sx={{ overflowY: 'auto', flex: 1, px: 1, pt: 1 }}>
        {NAV_GROUPS.map((group, gi) => (
          <Box key={group.label} sx={{ mb: gi < NAV_GROUPS.length - 1 ? 1 : 0 }}>
            <Typography
              variant="caption"
              sx={{
                px: 1.5,
                py: 0.5,
                display: 'block',
                color: '#475569',
                fontWeight: 600,
                fontSize: '0.65rem',
                letterSpacing: '0.8px',
                textTransform: 'uppercase',
              }}
            >
              {group.label}
            </Typography>
            <List dense disablePadding>
              {group.items.map((item) => {
                const isActive =
                  location.pathname === item.path ||
                  (item.path !== '/' && location.pathname.startsWith(item.path));
                return (
                  <ListItem key={item.label} disablePadding sx={{ mb: 0.25 }}>
                    <ListItemButton
                      onClick={() => handleNav(item.path)}
                      sx={{
                        borderRadius: 1.5,
                        py: 0.65,
                        px: 1.5,
                        bgcolor: isActive ? 'rgba(59, 130, 246, 0.12)' : 'transparent',
                        '&:hover': {
                          bgcolor: isActive ? 'rgba(59, 130, 246, 0.18)' : 'rgba(255,255,255,0.04)',
                        },
                      }}
                    >
                      <ListItemIcon sx={{ minWidth: 32, color: isActive ? '#3b82f6' : '#64748b' }}>
                        {item.icon}
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Typography
                            variant="body2"
                            sx={{
                              fontSize: '0.8125rem',
                              fontWeight: isActive ? 600 : 400,
                              color: isActive ? '#e2e8f0' : '#94a3b8',
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
            {gi < NAV_GROUPS.length - 1 && (
              <Divider sx={{ borderColor: '#2a3a5240', my: 1 }} />
            )}
          </Box>
        ))}
      </Box>

      <Box sx={{ p: 2 }}>
        <Divider sx={{ borderColor: '#2a3a52', mb: 1.5 }} />
        <Typography variant="caption" sx={{ color: '#475569', display: 'block', fontSize: '0.7rem' }}>
          FreightHero Watchtower v0.1.0
        </Typography>
        <Typography variant="caption" sx={{ color: '#334155', fontSize: '0.7rem' }}>
          Agent Operations Console
        </Typography>
      </Box>
    </>
  );

  if (isMobile) {
    return (
      <Drawer
        variant="temporary"
        anchor="left"
        open={open}
        onClose={onClose}
        ModalProps={{ keepMounted: true }}
        sx={{
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            bgcolor: '#111827',
            borderRight: '1px solid #2a3a52',
            boxSizing: 'border-box',
            display: 'flex',
            flexDirection: 'column',
          },
        }}
      >
        <Box sx={{ mt: 0, display: 'flex', flexDirection: 'column', height: '100%' }}>
          {drawerContent}
        </Box>
      </Drawer>
    );
  }

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
          display: 'flex',
          flexDirection: 'column',
        },
      }}
    >
      {drawerContent}
    </Drawer>
  );
}
