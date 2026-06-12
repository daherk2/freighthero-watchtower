import React from 'react';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import Slider from '@mui/material/Slider';
import Button from '@mui/material/Button';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import PauseIcon from '@mui/icons-material/Pause';
import FastRewindIcon from '@mui/icons-material/FastRewind';
import FastForwardIcon from '@mui/icons-material/FastForward';
import { useSearchParams } from 'react-router-dom';
import { SectionHeader, StatusChip, LoadSelector } from '@/components/shared';
// Direct fetch - React Query hooks had loading issues
import type { AgentRun } from '@/types';
import { stateColors, memoryTypeColors } from '@/theme';

interface Step {
  label: string;
  type: 'event' | 'state' | 'memory' | 'tool' | 'decision' | 'output';
  detail: string;
  data?: Record<string, unknown>;
}

function buildSteps(run: AgentRun): Step[] {
  const steps: Step[] = [];

  // 1. Event received
  steps.push({
    label: 'Event Received',
    type: 'event',
    detail: run.workflow.replace(/_/g, ' '),
  });

  // 2. State before
  if (run.state_before) {
    steps.push({
      label: 'Initial State',
      type: 'state',
      detail: run.state_before.replace(/_/g, ' '),
    });
  }

  // 3. Memory retrieval
  run.memory_operations.filter((m) => m.operation === 'retrieve').forEach((mem) => {
    steps.push({
      label: `Memory Retrieved (${mem.memory_type})`,
      type: 'memory',
      detail: mem.content,
      data: { tags: mem.tags },
    });
  });

  // 4. Tool calls
  run.tool_calls.forEach((tc) => {
    steps.push({
      label: `Tool: ${tc.tool}`,
      type: 'tool',
      detail: JSON.stringify(tc.arguments).slice(0, 80),
      data: { result: tc.result },
    });
  });

  // 5. Memory store
  run.memory_operations.filter((m) => m.operation === 'store').forEach((mem) => {
    steps.push({
      label: `Memory Stored (${mem.memory_type})`,
      type: 'memory',
      detail: mem.content,
    });
  });

  // 6. Decision
  steps.push({
    label: 'Decision Made',
    type: 'decision',
    detail: run.sop_branch?.replace(/_/g, ' ') || 'Default branch',
  });

  // 7. State after
  if (run.state_after) {
    steps.push({
      label: 'Final State',
      type: 'state',
      detail: run.state_after.replace(/_/g, ' '),
    });
  }

  // 8. Output
  steps.push({
    label: 'Execution Complete',
    type: 'output',
    detail: run.status,
  });

  return steps;
}

const stepTypeColors: Record<string, string> = {
  event: '#f59e0b',
  state: '#3b82f6',
  memory: '#06b6d4',
  tool: '#22c55e',
  decision: '#f97316',
  output: '#10b981',
};

export function AgentDebugger() {
  const [searchParams] = useSearchParams();
  const [selectedLoadId, setSelectedLoadId] = React.useState<string | null>(
    searchParams.get('load_id') || localStorage.getItem('freighthero_selected_load') || null
  );
  const [selectedRun, setSelectedRun] = React.useState(0);
  const [currentStep, setCurrentStep] = React.useState(0);
  const [isPlaying, setIsPlaying] = React.useState(false);
  const [runs, setRuns] = React.useState<AgentRun[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    const fetchRuns = async () => {
      try {
        const url = selectedLoadId ? `/api/v1/monitoring/agent-runs?load_id=${selectedLoadId}` : '/api/v1/monitoring/agent-runs';
        const res = await fetch(url);
        const data = await res.json();
        // Fetch detailed agent runs to get tool_calls and memory_operations
        const detailedRuns = await Promise.all(
          data.map(async (run: Record<string, unknown>) => {
            try {
              const detailRes = await fetch(`/api/v1/debugger/agent-runs/${run.run_id}`);
              const detail = await detailRes.json();
              return {
                ...run,
                tool_calls: detail.tool_calls || [],
                memory_operations: detail.memory_operations || [],
                customer_rules_applied: detail.customer_rules_applied || [],
                error: detail.error || null,
                state_before: detail.state_before || run.state_before || null,
                state_after: detail.state_after || run.state_after || null,
                sop_branch: detail.sop_branch || run.sop_branch || null,
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
                sop_branch: run.sop_branch || null,
              };
            }
          })
        );
        setRuns(detailedRuns);
      } catch (err) {
        console.error('Failed to fetch agent runs:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchRuns();
  }, [selectedLoadId]);

  const run = runs[selectedRun];
  const steps = run ? buildSteps(run) : [];

  const handlePlay = () => {
    if (isPlaying) {
      setIsPlaying(false);
      return;
    }
    setIsPlaying(true);
    const interval = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev >= steps.length - 1) {
          setIsPlaying(false);
          clearInterval(interval);
          return prev;
        }
        return prev + 1;
      });
    }, 1500);
  };

  const visibleSteps = steps.slice(0, currentStep + 1);
  const currentStepData = steps[currentStep];

  return (
    <Box>
      <SectionHeader title="Agent Debugger" subtitle="Step-by-step replay with state, memory, decision, and tool inspection" />

      <LoadSelector
        onLoadChange={(loadId) => { setSelectedLoadId(loadId); setSelectedRun(0); setCurrentStep(0); setIsPlaying(false); }}
        showViewDetails
        navigate={(path) => window.location.href = path}
      />

      <Grid container spacing={3}>
        {/* Run Selector */}
        <Grid size={{ xs: 12, md: 3 }}>
          <Card sx={{ bgcolor: '#1a2235' }}>
            <CardContent>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>Select Run</Typography>
              {runs.map((r, i) => (
                <Box
                  key={r.run_id}
                  onClick={() => { setSelectedRun(i); setCurrentStep(0); setIsPlaying(false); }}
                  sx={{
                    p: 1.5, mb: 0.5, borderRadius: 1, cursor: 'pointer',
                    bgcolor: selectedRun === i ? '#3b82f615' : 'transparent',
                    border: selectedRun === i ? '1px solid #3b82f6' : '1px solid transparent',
                    '&:hover': { bgcolor: '#0a0e17' },
                  }}
                >
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <StatusChip status={r.status} />
                    <Typography variant="caption" sx={{ color: '#64748b', fontFamily: 'monospace' }}>
                      {r.run_id.slice(0, 8)}
                    </Typography>
                  </Box>
                  <Typography variant="caption" sx={{ color: '#94a3b8', mt: 0.5, display: 'block' }}>
                    {r.workflow.replace(/_/g, ' ')}
                  </Typography>
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>

        {/* Replay Controls & Timeline */}
        <Grid size={{ xs: 12, md: 9 }}>
          {/* Controls */}
          <Card sx={{ bgcolor: '#1a2235', mb: 2 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <IconButton onClick={() => setCurrentStep(0)} sx={{ color: '#94a3b8' }}>
                  <FastRewindIcon />
                </IconButton>
                <IconButton onClick={handlePlay} sx={{ color: '#e2e8f0', bgcolor: '#3b82f6', '&:hover': { bgcolor: '#2563eb' } }}>
                  {isPlaying ? <PauseIcon /> : <PlayArrowIcon />}
                </IconButton>
                <IconButton onClick={() => setCurrentStep(Math.min(steps.length - 1, currentStep + 1))} sx={{ color: '#94a3b8' }}>
                  <FastForwardIcon />
                </IconButton>
                <Box sx={{ flex: 1 }}>
                  <Slider
                    value={currentStep}
                    onChange={(_, v) => setCurrentStep(v as number)}
                    min={0}
                    max={steps.length - 1}
                    step={1}
                    marks={steps.map((_, i) => ({ value: i }))}
                    sx={{
                      color: '#3b82f6',
                      '& .MuiSlider-mark': { bgcolor: '#2a3a52', width: 2, height: 8 },
                      '& .MuiSlider-thumb': { width: 14, height: 14 },
                    }}
                  />
                </Box>
                <Typography variant="caption" sx={{ color: '#64748b', fontFamily: 'monospace' }}>
                  Step {currentStep + 1}/{steps.length}
                </Typography>
              </Box>

              {/* Current Step Detail */}
              {currentStepData && (
                <Box sx={{ p: 2, bgcolor: '#0a0e17', borderRadius: 1.5, borderLeft: `3px solid ${stepTypeColors[currentStepData.type]}` }}>
                  <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mb: 1 }}>
                    <Chip
                      label={currentStepData.type}
                      size="small"
                      sx={{ bgcolor: `${stepTypeColors[currentStepData.type]}20`, color: stepTypeColors[currentStepData.type] }}
                    />
                    <Typography variant="subtitle2" sx={{ fontWeight: 600, color: '#e2e8f0' }}>
                      {currentStepData.label}
                    </Typography>
                  </Box>
                  <Typography variant="body2" sx={{ color: '#94a3b8' }}>{currentStepData.detail}</Typography>
                  {currentStepData.data && (
                    <Box component="pre" sx={{ fontSize: '0.75rem', color: '#64748b', bgcolor: '#111827', p: 1, borderRadius: 1, mt: 1, overflow: 'auto', m: 0 }}>
                      {JSON.stringify(currentStepData.data, null, 2)}
                    </Box>
                  )}
                </Box>
              )}
            </CardContent>
          </Card>

          {/* Step Timeline */}
          <Card sx={{ bgcolor: '#1a2235' }}>
            <CardContent>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>Execution Timeline</Typography>
              {visibleSteps.map((step, i) => (
                <Box key={i} sx={{ display: 'flex', gap: 2, mb: 1.5 }}>
                  {/* Timeline line */}
                  <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 24 }}>
                    <Box sx={{
                      width: 12, height: 12, borderRadius: '50%',
                      bgcolor: stepTypeColors[step.type], mt: 0.5,
                      border: i === currentStep ? '2px solid #fff' : '2px solid transparent',
                    }} />
                    {i < visibleSteps.length - 1 && (
                      <Box sx={{ width: 2, flex: 1, bgcolor: '#2a3a52', mt: 0.5 }} />
                    )}
                  </Box>
                  {/* Step content */}
                  <Box sx={{ flex: 1, pb: 1 }}>
                    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                      <Typography variant="body2" sx={{ fontWeight: 600, color: '#e2e8f0' }}>
                        {step.label}
                      </Typography>
                      <Chip label={step.type} size="small" sx={{ fontSize: '0.625rem', height: 16, bgcolor: `${stepTypeColors[step.type]}20`, color: stepTypeColors[step.type] }} />
                    </Box>
                    <Typography variant="caption" sx={{ color: '#94a3b8' }}>{step.detail}</Typography>
                  </Box>
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}