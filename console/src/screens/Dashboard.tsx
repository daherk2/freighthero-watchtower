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
import Skeleton from '@mui/material/Skeleton';
import Tooltip from '@mui/material/Tooltip';
import IconButton from '@mui/material/IconButton';
import LocalShippingIcon from '@mui/icons-material/LocalShipping';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import ErrorIcon from '@mui/icons-material/Error';
import ScheduleIcon from '@mui/icons-material/Schedule';
import WarningIcon from '@mui/icons-material/Warning';
import TaskIcon from '@mui/icons-material/Task';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import RefreshIcon from '@mui/icons-material/Refresh';
import InboxIcon from '@mui/icons-material/Inbox';
import AddIcon from '@mui/icons-material/Add';
import { useNavigate } from 'react-router-dom';
import { StatCard, StateChip, StatusChip, TruncatedId, EmptyState } from '@/components/shared';
import { useDashboardStats, useLoads, useAgentRuns } from '@/api/hooks';
import type { Load, AgentRun } from '@/types';
import { stateColors } from '@/theme';
import { LOAD_STORAGE_KEY } from '@/api/client';

export function Dashboard() {
  const navigate = useNavigate();
  const { data: dashboardData, isLoading: statsLoading, refetch: refetchStats } = useDashboardStats();
  const { data: loadsRaw, isLoading: loadsLoading, refetch: refetchLoads } = useLoads();
  const { data: agentRunsRaw, isLoading: runsLoading, refetch: refetchRuns } = useAgentRuns();

  const loads = (loadsRaw as Load[]) ?? [];
  const agentRuns = (agentRunsRaw as AgentRun[]) ?? [];

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

  const handleRefresh = () => {
    refetchStats();
    refetchLoads();
    refetchRuns();
  };

  const statCards = [
    { title: 'Active Loads', value: stats.active_loads, icon: <LocalShippingIcon fontSize="small" />, color: '#3b82f6' },
    { title: 'Running Agents', value: stats.running_agents, icon: <SmartToyIcon fontSize="small" />, color: '#22c55e' },
    { title: 'Failed Agents', value: stats.failed_agents, icon: <ErrorIcon fontSize="small" />, color: '#ef4444' },
    { title: 'Follow-Ups', value: stats.scheduled_followups, icon: <ScheduleIcon fontSize="small" />, color: '#f59e0b' },
    { title: 'Open Issues', value: stats.open_issues, icon: <WarningIcon fontSize="small" />, color: '#ef4444' },
    { title: 'Active Tasks', value: stats.active_tasks, icon: <TaskIcon fontSize="small" />, color: '#a855f7' },
  ];

  const stateDistribution = loads.reduce<Record<string, number>>((acc, l) => {
    acc[l.current_state] = (acc[l.current_state] || 0) + 1;
    return acc;
  }, {});

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.25, fontSize: '1.5rem' }}>
            Operations Dashboard
          </Typography>
          <Typography variant="body2" sx={{ color: '#64748b' }}>
            Real-time view of freight operations and agent activity
          </Typography>
        </Box>
        <Tooltip title="Refresh all data">
          <IconButton
            onClick={handleRefresh}
            size="small"
            sx={{ color: '#64748b', mt: 0.5, '&:hover': { color: '#94a3b8' } }}
            aria-label="refresh dashboard"
          >
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Stats Grid */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {statCards.map((card) => (
          <Grid key={card.title} size={{ xs: 6, sm: 4, md: 2 }}>
            <StatCard {...card} loading={statsLoading} />
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={3}>
        {/* Active Loads Table */}
        <Grid size={{ xs: 12, lg: 7 }}>
          <Card sx={{ bgcolor: '#1a2235' }}>
            <CardContent sx={{ p: 0 }}>
              <Box sx={{ px: 3, py: 2, borderBottom: '1px solid #2a3a52', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Typography variant="h6" sx={{ fontWeight: 600, fontSize: '0.9rem' }}>
                  Active Loads
                  {loads.length > 0 && (
                    <Chip
                      label={loads.length}
                      size="small"
                      sx={{ ml: 1.5, bgcolor: '#3b82f620', color: '#3b82f6', height: 18, fontSize: '0.65rem' }}
                    />
                  )}
                </Typography>
                <Button
                  size="small"
                  startIcon={<AddIcon fontSize="small" />}
                  onClick={() => navigate('/loads/new')}
                  sx={{ fontSize: '0.75rem', color: '#64748b', '&:hover': { color: '#94a3b8' } }}
                >
                  New
                </Button>
              </Box>

              {loadsLoading ? (
                <Box sx={{ p: 2 }}>
                  {[...Array(4)].map((_, i) => (
                    <Skeleton key={i} variant="rectangular" height={40} sx={{ mb: 1, borderRadius: 1, bgcolor: '#243049' }} />
                  ))}
                </Box>
              ) : loads.length === 0 ? (
                <EmptyState
                  icon={<InboxIcon sx={{ fontSize: 40 }} />}
                  title="No loads yet"
                  description="Create your first load to start monitoring agent activity."
                  action={
                    <Button variant="outlined" size="small" startIcon={<AddIcon />} onClick={() => navigate('/loads/new')}>
                      Create Load
                    </Button>
                  }
                />
              ) : (
                <TableContainer sx={{ overflowX: 'auto' }}>
                  <Table size="small" sx={{ minWidth: 560 }}>
                    <TableHead>
                      <TableRow>
                        <TableCell sx={{ color: '#64748b', fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Load ID</TableCell>
                        <TableCell sx={{ color: '#64748b', fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Customer</TableCell>
                        <TableCell sx={{ color: '#64748b', fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>State</TableCell>
                        <TableCell sx={{ color: '#64748b', fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>ETA</TableCell>
                        <TableCell sx={{ color: '#64748b', fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>Driver</TableCell>
                        <TableCell sx={{ color: '#64748b', fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}></TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {loads.map((load) => (
                        <TableRow
                          key={load.load_id}
                          hover
                          onClick={() => navigate(`/loads/${load.load_id}`)}
                          sx={{ cursor: 'pointer', '&:last-child td': { borderBottom: 0 } }}
                        >
                          <TableCell sx={{ py: 1 }}>
                            <TruncatedId id={load.load_id} chars={10} />
                          </TableCell>
                          <TableCell sx={{ py: 1 }}>
                            <Chip
                              label={load.customer_id.replace(/_/g, ' ')}
                              size="small"
                              variant="outlined"
                              sx={{ fontSize: '0.7rem', height: 20, textTransform: 'capitalize' }}
                            />
                          </TableCell>
                          <TableCell sx={{ py: 1 }}><StateChip state={load.current_state} /></TableCell>
                          <TableCell sx={{ fontSize: '0.8rem', color: '#94a3b8', py: 1 }}>
                            {load.current_eta_utc
                              ? new Date(load.current_eta_utc).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                              : <span style={{ color: '#475569' }}>—</span>}
                          </TableCell>
                          <TableCell sx={{ fontSize: '0.8rem', color: '#94a3b8', py: 1 }}>
                            {(load.load_data?.driver as { name?: string })?.name || <span style={{ color: '#475569' }}>—</span>}
                          </TableCell>
                          <TableCell sx={{ py: 1 }}>
                            <Button
                              size="small"
                              variant="outlined"
                              startIcon={<PlayArrowIcon sx={{ fontSize: '0.75rem !important' }} />}
                              onClick={(e) => {
                                e.stopPropagation();
                                localStorage.setItem(LOAD_STORAGE_KEY, load.load_id);
                                navigate('/simulation');
                              }}
                              sx={{ fontSize: '0.7rem', py: 0.25, px: 1, minWidth: 0 }}
                            >
                              Sim
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Right column */}
        <Grid size={{ xs: 12, lg: 5 }}>
          {/* Recent Agent Runs */}
          <Card sx={{ bgcolor: '#1a2235', mb: 3 }}>
            <CardContent sx={{ p: 0 }}>
              <Box sx={{ px: 3, py: 2, borderBottom: '1px solid #2a3a52' }}>
                <Typography variant="h6" sx={{ fontWeight: 600, fontSize: '0.9rem' }}>Recent Agent Runs</Typography>
              </Box>

              {runsLoading ? (
                <Box sx={{ px: 3, py: 1 }}>
                  {[...Array(4)].map((_, i) => (
                    <Skeleton key={i} variant="rectangular" height={52} sx={{ mb: 1, borderRadius: 1, bgcolor: '#243049' }} />
                  ))}
                </Box>
              ) : agentRuns.length === 0 ? (
                <EmptyState
                  icon={<SmartToyIcon sx={{ fontSize: 36 }} />}
                  title="No agent runs yet"
                  description="Fire events on a load to trigger the agent pipeline."
                />
              ) : (
                <Box sx={{ px: 2, py: 1, maxHeight: 320, overflowY: 'auto' }}>
                  {agentRuns.slice(0, 10).map((run) => (
                    <Box
                      key={run.run_id}
                      onClick={() => navigate(`/agent/${run.run_id}`)}
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        py: 1.25,
                        px: 1.5,
                        borderRadius: 1.5,
                        cursor: 'pointer',
                        '&:hover': { bgcolor: '#243049' },
                        borderBottom: '1px solid #2a3a5228',
                        '&:last-child': { borderBottom: 0 },
                      }}
                    >
                      <Box sx={{ flex: 1, minWidth: 0 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.25 }}>
                          <StatusChip status={run.status} />
                          <TruncatedId id={run.run_id} chars={8} color="#64748b" />
                        </Box>
                        <Typography variant="caption" sx={{ color: '#64748b' }} noWrap>
                          {run.workflow.replace(/_/g, ' ')}
                          {run.sop_branch && ` → ${run.sop_branch.replace(/_/g, ' ')}`}
                        </Typography>
                      </Box>
                      <Box sx={{ textAlign: 'right', flexShrink: 0, ml: 1 }}>
                        <Typography variant="caption" sx={{ color: '#475569', display: 'block' }}>
                          {run.tool_calls.length} tools
                        </Typography>
                      </Box>
                    </Box>
                  ))}
                </Box>
              )}
            </CardContent>
          </Card>

          {/* Load State Distribution */}
          {loads.length > 0 && (
            <Card sx={{ bgcolor: '#1a2235' }}>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 2, fontSize: '0.9rem' }}>
                  Load State Distribution
                </Typography>
                {Object.entries(stateDistribution).map(([state, count]) => (
                  <Box key={state} sx={{ mb: 1.5 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="caption" sx={{ color: '#94a3b8', textTransform: 'capitalize' }}>
                        {state.replace(/_/g, ' ')}
                      </Typography>
                      <Typography variant="caption" sx={{ color: '#64748b' }}>
                        {count} / {loads.length}
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={(count / loads.length) * 100}
                      sx={{
                        height: 5,
                        borderRadius: 3,
                        bgcolor: '#243049',
                        '& .MuiLinearProgress-bar': {
                          bgcolor: stateColors[state] || '#94a3b8',
                          borderRadius: 3,
                        },
                      }}
                    />
                  </Box>
                ))}
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
    </Box>
  );
}
