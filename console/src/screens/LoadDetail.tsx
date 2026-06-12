import { useParams, useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import IconButton from '@mui/material/IconButton';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import Button from '@mui/material/Button';
import { useState } from 'react';
import CircularProgress from '@mui/material/CircularProgress';
import { StateChip, StatusChip, SectionHeader } from '@/components/shared';
import { useLoad, useLoads, useAgentRuns } from '@/api/hooks';
import { mockEvents, mockMemories } from '@/api/mockData';
import type { Load, AgentRun } from '@/types';
import { stateColors, memoryTypeColors } from '@/theme';

function TabPanel({ children, value, index }: { children: React.ReactNode; value: number; index: number }) {
  return value === index ? <Box sx={{ pt: 3 }}>{children}</Box> : null;
}

export function LoadDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [tab, setTab] = useState(0);
  const { data: loadData } = useLoad(id || '');
  const { data: agentRunsData } = useAgentRuns(id);
  const load = (loadData as Load) || null;
  const allAgentRuns = (agentRunsData as AgentRun[]) || [];

  if (!load) {
    return (
      <Box sx={{ p: 4, textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
        <CircularProgress size={32} />
        <Typography variant="body1" sx={{ color: '#64748b' }}>Loading load details...</Typography>
      </Box>
    );
  }

  const loadEvents = mockEvents.filter((e) => e.load_id === load.load_id);
  const loadRuns = allAgentRuns.filter((r: AgentRun) => r.load_id === load.load_id);
  const loadMemories = mockMemories.filter((m) => m.scope_id === load.load_id);

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <IconButton onClick={() => navigate('/loads')} sx={{ color: '#94a3b8' }}>
          <ArrowBackIcon />
        </IconButton>
        <Box sx={{ flex: 1 }}>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>
            {load.load_id}
          </Typography>
          <Box sx={{ mt: 1 }}>
            <Button
              size="small"
              variant="contained"
              startIcon={<PlayArrowIcon />}
              onClick={() => {
                localStorage.setItem('freighthero_selected_load', load.load_id);
                navigate('/simulation');
              }}
              sx={{ mr: 1 }}
            >
              Simulate
            </Button>
          </Box>
          <Box sx={{ display: 'flex', gap: 1, mt: 0.5 }}>
            <StateChip state={load.current_state} />
            <Chip label={load.customer_id} size="small" variant="outlined" sx={{ textTransform: 'capitalize' }} />
            <Chip label={load.external_load_id} size="small" sx={{ color: '#64748b', fontFamily: 'monospace' }} />
          </Box>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Load Info Card */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card sx={{ bgcolor: '#1a2235' }}>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>Load Information</Typography>
              {[
                ['PO Number', load.po_number || '—'],
                ['Instructions', load.instructions || '—'],
                ['ETA', load.current_eta_utc ? new Date(load.current_eta_utc).toLocaleString() : '—'],
                ['Created', new Date(load.created_at).toLocaleString()],
                ['Updated', new Date(load.updated_at).toLocaleString()],
              ].map(([label, value]) => (
                <Box key={label} sx={{ mb: 1.5 }}>
                  <Typography variant="caption" sx={{ color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                    {label}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#e2e8f0' }}>{value}</Typography>
                </Box>
              ))}
              {(load.load_data.driver as { name: string; phone: string }) && (
                <Box sx={{ mt: 2, p: 1.5, bgcolor: '#0a0e17', borderRadius: 1 }}>
                  <Typography variant="caption" sx={{ color: '#64748b' }}>Driver</Typography>
                  <Typography variant="body2" sx={{ color: '#e2e8f0' }}>
                    {(load.load_data.driver as { name: string; phone: string }).name}
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#94a3b8' }}>
                    {(load.load_data.driver as { name: string; phone: string }).phone}
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Tabbed Content */}
        <Grid size={{ xs: 12, md: 8 }}>
          <Card sx={{ bgcolor: '#1a2235' }}>
            <Box sx={{ borderBottom: '1px solid #2a3a52' }}>
              <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ px: 2 }}>
                <Tab label="Events" />
                <Tab label="Agent Runs" />
                <Tab label="Memory" />
                <Tab label="Tracking" />
              </Tabs>
            </Box>
            <CardContent>
              <TabPanel value={tab} index={0}>
                <TableContainer sx={{ overflowX: 'auto' }}>
                  <Table size="small" sx={{ minWidth: 650 }}>
                    <TableHead>
                      <TableRow>
                        <TableCell sx={{ minWidth: 150 }}>Event ID</TableCell>
                        <TableCell sx={{ minWidth: 120 }}>Type</TableCell>
                        <TableCell sx={{ minWidth: 150 }}>Occurred At</TableCell>
                        <TableCell sx={{ minWidth: 200, maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>Summary</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {loadEvents.map((event) => (
                        <TableRow key={event.event_id} hover>
                          <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.75rem', color: '#3b82f6' }}>
                            {event.event_id.slice(0, 16)}
                          </TableCell>
                          <TableCell><Chip label={event.event_type.replace(/_/g, ' ')} size="small" /></TableCell>
                          <TableCell sx={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                            {new Date(event.occurred_at).toLocaleString()}
                          </TableCell>
                          <TableCell sx={{ fontSize: '0.75rem', color: '#94a3b8', maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {(event.event_data as { message?: string }).message || JSON.stringify(event.event_data).slice(0, 60)}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </TabPanel>

              <TabPanel value={tab} index={1}>
                {loadRuns.map((run) => (
                  <Box
                    key={run.run_id}
                    onClick={() => navigate(`/agent/${run.run_id}`)}
                    sx={{
                      p: 2, mb: 1.5, borderRadius: 1.5, cursor: 'pointer',
                      bgcolor: '#0a0e17', border: '1px solid #2a3a52',
                      '&:hover': { borderColor: '#3b82f6' },
                    }}
                  >
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                        <StatusChip status={run.status} />
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          {run.workflow.replace(/_/g, ' ')}
                        </Typography>
                      </Box>
                      <Typography variant="caption" sx={{ color: '#64748b', fontFamily: 'monospace' }}>
                        {run.run_id.slice(0, 12)}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', gap: 2 }}>
                      <Typography variant="caption" sx={{ color: '#94a3b8' }}>
                        Branch: <strong>{run.sop_branch?.replace(/_/g, ' ') || '—'}</strong>
                      </Typography>
                      <Typography variant="caption" sx={{ color: '#94a3b8' }}>
                        Tools: <strong>{run.tool_calls.length}</strong>
                      </Typography>
                      <Typography variant="caption" sx={{ color: '#94a3b8' }}>
                        Memory ops: <strong>{run.memory_operations.length}</strong>
                      </Typography>
                    </Box>
                  </Box>
                ))}
              </TabPanel>

              <TabPanel value={tab} index={2}>
                {loadMemories.map((mem) => (
                  <Box key={mem.id} sx={{ p: 2, mb: 1.5, borderRadius: 1.5, bgcolor: '#0a0e17', border: '1px solid #2a3a52' }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Chip
                        label={mem.memory_type}
                        size="small"
                        sx={{ bgcolor: `${memoryTypeColors[mem.memory_type]}20`, color: memoryTypeColors[mem.memory_type] }}
                      />
                      <Typography variant="caption" sx={{ color: '#64748b' }}>
                        conf: {mem.confidence.toFixed(2)} · rel: {mem.relevance_score.toFixed(2)}
                      </Typography>
                    </Box>
                    <Typography variant="body2" sx={{ color: '#e2e8f0', mb: 1 }}>{mem.content}</Typography>
                    <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                      {mem.tags.map((tag) => (
                        <Chip key={tag} label={tag} size="small" variant="outlined" sx={{ fontSize: '0.625rem', height: 20 }} />
                      ))}
                    </Box>
                  </Box>
                ))}
              </TabPanel>

              <TabPanel value={tab} index={3}>
                <Typography variant="body2" sx={{ color: '#64748b', textAlign: 'center', py: 4 }}>
                  Tracking history visualization coming soon
                </Typography>
              </TabPanel>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}

export function LoadList() {
  const navigate = useNavigate();
  const { data: loads } = useLoads();
  const allLoads = (loads as Load[]) || [];

  return (
    <Box>
      <SectionHeader title="Loads" subtitle="All active and recent loads" />
      <Card sx={{ bgcolor: '#1a2235' }}>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Load ID</TableCell>
                <TableCell>Customer</TableCell>
                <TableCell>State</TableCell>
                <TableCell>PO Number</TableCell>
                <TableCell>ETA</TableCell>
                <TableCell>Driver</TableCell>
                <TableCell>Updated</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {allLoads.map((load) => (
                <TableRow key={load.load_id} hover onClick={() => navigate(`/loads/${load.load_id}`)} sx={{ cursor: 'pointer' }}>
                  <TableCell sx={{ fontFamily: 'monospace', color: '#3b82f6' }}>{load.load_id}</TableCell>
                  <TableCell><Chip label={load.customer_id} size="small" variant="outlined" /></TableCell>
                  <TableCell><StateChip state={load.current_state} /></TableCell>
                  <TableCell sx={{ color: '#94a3b8' }}>{load.po_number || '—'}</TableCell>
                  <TableCell sx={{ color: '#94a3b8' }}>{load.current_eta_utc ? new Date(load.current_eta_utc).toLocaleTimeString() : '—'}</TableCell>
                  <TableCell>{((load.load_data as Record<string, unknown> | undefined)?.driver as { name: string } | undefined)?.name || '—'}</TableCell>
                  <TableCell sx={{ color: '#64748b', fontSize: '0.75rem' }}>{load.updated_at ? new Date(load.updated_at).toLocaleString() : '—'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Card>
    </Box>
  );
}