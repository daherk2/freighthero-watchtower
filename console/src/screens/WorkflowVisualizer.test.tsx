import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/test/utils';

// Mock ReactFlow since it requires canvas/DOM features not available in jsdom
vi.mock('@xyflow/react', async () => {
  return {
    ReactFlow: ({ nodes }: { nodes: Array<{ id: string; data: Record<string, unknown> }> }) => (
      <div data-testid="react-flow">
        {nodes.map((node) => (
          <div key={node.id} data-testid={`node-${node.id}`}>
            {node.data.label as string}
          </div>
        ))}
      </div>
    ),
    Background: () => <div data-testid="background" />,
    Controls: () => <div data-testid="controls" />,
    MiniMap: () => <div data-testid="minimap" />,
    Handle: () => <div data-testid="handle" />,
    Position: { Top: 'top', Bottom: 'bottom', Left: 'left', Right: 'right' },
  };
});

vi.mock('@xyflow/react/dist/style.css', () => ({}));

// Mock fetch for agent runs
const mockAgentRuns = [
  {
    run_id: 'run-001',
    load_id: 'load-001',
    workflow: 'confirm_delivery',
    status: 'completed',
    started_at: '2026-06-11T17:35:01',
    completed_at: '2026-06-11T17:36:01',
    tool_calls: [
      { tool: 'send_message', arguments: { to: 'driver' }, result: { success: true } },
      { tool: 'schedule_followup', arguments: { delay: 300 }, result: { scheduled: true } },
    ],
    memory_operations: [
      { operation: 'retrieve', memory_type: 'episodic', content: 'Previous delivery info' },
      { operation: 'store', memory_type: 'semantic', content: 'New delivery record' },
      { operation: 'update', memory_type: 'procedural', content: 'Updated procedure' },
    ],
    customer_rules_applied: [],
    state_before: 'at_delivery',
    state_after: 'delivered',
    sop_branch: 'first_arrival_contact',
    error: null,
  },
];

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn(() =>
    Promise.resolve({ ok: true, json: () => Promise.resolve(mockAgentRuns) })
  ));
});

import { WorkflowVisualizer } from '@/screens/WorkflowVisualizer';

describe('WorkflowVisualizer', () => {
  it('should render page title', () => {
    render(<WorkflowVisualizer />);
    expect(screen.getByText('Workflow Visualizer')).toBeInTheDocument();
  });

  it('should render subtitle', () => {
    render(<WorkflowVisualizer />);
    expect(screen.getByText(/Interactive execution graph/)).toBeInTheDocument();
  });

  it('should render ReactFlow component', () => {
    render(<WorkflowVisualizer />);
    expect(screen.getByTestId('react-flow')).toBeInTheDocument();
  });

  it('should render flow nodes from mock data', async () => {
    render(<WorkflowVisualizer />);
    await waitFor(() => {
      expect(screen.getByTestId('node-event-1')).toBeInTheDocument();
      expect(screen.getByTestId('node-workflow-1')).toBeInTheDocument();
      expect(screen.getByTestId('node-agent-1')).toBeInTheDocument();
    });
  });

  it('should render memory nodes', async () => {
    render(<WorkflowVisualizer />);
    await waitFor(() => {
      expect(screen.getByTestId('node-memory-0')).toBeInTheDocument();
      expect(screen.getByTestId('node-memory-1')).toBeInTheDocument();
      expect(screen.getByTestId('node-memory-2')).toBeInTheDocument();
    });
  });

  it('should render tool nodes', async () => {
    render(<WorkflowVisualizer />);
    await waitFor(() => {
      expect(screen.getByTestId('node-tool-0')).toBeInTheDocument();
      expect(screen.getByTestId('node-tool-1')).toBeInTheDocument();
    });
  });

  it('should render legend items', () => {
    render(<WorkflowVisualizer />);
    expect(screen.getByText('Event')).toBeInTheDocument();
    expect(screen.getByText('Workflow')).toBeInTheDocument();
    expect(screen.getByText('Agent')).toBeInTheDocument();
    expect(screen.getByText('Memory')).toBeInTheDocument();
    expect(screen.getByText('Tool')).toBeInTheDocument();
    expect(screen.getByText('Outcome')).toBeInTheDocument();
  });
});