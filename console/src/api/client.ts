const API_BASE = '/api/v1';

export const AUTH_KEY = 'freighthero_token';

/** Drop-in replacement for fetch() that injects the stored API key. */
export function authFetch(input: string, init?: RequestInit): Promise<Response> {
  const token = localStorage.getItem(AUTH_KEY) || '';
  return fetch(input, {
    ...init,
    headers: { 'X-API-Key': token, ...init?.headers },
  });
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem(AUTH_KEY) || '';
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': token,
      ...options?.headers,
    },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json();
}

// --- Loads ---
export const loadsApi = {
  list: () => request<unknown[]>('/loads/'),
  get: (id: string) => request<unknown>(`/loads/${id}`),
  create: (data: unknown) => request<unknown>('/loads/', { method: 'POST', body: JSON.stringify(data) }),
  transition: (id: string, state: string) =>
    request<unknown>(`/loads/${id}/transition?new_state=${state}`, { method: 'POST' }),
};

// --- Events ---
export const eventsApi = {
  submitTask: (data: unknown) => request<unknown>('/events/submit-task', { method: 'POST', body: JSON.stringify(data) }),
  inboundCommunication: (data: unknown) =>
    request<unknown>('/events/inbound-communication', { method: 'POST', body: JSON.stringify(data) }),
  tracking: (data: unknown) => request<unknown>('/events/tracking', { method: 'POST', body: JSON.stringify(data) }),
  loadUpdate: (data: unknown) => request<unknown>('/events/load-update', { method: 'POST', body: JSON.stringify(data) }),
};

// --- Monitoring ---
export const monitoringApi = {
  dashboard: () => request<unknown>('/monitoring/dashboard'),
  agentRuns: (loadId?: string) =>
    request<unknown[]>(`/monitoring/agent-runs${loadId ? `?load_id=${loadId}` : ''}`),
  memoryMetrics: (scope?: string, scopeId?: string) =>
    request<unknown>(`/monitoring/memory-metrics?scope=${scope || 'global'}&scope_id=${scopeId || 'all'}`),
  failures: () => request<unknown[]>('/monitoring/failures'),
  scheduledFollowups: (loadId?: string) =>
    request<unknown[]>(`/monitoring/scheduled-followups${loadId ? `?load_id=${loadId}` : ''}`),
};

// --- Debugger ---
export const debuggerApi = {
  agentRun: (runId: string) => request<unknown>(`/debugger/agent-runs/${runId}`),
  loadHistory: (loadId: string) => request<unknown>(`/debugger/loads/${loadId}/history`),
  memoryState: (scope: string, scopeId: string, memoryType?: string) =>
    request<unknown>(`/debugger/memory/${scope}/${scopeId}${memoryType ? `?memory_type=${memoryType}` : ''}`),
  addMemory: (data: unknown) => request<unknown>('/debugger/memory/add', { method: 'POST', body: JSON.stringify(data) }),
  deleteMemory: (id: string) => request<unknown>(`/debugger/memory/${id}`, { method: 'DELETE' }),
  workflows: () => request<unknown>('/debugger/workflows'),
  testWorkflow: (workflow: string, data: unknown) =>
    request<unknown>(`/debugger/workflows/${workflow}/test`, { method: 'POST', body: JSON.stringify(data) }),
};

// --- Health ---
export const healthApi = {
  check: () => request<{ status: string; version: string }>('/health'),
};