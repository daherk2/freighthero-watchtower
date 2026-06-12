export interface Load {
  load_id: string;
  customer_id: string;
  external_load_id: string;
  po_number: string | null;
  instructions: string | null;
  load_data: LoadData;
  current_state: LoadState;
  current_eta_utc: string | null;
  created_at: string;
  updated_at: string;
}

export interface LoadData {
  pickup?: StopInfo;
  delivery?: StopInfo;
  driver?: { name: string; phone: string };
  trailer?: { number: string };
  [key: string]: unknown;
}

export interface StopInfo {
  address: string;
  appointment?: string;
  contact?: { name: string; phone: string };
  geofence?: { latitude: number; longitude: number; radius_miles: number };
  [key: string]: unknown;
}

export type LoadState =
  | 'dispatched'
  | 'on_route_to_delivery'
  | 'at_delivery'
  | 'confirm_delivery'
  | 'delivered';

export type CustomerId = 'customer_a' | 'customer_b' | 'customer_c';

export type EventType =
  | 'inbound_communication'
  | 'tracking'
  | 'load_update'
  | 'timer_callback';

export type SOPBranch =
  | 'tracking_ping'
  | 'arrival_confirmation'
  | 'driver_provides_eta'
  | 'load_information_question'
  | 'operational_issue'
  | 'broker_message'
  | 'no_action'
  | 'attachment_pod'
  | 'attachment_lumper'
  | 'attachment_other'
  | 'unloading_started'
  | 'unloading_not_started'
  | 'delivery_confirmed_no_pod'
  | 'first_arrival_contact';

export type ConfirmDeliveryBranch =
  | 'attachment_pod'
  | 'attachment_lumper'
  | 'attachment_other'
  | 'unloading_started'
  | 'unloading_not_started'
  | 'delivery_confirmed_no_pod'
  | 'first_arrival_contact'
  | 'operational_issue'
  | 'broker_message'
  | 'no_action';

export interface Event {
  event_id: string;
  event_type: EventType;
  load_id: string;
  customer_id: string;
  occurred_at: string;
  event_data: Record<string, unknown>;
}

export interface InboundCommunication extends Event {
  event_type: 'inbound_communication';
  sender_type: 'driver' | 'dispatcher' | 'carrier' | 'broker';
  channel: 'sms' | 'email' | 'edi';
  message: string;
  attachments: Attachment[];
}

export interface TrackingPing extends Event {
  event_type: 'tracking';
  latitude: number;
  longitude: number;
  distance_to_delivery: number;
  timestamp: string;
}

export interface Attachment {
  url: string;
  classification?: string;
  content_type?: string;
}

export interface AgentRun {
  run_id: string;
  event_id: string;
  load_id: string;
  customer_id: string;
  workflow: string;
  sop_branch: string | null;
  customer_rules_applied: string[];
  tool_calls: ToolCallRecord[];
  memory_operations: MemoryOperationRecord[];
  tool_calls_count?: number;
  memory_operations_count?: number;
  state_before: LoadState | null;
  state_after: LoadState | null;
  status: 'pending' | 'running' | 'completed' | 'failed';
  error: string | null;
  trace_id: string | null;
  started_at: string;
  completed_at: string | null;
}

export interface ToolCallRecord {
  tool_call_id?: string;
  event_id?: string;
  load_id?: string;
  tool: string;
  arguments: Record<string, unknown>;
  result: Record<string, unknown>;
  latency_ms?: number;
  timestamp?: string;
  created_at?: string;
}

export interface MemoryOperationRecord {
  operation_id?: string;
  event_id?: string;
  load_id?: string;
  operation: string;
  memory_type: string;
  scope: string;
  scope_id: string;
  content: string;
  tags?: string[];
  result?: Record<string, unknown>;
  created_at?: string;
}

export interface MemoryEntry {
  id: string;
  memory_type: 'episodic' | 'semantic' | 'procedural';
  scope: 'load' | 'customer' | 'global';
  scope_id: string;
  content: string;
  summary: string | null;
  tags: string[];
  source_event_ids: string[];
  confidence: number;
  relevance_score: number;
  access_count: number;
  content_type: string;
  created_at: string;
  updated_at: string;
  expires_at: string | null;
}

export interface MemoryMetrics {
  total_memories: number;
  by_type: Record<string, number>;
  avg_confidence: number;
  avg_relevance: number;
  total_access_count: number;
}

export interface CustomerConfig {
  customer_id: string;
  escalation_channel: string;
  missing_load_info_action: string;
  pod_validation_type: string;
  pod_received_visibility: string;
  delivered_without_pod_visibility: string;
  delivery_geofence_radius_miles: number;
  eta_followup_timer_minutes: number;
  lumper_receipt_handling: string;
  first_arrival_message: string;
}

export interface DashboardStats {
  active_loads: number;
  running_agents: number;
  failed_agents: number;
  scheduled_followups: number;
  open_issues: number;
  active_tasks: number;
  agent_runs_24h: number;
  memory_operations_24h: number;
  error_rate_24h: number;
}

export interface TraceNode {
  id: string;
  name: string;
  type: 'event' | 'workflow' | 'agent' | 'memory' | 'tool' | 'decision' | 'llm' | 'output';
  data: Record<string, unknown>;
  children?: TraceNode[];
  duration_ms?: number;
  timestamp: string;
  status?: string;
  input?: unknown;
  output?: unknown;
}

export interface WorkflowNode {
  id: string;
  type: string;
  data: Record<string, unknown>;
  position: { x: number; y: number };
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
  type?: string;
}