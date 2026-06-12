import { describe, it, expect } from 'vitest';
import type {
  Load, LoadData, StopInfo, LoadState, EventType, SOPBranch,
  Event, InboundCommunication, TrackingPing, Attachment,
  AgentRun, ToolCallRecord, MemoryOperationRecord, MemoryEntry,
  MemoryMetrics, CustomerConfig, DashboardStats, TraceNode,
  WorkflowNode, WorkflowEdge,
} from '@/types';

describe('Type guards and structure validation', () => {
  describe('Load type', () => {
    it('should accept valid Load object', () => {
      const load: Load = {
        load_id: 'load-001',
        customer_id: 'customer_a',
        external_load_id: 'EXT-123',
        po_number: 'PO-456',
        instructions: 'Deliver to dock B',
        load_data: {},
        current_state: 'on_route_to_delivery',
        current_eta_utc: '2024-01-15T14:00:00Z',
        created_at: '2024-01-15T06:00:00Z',
        updated_at: '2024-01-15T12:00:00Z',
      };
      expect(load.load_id).toBe('load-001');
      expect(load.current_state).toBe('on_route_to_delivery');
    });

    it('should allow null optional fields', () => {
      const load: Load = {
        load_id: 'load-002',
        customer_id: 'customer_b',
        external_load_id: 'EXT-456',
        po_number: null,
        instructions: null,
        load_data: {},
        current_state: 'dispatched',
        current_eta_utc: null,
        created_at: '2024-01-15T06:00:00Z',
        updated_at: '2024-01-15T06:00:00Z',
      };
      expect(load.po_number).toBeNull();
      expect(load.instructions).toBeNull();
      expect(load.current_eta_utc).toBeNull();
    });
  });

  describe('LoadState type', () => {
    it('should accept all valid states', () => {
      const states: LoadState[] = ['dispatched', 'on_route_to_delivery', 'at_delivery', 'confirm_delivery', 'delivered'];
      expect(states).toHaveLength(5);
      states.forEach((state) => {
        expect(typeof state).toBe('string');
      });
    });
  });

  describe('EventType type', () => {
    it('should accept all valid event types', () => {
      const types: EventType[] = ['inbound_communication', 'tracking', 'load_update', 'timer_callback'];
      expect(types).toHaveLength(4);
    });
  });

  describe('AgentRun type', () => {
    it('should accept valid AgentRun object', () => {
      const run: AgentRun = {
        run_id: 'run-001',
        event_id: 'evt-001',
        load_id: 'load-001',
        customer_id: 'customer_a',
        workflow: 'delivery_eta_checkpoint',
        sop_branch: 'tracking_ping',
        customer_rules_applied: ['rule1'],
        tool_calls: [],
        memory_operations: [],
        state_before: 'on_route_to_delivery',
        state_after: 'confirm_delivery',
        status: 'completed',
        error: null,
        trace_id: 'trace-001',
        started_at: '2024-01-15T12:00:00Z',
        completed_at: '2024-01-15T12:01:00Z',
      };
      expect(run.run_id).toBe('run-001');
      expect(run.status).toBe('completed');
    });

    it('should allow null optional fields', () => {
      const run: AgentRun = {
        run_id: 'run-002',
        event_id: 'evt-002',
        load_id: 'load-002',
        customer_id: 'customer_b',
        workflow: 'confirm_delivery',
        sop_branch: null,
        customer_rules_applied: [],
        tool_calls: [],
        memory_operations: [],
        state_before: null,
        state_after: null,
        status: 'pending',
        error: null,
        trace_id: null,
        started_at: '2024-01-15T12:00:00Z',
        completed_at: null,
      };
      expect(run.sop_branch).toBeNull();
      expect(run.completed_at).toBeNull();
    });
  });

  describe('ToolCallRecord type', () => {
    it('should accept valid tool call', () => {
      const tc: ToolCallRecord = {
        tool: 'send_sms',
        arguments: { to: '+1555123456', message: 'ETA update' },
        result: { success: true },
      };
      expect(tc.tool).toBe('send_sms');
    });
  });

  describe('MemoryOperationRecord type', () => {
    it('should accept valid memory operation', () => {
      const op: MemoryOperationRecord = {
        operation: 'store',
        memory_type: 'episodic',
        scope: 'load',
        scope_id: 'load-001',
        content: 'Driver confirmed delivery',
        tags: ['delivery', 'confirmation'],
      };
      expect(op.operation).toBe('store');
    });
  });

  describe('MemoryEntry type', () => {
    it('should accept valid memory entry', () => {
      const mem: MemoryEntry = {
        id: 'mem-001',
        memory_type: 'episodic',
        scope: 'load',
        scope_id: 'load-001',
        content: 'Driver called to confirm ETA',
        summary: 'Driver ETA confirmation',
        tags: ['eta', 'driver'],
        source_event_ids: ['evt-001'],
        confidence: 0.95,
        relevance_score: 0.88,
        access_count: 3,
        content_type: 'text',
        created_at: '2024-01-15T12:00:00Z',
        updated_at: '2024-01-15T12:00:00Z',
        expires_at: null,
      };
      expect(mem.id).toBe('mem-001');
      expect(mem.confidence).toBe(0.95);
    });
  });

  describe('DashboardStats type', () => {
    it('should accept valid stats', () => {
      const stats: DashboardStats = {
        active_loads: 4,
        running_agents: 1,
        failed_agents: 1,
        scheduled_followups: 3,
        open_issues: 2,
        active_tasks: 6,
        agent_runs_24h: 24,
        memory_operations_24h: 156,
        error_rate_24h: 4.2,
      };
      expect(stats.active_loads).toBe(4);
      expect(stats.error_rate_24h).toBe(4.2);
    });
  });

  describe('TraceNode type', () => {
    it('should accept valid trace node', () => {
      const node: TraceNode = {
        id: 'node-1',
        name: 'Event Received',
        type: 'event',
        data: {},
        timestamp: '2024-01-15T12:00:00Z',
        duration_ms: 150,
        status: 'completed',
      };
      expect(node.id).toBe('node-1');
      expect(node.type).toBe('event');
    });

    it('should accept trace node with children', () => {
      const node: TraceNode = {
        id: 'root',
        name: 'Workflow',
        type: 'workflow',
        data: {},
        timestamp: '2024-01-15T12:00:00Z',
        children: [
          {
            id: 'child-1',
            name: 'Agent Step',
            type: 'agent',
            data: {},
            timestamp: '2024-01-15T12:00:01Z',
          },
        ],
      };
      expect(node.children).toHaveLength(1);
    });
  });

  describe('CustomerConfig type', () => {
    it('should accept valid customer config', () => {
      const config: CustomerConfig = {
        customer_id: 'customer_a',
        escalation_channel: 'sms',
        missing_load_info_action: 'ask_driver',
        pod_validation_type: 'strict',
        pod_received_visibility: 'visible',
        delivered_without_pod_visibility: 'hidden',
        delivery_geofence_radius_miles: 5,
        eta_followup_timer_minutes: 30,
        lumper_receipt_handling: 'auto_approve',
        first_arrival_message: 'You have arrived at the delivery location.',
      };
      expect(config.customer_id).toBe('customer_a');
    });
  });
});