import { useState } from 'react';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Box from '@mui/material/Box';
import InputBase from '@mui/material/InputBase';
import MenuIcon from '@mui/icons-material/Menu';
import SearchIcon from '@mui/icons-material/Search';
import RefreshIcon from '@mui/icons-material/Refresh';
import { useSidebarStore } from '@/stores';
import { useNavigate } from 'react-router-dom';

interface AppHeaderProps {
  drawerWidth: number;
}

export function AppHeader({ drawerWidth: _drawerWidth }: AppHeaderProps) {
  const toggle = useSidebarStore((s) => s.toggle);
  const navigate = useNavigate();
  const [search, setSearch] = useState('');

  const handleSearch = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && search.trim()) {
      navigate(`/loads?search=${encodeURIComponent(search.trim())}`);
    }
  };

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
      <Toolbar sx={{ gap: 1 }}>
        <Tooltip title="Toggle sidebar">
          <IconButton color="inherit" edge="start" onClick={toggle} sx={{ mr: 0.5 }} aria-label="toggle sidebar">
            <MenuIcon />
          </IconButton>
        </Tooltip>

        <Box
          onClick={() => navigate('/')}
          sx={{ display: 'flex', alignItems: 'center', gap: 1, cursor: 'pointer', mr: 2, flexShrink: 0 }}
        >
          <Typography variant="h6" sx={{ fontWeight: 700, color: '#3b82f6', letterSpacing: '-0.5px' }}>
            FreightHero
          </Typography>
          <Typography
            variant="caption"
            sx={{
              color: '#475569',
              bgcolor: '#1a2235',
              border: '1px solid #2a3a52',
              px: 0.75,
              py: 0.2,
              borderRadius: 1,
              fontSize: '0.65rem',
              fontWeight: 600,
              letterSpacing: '0.5px',
              display: { xs: 'none', sm: 'block' },
            }}
          >
            WATCHTOWER
          </Typography>
        </Box>

        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            bgcolor: '#1a2235',
            border: '1px solid #2a3a52',
            borderRadius: 1,
            px: 1.5,
            py: 0.5,
            flex: 1,
            maxWidth: { xs: '100%', sm: 280, md: 440 },
            transition: 'border-color 0.15s',
            '&:focus-within': { borderColor: '#3b82f6' },
          }}
        >
          <SearchIcon sx={{ color: '#475569', mr: 1, fontSize: 18, flexShrink: 0 }} />
          <InputBase
            placeholder="Search loads by ID or PO..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={handleSearch}
            sx={{ color: '#94a3b8', flex: 1, fontSize: '0.8125rem', minWidth: 0 }}
            inputProps={{ 'aria-label': 'search loads' }}
          />
          {search && (
            <Typography variant="caption" sx={{ color: '#475569', ml: 1, flexShrink: 0 }}>
              ↵
            </Typography>
          )}
        </Box>

        <Box sx={{ flexGrow: 1 }} />

        <Tooltip title="Refresh page">
          <IconButton
            color="inherit"
            size="small"
            onClick={() => window.location.reload()}
            aria-label="refresh"
            sx={{ color: '#64748b', '&:hover': { color: '#94a3b8' } }}
          >
            <RefreshIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Toolbar>
    </AppBar>
  );
}
