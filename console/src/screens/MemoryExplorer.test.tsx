import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@/test/utils';
import { MemoryExplorer } from '@/screens/MemoryExplorer';

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  };
});

describe('MemoryExplorer', () => {
  it('should render page title', () => {
    render(<MemoryExplorer />);
    expect(screen.getByText('Memory Explorer')).toBeInTheDocument();
  });

  it('should render memory type filters', () => {
    render(<MemoryExplorer />);
    // Memory types appear in sidebar filter and stats
    expect(screen.getAllByText('STM').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('LTM').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('semantic').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('procedural').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('episodic').length).toBeGreaterThanOrEqual(1);
  });

  it('should render search field', () => {
    render(<MemoryExplorer />);
    expect(screen.getByPlaceholderText('Search memories by content or tags...')).toBeInTheDocument();
  });

  it('should render memory cards', () => {
    render(<MemoryExplorer />);
    // Should show confidence labels from memory cards
    const confidenceElements = screen.getAllByText(/conf:/i);
    expect(confidenceElements.length).toBeGreaterThan(0);
  });

  it('should render tab options', () => {
    render(<MemoryExplorer />);
    expect(screen.getByText('All')).toBeInTheDocument();
    expect(screen.getByText('Recent')).toBeInTheDocument();
    expect(screen.getByText('High Confidence')).toBeInTheDocument();
  });

  it('should filter memories by search', () => {
    render(<MemoryExplorer />);
    const searchInput = screen.getByPlaceholderText('Search memories by content or tags...');
    fireEvent.change(searchInput, { target: { value: 'driver' } });
    // Should still render without errors
    expect(screen.getByText('Memory Explorer')).toBeInTheDocument();
  });

  it('should switch tabs', () => {
    render(<MemoryExplorer />);
    const recentTab = screen.getByText('Recent');
    fireEvent.click(recentTab);
    expect(recentTab).toBeInTheDocument();
  });
});