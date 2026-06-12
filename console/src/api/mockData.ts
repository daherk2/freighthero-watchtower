import type { Load, AgentRun, Event, MemoryEntry, DashboardStats, TraceNode } from '@/types';

const now = new Date().toISOString();

export const mockLoads: Load[] = [
  {
    load_id: 'load-001',
    customer_id: 'customer_a',
    external_load_id: 'EXT-12345',
    po_number: 'PO-67890',
    instructions: 'Deliver to dock B, call 30 min before arrival',
    load_data: {
      pickup: { address: '123 Shipper St, Chicago, IL 60601', appointment: '2024-01-15T08:00:00Z' },
      delivery: { address: '456 Receiver Ave, Milwaukee, WI 53201', appointment: '2024-01-15T14:00:00Z', contact: { name: 'John Receiver', phone: '+1555123456' } },
      driver: { name: 'Jane Driver', phone: '+1555789012' },
      trailer: { number: 'TRAIL-001' },
    },
    current_state: 'on_route_to_delivery',
    current_eta_utc: '2024-01-15T13:30:00Z',
    created_at: '2024-01-15T06:00:00Z',
    updated_at: '2024-01-15T12:30:00Z',
  },
  {
    load_id: 'load-002',
    customer_id: 'customer_b',
    external_load_id: 'EXT-23456',
    po_number: 'PO-54321',
    instructions: 'POD required, lumper receipt expected',
    load_data: {
      pickup: { address: '789 Shipper Blvd, Detroit, MI 48201', appointment: '2024-01-15T09:00:00Z' },
      delivery: { address: '321 Receiver Rd, Grand Rapids, MI 49501', appointment: '2024-01-15T15:00:00Z' },
      driver: { name: 'Bob Trucker', phone: '+1555987654' },
    },
    current_state: 'confirm_delivery',
    current_eta_utc: '2024-01-15T14:45:00Z',
    created_at: '2024-01-15T07:00:00Z',
    updated_at: '2024-01-15T14:00:00Z',
  },
  {
    load_id: 'load-003',
    customer_id: 'customer_c',
    external_load_id: 'EXT-34567',
    po_number: 'PO-11111',
    instructions: 'Auto-approve lumper, tight geofence',
    load_data: {
      pickup: { address: '555 Shipper Ln, Minneapolis, MN 55401', appointment: '2024-01-15T07:00:00Z' },
      delivery: { address: '777 Receiver Way, Madison, WI 53701', appointment: '2024-01-15T12:00:00Z' },
      driver: { name: 'Carol Hauler', phone: '+1555345678' },
    },
    current_state: 'at_delivery',
    current_eta_utc: null,
    created_at: '2024-01-15T05:00:00Z',
    updated_at: '2024-01-15T11:30:00Z',
  },
  {
    load_id: 'load-004',
    customer_id: 'customer_a',
    external_load_id: 'EXT-45678',
    po_number: 'PO-22222',
    instructions: 'Standard delivery, no special instructions',
    load_data: {
      pickup: { address: '888 Shipper Ct, Columbus, OH 43201', appointment: '2024-01-15T10:00:00Z' },
      delivery: { address: '999 Receiver Pl, Cleveland, OH 44101', appointment: '2024-01-15T16:00:00Z' },
      driver: { name: 'Dave Wheeler', phone: '+1555456789' },
    },
    current_state: 'dispatched',
    current_eta_utc: '2024-01-15T15:30:00Z',
    created_at: '2024-01-15T08:00:00Z',
    updated_at: '2024-01-15T08:00:00Z',
  },
];

export const mockAgentRuns: AgentRun[] = [
  {
    run_id: 'run-001',
    event_id: 'evt-001',
    load_id: 'load-001',
    customer_id: 'customer_a',
    workflow: 'delivery_eta_checkpoint',
    sop_branch: 'driver_provides_eta',
    customer_rules_applied: ['escalation_channel', 'eta_followup_timer_minutes'],
    tool_calls: [
      { tool: 'record_sop_branch', arguments: { branch: 'driver_provides_eta', reason: 'Driver provided ETA' }, result: { record_id: 'branch-001' } },
      { tool: 'send_message', arguments: { channel: 'sms', recipient: 'driver', message: 'Thanks for the ETA update.' }, result: { message_id: 'msg-001', status: 'sent' } },
      { tool: 'schedule_followup', arguments: { followup_type: 'eta_check', delay_minutes: 30 }, result: { timer_id: 'timer-001', status: 'scheduled' } },
    ],
    memory_operations: [
      { operation: 'add', memory_type: 'semantic', scope: 'load', scope_id: 'load-001', content: 'Driver provided ETA of 30 minutes', tags: ['eta', 'driver_update'] },
    ],
    state_before: 'on_route_to_delivery',
    state_after: null,
    status: 'completed',
    error: null,
    trace_id: 'trace-001',
    started_at: '2024-01-15T12:30:00Z',
    completed_at: '2024-01-15T12:30:05Z',
  },
  {
    run_id: 'run-002',
    event_id: 'evt-002',
    load_id: 'load-002',
    customer_id: 'customer_b',
    workflow: 'confirm_delivery',
    sop_branch: 'attachment_pod',
    customer_rules_applied: ['pod_validation_type', 'pod_received_visibility'],
    tool_calls: [
      { tool: 'record_sop_branch', arguments: { branch: 'attachment_pod', reason: 'POD document received' }, result: { record_id: 'branch-002' } },
      { tool: 'classify_attachment', arguments: { attachment_url: 'https://example.com/pod.pdf' }, result: { classification: 'pod', confidence: 0.95 } },
      { tool: 'update_load_state', arguments: { new_state: 'delivered', reason: 'POD received and validated' }, result: { load_id: 'load-002', new_state: 'delivered' } },
    ],
    memory_operations: [
      { operation: 'add', memory_type: 'episodic', scope: 'load', scope_id: 'load-002', content: 'POD document received and classified as valid', tags: ['pod', 'delivery_confirmation'] },
    ],
    state_before: 'confirm_delivery',
    state_after: 'delivered',
    status: 'completed',
    error: null,
    trace_id: 'trace-002',
    started_at: '2024-01-15T14:05:00Z',
    completed_at: '2024-01-15T14:05:08Z',
  },
  {
    run_id: 'run-003',
    event_id: 'evt-003',
    load_id: 'load-001',
    customer_id: 'customer_a',
    workflow: 'delivery_eta_checkpoint',
    sop_branch: 'operational_issue',
    customer_rules_applied: ['escalation_channel'],
    tool_calls: [
      { tool: 'record_sop_branch', arguments: { branch: 'operational_issue', reason: 'Driver reports breakdown' }, result: { record_id: 'branch-003' } },
      { tool: 'escalate_to_ops', arguments: { issue_type: 'operational', details: 'Driver reports truck breakdown on I-94', channel: 'internal' }, result: { escalation_id: 'esc-001', status: 'escalated' } },
    ],
    memory_operations: [
      { operation: 'add', memory_type: 'episodic', scope: 'load', scope_id: 'load-001', content: 'Driver reported truck breakdown on I-94', tags: ['operational_issue', 'breakdown'] },
    ],
    state_before: 'on_route_to_delivery',
    state_after: null,
    status: 'completed',
    error: null,
    trace_id: 'trace-003',
    started_at: '2024-01-15T13:00:00Z',
    completed_at: '2024-01-15T13:00:06Z',
  },
  {
    run_id: 'run-004',
    event_id: 'evt-004',
    load_id: 'load-003',
    customer_id: 'customer_c',
    workflow: 'confirm_delivery',
    sop_branch: null,
    customer_rules_applied: [],
    tool_calls: [],
    memory_operations: [],
    state_before: 'at_delivery',
    state_after: null,
    status: 'failed',
    error: 'LLM timeout after 30s',
    trace_id: 'trace-004',
    started_at: '2024-01-15T11:45:00Z',
    completed_at: null,
  },
];

export const mockEvents: Event[] = [
  { event_id: 'evt-001', event_type: 'inbound_communication', load_id: 'load-001', customer_id: 'customer_a', occurred_at: '2024-01-15T12:30:00Z', event_data: { sender_type: 'driver', channel: 'sms', message: 'I will be there in about 30 minutes' } },
  { event_id: 'evt-002', event_type: 'inbound_communication', load_id: 'load-002', customer_id: 'customer_b', occurred_at: '2024-01-15T14:05:00Z', event_data: { sender_type: 'driver', channel: 'sms', message: 'Here is the POD', attachments: [{ url: 'https://example.com/pod.pdf', classification: 'pod' }] } },
  { event_id: 'evt-003', event_type: 'inbound_communication', load_id: 'load-001', customer_id: 'customer_a', occurred_at: '2024-01-15T13:00:00Z', event_data: { sender_type: 'driver', channel: 'sms', message: 'Truck broke down on I-94' } },
  { event_id: 'evt-004', event_type: 'tracking', load_id: 'load-001', customer_id: 'customer_a', occurred_at: '2024-01-15T11:00:00Z', event_data: { latitude: 43.0389, longitude: -87.9065, distance_to_delivery: 5.2 } },
  { event_id: 'evt-005', event_type: 'tracking', load_id: 'load-001', customer_id: 'customer_a', occurred_at: '2024-01-15T12:00:00Z', event_data: { latitude: 43.05, longitude: -87.92, distance_to_delivery: 2.1 } },
];

export const mockMemories: MemoryEntry[] = [
  { id: 'mem-001', memory_type: 'episodic', scope: 'load', scope_id: 'load-001', content: 'Driver provided ETA of 30 minutes', summary: null, tags: ['eta', 'driver_update'], source_event_ids: ['evt-001'], confidence: 0.95, relevance_score: 0.9, access_count: 3, content_type: 'fact', created_at: '2024-01-15T12:30:05Z', updated_at: '2024-01-15T12:30:05Z', expires_at: null },
  { id: 'mem-002', memory_type: 'episodic', scope: 'load', scope_id: 'load-001', content: 'Driver reported truck breakdown on I-94', summary: null, tags: ['operational_issue', 'breakdown'], source_event_ids: ['evt-003'], confidence: 0.98, relevance_score: 0.95, access_count: 5, content_type: 'fact', created_at: '2024-01-15T13:00:06Z', updated_at: '2024-01-15T13:00:06Z', expires_at: null },
  { id: 'mem-003', memory_type: 'semantic', scope: 'customer', scope_id: 'customer_a', content: 'Customer A prefers internal escalation channel', summary: null, tags: ['escalation', 'customer_preference'], source_event_ids: [], confidence: 1.0, relevance_score: 0.85, access_count: 12, content_type: 'fact', created_at: '2024-01-10T00:00:00Z', updated_at: '2024-01-15T12:00:00Z', expires_at: null },
  { id: 'mem-004', memory_type: 'semantic', scope: 'customer', scope_id: 'customer_a', content: 'Customer A uses 30-minute ETA follow-up timer', summary: null, tags: ['eta', 'timer', 'customer_preference'], source_event_ids: [], confidence: 1.0, relevance_score: 0.8, access_count: 8, content_type: 'fact', created_at: '2024-01-10T00:00:00Z', updated_at: '2024-01-15T12:00:00Z', expires_at: null },
  { id: 'mem-005', memory_type: 'procedural', scope: 'global', scope_id: 'all', content: 'When driver arrives, transition load to at_delivery and begin confirm delivery workflow', summary: null, tags: ['arrival', 'state_transition'], source_event_ids: [], confidence: 0.95, relevance_score: 0.9, access_count: 25, content_type: 'procedure', created_at: '2024-01-01T00:00:00Z', updated_at: '2024-01-15T00:00:00Z', expires_at: null },
  { id: 'mem-006', memory_type: 'episodic', scope: 'load', scope_id: 'load-002', content: 'POD document received and classified as valid', summary: null, tags: ['pod', 'delivery_confirmation'], source_event_ids: ['evt-002'], confidence: 0.95, relevance_score: 0.92, access_count: 2, content_type: 'fact', created_at: '2024-01-15T14:05:08Z', updated_at: '2024-01-15T14:05:08Z', expires_at: null },
];

export const mockDashboardStats: DashboardStats = {
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

export const mockTraceTree: TraceNode = {
  id: 'root',
  name: 'Event Processing',
  type: 'event',
  data: { event_type: 'inbound_communication', message: 'I will be there in about 30 minutes' },
  timestamp: '2024-01-15T12:30:00Z',
  duration_ms: 5000,
  children: [
    {
      id: 'workflow-1',
      name: 'ETA Checkpoint Workflow',
      type: 'workflow',
      data: { workflow: 'delivery_eta_checkpoint' },
      timestamp: '2024-01-15T12:30:01Z',
      duration_ms: 4800,
      children: [
        {
          id: 'agent-1',
          name: 'Agent Decision',
          type: 'agent',
          data: { sop_branch: 'driver_provides_eta', reason: 'Driver provided ETA' },
          timestamp: '2024-01-15T12:30:02Z',
          duration_ms: 2000,
          children: [
            {
              id: 'memory-1',
              name: 'Memory: Add Semantic',
              type: 'memory',
              data: { operation: 'add', memory_type: 'semantic', content: 'Driver provided ETA of 30 minutes' },
              timestamp: '2024-01-15T12:30:03Z',
              duration_ms: 150,
            },
            {
              id: 'tool-1',
              name: 'Tool: send_message',
              type: 'tool',
              data: { tool: 'send_message', channel: 'sms', message: 'Thanks for the ETA update.' },
              timestamp: '2024-01-15T12:30:03.5Z',
              duration_ms: 800,
            },
            {
              id: 'tool-2',
              name: 'Tool: schedule_followup',
              type: 'tool',
              data: { tool: 'schedule_followup', followup_type: 'eta_check', delay_minutes: 30 },
              timestamp: '2024-01-15T12:30:04.5Z',
              duration_ms: 500,
            },
          ],
        },
      ],
    },
  ],
};

export const mockCustomerConfigs: Record<string, unknown> = {
  customer_a: { escalation_channel: 'internal', pod_validation_type: 'automatic', delivery_geofence_radius_miles: 1, eta_followup_timer_minutes: 30 },
  customer_b: { escalation_channel: 'sms', pod_validation_type: 'manual', delivery_geofence_radius_miles: 2, eta_followup_timer_minutes: 60 },
  customer_c: { escalation_channel: 'email', pod_validation_type: 'automatic', delivery_geofence_radius_miles: 0.5, eta_followup_timer_minutes: 15 },
};