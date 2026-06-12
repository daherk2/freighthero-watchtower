import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/utils';
import { StatCard, StatusChip, StateChip, SectionHeader, EmptyState } from '@/components/shared';

describe('StatCard', () => {
  it('should render title and value', () => {
    render(<StatCard title="Active Loads" value={4} />);
    expect(screen.getByText('Active Loads')).toBeInTheDocument();
    expect(screen.getByText('4')).toBeInTheDocument();
  });

  it('should render string value', () => {
    render(<StatCard title="Error Rate" value="4.2%" />);
    expect(screen.getByText('4.2%')).toBeInTheDocument();
  });

  it('should render subtitle when provided', () => {
    render(<StatCard title="Active Loads" value={4} subtitle="from last 24h" />);
    expect(screen.getByText('from last 24h')).toBeInTheDocument();
  });

  it('should render with custom color', () => {
    render(<StatCard title="Errors" value={2} color="#ef4444" />);
    expect(screen.getByText('2')).toBeInTheDocument();
  });

  it('should render trend when provided', () => {
    render(<StatCard title="Active Loads" value={4} trend="up" trendValue="+12%" />);
    // Trend renders as "↑ +12%" (arrow + value)
    expect(screen.getByText(/↑.*\+12%/)).toBeInTheDocument();
  });
});

describe('StatusChip', () => {
  it('should render status text', () => {
    render(<StatusChip status="completed" />);
    expect(screen.getByText('completed')).toBeInTheDocument();
  });

  it('should format status with underscores', () => {
    render(<StatusChip status="on_route" />);
    expect(screen.getByText('on route')).toBeInTheDocument();
  });
});

describe('StateChip', () => {
  it('should render state text', () => {
    render(<StateChip state="on_route_to_delivery" />);
    expect(screen.getByText('on route to delivery')).toBeInTheDocument();
  });

  it('should render dispatched state', () => {
    render(<StateChip state="dispatched" />);
    expect(screen.getByText('dispatched')).toBeInTheDocument();
  });
});

describe('SectionHeader', () => {
  it('should render title', () => {
    render(<SectionHeader title="Test Section" />);
    expect(screen.getByText('Test Section')).toBeInTheDocument();
  });

  it('should render subtitle when provided', () => {
    render(<SectionHeader title="Test" subtitle="A description" />);
    expect(screen.getByText('A description')).toBeInTheDocument();
  });
});

describe('EmptyState', () => {
  it('should render title', () => {
    render(<EmptyState title="No data" />);
    expect(screen.getByText('No data')).toBeInTheDocument();
  });

  it('should render description when provided', () => {
    render(<EmptyState title="No data" description="Try again later" />);
    expect(screen.getByText('Try again later')).toBeInTheDocument();
  });
});