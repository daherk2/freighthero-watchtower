import { describe, it, expect } from 'vitest';
import { useDashboardStore, useLoadDetailStore, useAgentRunStore, useMemoryExplorerStore, useSidebarStore } from '@/stores';
import { mockLoads, mockAgentRuns, mockMemories, mockDashboardStats, mockTraceTree } from '@/api/mockData';

describe('useDashboardStore', () => {
  it('should initialize with default values', () => {
    const state = useDashboardStore.getState();
    expect(state.stats).toBeNull();
    expect(state.loads).toEqual([]);
    expect(state.recentRuns).toEqual([]);
    expect(state.loading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('should set stats', () => {
    useDashboardStore.getState().setStats(mockDashboardStats);
    expect(useDashboardStore.getState().stats).toEqual(mockDashboardStats);
  });

  it('should set loads', () => {
    useDashboardStore.getState().setLoads(mockLoads);
    expect(useDashboardStore.getState().loads).toEqual(mockLoads);
  });

  it('should set recent runs', () => {
    useDashboardStore.getState().setRecentRuns(mockAgentRuns);
    expect(useDashboardStore.getState().recentRuns).toEqual(mockAgentRuns);
  });

  it('should set loading', () => {
    useDashboardStore.getState().setLoading(true);
    expect(useDashboardStore.getState().loading).toBe(true);
  });

  it('should set error', () => {
    useDashboardStore.getState().setError('test error');
    expect(useDashboardStore.getState().error).toBe('test error');
    useDashboardStore.getState().setError(null);
    expect(useDashboardStore.getState().error).toBeNull();
  });
});

describe('useLoadDetailStore', () => {
  it('should initialize with default values', () => {
    const state = useLoadDetailStore.getState();
    expect(state.load).toBeNull();
    expect(state.events).toEqual([]);
    expect(state.agentRuns).toEqual([]);
    expect(state.memories).toEqual([]);
    expect(state.loading).toBe(false);
  });

  it('should set load', () => {
    useLoadDetailStore.getState().setLoad(mockLoads[0]);
    expect(useLoadDetailStore.getState().load).toEqual(mockLoads[0]);
  });

  it('should set events', () => {
    const events = [{ event_id: 'evt-1', event_type: 'tracking' as const, load_id: 'load-001', customer_id: 'customer_a', occurred_at: '2024-01-15T12:00:00Z', event_data: {} }];
    useLoadDetailStore.getState().setEvents(events);
    expect(useLoadDetailStore.getState().events).toEqual(events);
  });

  it('should set agent runs', () => {
    useLoadDetailStore.getState().setAgentRuns(mockAgentRuns);
    expect(useLoadDetailStore.getState().agentRuns).toEqual(mockAgentRuns);
  });

  it('should set memories', () => {
    useLoadDetailStore.getState().setMemories(mockMemories);
    expect(useLoadDetailStore.getState().memories).toEqual(mockMemories);
  });

  it('should clear load', () => {
    useLoadDetailStore.getState().setLoad(null);
    expect(useLoadDetailStore.getState().load).toBeNull();
  });
});

describe('useAgentRunStore', () => {
  it('should initialize with default values', () => {
    const state = useAgentRunStore.getState();
    expect(state.currentRun).toBeNull();
    expect(state.traceTree).toBeNull();
    expect(state.toolCalls).toEqual([]);
    expect(state.memoryOps).toEqual([]);
    expect(state.loading).toBe(false);
  });

  it('should set current run', () => {
    useAgentRunStore.getState().setCurrentRun(mockAgentRuns[0]);
    expect(useAgentRunStore.getState().currentRun).toEqual(mockAgentRuns[0]);
  });

  it('should set tool calls', () => {
    const calls = [{ tool: 'test', arguments: {}, result: {} }];
    useAgentRunStore.getState().setToolCalls(calls);
    expect(useAgentRunStore.getState().toolCalls).toEqual(calls);
  });

  it('should set memory ops', () => {
    const ops = [{ operation: 'store', memory_type: 'STM' }];
    useAgentRunStore.getState().setMemoryOps(ops);
    expect(useAgentRunStore.getState().memoryOps).toEqual(ops);
  });

  it('should set trace tree', () => {
    useAgentRunStore.getState().setTraceTree(mockTraceTree);
    expect(useAgentRunStore.getState().traceTree).toEqual(mockTraceTree);
  });

  it('should set loading', () => {
    useAgentRunStore.getState().setLoading(true);
    expect(useAgentRunStore.getState().loading).toBe(true);
  });

  it('should set error', () => {
    useAgentRunStore.getState().setError('test error');
    expect(useAgentRunStore.getState().error).toBe('test error');
  });

  it('should clear current run', () => {
    useAgentRunStore.getState().setCurrentRun(null);
    expect(useAgentRunStore.getState().currentRun).toBeNull();
  });
});

describe('useMemoryExplorerStore', () => {
  it('should initialize with default values', () => {
    const state = useMemoryExplorerStore.getState();
    expect(state.memories).toEqual([]);
    expect(state.selectedType).toBe('all');
    expect(state.selectedScope).toBe('load');
    expect(state.loading).toBe(false);
  });

  it('should set selected type', () => {
    useMemoryExplorerStore.getState().setSelectedType('semantic');
    expect(useMemoryExplorerStore.getState().selectedType).toBe('semantic');
  });

  it('should set selected scope', () => {
    useMemoryExplorerStore.getState().setSelectedScope('customer');
    expect(useMemoryExplorerStore.getState().selectedScope).toBe('customer');
  });

  it('should set memories', () => {
    useMemoryExplorerStore.getState().setMemories(mockMemories);
    expect(useMemoryExplorerStore.getState().memories).toEqual(mockMemories);
  });

  it('should set metrics', () => {
    useMemoryExplorerStore.getState().setMetrics({ total: 100 });
    expect(useMemoryExplorerStore.getState().metrics).toEqual({ total: 100 });
  });

  it('should set loading', () => {
    useMemoryExplorerStore.getState().setLoading(true);
    expect(useMemoryExplorerStore.getState().loading).toBe(true);
  });

  it('should set error', () => {
    useMemoryExplorerStore.getState().setError('test error');
    expect(useMemoryExplorerStore.getState().error).toBe('test error');
  });
});

describe('useSidebarStore', () => {
  it('should initialize with open=true', () => {
    expect(useSidebarStore.getState().open).toBe(true);
  });

  it('should toggle sidebar', () => {
    useSidebarStore.getState().toggle();
    expect(useSidebarStore.getState().open).toBe(false);
    useSidebarStore.getState().toggle();
    expect(useSidebarStore.getState().open).toBe(true);
  });

  it('should set open state', () => {
    useSidebarStore.getState().setOpen(false);
    expect(useSidebarStore.getState().open).toBe(false);
    useSidebarStore.getState().setOpen(true);
    expect(useSidebarStore.getState().open).toBe(true);
  });
});