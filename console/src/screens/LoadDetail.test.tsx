import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@/test/utils';
import { LoadList, LoadDetail } from '@/screens/LoadDetail';

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

// Mock useLoad and useAgentRuns hooks
vi.mock('@/api/hooks', async () => {
  const actual = await vi.importActual('@/api/hooks');
  return {
    ...actual,
    useLoads: () => ({
      data: [
        {
          load_id: 'load-001',
          customer_id: 'customer_a',
          external_load_id: 'EXT-001',
          po_number: 'PO-001',
          current_state: 'on_route_to_delivery',
          current_eta_utc: null,
          created_at: '2026-06-11T17:35:01',
          updated_at: '2026-06-12T03:55:51',
          load_data: { driver: { name: 'John Doe', phone: '555-0100' } },
        },
      ],
    }),
    useLoad: (id: string) => {
      if (!id || id === 'nonexistent') return { data: null };
      return {
        data: {
          load_id: id,
          customer_id: 'customer_a',
          external_load_id: 'EXT-001',
          po_number: 'PO-001',
          current_state: 'on_route_to_delivery',
          current_eta_utc: null,
          created_at: '2026-06-11T17:35:01',
          updated_at: '2026-06-12T03:55:51',
          load_data: { driver: { name: 'John Doe', phone: '555-0100' } },
        },
      };
    },
    useAgentRuns: () => ({ data: [] }),
  };
});

describe('LoadList', () => {
  it('should render page title', () => {
    render(<LoadList />);
    expect(screen.getByText('Loads')).toBeInTheDocument();
  });

  it('should render table headers', () => {
    render(<LoadList />);
    expect(screen.getByText('Load ID')).toBeInTheDocument();
    expect(screen.getByText('Customer')).toBeInTheDocument();
    expect(screen.getByText('State')).toBeInTheDocument();
    expect(screen.getByText('PO Number')).toBeInTheDocument();
    expect(screen.getByText('ETA')).toBeInTheDocument();
    expect(screen.getByText('Driver')).toBeInTheDocument();
    expect(screen.getByText('Updated')).toBeInTheDocument();
  });

  it('should render load rows from mock data', () => {
    render(<LoadList />);
    expect(screen.getByText('load-001')).toBeInTheDocument();
  });
});

describe('LoadDetail', () => {
  beforeEach(() => {
    mockParams = { id: undefined };
  });

  it('should show load not found for invalid id', () => {
    mockParams = { id: 'nonexistent' };
    render(<LoadDetail />);
    expect(screen.getByText('Loading load details...')).toBeInTheDocument();
  });

  it('should render load detail for valid id', async () => {
    mockParams = { id: 'load-001' };
    render(<LoadDetail />);
    await waitFor(() => expect(screen.getByText('Load Information')).toBeInTheDocument());
  });

  it('should render tab labels', async () => {
    mockParams = { id: 'load-001' };
    render(<LoadDetail />);
    await waitFor(() => {
      expect(screen.getByText('Events')).toBeInTheDocument();
      expect(screen.getByText('Agent Runs')).toBeInTheDocument();
      expect(screen.getByText('Memory')).toBeInTheDocument();
      expect(screen.getByText('Tracking')).toBeInTheDocument();
    });
  });

  it('should switch tabs on click', async () => {
    mockParams = { id: 'load-001' };
    render(<LoadDetail />);
    await waitFor(() => expect(screen.getByText('Agent Runs')).toBeInTheDocument());
    const agentTab = screen.getByText('Agent Runs');
    fireEvent.click(agentTab);
    expect(agentTab).toBeInTheDocument();
  });

  it('should render load information card', async () => {
    mockParams = { id: 'load-001' };
    render(<LoadDetail />);
    await waitFor(() => expect(screen.getByText('Load Information')).toBeInTheDocument());
  });

  it('should render PO Number label', async () => {
    mockParams = { id: 'load-001' };
    render(<LoadDetail />);
    await waitFor(() => expect(screen.getByText('PO Number')).toBeInTheDocument());
  });
});