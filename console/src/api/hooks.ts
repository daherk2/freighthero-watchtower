/**
 * Data fetching hooks for FreightHero API.
 *
 * Uses direct fetch with React state for simplicity and reliability.
 */

import { useState, useEffect, useCallback } from 'react';
import {
  loadsApi,
  eventsApi,
  monitoringApi,
  debuggerApi,
  healthApi,
} from './client';
import {
  mockLoads,
  mockAgentRuns,
  mockMemories,
  mockDashboardStats,
  mockTraceTree,
  mockCustomerConfigs,
} from './mockData';
import type { AgentRun, DashboardStats } from '@/types';

// --- Health ---

export function useHealth() {
  const [data, setData] = useState<{ status: string; version: string } | null>(null);
  useEffect(() => {
    healthApi.check().then(setData).catch(() => setData({ status: 'error', version: 'unknown' }));
  }, []);
  return { data };
}

// --- Loads ---

export function useLoads() {
  const [data, setData] = useState<unknown[]>([]);
  useEffect(() => {
    loadsApi.list().then((res) => {
      const mapped = Array.isArray(res) ? res : ((res as Record<string, unknown>).active_loads || []) as unknown[];
      console.log('[useLoads] Got', (mapped as unknown[]).length, 'loads from API');
      setData(mapped);
    }).catch((err) => { console.error('[useLoads] Error:', err); });
  }, []);
  return { data };
}

export function useLoad(id: string) {
  const [data, setData] = useState<unknown>(null);
  useEffect(() => {
    if (!id) return;
    loadsApi.get(id).then(setData).catch(() => {});
  }, [id]);
  return { data };
}

export function useCreateLoad() {
  return {
    mutateAsync: (data: unknown) => loadsApi.create(data),
  };
}

// --- Events ---

export function useSubmitTask() {
  return {
    mutateAsync: (data: unknown) => eventsApi.submitTask(data),
  };
}

export function useSubmitInboundCommunication() {
  return {
    mutateAsync: (data: unknown) => eventsApi.inboundCommunication(data),
  };
}

export function useSubmitTracking() {
  return {
    mutateAsync: (data: unknown) => eventsApi.tracking(data),
  };
}

export function useSubmitLoadUpdate() {
  return {
    mutateAsync: (data: unknown) => eventsApi.loadUpdate(data),
  };
}

// --- Monitoring ---

export function useDashboardStats() {
  const [data, setData] = useState<DashboardStats | null>(null);
  useEffect(() => {
    monitoringApi.dashboard().then((res) => {
      const raw = res as Record<string, unknown>;
      const mapped: DashboardStats = {
        active_loads: typeof raw.active_loads_count === 'number' ? raw.active_loads_count : (typeof raw.active_loads === 'number' ? raw.active_loads : (Array.isArray(raw.active_loads) ? raw.active_loads.length : 0)),
        running_agents: typeof raw.running_agents === 'number' ? raw.running_agents : 0,
        failed_agents: typeof raw.failed_agents === 'number' ? raw.failed_agents : 0,
        scheduled_followups: typeof raw.scheduled_followups === 'number' ? raw.scheduled_followups : 0,
        open_issues: typeof raw.open_issues === 'number' ? raw.open_issues : 0,
        active_tasks: typeof raw.active_tasks === 'number' ? raw.active_tasks : 0,
        agent_runs_24h: typeof raw.agent_runs_24h === 'number' ? raw.agent_runs_24h : 0,
        memory_operations_24h: typeof raw.memory_operations_24h === 'number' ? raw.memory_operations_24h : 0,
        error_rate_24h: typeof raw.error_rate_24h === 'number' ? raw.error_rate_24h : 0,
      };
      setData(mapped);
    }).catch((err) => { console.error('[useDashboardStats] Error:', err); setData(mockDashboardStats); });
  }, []);
  return { data };
}

export function useAgentRuns(loadId?: string) {
  const [data, setData] = useState<AgentRun[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchRuns = useCallback(async () => {
    try {
      const result = await monitoringApi.agentRuns(loadId) as Record<string, unknown>[];
      const mapped = result.map((run) => ({
        ...run,
        tool_calls: run.tool_calls || (run.tool_calls_count != null ? [] : []),
        memory_operations: run.memory_operations || (run.memory_operations_count != null ? [] : []),
        customer_rules_applied: run.customer_rules_applied || [],
        error: run.error || null,
        state_before: run.state_before || null,
        state_after: run.state_after || null,
      }));
            setData(mapped as AgentRun[]);
    } catch (err) {
      console.error('[useAgentRuns] Error:', err);
      setData(mockAgentRuns);
    } finally {
      setIsLoading(false);
    }
  }, [loadId]);

  useEffect(() => {
    fetchRuns();
  }, [fetchRuns]);

  return { data, isLoading, refetch: fetchRuns };
}

export function useMemoryMetrics(scope?: string, scopeId?: string) {
  const [data, setData] = useState<unknown>({ total: mockMemories.length, by_type: {} });
  useEffect(() => {
    monitoringApi.memoryMetrics(scope, scopeId).then(setData).catch(() => {});
  }, [scope, scopeId]);
  return { data };
}

export function useFailures() {
  const [data, setData] = useState<unknown[]>([]);
  useEffect(() => {
    monitoringApi.failures().then(setData).catch(() => {});
  }, []);
  return { data };
}

// --- Debugger ---

export function useAgentRunDetail(runId: string) {
  const [data, setData] = useState<unknown>(null);
  useEffect(() => {
    if (!runId) return;
    debuggerApi.agentRun(runId).then((res) => {
      const run = res as Record<string, unknown>;
      setData({
        ...run,
        tool_calls: run.tool_calls || [],
        memory_operations: run.memory_operations || [],
        customer_rules_applied: run.customer_rules_applied || [],
        error: run.error || null,
        state_before: run.state_before || null,
        state_after: run.state_after || null,
      });
    }).catch(() => {});
  }, [runId]);
  return { data };
}

export function useLoadHistory(loadId: string) {
  const [data, setData] = useState<unknown>({ events: [], agent_runs: [] });
  useEffect(() => {
    if (!loadId) return;
    debuggerApi.loadHistory(loadId).then(setData).catch(() => {});
  }, [loadId]);
  return { data };
}

export function useMemoryState(scope: string, scopeId: string, memoryType?: string) {
  const [data, setData] = useState<unknown>({ memories: mockMemories });
  useEffect(() => {
    if (!scope || !scopeId) return;
    debuggerApi.memoryState(scope, scopeId, memoryType).then(setData).catch(() => {});
  }, [scope, scopeId, memoryType]);
  return { data };
}

export function useWorkflows() {
  const [data, setData] = useState<unknown>({ workflows: ['delivery_eta_checkpoint', 'confirm_delivery'] });
  useEffect(() => {
    debuggerApi.workflows().then(setData).catch(() => {});
  }, []);
  return { data };
}

export function useTestWorkflow() {
  return {
    mutateAsync: ({ workflow, data }: { workflow: string; data: unknown }) =>
      debuggerApi.testWorkflow(workflow, data),
  };
}

// --- Trace ---

export function useTraceTree(runId?: string) {
  const [data, setData] = useState<unknown>(mockTraceTree);
  useEffect(() => {
    setData(mockTraceTree);
  }, [runId]);
  return { data };
}

// --- Customer Configs ---

export function useCustomerConfigs() {
  const [data, setData] = useState<unknown[]>(mockCustomerConfigs);
  useEffect(() => {
    setData(mockCustomerConfigs);
  }, []);
  return { data };
}
