import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import { loadsApi, eventsApi, monitoringApi, debuggerApi, healthApi } from '@/api/client';

const BASE = '/api/v1';

// Mock data
const mockLoad = {
  load_id: 'load-test-001',
  customer_id: 'customer_a',
  external_load_id: 'EXT-TEST',
  po_number: 'PO-TEST',
  instructions: null,
  load_data: {},
  current_state: 'on_route_to_delivery' as const,
  current_eta_utc: null,
  created_at: '2024-01-15T06:00:00Z',
  updated_at: '2024-01-15T12:00:00Z',
};

const server = setupServer(
  http.get(`${BASE}/loads/`, () => HttpResponse.json({ active_loads: [mockLoad], active_loads_count: 1 })),
  http.get(`${BASE}/loads/:id`, () => HttpResponse.json(mockLoad)),
  http.post(`${BASE}/loads/`, async () => HttpResponse.json(mockLoad)),
  http.post(`${BASE}/loads/:id/transition`, () => HttpResponse.json(mockLoad)),
  http.post(`${BASE}/events/submit-task`, () => HttpResponse.json({ status: 'ok' })),
  http.post(`${BASE}/events/inbound-communication`, () => HttpResponse.json({ status: 'ok' })),
  http.post(`${BASE}/events/tracking`, () => HttpResponse.json({ status: 'ok' })),
  http.post(`${BASE}/events/load-update`, () => HttpResponse.json({ status: 'ok' })),
  http.get(`${BASE}/monitoring/dashboard`, () => HttpResponse.json({ active_loads: 4, running_agents: 1, failed_agents: 1, scheduled_followups: 3, open_issues: 2, active_tasks: 6, agent_runs_24h: 24, memory_operations_24h: 156, error_rate_24h: 4.2 })),
  http.get(`${BASE}/monitoring/agent-runs`, () => HttpResponse.json([])),
  http.get(`${BASE}/monitoring/memory-metrics`, () => HttpResponse.json({})),
  http.get(`${BASE}/monitoring/failures`, () => HttpResponse.json([])),
  http.get(`${BASE}/monitoring/scheduled-followups`, () => HttpResponse.json([])),
  http.get(`${BASE}/debugger/agent-runs/:id`, () => HttpResponse.json({})),
  http.get(`${BASE}/debugger/loads/:id/history`, () => HttpResponse.json({})),
  http.get(`${BASE}/debugger/memory/:scope/:scopeId`, () => HttpResponse.json({})),
  http.post(`${BASE}/debugger/memory/add`, () => HttpResponse.json({})),
  http.delete(`${BASE}/debugger/memory/:id`, () => HttpResponse.json({})),
  http.get(`${BASE}/debugger/workflows`, () => HttpResponse.json([])),
  http.post(`${BASE}/debugger/workflows/:workflow/test`, () => HttpResponse.json({})),
  http.get(`${BASE}/health`, () => HttpResponse.json({ status: 'ok', version: '1.0.0' }))
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('loadsApi', () => {
  it('should fetch loads list', async () => {
    const result = await loadsApi.list();
    expect(result).toHaveProperty('active_loads');
    expect(result).toHaveProperty('active_loads_count');
  });

  it('should fetch a single load', async () => {
    const result = await loadsApi.get('load-test-001');
    expect(result).toHaveProperty('load_id', 'load-test-001');
  });

  it('should create a load', async () => {
    const result = await loadsApi.create({ customer_id: 'customer_a' });
    expect(result).toHaveProperty('load_id');
  });

  it('should transition a load', async () => {
    const result = await loadsApi.transition('load-test-001', 'confirm_delivery');
    expect(result).toHaveProperty('load_id');
  });
});

describe('eventsApi', () => {
  it('should submit a task', async () => {
    const result = await eventsApi.submitTask({ load_id: 'load-001' });
    expect(result).toHaveProperty('status');
  });

  it('should submit inbound communication', async () => {
    const result = await eventsApi.inboundCommunication({ load_id: 'load-001', message: 'test' });
    expect(result).toHaveProperty('status');
  });

  it('should submit tracking ping', async () => {
    const result = await eventsApi.tracking({ load_id: 'load-001', latitude: 0, longitude: 0 });
    expect(result).toHaveProperty('status');
  });

  it('should submit load update', async () => {
    const result = await eventsApi.loadUpdate({ load_id: 'load-001' });
    expect(result).toHaveProperty('status');
  });
});

describe('monitoringApi', () => {
  it('should fetch dashboard stats', async () => {
    const result = await monitoringApi.dashboard();
    expect(result).toHaveProperty('active_loads');
  });

  it('should fetch agent runs', async () => {
    const result = await monitoringApi.agentRuns();
    expect(Array.isArray(result)).toBe(true);
  });

  it('should fetch agent runs with loadId filter', async () => {
    const result = await monitoringApi.agentRuns('load-001');
    expect(Array.isArray(result)).toBe(true);
  });

  it('should fetch memory metrics', async () => {
    const result = await monitoringApi.memoryMetrics('load', 'load-001');
    expect(result).toBeDefined();
  });

  it('should fetch failures', async () => {
    const result = await monitoringApi.failures();
    expect(Array.isArray(result)).toBe(true);
  });

  it('should fetch scheduled followups', async () => {
    const result = await monitoringApi.scheduledFollowups();
    expect(Array.isArray(result)).toBe(true);
  });
});

describe('debuggerApi', () => {
  it('should fetch agent run', async () => {
    const result = await debuggerApi.agentRun('run-001');
    expect(result).toBeDefined();
  });

  it('should fetch load history', async () => {
    const result = await debuggerApi.loadHistory('load-001');
    expect(result).toBeDefined();
  });

  it('should fetch memory state', async () => {
    const result = await debuggerApi.memoryState('load', 'load-001');
    expect(result).toBeDefined();
  });

  it('should add memory', async () => {
    const result = await debuggerApi.addMemory({ scope: 'load', scope_id: 'load-001', content: 'test' });
    expect(result).toBeDefined();
  });

  it('should delete memory', async () => {
    const result = await debuggerApi.deleteMemory('mem-001');
    expect(result).toBeDefined();
  });

  it('should fetch workflows', async () => {
    const result = await debuggerApi.workflows();
    expect(Array.isArray(result)).toBe(true);
  });

  it('should test workflow', async () => {
    const result = await debuggerApi.testWorkflow('delivery_eta_checkpoint', { load_id: 'load-001' });
    expect(result).toBeDefined();
  });
});

describe('healthApi', () => {
  it('should check health', async () => {
    const result = await healthApi.check();
    expect(result).toHaveProperty('status', 'ok');
    expect(result).toHaveProperty('version', '1.0.0');
  });
});

describe('API error handling', () => {
  it('should throw on non-OK response', async () => {
    server.use(
      http.get(`${BASE}/loads/`, () => new HttpResponse(null, { status: 500 }))
    );
    await expect(loadsApi.list()).rejects.toThrow('API 500');
  });

  it('should throw on 404 response', async () => {
    server.use(
      http.get(`${BASE}/loads/:id`, () => new HttpResponse(null, { status: 404 }))
    );
    await expect(loadsApi.get('nonexistent')).rejects.toThrow('API 404');
  });
});