import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { StatusChip, StateChip, LoadSelector, TruncatedId } from '@/components/shared';
import { useAgentRuns } from '@/api/hooks';
import type { AgentRun } from '@/types';
import { statusColors, memoryTypeColors } from '@/theme';
import { authFetch } from '@/api/client';

export function AgentViewer() {
  const navigate = useNavigate();
  const [selectedLoadId, setSelectedLoadId] = React.useState<string | null>(
    localStorage.getItem('freighthero_selected_load') || null
  );
  const [runs, setRuns] = React.useState<AgentRun[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    const fetchRuns = async () => {
      try {
        const url = selectedLoadId ? `/api/v1/monitoring/agent-runs?load_id=${selectedLoadId}` : '/api/v1/monitoring/agent-runs';
        const res = await authFetch(url);
        const data = await res.json();
        const mapped = data.map((run: Record<string, unknown>) => ({
          ...run,
          tool_calls: Array.isArray(run.tool_calls) ? run.tool_calls : [],
          memory_operations: Array.isArray(run.memory_operations) ? run.memory_operations : [],
          tool_calls_count: (run.tool_calls_count as number) || (Array.isArray(run.tool_calls) ? (run.tool_calls as unknown[]).length : 0),
          memory_operations_count: (run.memory_operations_count as number) || (Array.isArray(run.memory_operations) ? (run.memory_operations as unknown[]).length : 0),
          customer_rules_applied: run.customer_rules_applied || [],
          error: run.error || null,
          state_before: run.state_before || null,
          state_after: run.state_after || null,
        }));
        setRuns(mapped);
      } catch (err) {
        console.error('Failed to fetch agent runs:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchRuns();
  }, [selectedLoadId]);

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>Agent Execution Viewer</Typography>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
        <Typography variant="body2" sx={{ color: '#64748b' }}>
          Inspect agent decisions, tool calls, and memory operations
        </Typography>
      </Box>

      <LoadSelector
        onLoadChange={(loadId) => setSelectedLoadId(loadId)}
        showViewDetails
        navigate={(path) => navigate(path)}
      />

      {loading && runs.length === 0 && <Typography variant="body2" sx={{ color: '#64748b', textAlign: 'center', py: 4 }}>Loading agent runs...</Typography>}
      {!loading && runs.length === 0 && <Typography variant="body2" sx={{ color: '#64748b', textAlign: 'center', py: 4 }}>No agent runs found. {selectedLoadId ? 'Try firing events in the Simulation page.' : 'Select a load to filter.'}</Typography>}

      <Grid container spacing={2}>
        {runs.map((run) => (
          <Grid size={{ xs: 12, sm: 6, lg: 4 }} key={run.run_id}>
            <Card
              sx={{ bgcolor: '#1a2235', cursor: 'pointer', '&:hover': { borderColor: '#3b82f6' } }}
              onClick={() => navigate(`/agent/${run.run_id}`)}
            >
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                    <StatusChip status={run.status} />
                    <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                      {run.workflow.replace(/_/g, ' ')}
                    </Typography>
                  </Box>
                  <Typography variant="caption" sx={{ color: '#64748b', fontFamily: 'monospace' }}>
                    {run.run_id.slice(0, 12)}
                  </Typography>
                </Box>

                <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1.5, mb: 2, minWidth: 0 }}>
                  <Box sx={{ minWidth: 0 }}>
                    <Typography variant="caption" sx={{ color: '#64748b' }}>Load</Typography>
                    <TruncatedId id={run.load_id} chars={10} />
                  </Box>
                  <Box sx={{ minWidth: 0 }}>
                    <Typography variant="caption" sx={{ color: '#64748b' }}>Customer</Typography>
                    <Typography variant="body2" noWrap>{run.customer_id}</Typography>
                  </Box>
                  <Box sx={{ minWidth: 0 }}>
                    <Typography variant="caption" sx={{ color: '#64748b' }}>Branch</Typography>
                    <Typography variant="body2" noWrap>{run.sop_branch?.replace(/_/g, ' ') || '—'}</Typography>
                  </Box>
                  <Box sx={{ minWidth: 0 }}>
                    <Typography variant="caption" sx={{ color: '#64748b' }}>State</Typography>
                    <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center', flexWrap: 'wrap' }}>
                      {run.state_before && <StateChip state={run.state_before} />}
                      {run.state_after && <Typography variant="caption" sx={{ color: '#64748b' }}>→</Typography>}
                      {run.state_after && <StateChip state={run.state_after} />}
                    </Box>
                  </Box>
                </Box>

                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Chip label={`${run.tool_calls_count ?? run.tool_calls.length} tools`} size="small" sx={{ bgcolor: '#22c55e20', color: '#22c55e' }} />
                  <Chip label={`${run.memory_operations_count ?? run.memory_operations.length} memory`} size="small" sx={{ bgcolor: '#06b6d420', color: '#06b6d4' }} />
                  {run.error && <Chip label="error" size="small" sx={{ bgcolor: '#ef444420', color: '#ef4444' }} />}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}

export function AgentRunDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [run, setRun] = React.useState<AgentRun | null>(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    if (!id) return;
    const fetchDetail = async () => {
      try {
        const res = await authFetch(`/api/v1/debugger/agent-runs/${id}`);
        if (!res.ok) {
          setRun(null);
          return;
        }
        const data = await res.json();
        setRun({
          ...data,
          tool_calls: Array.isArray(data.tool_calls) ? data.tool_calls : [],
          memory_operations: Array.isArray(data.memory_operations) ? data.memory_operations : [],
          tool_calls_count: data.tool_calls?.length || 0,
          memory_operations_count: data.memory_operations?.length || 0,
          customer_rules_applied: data.customer_rules_applied || [],
          error: data.error || null,
          state_before: data.state_before || null,
          state_after: data.state_after || null,
        } as AgentRun);
      } catch (err) {
        console.error('Failed to fetch agent run detail:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchDetail();
  }, [id]);

  if (loading) {
    return <Typography variant="body2" sx={{ color: '#64748b', textAlign: 'center', py: 4 }}>Loading agent run...</Typography>;
  }
  if (!run) {
    return (
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="h5" sx={{ color: '#64748b' }}>Agent run not found</Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <IconButton onClick={() => navigate('/agent')} sx={{ color: '#94a3b8' }}>
          <ArrowBackIcon />
        </IconButton>
        <Box sx={{ flex: 1 }}>
          <Typography variant="h4" sx={{ fontWeight: 700 }}>Agent Run</Typography>
          <Box sx={{ display: 'flex', gap: 1, mt: 0.5, alignItems: 'center', flexWrap: 'wrap' }}>
            <StatusChip status={run.status} />
            <Chip label={run.workflow.replace(/_/g, ' ')} size="small" sx={{ bgcolor: '#3b82f620', color: '#3b82f6' }} />
            <TruncatedId id={run.run_id} chars={16} color="#64748b" />
          </Box>
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Context */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Card sx={{ bgcolor: '#1a2235', mb: 3 }}>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>Context</Typography>
              {([
                ['Load', run.load_id, true],
                ['Customer', run.customer_id, false],
                ['Event', run.event_id, true],
                ['Branch', run.sop_branch?.replace(/_/g, ' ') || '—', false],
                ['State Before', run.state_before || '—', false],
                ['State After', run.state_after || '—', false],
                ['Started', new Date(run.started_at).toLocaleString(), false],
                ['Completed', run.completed_at ? new Date(run.completed_at).toLocaleString() : '—', false],
              ] as [string, string, boolean][]).map(([label, value, isId]) => (
                <Box key={label} sx={{ mb: 1.5 }}>
                  <Typography variant="caption" sx={{ color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                    {label}
                  </Typography>
                  {isId && value && value !== '—'
                    ? <TruncatedId id={value} chars={14} color="#e2e8f0" />
                    : <Typography variant="body2" sx={{ color: '#e2e8f0', wordBreak: 'break-word' }}>{value}</Typography>
                  }
                </Box>
              ))}
              {run.error && (
                <Box sx={{ mt: 2, p: 1.5, bgcolor: '#ef444415', borderRadius: 1, border: '1px solid #ef444430' }}>
                  <Typography variant="caption" sx={{ color: '#ef4444', fontWeight: 600 }}>Error</Typography>
                  <Typography variant="body2" sx={{ color: '#ef4444' }}>{run.error}</Typography>
                </Box>
              )}
            </CardContent>
          </Card>

          {/* Customer Rules Applied */}
          <Card sx={{ bgcolor: '#1a2235' }}>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>Customer Rules</Typography>
              {run.customer_rules_applied.map((rule) => (
                <Chip key={rule} label={rule.replace(/_/g, ' ')} size="small" sx={{ mr: 0.5, mb: 0.5 }} />
              ))}
            </CardContent>
          </Card>
        </Grid>

        {/* Tool Calls */}
        <Grid size={{ xs: 12, md: 8 }}>
          <Card sx={{ bgcolor: '#1a2235', mb: 3 }}>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Tool Calls ({run.tool_calls.length})
              </Typography>
              {run.tool_calls.length === 0 ? (
                <Typography variant="body2" sx={{ color: '#64748b' }}>No tool calls recorded</Typography>
              ) : (
                run.tool_calls.map((tc, i) => (
                  <Box key={i} sx={{ mb: 2, p: 2, bgcolor: '#0a0e17', borderRadius: 1.5, border: '1px solid #2a3a52' }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Chip label={tc.tool} size="small" sx={{ bgcolor: '#22c55e20', color: '#22c55e', fontFamily: 'monospace' }} />
                      <Typography variant="caption" sx={{ color: '#64748b' }}>Step {i + 1} {(tc.created_at || tc.timestamp) ? `· ${new Date(tc.created_at || tc.timestamp).toLocaleTimeString()}` : ''}</Typography>
                    </Box>
                    <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2, minWidth: 0 }}>
                      <Box sx={{ minWidth: 0, overflow: 'hidden' }}>
                        <Typography variant="caption" sx={{ color: '#64748b' }}>Input</Typography>
                        <Box component="pre" sx={{ fontSize: '0.75rem', color: '#94a3b8', bgcolor: '#111827', p: 1.5, borderRadius: 1, overflow: 'auto', maxHeight: 120, m: 0 }}>
                          {JSON.stringify(tc.arguments, null, 2)}
                        </Box>
                      </Box>
                      <Box sx={{ minWidth: 0, overflow: 'hidden' }}>
                        <Typography variant="caption" sx={{ color: '#64748b' }}>Output</Typography>
                        <Box component="pre" sx={{ fontSize: '0.75rem', color: '#94a3b8', bgcolor: '#111827', p: 1.5, borderRadius: 1, overflow: 'auto', maxHeight: 120, m: 0 }}>
                          {JSON.stringify(tc.result, null, 2)}
                        </Box>
                      </Box>
                    </Box>
                  </Box>
                ))
              )}
            </CardContent>
          </Card>

          {/* Memory Operations */}
          <Card sx={{ bgcolor: '#1a2235' }}>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
                Memory Operations ({run.memory_operations.length})
              </Typography>
              {run.memory_operations.length === 0 ? (
                <Typography variant="body2" sx={{ color: '#64748b' }}>No memory operations recorded</Typography>
              ) : (
                run.memory_operations.map((mem, i) => (
                  <Box key={i} sx={{ mb: 1.5, p: 2, bgcolor: '#0a0e17', borderRadius: 1.5, border: '1px solid #2a3a52' }}>
                    <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                      <Chip label={mem.operation} size="small" sx={{ bgcolor: '#06b6d420', color: '#06b6d4' }} />
                      <Chip label={mem.memory_type} size="small" sx={{ bgcolor: `${memoryTypeColors[mem.memory_type]}20`, color: memoryTypeColors[mem.memory_type] }} />
                      <Chip label={`${mem.scope}:${String(mem.scope_id).slice(0, 10)}`} size="small" variant="outlined" sx={{ fontFamily: 'monospace', fontSize: '0.7rem' }} />
                    </Box>
                    <Typography variant="body2" sx={{ color: '#e2e8f0' }}>{mem.content}</Typography>
                    {mem.tags && mem.tags.length > 0 && (
                      <Box sx={{ display: 'flex', gap: 0.5, mt: 1 }}>
                        {mem.tags.map((tag) => (
                          <Chip key={tag} label={tag} size="small" variant="outlined" sx={{ fontSize: '0.625rem', height: 18 }} />
                        ))}
                      </Box>
                    )}
                  </Box>
                ))
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}