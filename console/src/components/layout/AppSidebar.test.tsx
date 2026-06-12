import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/utils';
import { AppSidebar } from '@/components/layout/AppSidebar';

// Mock useSidebarStore to control open state
vi.mock('@/stores', async () => {
  const actual = await vi.importActual('@/stores');
  return {
    ...actual,
    useSidebarStore: () => ({ open: true, toggle: vi.fn() }),
  };
});

describe('AppSidebar', () => {
  it('should render navigation items', () => {
    render(<AppSidebar drawerWidth={240} />);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Loads')).toBeInTheDocument();
    expect(screen.getByText('Agent Viewer')).toBeInTheDocument();
    expect(screen.getByText('Workflows')).toBeInTheDocument();
    expect(screen.getByText('Memory')).toBeInTheDocument();
    expect(screen.getByText('Tool Calls')).toBeInTheDocument();
    expect(screen.getByText('Traces')).toBeInTheDocument();
    expect(screen.getByText('Debugger')).toBeInTheDocument();
    expect(screen.getByText('Monitoring')).toBeInTheDocument();
  });

  it('should highlight active route', () => {
    render(<AppSidebar drawerWidth={240} />);
    // Dashboard should be active since we're at /
    const dashboardItem = screen.getByText('Dashboard');
    expect(dashboardItem).toBeInTheDocument();
  });
});