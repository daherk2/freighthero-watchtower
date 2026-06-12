import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@/test/utils';
import { AgentDebugger } from '@/screens/AgentDebugger';

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  };
});

// Mock fetch for agent runs
const mockAgentRuns = [
  {
    run_id: 'run-001',
    load_id: 'load-001',
    workflow: 'confirm_delivery',
    status: 'completed',
    started_at: '2026-06-11T17:35:01',
    completed_at: '2026-06-11T17:36:01',
    tool_calls: [{ tool: 'send_message', arguments: { to: 'driver' }, result: { success: true } }],
    memory_operations: [{ operation: 'retrieve', memory_type: 'episodic', content: 'Previous delivery info' }],
    customer_rules_applied: [],
    state_before: 'at_delivery',
    state_after: 'delivered',
    sop_branch: 'first_arrival_contact',
    error: null,
  },
];

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn((url: string) => {
    if (url.includes('/debugger/agent-runs/')) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(mockAgentRuns[0]) });
    }
    return Promise.resolve({ ok: true, json: () => Promise.resolve(mockAgentRuns) });
  }));
});

describe('AgentDebugger', () => {
  it('should render page title', () => {
    render(<AgentDebugger />);
    expect(screen.getByText('Agent Debugger')).toBeInTheDocument();
  });

  it('should render subtitle', () => {
    render(<AgentDebugger />);
    expect(screen.getByText(/Step-by-step replay/)).toBeInTheDocument();
  });

  it('should render run selector', () => {
    render(<AgentDebugger />);
    expect(screen.getByText('Select Run')).toBeInTheDocument();
  });

  it('should render replay controls', () => {
    render(<AgentDebugger />);
    // Should have play/pause button (multiple icon buttons exist, so use getAllByRole)
    const buttons = screen.getAllByRole('button');
    expect(buttons.length).toBeGreaterThan(0);
  });

  it('should render execution timeline', () => {
    render(<AgentDebugger />);
    expect(screen.getByText('Execution Timeline')).toBeInTheDocument();
  });

  it('should render step details section', async () => {
    render(<AgentDebugger />);
    await waitFor(() => {
      const stepDetails = screen.getAllByText(/Event Received|Initial State|Memory Retrieved|confirm delivery/i);
      expect(stepDetails.length).toBeGreaterThanOrEqual(1);
    });
  });

  it('should render initial step content', async () => {
    render(<AgentDebugger />);
    await waitFor(() => {
      // Should show workflow name or step content
      const content = screen.getAllByText(/Event Received|confirm delivery|Initial State/i);
      expect(content.length).toBeGreaterThanOrEqual(1);
    });
  });

  it('should render run status chips in selector', async () => {
    render(<AgentDebugger />);
    await waitFor(() => {
      const statusChips = screen.getAllByText(/completed|failed|running/i);
      expect(statusChips.length).toBeGreaterThan(0);
    });
  });

  it('should render workflow names in selector', async () => {
    render(<AgentDebugger />);
    await waitFor(() => {
      const workflowNames = screen.getAllByText(/confirm delivery|delivery eta checkpoint/i);
      expect(workflowNames.length).toBeGreaterThanOrEqual(1);
    });
  });

  it('should allow clicking on different runs', async () => {
    render(<AgentDebugger />);
    await waitFor(() => {
      const statusChips = screen.getAllByText(/completed|failed/i);
      expect(statusChips.length).toBeGreaterThan(0);
      fireEvent.click(statusChips[0]);
    });
    expect(screen.getByText('Agent Debugger')).toBeInTheDocument();
  });

  it('should render slider for step navigation', () => {
    render(<AgentDebugger />);
    // MUI Slider should be present
    const sliders = screen.getAllByRole('slider');
    expect(sliders.length).toBeGreaterThan(0);
  });
});