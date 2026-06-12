import { create } from 'zustand';
import type {
  Load,
  AgentRun,
  DashboardStats,
  MemoryEntry,
  Event,
  TraceNode,
} from '@/types';

// --- Dashboard Store ---
interface DashboardState {
  stats: DashboardStats | null;
  loads: Load[];
  recentRuns: AgentRun[];
  loading: boolean;
  error: string | null;
  setStats: (stats: DashboardStats) => void;
  setLoads: (loads: Load[]) => void;
  setRecentRuns: (runs: AgentRun[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  stats: null,
  loads: [],
  recentRuns: [],
  loading: false,
  error: null,
  setStats: (stats) => set({ stats }),
  setLoads: (loads) => set({ loads }),
  setRecentRuns: (recentRuns) => set({ recentRuns }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
}));

// --- Load Detail Store ---
interface LoadDetailState {
  load: Load | null;
  events: Event[];
  agentRuns: AgentRun[];
  memories: MemoryEntry[];
  loading: boolean;
  error: string | null;
  setLoad: (load: Load | null) => void;
  setEvents: (events: Event[]) => void;
  setAgentRuns: (runs: AgentRun[]) => void;
  setMemories: (memories: MemoryEntry[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useLoadDetailStore = create<LoadDetailState>((set) => ({
  load: null,
  events: [],
  agentRuns: [],
  memories: [],
  loading: false,
  error: null,
  setLoad: (load) => set({ load }),
  setEvents: (events) => set({ events }),
  setAgentRuns: (agentRuns) => set({ agentRuns }),
  setMemories: (memories) => set({ memories }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
}));

// --- Agent Run Store ---
interface AgentRunState {
  currentRun: AgentRun | null;
  traceTree: TraceNode | null;
  toolCalls: unknown[];
  memoryOps: unknown[];
  loading: boolean;
  error: string | null;
  setCurrentRun: (run: AgentRun | null) => void;
  setTraceTree: (tree: TraceNode | null) => void;
  setToolCalls: (calls: unknown[]) => void;
  setMemoryOps: (ops: unknown[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useAgentRunStore = create<AgentRunState>((set) => ({
  currentRun: null,
  traceTree: null,
  toolCalls: [],
  memoryOps: [],
  loading: false,
  error: null,
  setCurrentRun: (currentRun) => set({ currentRun }),
  setTraceTree: (traceTree) => set({ traceTree }),
  setToolCalls: (toolCalls) => set({ toolCalls }),
  setMemoryOps: (memoryOps) => set({ memoryOps }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
}));

// --- Memory Explorer Store ---
interface MemoryExplorerState {
  memories: MemoryEntry[];
  metrics: Record<string, unknown>;
  selectedType: string;
  selectedScope: string;
  loading: boolean;
  error: string | null;
  setMemories: (memories: MemoryEntry[]) => void;
  setMetrics: (metrics: Record<string, unknown>) => void;
  setSelectedType: (type: string) => void;
  setSelectedScope: (scope: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useMemoryExplorerStore = create<MemoryExplorerState>((set) => ({
  memories: [],
  metrics: {},
  selectedType: 'all',
  selectedScope: 'load',
  loading: false,
  error: null,
  setMemories: (memories) => set({ memories }),
  setMetrics: (metrics) => set({ metrics }),
  setSelectedType: (selectedType) => set({ selectedType }),
  setSelectedScope: (selectedScope) => set({ selectedScope }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
}));

// --- Sidebar Store ---
interface SidebarState {
  open: boolean;
  toggle: () => void;
  setOpen: (open: boolean) => void;
}

export const useSidebarStore = create<SidebarState>((set) => ({
  open: true,
  toggle: () => set((s) => ({ open: !s.open })),
  setOpen: (open) => set({ open }),
}));