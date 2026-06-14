import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import TextField from '@mui/material/TextField';
import InputAdornment from '@mui/material/InputAdornment';
import Grid from '@mui/material/Grid';
import SearchIcon from '@mui/icons-material/Search';
import { SectionHeader, LoadSelector } from '@/components/shared';
import type { AgentRun } from '@/types';
import { authFetch } from '@/api/client';

export function ToolCallExplorer() {
  const [selectedLoadId, setSelectedLoadId] = React.useState<string | null>(null);
  const [search, setSearch] = React.useState('');
  const [selectedTool, setSelectedTool] = React.useState<string | null>(null);
  const [runs, setRuns] = React.useState<AgentRun[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    const fetchRuns = async () => {
      setLoading(true);
      try {
        // Handle both null and empty string as "no filter"
        const hasLoadFilter = selectedLoadId && selectedLoadId.trim() !== '';
        const url = hasLoadFilter ? `/api/v1/monitoring/agent-runs?load_id=${selectedLoadId}` : '/api/v1/monitoring/agent-runs';
        const res = await authFetch(url);
        const data = await res.json();
        // Fetch detailed agent runs to get tool_calls
        const detailedRuns = await Promise.all(
          data.map(async (run: AgentRun) => {
            if ((run.tool_calls_count as number) > 0) {
              try {
                const detailRes = await authFetch(`/api/v1/debugger/agent-runs/${run.run_id}`);
                const detail = await detailRes.json();
                return {
                  ...run,
                  tool_calls: detail.tool_calls || [],
                  memory_operations: detail.memory_operations || [],
                  customer_rules_applied: detail.customer_rules_applied || [],
                  error: detail.error || null,
                  state_before: detail.state_before || run.state_before || null,
                  state_after: detail.state_after || run.state_after || null,
                };
              } catch {
                return {
                  ...run,
                  tool_calls: [],
                  memory_operations: [],
                  customer_rules_applied: [],
                  error: null,
                  state_before: run.state_before || null,
                  state_after: run.state_after || null,
                };
              }
            }
            return {
              ...run,
              tool_calls: [],
              memory_operations: [],
              customer_rules_applied: [],
              error: null,
              state_before: run.state_before || null,
              state_after: run.state_after || null,
            };
          })
        );
        setRuns(detailedRuns);
      } catch {
        // silently fall through — runs state stays empty
      } finally {
        setLoading(false);
      }
    };
    fetchRuns();
  }, [selectedLoadId]);

  // Flatten all tool calls from all agent runs
  const allToolCalls = runs.flatMap((run) =>
    run.tool_calls.map((tc) => ({
      ...tc,
      run_id: run.run_id,
      load_id: run.load_id,
      workflow: run.workflow,
      status: run.status,
    }))
  );

  const toolNames = [...new Set(allToolCalls.map((tc) => tc.tool))];
  const filtered = allToolCalls.filter((tc) => {
    const matchesSearch = !search || tc.tool.toLowerCase().includes(search.toLowerCase());
    const matchesTool = !selectedTool || tc.tool === selectedTool;
    return matchesSearch && matchesTool;
  });

  return (
    <Box>
      <SectionHeader title="Tool Call Explorer" subtitle="Inspect tool names, inputs, outputs, latency, and correlation IDs" />

      <LoadSelector
        onLoadChange={(loadId) => setSelectedLoadId(loadId)}
        showViewDetails
        navigate={(path) => window.location.href = path}
      />

      <Grid container spacing={3}>
        {/* Tool Filter Sidebar */}
        <Grid size={{ xs: 12, sm: 6, md: 4, lg: 3 }}>
          <Card sx={{ bgcolor: '#1a2235' }}>
            <CardContent>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>Tools</Typography>
              {toolNames.map((name) => {
                const count = allToolCalls.filter((tc) => tc.tool === name).length;
                return (
                  <Box
                    key={name}
                    onClick={() => setSelectedTool(selectedTool === name ? null : name)}
                    sx={{
                      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                      p: 1.5, mb: 0.5, borderRadius: 1, cursor: 'pointer',
                      bgcolor: selectedTool === name ? '#22c55e15' : 'transparent',
                      border: selectedTool === name ? '1px solid #22c55e' : '1px solid transparent',
                      '&:hover': { bgcolor: '#0a0e17' },
                    }}
                  >
                    <Typography variant="body2" sx={{ color: selectedTool === name ? '#22c55e' : '#e2e8f0', fontFamily: 'monospace' }}>
                      {name}
                    </Typography>
                    <Chip label={count} size="small" sx={{ height: 20, fontSize: '0.625rem' }} />
                  </Box>
                );
              })}
            </CardContent>
          </Card>
        </Grid>

        {/* Tool Call List */}
        <Grid size={{ xs: 12, sm: 6, md: 8, lg: 9 }}>
          <Box sx={{ mb: 2 }}>
            <TextField
              fullWidth
              size="small"
              placeholder="Search tool calls..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start"><SearchIcon sx={{ color: '#64748b' }} /></InputAdornment>
                  ),
                },
              }}
              sx={{
                '& .MuiOutlinedInput-root': { bgcolor: '#1a2235', color: '#e2e8f0' },
                '& .MuiOutlinedInput-notchedOutline': { borderColor: '#2a3a52' },
              }}
            />
          </Box>

          {filtered.map((tc, i) => (
            <Card key={`${tc.run_id}-${i}`} sx={{ bgcolor: '#1a2235', mb: 1.5, '&:hover': { borderColor: '#22c55e' } }}>
              <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1.5 }}>
                  <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                    <Chip
                      label={tc.tool}
                      size="small"
                      sx={{ bgcolor: '#22c55e20', color: '#22c55e', fontFamily: 'monospace' }}
                    />
                    <Chip label={tc.workflow.replace(/_/g, ' ')} size="small" variant="outlined" />
                    <Chip
                      label={tc.status}
                      size="small"
                      sx={{
                        bgcolor: tc.status === 'completed' ? '#22c55e20' : '#f59e0b20',
                        color: tc.status === 'completed' ? '#22c55e' : '#f59e0b',
                      }}
                    />
                  </Box>
                  <Typography variant="caption" sx={{ color: '#64748b', fontFamily: 'monospace' }}>
                    {tc.run_id.slice(0, 12)}
                  </Typography>
                </Box>

                <Grid container spacing={2}>
                  <Grid size={{ xs: 12, md: 6 }}>
                    <Typography variant="caption" sx={{ color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                      Input
                    </Typography>
                    <Box
                      component="pre"
                      sx={{
                        fontSize: '0.75rem', color: '#94a3b8', bgcolor: '#0a0e17', p: 1.5,
                        borderRadius: 1, overflow: 'auto', maxHeight: 160, m: 0, mt: 0.5,
                      }}
                    >
                      {JSON.stringify(tc.arguments, null, 2)}
                    </Box>
                  </Grid>
                  <Grid size={{ xs: 12, md: 6 }}>
                    <Typography variant="caption" sx={{ color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                      Output
                    </Typography>
                    <Box
                      component="pre"
                      sx={{
                        fontSize: '0.75rem', color: '#94a3b8', bgcolor: '#0a0e17', p: 1.5,
                        borderRadius: 1, overflow: 'auto', maxHeight: 160, m: 0, mt: 0.5,
                      }}
                    >
                      {JSON.stringify(tc.result, null, 2)}
                    </Box>
                  </Grid>
                </Grid>

                <Box sx={{ display: 'flex', gap: 2, mt: 1 }}>
                  <Typography variant="caption" sx={{ color: '#475569' }}>
                    Load: {tc.load_id}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          ))}

          {filtered.length === 0 && allToolCalls.length === 0 && runs.length > 0 && (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography variant="body2" sx={{ color: '#64748b', mb: 1 }}>
                No tool calls recorded yet
              </Typography>
              <Typography variant="caption" sx={{ color: '#475569' }}>
                {runs.length} agent runs found, but none have tool calls. Tool calls appear when the agent uses tools during execution.
              </Typography>
              <Box sx={{ mt: 2 }}>
                {runs.slice(0, 5).map((run) => (
                  <Box key={run.run_id} sx={{ display: 'inline-flex', gap: 0.5, alignItems: 'center', mr: 1, mb: 0.5 }}>
                    <Chip
                      label={run.workflow.replace(/_/g, ' ')}
                      size="small"
                      variant="outlined"
                      sx={{ fontSize: '0.7rem' }}
                    />
                    <Typography variant="caption" sx={{ color: '#64748b', fontFamily: 'monospace' }}>
                      {run.run_id.slice(0, 8)}
                    </Typography>
                  </Box>
                ))}
              </Box>
            </Box>
          )}
          {filtered.length === 0 && allToolCalls.length === 0 && runs.length === 0 && (
            <Typography variant="body2" sx={{ color: '#64748b', textAlign: 'center', py: 4 }}>
              No agent runs found. Create a load and fire events to generate tool calls.
            </Typography>
          )}
          {filtered.length === 0 && allToolCalls.length > 0 && (
            <Typography variant="body2" sx={{ color: '#64748b', textAlign: 'center', py: 4 }}>
              No tool calls match your search
            </Typography>
          )}
        </Grid>
      </Grid>
    </Box>
  );
}