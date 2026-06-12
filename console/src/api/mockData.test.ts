import { describe, it, expect } from 'vitest';
import { mockLoads, mockAgentRuns, mockEvents, mockMemories, mockDashboardStats, mockTraceTree, mockCustomerConfigs } from '@/api/mockData';

describe('mockData', () => {
  describe('mockLoads', () => {
    it('should have at least one load', () => {
      expect(mockLoads.length).toBeGreaterThan(0);
    });

    it('should have required load fields', () => {
      const load = mockLoads[0];
      expect(load).toHaveProperty('load_id');
      expect(load).toHaveProperty('customer_id');
      expect(load).toHaveProperty('external_load_id');
      expect(load).toHaveProperty('current_state');
      expect(load).toHaveProperty('load_data');
      expect(load).toHaveProperty('created_at');
      expect(load).toHaveProperty('updated_at');
    });

    it('should have valid load states', () => {
      const validStates = ['dispatched', 'on_route_to_delivery', 'at_delivery', 'confirm_delivery', 'delivered'];
      mockLoads.forEach((load) => {
        expect(validStates).toContain(load.current_state);
      });
    });

    it('should have unique load IDs', () => {
      const ids = mockLoads.map((l) => l.load_id);
      expect(new Set(ids).size).toBe(ids.length);
    });
  });

  describe('mockAgentRuns', () => {
    it('should have at least one agent run', () => {
      expect(mockAgentRuns.length).toBeGreaterThan(0);
    });

    it('should have required agent run fields', () => {
      const run = mockAgentRuns[0];
      expect(run).toHaveProperty('run_id');
      expect(run).toHaveProperty('event_id');
      expect(run).toHaveProperty('load_id');
      expect(run).toHaveProperty('customer_id');
      expect(run).toHaveProperty('workflow');
      expect(run).toHaveProperty('tool_calls');
      expect(run).toHaveProperty('memory_operations');
      expect(run).toHaveProperty('status');
      expect(run).toHaveProperty('started_at');
    });

    it('should have valid statuses', () => {
      const validStatuses = ['pending', 'running', 'completed', 'failed'];
      mockAgentRuns.forEach((run) => {
        expect(validStatuses).toContain(run.status);
      });
    });

    it('should have tool calls as arrays', () => {
      mockAgentRuns.forEach((run) => {
        expect(Array.isArray(run.tool_calls)).toBe(true);
      });
    });

    it('should have memory operations as arrays', () => {
      mockAgentRuns.forEach((run) => {
        expect(Array.isArray(run.memory_operations)).toBe(true);
      });
    });
  });

  describe('mockEvents', () => {
    it('should have at least one event', () => {
      expect(mockEvents.length).toBeGreaterThan(0);
    });

    it('should have required event fields', () => {
      const event = mockEvents[0];
      expect(event).toHaveProperty('event_id');
      expect(event).toHaveProperty('event_type');
      expect(event).toHaveProperty('load_id');
      expect(event).toHaveProperty('customer_id');
      expect(event).toHaveProperty('occurred_at');
      expect(event).toHaveProperty('event_data');
    });
  });

  describe('mockMemories', () => {
    it('should have at least one memory', () => {
      expect(mockMemories.length).toBeGreaterThan(0);
    });

    it('should have required memory fields', () => {
      const mem = mockMemories[0];
      expect(mem).toHaveProperty('id');
      expect(mem).toHaveProperty('memory_type');
      expect(mem).toHaveProperty('scope');
      expect(mem).toHaveProperty('scope_id');
      expect(mem).toHaveProperty('content');
      expect(mem).toHaveProperty('tags');
      expect(mem).toHaveProperty('confidence');
      expect(mem).toHaveProperty('relevance_score');
      expect(mem).toHaveProperty('created_at');
    });

    it('should have confidence between 0 and 1', () => {
      mockMemories.forEach((mem) => {
        expect(mem.confidence).toBeGreaterThanOrEqual(0);
        expect(mem.confidence).toBeLessThanOrEqual(1);
      });
    });

    it('should have relevance_score between 0 and 1', () => {
      mockMemories.forEach((mem) => {
        expect(mem.relevance_score).toBeGreaterThanOrEqual(0);
        expect(mem.relevance_score).toBeLessThanOrEqual(1);
      });
    });
  });

  describe('mockDashboardStats', () => {
    it('should have all required fields', () => {
      expect(mockDashboardStats).toHaveProperty('active_loads');
      expect(mockDashboardStats).toHaveProperty('running_agents');
      expect(mockDashboardStats).toHaveProperty('failed_agents');
      expect(mockDashboardStats).toHaveProperty('scheduled_followups');
      expect(mockDashboardStats).toHaveProperty('open_issues');
      expect(mockDashboardStats).toHaveProperty('active_tasks');
      expect(mockDashboardStats).toHaveProperty('agent_runs_24h');
      expect(mockDashboardStats).toHaveProperty('memory_operations_24h');
      expect(mockDashboardStats).toHaveProperty('error_rate_24h');
    });

    it('should have numeric values', () => {
      expect(typeof mockDashboardStats.active_loads).toBe('number');
      expect(typeof mockDashboardStats.error_rate_24h).toBe('number');
    });
  });

  describe('mockTraceTree', () => {
    it('should have required trace node fields', () => {
      expect(mockTraceTree).toHaveProperty('id');
      expect(mockTraceTree).toHaveProperty('name');
      expect(mockTraceTree).toHaveProperty('type');
      expect(mockTraceTree).toHaveProperty('timestamp');
    });

    it('should have children array', () => {
      expect(Array.isArray(mockTraceTree.children)).toBe(true);
    });
  });

  describe('mockCustomerConfigs', () => {
    it('should have at least one config', () => {
      expect(Object.keys(mockCustomerConfigs).length).toBeGreaterThan(0);
    });

    it('should have required config fields', () => {
      const key = Object.keys(mockCustomerConfigs)[0];
      const config = mockCustomerConfigs[key] as Record<string, unknown>;
      expect(config).toHaveProperty('escalation_channel');
      expect(config).toHaveProperty('pod_validation_type');
    });
  });
});