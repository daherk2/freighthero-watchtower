import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppLayout } from '@/components/layout/AppLayout';
import { Dashboard } from '@/screens/Dashboard';
import { LoadList, LoadDetail } from '@/screens/LoadDetail';
import { AgentViewer, AgentRunDetail } from '@/screens/AgentViewer';
import { WorkflowVisualizer } from '@/screens/WorkflowVisualizer';
import { MemoryExplorer } from '@/screens/MemoryExplorer';
import { ToolCallExplorer } from '@/screens/ToolCallExplorer';
import { TraceExplorer } from '@/screens/TraceExplorer';
import { AgentDebugger } from '@/screens/AgentDebugger';
import { Monitoring } from '@/screens/Monitoring';
import { NewLoad } from '@/screens/NewLoad';
import { Simulation } from '@/screens/Simulation';
import { Login } from '@/screens/Login';
import { AUTH_KEY } from '@/api/client';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
});

export default function App() {
  const [authed, setAuthed] = React.useState(() => !!localStorage.getItem(AUTH_KEY));

  if (!authed) {
    return <Login onAuth={() => setAuthed(true)} />;
  }

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/loads" element={<LoadList />} />
            <Route path="/loads/new" element={<NewLoad />} />
            <Route path="/simulation" element={<Simulation />} />
            <Route path="/loads/:id" element={<LoadDetail />} />
            <Route path="/agent" element={<AgentViewer />} />
            <Route path="/agent/:id" element={<AgentRunDetail />} />
            <Route path="/workflow" element={<WorkflowVisualizer />} />
            <Route path="/memory" element={<MemoryExplorer />} />
            <Route path="/tools" element={<ToolCallExplorer />} />
            <Route path="/traces" element={<TraceExplorer />} />
            <Route path="/debugger" element={<AgentDebugger />} />
            <Route path="/monitoring" element={<Monitoring />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
