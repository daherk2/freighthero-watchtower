import React from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import IconButton from '@mui/material/IconButton';
import Collapse from '@mui/material/Collapse';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import { SectionHeader, LoadSelector } from '@/components/shared';
// Direct fetch - React Query hooks had loading issues
import type { TraceNode } from '@/types';

const nodeTypeColors: Record<string, string> = {
  event: '#f59e0b',
  workflow: '#3b82f6',
  agent: '#8b5cf6',
  llm: '#ec4899',
  tool: '#22c55e',
  memory: '#06b6d4',
  decision: '#f97316',
  output: '#10b981',
};

const nodeTypeIcons: Record<string, string> = {
  event: '⚡',
  workflow: '🔄',
  agent: '🤖',
  llm: '🧠',
  tool: '🔧',
  memory: '💾',
  decision: '⚖️',
  output: '📤',
};

function TraceNodeCard({ node, depth = 0 }: { node: TraceNode; depth?: number }) {
  const [expanded, setExpanded] = React.useState(depth < 2);
  const color = nodeTypeColors[node.type] || '#64748b';
  const icon = nodeTypeIcons[node.type] || '📦';
  const hasChildren = node.children && node.children.length > 0;

  return (
    <Box sx={{ ml: depth * 2 }}>
      <Card
        sx={{
          bgcolor: '#1a2235', mb: 0.75,
          borderLeft: `3px solid ${color}`,
          '&:hover': { borderColor: color },
        }}
      >
        <CardContent sx={{ py: 1, '&:last-child': { pb: 1 } }}>
          <Box
            sx={{ display: 'flex', alignItems: 'center', gap: 1, cursor: hasChildren ? 'pointer' : 'default' }}
            onClick={() => hasChildren && setExpanded(!expanded)}
          >
            {hasChildren && (
              <IconButton size="small" sx={{ color: '#64748b', p: 0.25 }}>
                {expanded ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
              </IconButton>
            )}
            <Typography variant="body1" sx={{ mr: 0.5 }}>{icon}</Typography>
            <Chip
              label={node.type}
              size="small"
              sx={{ bgcolor: `${color}20`, color, fontSize: '0.625rem', height: 20 }}
            />
            <Typography variant="body2" sx={{ fontWeight: 600, color: '#e2e8f0', flex: 1 }}>
              {node.name}
            </Typography>
            {node.duration_ms && (
              <Typography variant="caption" sx={{ color: '#64748b', fontFamily: 'monospace' }}>
                {node.duration_ms}ms
              </Typography>
            )}
            {node.status && (
              <Chip
                label={node.status}
                size="small"
                sx={{
                  fontSize: '0.625rem', height: 18,
                  bgcolor: node.status === 'completed' ? '#22c55e20' : node.status === 'error' ? '#ef444420' : '#f59e0b20',
                  color: node.status === 'completed' ? '#22c55e' : node.status === 'error' ? '#ef4444' : '#f59e0b',
                }}
              />
            )}
          </Box>

          {/* Input/Output preview */}
          <Box sx={{ ml: hasChildren ? 4.5 : 2.5, mt: 0.5 }}>
            {node.input ? (
              <Box sx={{ mb: 0.5 }}>
                <Typography variant="caption" sx={{ color: '#64748b' }}>Input</Typography>
                <Box
                  component="pre"
                  sx={{
                    fontSize: '0.7rem', color: '#94a3b8', bgcolor: '#0a0e17', p: 1,
                    borderRadius: 0.5, overflow: 'auto', maxHeight: 80, m: 0,
                  }}
                >
                  {typeof node.input === 'string' ? node.input : JSON.stringify(node.input, null, 2)}
                </Box>
              </Box>
            ) : null}
            {node.output ? (
              <Box>
                <Typography variant="caption" sx={{ color: '#64748b' }}>Output</Typography>
                <Box
                  component="pre"
                  sx={{
                    fontSize: '0.7rem', color: '#94a3b8', bgcolor: '#0a0e17', p: 1,
                    borderRadius: 0.5, overflow: 'auto', maxHeight: 80, m: 0,
                  }}
                >
                  {typeof node.output === 'string' ? node.output : JSON.stringify(node.output, null, 2)}
                </Box>
              </Box>
            ) : null}
          </Box>
        </CardContent>
      </Card>

      <Collapse in={expanded} timeout="auto" unmountOnExit={false}>
        {hasChildren && node.children!.map((child, i) => (
          <TraceNodeCard key={`${child.id}-${i}`} node={child} depth={depth + 1} />
        ))}
      </Collapse>
    </Box>
  );
}

export function TraceExplorer() {
  const [selectedLoadId, setSelectedLoadId] = React.useState<string | null>(null);
  const [treeArray, setTreeArray] = React.useState<TraceNode[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    const fetchTrace = async () => {
      setLoading(true);
      try {
        // Fetch agent runs and build trace tree from real data
        const url = selectedLoadId ? `/api/v1/monitoring/agent-runs?load_id=${selectedLoadId}` : '/api/v1/monitoring/agent-runs';
        const res = await fetch(url);
        const runs = await res.json();

        if (runs.length === 0) {
          setTreeArray([]);
          return;
        }

        // Fetch details for runs that have tool_calls or memory_operations
        const detailedRuns = await Promise.all(
          runs.map(async (run: Record<string, unknown>) => {
            const hasDetails = (run.tool_calls_count as number) > 0 || (run.memory_operations_count as number) > 0;
            if (!hasDetails) return run;
            try {
              const detailRes = await fetch(`/api/v1/debugger/agent-runs/${run.run_id}`);
              const detail = await detailRes.json();
              return { ...run, tool_calls: detail.tool_calls || [], memory_operations: detail.memory_operations || [] };
            } catch {
              return run;
            }
          })
        );

        // Build trace tree from agent runs
        const trees: TraceNode[] = detailedRuns.map((run: Record<string, unknown>, idx: number) => {
          const children: TraceNode[] = [];

          // Add tool calls as children
          const toolCalls = (run.tool_calls || []) as Record<string, unknown>[];
          toolCalls.forEach((tc: Record<string, unknown>, i: number) => {
            children.push({
              id: `tool-${idx}-${i}`,
              name: String(tc.tool || 'unknown'),
              type: 'tool' as const,
              data: tc,
              timestamp: String(run.started_at || ''),
              duration_ms: undefined,
              children: [],
              input: tc.arguments,
              output: tc.result,
              status: 'completed' as const,
            });
          });

          // Add memory operations as children
          const memOps = (run.memory_operations || []) as Record<string, unknown>[];
          memOps.forEach((mem: Record<string, unknown>, i: number) => {
            children.push({
              id: `memory-${idx}-${i}`,
              name: String(mem.memory_type || 'memory'),
              type: 'memory' as const,
              data: mem,
              timestamp: String(run.started_at || ''),
              duration_ms: undefined,
              children: [],
              input: mem.operation === 'retrieve' ? 'retrieve' : undefined,
              output: mem.content ? String(mem.content) : undefined,
              status: 'completed' as const,
            });
          });

          return {
            id: String(run.run_id || `run-${idx}`),
            name: String(run.workflow || 'unknown').replace(/_/g, ' '),
            type: 'workflow' as const,
            data: run,
            timestamp: String(run.started_at || ''),
            duration_ms: undefined,
            children,
            status: String(run.status || 'unknown') as TraceNode['status'],
          };
        });

        setTreeArray(trees);
      } catch (err) {
        console.error('Failed to fetch trace data:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchTrace();
  }, [selectedLoadId]);

  return (
    <Box>
      <SectionHeader title="Trace Explorer" subtitle="LangSmith-style full execution tree viewer" />

      <LoadSelector
        onLoadChange={(loadId) => setSelectedLoadId(loadId)}
        showViewDetails
        navigate={(path) => window.location.href = path}
      />

      {/* Legend */}
      <Box sx={{ display: 'flex', gap: 1.5, mb: 2, flexWrap: 'wrap' }}>
        {Object.entries(nodeTypeColors).map(([type, color]) => (
          <Box key={type} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: color }} />
            <Typography variant="caption" sx={{ color: '#94a3b8', textTransform: 'capitalize' }}>{type}</Typography>
          </Box>
        ))}
      </Box>

      {loading && (
        <Typography variant="body2" sx={{ color: '#64748b', textAlign: 'center', py: 4 }}>
          Loading traces...
        </Typography>
      )}
      {!loading && treeArray.length === 0 && (
        <Typography variant="body2" sx={{ color: '#64748b', textAlign: 'center', py: 4 }}>
          No traces found. {selectedLoadId ? 'Try firing events in the Simulation page.' : 'Select a load to filter.'}
        </Typography>
      )}
      {treeArray.map((rootNode) => (
        <TraceNodeCard key={rootNode.id} node={rootNode} depth={0} />
      ))}
    </Box>
  );
}