import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/utils';
import { Dashboard } from '@/screens/Dashboard';

// Mock useNavigate
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  };
});

describe('Dashboard', () => {
  it('should render dashboard title', () => {
    render(<Dashboard />);
    expect(screen.getByText('Operations Dashboard')).toBeInTheDocument();
  });

  it('should render stat cards', () => {
    render(<Dashboard />);
    // 'Active Loads' appears in stat card and table header, use getAllByText
    expect(screen.getAllByText('Active Loads').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Running Agents')).toBeInTheDocument();
    expect(screen.getByText('Failed Agents')).toBeInTheDocument();
    expect(screen.getByText('Follow-Ups')).toBeInTheDocument();
    expect(screen.getByText('Open Issues')).toBeInTheDocument();
    expect(screen.getByText('Active Tasks')).toBeInTheDocument();
  });

  it('should render active loads table', () => {
    render(<Dashboard />);
    // 'Active Loads' appears in stat card and table header
    const activeLoadsElements = screen.getAllByText('Active Loads');
    expect(activeLoadsElements.length).toBeGreaterThanOrEqual(1);
  });

  it('should render recent agent runs section', () => {
    render(<Dashboard />);
    expect(screen.getByText('Recent Agent Runs')).toBeInTheDocument();
  });

  it('should render load state distribution', () => {
    render(<Dashboard />);
    expect(screen.getByText('Load State Distribution')).toBeInTheDocument();
  });
});