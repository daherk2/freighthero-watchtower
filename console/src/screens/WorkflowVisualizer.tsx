import React, { useCallback } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  type Node,
  type Edge,
  type NodeTypes,
  Handle,
  Position,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useSearchParams } from 'react-router-dom';
// Direct fetch - React Query hooks had loading issues
import type { AgentRun } from '@/types';
import { stateColors, statusColors } from '@/theme';
import { authFetch, LOAD_STORAGE_KEY } from '@/api/client';

// Custom node components
function EventNode({ data }: { data: Record<string, unknown> }) {
  return (
    <Box sx={{
      px: 2, py: 1, borderRadius: 2, bgcolor: '#f59e0b20', border: '2px solid #f59e0b',
      minWidth: 140, textAlign: 'center',
    }}>
      <Handle type="source" position={Position.Bottom} />
      <Typography variant="caption" sx={{ color: '#f59e0b', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        Event
      </Typography>
      <Typography variant="body2" sx={{ color: '#e2e8f0', fontWeight: 600 }}>
        {data.label as string}
      </Typography>
    </Box>
  );
}

function WorkflowNode({ data }: { data: Record<string, unknown> }) {
  return (
    <Box sx={{
      px: 2, py: 1.5, borderRadius: 2, bgcolor: '#3b82f620', border: '2px solid #3b82f6',
      minWidth: 160, textAlign: 'center',
    }}>
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
      <Typography variant="caption" sx={{ color: '#3b82f6', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        Workflow
      </Typography>
      <Typography variant="body2" sx={{ color: '#e2e8f0', fontWeight: 600 }}>
        {data.label as string}
      </Typography>
      {data.branch ? (
        <Chip label={data.branch as string} size="small" sx={{ mt: 0.5, fontSize: '0.625rem', height: 18 }} />
      ) : null}
    </Box>
  );
}

function AgentNode({ data }: { data: Record<string, unknown> }) {
  const status = data.status as string;
  const color = statusColors[status] || '#64748b';
  return (
    <Box sx={{
      px: 2, py: 1.5, borderRadius: 2, bgcolor: `${color}20`, border: `2px solid ${color}`,
      minWidth: 160, textAlign: 'center',
    }}>
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
      <Typography variant="caption" sx={{ color, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        Agent
      </Typography>
      <Typography variant="body2" sx={{ color: '#e2e8f0', fontWeight: 600 }}>
        {data.label as string}
      </Typography>
      <Chip label={status} size="small" sx={{ mt: 0.5, bgcolor: `${color}30`, color, fontSize: '0.625rem', height: 18 }} />
    </Box>
  );
}

function MemoryNode({ data }: { data: Record<string, unknown> }) {
  return (
    <Box sx={{
      px: 2, py: 1, borderRadius: 2, bgcolor: '#06b6d420', border: '2px solid #06b6d4',
      minWidth: 140, textAlign: 'center',
    }}>
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
      <Typography variant="caption" sx={{ color: '#06b6d4', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        Memory
      </Typography>
      <Typography variant="body2" sx={{ color: '#e2e8f0', fontWeight: 600 }}>
        {data.label as string}
      </Typography>
    </Box>
  );
}

function ToolNode({ data }: { data: Record<string, unknown> }) {
  return (
    <Box sx={{
      px: 2, py: 1, borderRadius: 2, bgcolor: '#22c55e20', border: '2px solid #22c55e',
      minWidth: 140, textAlign: 'center',
    }}>
      <Handle type="target" position={Position.Top} />
      <Handle type="source" position={Position.Bottom} />
      <Typography variant="caption" sx={{ color: '#22c55e', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        Tool
      </Typography>
      <Typography variant="body2" sx={{ color: '#e2e8f0', fontWeight: 600, fontFamily: 'monospace' }}>
        {data.label as string}
      </Typography>
    </Box>
  );
}

function OutcomeNode({ data }: { data: Record<string, unknown> }) {
  const state = data.state as string;
  const color = stateColors[state] || '#64748b';
  return (
    <Box sx={{
      px: 2, py: 1.5, borderRadius: 2, bgcolor: `${color}20`, border: `2px solid ${color}`,
      minWidth: 140, textAlign: 'center',
    }}>
      <Handle type="target" position={Position.Top} />
      <Typography variant="caption" sx={{ color, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        Outcome
      </Typography>
      <Typography variant="body2" sx={{ color: '#e2e8f0', fontWeight: 600 }}>
        {data.label as string}
      </Typography>
    </Box>
  );
}

const nodeTypes: NodeTypes = {
  event: EventNode,
  workflow: WorkflowNode,
  agent: AgentNode,
  memory: MemoryNode,
  tool: ToolNode,
  outcome: OutcomeNode,
};

// Build flow from data
function buildFlowData(agentRuns: AgentRun[] | undefined) {
  const run = agentRuns?.[0]; // Use first run as example
  if (!run) {
    return { nodes: [], edges: [] };
  }
  const nodes: Node[] = [];
  const edges: Edge[] = [];
  let y = 0;
  const xCenter = 300;
  const yStep = 120;

  // Event node
  nodes.push({
    id: 'event-1',
    type: 'event',
    position: { x: xCenter, y },
    data: { label: run.workflow.replace(/_/g, ' ') },
  });
  y += yStep;

  // Workflow node
  nodes.push({
    id: 'workflow-1',
    type: 'workflow',
    position: { x: xCenter, y },
    data: { label: run.workflow.replace(/_/g, ' '), branch: run.sop_branch?.replace(/_/g, ' ') },
  });
  edges.push({ id: 'e-w1', source: 'event-1', target: 'workflow-1', animated: true, style: { stroke: '#3b82f6' } });
  y += yStep;

  // Agent node
  nodes.push({
    id: 'agent-1',
    type: 'agent',
    position: { x: xCenter, y },
    data: { label: 'LangGraph Agent', status: run.status },
  });
  edges.push({ id: 'w-a1', source: 'workflow-1', target: 'agent-1', animated: true, style: { stroke: '#3b82f6' } });
  y += yStep;

  // Memory nodes (left branch)
  const memoryTypes = ['STM', 'LTM', 'Semantic'];
  memoryTypes.forEach((memType, i) => {
    const memX = xCenter - 250;
    const memY = y + i * 80;
    nodes.push({
      id: `memory-${i}`,
      type: 'memory',
      position: { x: memX, y: memY },
      data: { label: memType },
    });
    edges.push({
      id: `a-m${i}`,
      source: 'agent-1',
      target: `memory-${i}`,
      style: { stroke: '#06b6d4' },
      label: i === 0 ? 'retrieve' : '',
    });
  });

  // Tool nodes (right branch)
  run.tool_calls.forEach((tc, i) => {
    const toolX = xCenter + 200;
    const toolY = y + i * 80;
    nodes.push({
      id: `tool-${i}`,
      type: 'tool',
      position: { x: toolX, y: toolY },
      data: { label: tc.tool },
    });
    edges.push({
      id: `a-t${i}`,
      source: 'agent-1',
      target: `tool-${i}`,
      style: { stroke: '#22c55e' },
    });
  });

  // Outcome node
  const outcomeY = y + Math.max(memoryTypes.length, run.tool_calls.length) * 80 + 40;
  nodes.push({
    id: 'outcome-1',
    type: 'outcome',
    position: { x: xCenter, y: outcomeY },
    data: { label: run.state_after?.replace(/_/g, ' ') || 'Completed', state: run.state_after },
  });

  // Connect tools and memory to outcome
  run.tool_calls.forEach((_, i) => {
    edges.push({ id: `t-o${i}`, source: `tool-${i}`, target: 'outcome-1', style: { stroke: '#22c55e' } });
  });
  memoryTypes.forEach((_, i) => {
    edges.push({ id: `m-o${i}`, source: `memory-${i}`, target: 'outcome-1', style: { stroke: '#06b6d4' } });
  });

  return { nodes, edges };
}

export function WorkflowVisualizer() {
  const [searchParams] = useSearchParams();
  const loadId = searchParams.get('load_id') || localStorage.getItem(LOAD_STORAGE_KEY) || undefined;
  const [agentRuns, setAgentRuns] = React.useState<AgentRun[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    const fetchRuns = async () => {
      try {
        const url = loadId ? `/api/v1/monitoring/agent-runs?load_id=${loadId}` : '/api/v1/monitoring/agent-runs';
        const res = await authFetch(url);
        const data = await res.json();
        setAgentRuns(data.map((run: AgentRun) => ({
          ...run,
          tool_calls: run.tool_calls || [],
          memory_operations: run.memory_operations || [],
          customer_rules_applied: run.customer_rules_applied || [],
          error: run.error || null,
          state_before: run.state_before || null,
          state_after: run.state_after || null,
        })));
      } catch {
        // silently fall through — agentRuns state stays empty
      } finally {
        setLoading(false);
      }
    };
    fetchRuns();
  }, [loadId]);

  const { nodes: initialNodes, edges: initialEdges } = buildFlowData(agentRuns);

  const onInit = useCallback((instance: { fitView: () => void }) => {
    setTimeout(() => instance.fitView(), 100);
  }, []);

  return (
    <Box sx={{ height: 'calc(100vh - 140px)', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ mb: 2 }}>
        <Typography variant="h4" sx={{ fontWeight: 700 }}>Workflow Visualizer</Typography>
        <Typography variant="body2" sx={{ color: '#64748b' }}>
          Interactive execution graph — event → workflow → agent → memory/tools → outcome
        </Typography>
      </Box>

      <Card sx={{ flex: 1, bgcolor: '#1a2235', overflow: 'hidden' }}>
        <Box sx={{ height: '100%', '& .react-flow__background': { bgcolor: '#0a0e17' } }}>
          <ReactFlow
            nodes={initialNodes}
            edges={initialEdges}
            nodeTypes={nodeTypes}
            onInit={onInit}
            fitView
            proOptions={{ hideAttribution: true }}
          >
            <Background color="#2a3a52" gap={20} />
            <Controls
              style={{ background: '#1a2235', border: '1px solid #2a3a52', borderRadius: 8 }}
            />
            <MiniMap
              nodeColor={(node) => {
                const typeColors: Record<string, string> = {
                  event: '#f59e0b',
                  workflow: '#3b82f6',
                  agent: '#8b5cf6',
                  memory: '#06b6d4',
                  tool: '#22c55e',
                  outcome: '#ef4444',
                };
                return typeColors[node.type || ''] || '#64748b';
              }}
              style={{ background: '#0a0e17', border: '1px solid #2a3a52' }}
            />
          </ReactFlow>
        </Box>
      </Card>

      {/* Legend */}
      <Box sx={{ display: 'flex', gap: 2, mt: 1.5, justifyContent: 'center' }}>
        {[
          { label: 'Event', color: '#f59e0b' },
          { label: 'Workflow', color: '#3b82f6' },
          { label: 'Agent', color: '#8b5cf6' },
          { label: 'Memory', color: '#06b6d4' },
          { label: 'Tool', color: '#22c55e' },
          { label: 'Outcome', color: '#ef4444' },
        ].map(({ label, color }) => (
          <Box key={label} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: color }} />
            <Typography variant="caption" sx={{ color: '#94a3b8' }}>{label}</Typography>
          </Box>
        ))}
      </Box>
    </Box>
  );
}