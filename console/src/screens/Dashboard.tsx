import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Button from '@mui/material/Button';
import LinearProgress from '@mui/material/LinearProgress';
import LocalShippingIcon from '@mui/icons-material/LocalShipping';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import ErrorIcon from '@mui/icons-material/Error';
import ScheduleIcon from '@mui/icons-material/Schedule';
import WarningIcon from '@mui/icons-material/Warning';
import TaskIcon from '@mui/icons-material/Task';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import { useNavigate } from 'react-router-dom';
import { StatCard, StateChip, StatusChip } from '@/components/shared';
import { useDashboardStats, useLoads, useAgentRuns } from '@/api/hooks';
import type { Load, AgentRun } from '@/types';
import { stateColors } from '@/theme';

export function Dashboard() {
  const navigate = useNavigate();
  const { data: dashboardData } = useDashboardStats();
  const { data: loads } = useLoads();
  const { data: agentRuns } = useAgentRuns();
  const stats = dashboardData ?? {
    active_loads: 0,
    running_agents: 0,
    failed_agents: 0,
    scheduled_followups: 0,
    open_issues: 0,
    active_tasks: 0,
    agent_runs_24h: 0,
    memory_operations_24h: 0,
    error_rate_24h: 0,
  };

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>
        Operations Dashboard
      </Typography>
      <Typography variant="body2" sx={{ color: '#64748b', mb: 3 }}>
        Real-time view of freight operations and agent activity
      </Typography>

      {/* Stats Grid */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 6, sm: 6, md: 2 }}>
          <StatCard title="Active Loads" value={stats.active_loads} icon={<LocalShippingIcon fontSize="small" />} color="#3b82f6" />
        </Grid>
        <Grid size={{ xs: 6, sm: 6, md: 2 }}>
          <StatCard title="Running Agents" value={stats.running_agents} icon={<SmartToyIcon fontSize="small" />} color="#22c55e" />
        </Grid>
        <Grid size={{ xs: 6, sm: 6, md: 2 }}>
          <StatCard title="Failed Agents" value={stats.failed_agents} icon={<ErrorIcon fontSize="small" />} color="#ef4444" />
        </Grid>
        <Grid size={{ xs: 6, sm: 6, md: 2 }}>
          <StatCard title="Follow-Ups" value={stats.scheduled_followups} icon={<ScheduleIcon fontSize="small" />} color="#f59e0b" />
        </Grid>
        <Grid size={{ xs: 6, sm: 6, md: 2 }}>
          <StatCard title="Open Issues" value={stats.open_issues} icon={<WarningIcon fontSize="small" />} color="#ef4444" />
        </Grid>
        <Grid size={{ xs: 6, sm: 6, md: 2 }}>
          <StatCard title="Active Tasks" value={stats.active_tasks} icon={<TaskIcon fontSize="small" />} color="#a855f7" />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Active Loads Table */}
        <Grid size={{ xs: 12, lg: 7 }}>
          <Card sx={{ bgcolor: '#1a2235' }}>
            <CardContent sx={{ p: 0 }}>
              <Box sx={{ px: 3, py: 2, borderBottom: '1px solid #2a3a52' }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>Active Loads</Typography>
              </Box>
              <TableContainer sx={{ overflowX: 'auto' }}>
                <Table size="small" sx={{ minWidth: 650 }}>
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ minWidth: 120 }}>Load ID</TableCell>
                      <TableCell sx={{ minWidth: 100 }}>Customer</TableCell>
                      <TableCell sx={{ minWidth: 120 }}>State</TableCell>
                      <TableCell sx={{ minWidth: 100 }}>ETA</TableCell>
                      <TableCell sx={{ minWidth: 120 }}>Driver</TableCell>
                      <TableCell sx={{ minWidth: 100 }}>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {(loads as Load[]).map((load) => (
                      <TableRow
                        key={load.load_id}
                        hover
                        onClick={() => navigate(`/loads/${load.load_id}`)}
                        sx={{ cursor: 'pointer' }}
                      >
                        <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.8125rem', color: '#3b82f6' }}>
                          {load.load_id}
                        </TableCell>
                        <TableCell>
                          <Chip label={load.customer_id} size="small" variant="outlined" sx={{ textTransform: 'capitalize' }} />
                        </TableCell>
                        <TableCell><StateChip state={load.current_state} /></TableCell>
                        <TableCell sx={{ fontSize: '0.8125rem', color: '#94a3b8' }}>
                          {load.current_eta_utc ? new Date(load.current_eta_utc).toLocaleTimeString() : '—'}
                        </TableCell>
                        <TableCell sx={{ fontSize: '0.8125rem' }}>
                          {(load.load_data.driver as { name: string })?.name || '—'}
                        </TableCell>
                        <TableCell>
                          <Button
                            size="small"
                            variant="outlined"
                            startIcon={<PlayArrowIcon fontSize="small" />}
                            onClick={(e) => {
                              e.stopPropagation();
                              localStorage.setItem('freighthero_selected_load', load.load_id);
                              navigate('/simulation');
                            }}
                            sx={{ fontSize: '0.7rem', py: 0.3 }}
                          >
                            Simulate
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Agent Runs */}
        <Grid size={{ xs: 12, lg: 5 }}>
          <Card sx={{ bgcolor: '#1a2235' }}>
            <CardContent sx={{ p: 0 }}>
              <Box sx={{ px: 3, py: 2, borderBottom: '1px solid #2a3a52' }}>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>Recent Agent Runs</Typography>
              </Box>
              <Box sx={{ px: 3, py: 1 }}>
                {((agentRuns as AgentRun[]) || []).map((run) => (
                  <Box
                    key={run.run_id}
                    onClick={() => navigate(`/agent/${run.run_id}`)}
                    sx={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      py: 1.5,
                      px: 1.5,
                      borderRadius: 1.5,
                      cursor: 'pointer',
                      '&:hover': { bgcolor: '#243049' },
                      borderBottom: '1px solid #2a3a5230',
                    }}
                  >
                    <Box sx={{ flex: 1, minWidth: 0 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
                        <StatusChip status={run.status} />
                        <Typography variant="caption" sx={{ color: '#64748b', fontFamily: 'monospace' }}>
                          {run.run_id.slice(0, 12)}
                        </Typography>
                      </Box>
                      <Typography variant="body2" sx={{ color: '#94a3b8', fontSize: '0.75rem' }} noWrap>
                        {run.workflow.replace(/_/g, ' ')} → {run.sop_branch?.replace(/_/g, ' ') || '...'}
                      </Typography>
                    </Box>
                    <Box sx={{ textAlign: 'right' }}>
                      <Typography variant="caption" sx={{ color: '#64748b' }}>
                        {run.load_id}
                      </Typography>
                      <br />
                      <Typography variant="caption" sx={{ color: '#475569' }}>
                        {run.tool_calls.length} tools
                      </Typography>
                    </Box>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>

          {/* Load State Distribution */}
          <Card sx={{ bgcolor: '#1a2235', mt: 3 }}>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>Load State Distribution</Typography>
              {Object.entries(
                (loads as Load[]).reduce<Record<string, number>>((acc, l) => {
                  acc[l.current_state] = (acc[l.current_state] || 0) + 1;
                  return acc;
                }, {})
              ).map(([state, count]) => (
                <Box key={state} sx={{ mb: 1.5 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="caption" sx={{ color: '#94a3b8', textTransform: 'capitalize' }}>
                      {state.replace(/_/g, ' ')}
                    </Typography>
                    <Typography variant="caption" sx={{ color: '#64748b' }}>{count}</Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={(count / (loads as Load[]).length) * 100}
                    sx={{
                      height: 6,
                      borderRadius: 3,
                      bgcolor: '#243049',
                      '& .MuiLinearProgress-bar': { bgcolor: stateColors[state] || '#94a3b8', borderRadius: 3 },
                    }}
                  />
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}