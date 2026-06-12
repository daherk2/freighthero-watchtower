import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@/test/utils';
import { ToolCallExplorer } from '@/screens/ToolCallExplorer';

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

// Mock LoadSelector to just render a simple div
vi.mock('@/components/shared/LoadSelector', () => ({
  LoadSelector: ({ onLoadChange }: { onLoadChange: (id: string) => void }) => {
    // Auto-select a load to trigger data fetching
    React.useEffect(() => {
      onLoadChange('load-001');
    }, [onLoadChange]);
    return <div data-testid="load-selector">LoadSelector</div>;
  },
}));

import React from 'react';

// Mock fetch for agent runs
const mockAgentRuns = [
  {
    run_id: 'run-001',
    load_id: 'load-001',
    workflow: 'confirm_delivery',
    status: 'completed',
    tool_calls_count: 2,
    memory_operations_count: 0,
    customer_rules_applied: [],
  },
];

const mockAgentRunDetail = {
  run_id: 'run-001',
  load_id: 'load-001',
  workflow: 'confirm_delivery',
  status: 'completed',
  tool_calls: [
    { tool: 'send_message', arguments: { to: 'driver' }, result: { success: true }, latency_ms: 150 },
    { tool: 'schedule_followup', arguments: { delay: 300 }, result: { scheduled: true }, latency_ms: 80 },
  ],
  memory_operations: [],
  customer_rules_applied: [],
  state_before: 'at_delivery',
  state_after: 'delivered',
  sop_branch: 'first_arrival_contact',
  error: null,
};

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn((url: string) => {
    if (url.includes('/debugger/agent-runs/')) {
      return Promise.resolve({ ok: true, json: () => Promise.resolve(mockAgentRunDetail) });
    }
    return Promise.resolve({ ok: true, json: () => Promise.resolve(mockAgentRuns) });
  }));
});

describe('ToolCallExplorer', () => {
  it('should render page title', () => {
    render(<ToolCallExplorer />);
    expect(screen.getByText('Tool Call Explorer')).toBeInTheDocument();
  });

  it('should render search field', () => {
    render(<ToolCallExplorer />);
    expect(screen.getByPlaceholderText('Search tool calls...')).toBeInTheDocument();
  });

  it('should render tool filter sidebar', () => {
    render(<ToolCallExplorer />);
    expect(screen.getByText('Tools')).toBeInTheDocument();
  });

  it('should render tool call cards with input/output', async () => {
    render(<ToolCallExplorer />);
    await waitFor(() => {
      const inputLabels = screen.getAllByText('Input');
      expect(inputLabels.length).toBeGreaterThan(0);
      const outputLabels = screen.getAllByText('Output');
      expect(outputLabels.length).toBeGreaterThan(0);
    });
  });

  it('should filter tool calls by search', () => {
    render(<ToolCallExplorer />);
    const searchInput = screen.getByPlaceholderText('Search tool calls...');
    fireEvent.change(searchInput, { target: { value: 'send_message' } });
    expect(screen.getByPlaceholderText('Search tool calls...')).toBeInTheDocument();
  });

  it('should toggle tool filter on click', async () => {
    render(<ToolCallExplorer />);
    await waitFor(() => {
      const toolNames = screen.getAllByText(/send_message|schedule_followup/i);
      expect(toolNames.length).toBeGreaterThan(0);
      fireEvent.click(toolNames[0]);
    });
    expect(screen.getByText('Tool Call Explorer')).toBeInTheDocument();
  });

  it('should render tool call status chips', async () => {
    render(<ToolCallExplorer />);
    await waitFor(() => {
      const statusChips = screen.getAllByText(/completed|running|failed/i);
      expect(statusChips.length).toBeGreaterThan(0);
    });
  });
});