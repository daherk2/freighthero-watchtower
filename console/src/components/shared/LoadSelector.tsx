import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import IconButton from '@mui/material/IconButton';
import RefreshIcon from '@mui/icons-material/Refresh';
import { StateChip, TruncatedId } from './index';
import { loadsApi } from '@/api/client';
import type { Load } from '@/types';

const STORAGE_KEY = 'freighthero_selected_load';

interface LoadSelectorProps {
  /** Called when the selected load changes */
  onLoadChange?: (loadId: string | null, load?: Load) => void;
  /** If true, show a "View Details" link */
  showViewDetails?: boolean;
  /** Navigate function for View Details link */
  navigate?: (path: string) => void;
}

export function LoadSelector({ onLoadChange, showViewDetails, navigate }: LoadSelectorProps) {
  const [selectedLoadId, setSelectedLoadId] = React.useState<string>(
    localStorage.getItem(STORAGE_KEY) || ''
  );
  const [loads, setLoads] = React.useState<Load[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [selectedLoad, setSelectedLoad] = React.useState<Load | null>(null);

  // Fetch available loads
  const fetchLoads = React.useCallback(async () => {
    setLoading(true);
    try {
      const data = await loadsApi.list() as Load[];
      setLoads(data);
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved && !data.some((l: Load) => l.load_id === saved)) {
        // Saved load no longer exists, clear it
        localStorage.removeItem(STORAGE_KEY);
        setSelectedLoadId('');
      }
    } catch (err) {
      console.error('Failed to fetch loads:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => { fetchLoads(); }, [fetchLoads]);

  // Fetch selected load details
  React.useEffect(() => {
    if (!selectedLoadId) {
      setSelectedLoad(null);
      onLoadChange?.(null);
      return;
    }
    loadsApi.get(selectedLoadId)
      .then((res) => {
        setSelectedLoad(res as Load);
        onLoadChange?.(selectedLoadId, res as Load);
      })
      .catch(() => {
        setSelectedLoad(null);
        onLoadChange?.(selectedLoadId);
      });
  }, [selectedLoadId]);

  const handleChange = (loadId: string) => {
    setSelectedLoadId(loadId);
    if (loadId) {
      localStorage.setItem(STORAGE_KEY, loadId);
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  };

  return (
    <Card sx={{ bgcolor: '#1a2235', mb: 3 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
            Select Load
          </Typography>
          <IconButton size="small" onClick={fetchLoads} sx={{ color: '#64748b' }}>
            <RefreshIcon fontSize="small" />
          </IconButton>
        </Box>

        <Select
          value={selectedLoadId}
          onChange={(e) => handleChange(e.target.value as string)}
          displayEmpty
          fullWidth
          size="small"
          sx={{
            bgcolor: '#0a0e17',
            color: '#e2e8f0',
            '& .MuiSelect-icon': { color: '#64748b' },
            '& .MuiOutlinedInput-notchedOutline': { borderColor: '#2a3a52' },
          }}
          MenuProps={{
            PaperProps: {
              sx: { bgcolor: '#1a2235', maxHeight: 300 },
            },
          }}
        >
          <MenuItem value="">
            <em style={{ color: '#64748b' }}>All loads (global)</em>
          </MenuItem>
          {loads.map((load) => (
            <MenuItem key={load.load_id} value={load.load_id}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <StateChip state={load.current_state} />
                <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                  {load.load_data?.po_number || load.external_load_id || load.load_id.slice(0, 12)}...
                </Typography>
                <Typography variant="caption" sx={{ color: '#64748b' }}>
                  {load.customer_id}
                </Typography>
              </Box>
            </MenuItem>
          ))}
        </Select>

        {selectedLoad && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 2, flexWrap: 'wrap' }}>
            <TruncatedId id={selectedLoad.load_id} chars={14} />
            <StateChip state={selectedLoad.current_state} />
            <Chip label={selectedLoad.customer_id} size="small" variant="outlined" />
            {showViewDetails && navigate && (
              <Chip
                label="View Details →"
                size="small"
                clickable
                onClick={() => navigate(`/loads/${selectedLoad.load_id}`)}
                sx={{ color: '#3b82f6', borderColor: '#3b82f6' }}
                variant="outlined"
              />
            )}
          </Box>
        )}
      </CardContent>
    </Card>
  );
}