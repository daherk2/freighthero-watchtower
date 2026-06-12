import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/test/utils';
import { TraceExplorer } from '@/screens/TraceExplorer';

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  };
});

vi.mock('@/api/hooks', async () => {
  const actual = await vi.importActual('@/api/hooks');
  return {
    ...actual,
    useLoads: () => ({ data: [] }),
    useAgentRuns: () => ({ data: [] }),
  };
});

// Mock fetch for agent runs
const mockAgentRuns = [
  {
    run_id: 'run-001',
    load_id: 'load-001',
    workflow: 'confirm_delivery',
    status: 'completed',
    tool_calls: [],
    memory_operations: [],
    customer_rules_applied: [],
  },
];

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn(() =>
    Promise.resolve({ ok: true, json: () => Promise.resolve(mockAgentRuns) })
  ));
});

describe('TraceExplorer', () => {
  it('should render page title', () => {
    render(<TraceExplorer />);
    expect(screen.getByText('Trace Explorer')).toBeInTheDocument();
  });

  it('should render legend', () => {
    render(<TraceExplorer />);
    // Legend shows node types
    const eventItems = screen.getAllByText('event');
    expect(eventItems.length).toBeGreaterThanOrEqual(1);
    const workflowItems = screen.getAllByText('workflow');
    expect(workflowItems.length).toBeGreaterThanOrEqual(1);
    const agentItems = screen.getAllByText('agent');
    expect(agentItems.length).toBeGreaterThanOrEqual(1);
    const memoryItems = screen.getAllByText('memory');
    expect(memoryItems.length).toBeGreaterThanOrEqual(1);
    const toolItems = screen.getAllByText('tool');
    expect(toolItems.length).toBeGreaterThanOrEqual(1);
  });

  it('should render trace nodes from agent runs', async () => {
    render(<TraceExplorer />);
    // Should show the workflow name from agent runs (confirm delivery)
    await waitFor(() => {
      expect(screen.getByText('confirm delivery')).toBeInTheDocument();
    });
  });
});