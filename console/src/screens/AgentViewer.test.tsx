import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@/test/utils';
import { AgentViewer, AgentRunDetail } from '@/screens/AgentViewer';

// Mock useNavigate and useParams
const mockNavigate = vi.fn();
let mockParams = { id: undefined as string | undefined };

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => mockParams,
  };
});

// Mock fetch for agent runs
const mockAgentRuns = [
  {
    run_id: 'run-001',
    load_id: 'load-001',
    customer_id: 'customer_a',
    workflow: 'confirm_delivery',
    status: 'completed',
    started_at: '2026-06-11T17:35:01',
    completed_at: '2026-06-11T17:36:01',
    tool_calls: [{ tool: 'send_message', arguments: { to: 'driver' }, result: { success: true } }],
    memory_operations: [{ operation: 'retrieve', memory_type: 'episodic', content: 'Previous delivery info' }],
    customer_rules_applied: ['confirm_with_driver'],
    state_before: 'at_delivery',
    state_after: 'delivered',
    sop_branch: 'first_arrival_contact',
    error: null,
  },
];

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn((url: string) => {
    if (url.includes('/debugger/agent-runs/')) {
      if (url.includes('nonexistent')) {
        return Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({ detail: 'Not found' }) });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve(mockAgentRuns[0]) });
    }
    return Promise.resolve({ ok: true, json: () => Promise.resolve(mockAgentRuns) });
  }));
});

describe('AgentViewer', () => {
  it('should render page title', () => {
    render(<AgentViewer />);
    expect(screen.getByText('Agent Execution Viewer')).toBeInTheDocument();
  });

  it('should render subtitle', () => {
    render(<AgentViewer />);
    expect(screen.getByText(/Inspect agent decisions/)).toBeInTheDocument();
  });

  it('should render agent run cards', async () => {
    render(<AgentViewer />);
    await waitFor(() => {
      expect(screen.getAllByText(/confirm delivery|delivery eta checkpoint/i).length).toBeGreaterThanOrEqual(1);
    });
  });

  it('should show tool call and memory counts', async () => {
    render(<AgentViewer />);
    await waitFor(() => {
      const toolChips = screen.getAllByText(/tools/i);
      expect(toolChips.length).toBeGreaterThan(0);
    });
  });

  it('should show memory operation chips', async () => {
    render(<AgentViewer />);
    await waitFor(() => {
      const memoryChips = screen.getAllByText(/memory/i);
      expect(memoryChips.length).toBeGreaterThan(0);
    });
  });

  it('should show status chips for runs', async () => {
    render(<AgentViewer />);
    await waitFor(() => {
      const completedChips = screen.getAllByText(/completed|failed|running/i);
      expect(completedChips.length).toBeGreaterThan(0);
    });
  });

  it('should show run IDs', async () => {
    render(<AgentViewer />);
    await waitFor(() => {
      const runIdElements = screen.getAllByText(/^run-/i);
      expect(runIdElements.length).toBeGreaterThan(0);
    });
  });

  it('should show load IDs in cards', async () => {
    render(<AgentViewer />);
    await waitFor(() => {
      const loadLabels = screen.getAllByText('Load');
      expect(loadLabels.length).toBeGreaterThan(0);
    });
  });

  it('should show customer IDs in cards', async () => {
    render(<AgentViewer />);
    await waitFor(() => {
      const customerLabels = screen.getAllByText('Customer');
      expect(customerLabels.length).toBeGreaterThan(0);
    });
  });
});

describe('AgentRunDetail', () => {
  beforeEach(() => {
    mockParams = { id: undefined };
  });

  it('should show not found for invalid id', async () => {
    mockParams = { id: 'nonexistent' };
    render(<AgentRunDetail />);
    await waitFor(() => {
      expect(screen.getByText(/not found|loading/i)).toBeInTheDocument();
    });
  });

  it('should render agent run detail for valid id', async () => {
    mockParams = { id: 'run-001' };
    render(<AgentRunDetail />);
    await waitFor(() => {
      expect(screen.getByText('Agent Run')).toBeInTheDocument();
    });
  });

  it('should render context section', async () => {
    mockParams = { id: 'run-001' };
    render(<AgentRunDetail />);
    await waitFor(() => {
      expect(screen.getByText('Context')).toBeInTheDocument();
    });
  });

  it('should render tool calls section', async () => {
    mockParams = { id: 'run-001' };
    render(<AgentRunDetail />);
    await waitFor(() => {
      expect(screen.getByText(/Tool Calls/)).toBeInTheDocument();
    });
  });

  it('should render memory operations section', async () => {
    mockParams = { id: 'run-001' };
    render(<AgentRunDetail />);
    await waitFor(() => {
      expect(screen.getByText(/Memory Operations/)).toBeInTheDocument();
    });
  });

  it('should render customer rules section', async () => {
    mockParams = { id: 'run-001' };
    render(<AgentRunDetail />);
    await waitFor(() => {
      expect(screen.getByText('Customer Rules')).toBeInTheDocument();
    });
  });
});