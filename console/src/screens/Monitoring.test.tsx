import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/utils';
import { Monitoring } from '@/screens/Monitoring';

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  };
});

describe('Monitoring', () => {
  it('should render page title', () => {
    render(<Monitoring />);
    expect(screen.getByText('Monitoring')).toBeInTheDocument();
  });

  it('should render stat cards', () => {
    render(<Monitoring />);
    expect(screen.getByText('Agent Runs (24h)')).toBeInTheDocument();
    expect(screen.getByText('Active Loads')).toBeInTheDocument();
    expect(screen.getByText('Memory Ops (24h)')).toBeInTheDocument();
    expect(screen.getByText('Error Rate')).toBeInTheDocument();
  });

  it('should render tab options', () => {
    render(<Monitoring />);
    expect(screen.getByText('Agent Metrics')).toBeInTheDocument();
    expect(screen.getByText('Memory Metrics')).toBeInTheDocument();
    expect(screen.getByText('Workflow Metrics')).toBeInTheDocument();
    expect(screen.getByText('Error Metrics')).toBeInTheDocument();
    expect(screen.getByText('Token Usage')).toBeInTheDocument();
  });
});