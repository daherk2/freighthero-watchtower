import React from 'react';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import ReactEChartsCoreModule from 'echarts-for-react/lib/core';
const ReactEChartsCore = (ReactEChartsCoreModule as any).default || ReactEChartsCoreModule;
import * as echarts from 'echarts/core';
import { BarChart, LineChart, PieChart, GaugeChart, SankeyChart, HeatmapChart } from 'echarts/charts';
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
  VisualMapComponent,
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import { useSearchParams } from 'react-router-dom';
import { SectionHeader, StatCard } from '@/components/shared';
// Direct fetch - React Query hooks had loading issues
import type { AgentRun } from '@/types';
import { mockMemories } from '@/api/mockData';
import { authFetch, LOAD_STORAGE_KEY } from '@/api/client';

echarts.use([
  BarChart, LineChart, PieChart, GaugeChart, SankeyChart, HeatmapChart,
  GridComponent, TooltipComponent, LegendComponent, TitleComponent, VisualMapComponent,
  CanvasRenderer,
]);

function TabPanel({ children, value, index }: { children: React.ReactNode; value: number; index: number }) {
  return value === index ? <Box sx={{ pt: 3 }}>{children}</Box> : null;
}

const chartTheme = {
  backgroundColor: 'transparent',
  textStyle: { color: '#94a3b8' },
  legend: { textStyle: { color: '#94a3b8' } },
};

export function Monitoring() {
  const [searchParams] = useSearchParams();
  const loadId = searchParams.get('load_id') || localStorage.getItem(LOAD_STORAGE_KEY) || undefined;
  const [tab, setTab] = React.useState(0);
  const [stats, setStats] = React.useState({
    active_loads: 0, running_agents: 0, failed_agents: 0,
    scheduled_followups: 0, open_issues: 0, active_tasks: 0,
    agent_runs_24h: 0, memory_operations_24h: 0, error_rate_24h: 0.0,
  });
  const [agentRuns, setAgentRuns] = React.useState<AgentRun[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, runsRes] = await Promise.all([
          authFetch('/api/v1/monitoring/dashboard'),
          authFetch(loadId ? `/api/v1/monitoring/agent-runs?load_id=${loadId}` : '/api/v1/monitoring/agent-runs'),
        ]);
        const statsData = await statsRes.json();
        const runsData = await runsRes.json();
        setStats(statsData);
        setAgentRuns(runsData.map((run: AgentRun) => ({
          ...run,
          tool_calls: run.tool_calls || [],
          memory_operations: run.memory_operations || [],
          customer_rules_applied: run.customer_rules_applied || [],
          error: run.error || null,
          state_before: run.state_before || null,
          state_after: run.state_after || null,
        })));
      } catch {
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [loadId]);

  // Agent metrics
  const agentStatusData = [
    { value: stats.active_loads, name: 'Active', itemStyle: { color: '#22c55e' } },
    { value: stats.running_agents, name: 'Running', itemStyle: { color: '#f59e0b' } },
    { value: stats.agent_runs_24h - stats.active_loads - stats.running_agents, name: 'Completed', itemStyle: { color: '#3b82f6' } },
  ];

  // Memory metrics
  const memoryTypeData = ['STM', 'LTM', 'semantic', 'procedural', 'episodic'].map((type) => {
    const count = mockMemories.filter((m) => m.memory_type === type).length;
    const colors: Record<string, string> = { STM: '#06b6d4', LTM: '#3b82f6', semantic: '#8b5cf6', procedural: '#f59e0b', episodic: '#ec4899' };
    return { value: count, name: type, itemStyle: { color: colors[type] } };
  });

  // Workflow metrics
  const workflowData = agentRuns.reduce<Record<string, number>>((acc, run) => {
    acc[run.workflow] = (acc[run.workflow] || 0) + 1;
    return acc;
  }, {});

  // Error metrics
  const errorData = agentRuns
    .filter((r) => r.error)
    .map((r) => ({
      workflow: r.workflow,
      error: r.error,
      run_id: r.run_id,
    }));

  // Token usage (simulated)
  const tokenUsageData = [
    { time: '00:00', tokens: 1200 },
    { time: '04:00', tokens: 800 },
    { time: '08:00', tokens: 2400 },
    { time: '12:00', tokens: 3200 },
    { time: '16:00', tokens: 2800 },
    { time: '20:00', tokens: 1600 },
    { time: 'Now', tokens: 2100 },
  ];

  return (
    <Box>
      <SectionHeader title="Monitoring" subtitle="Agent, memory, workflow, error, and token metrics dashboards" />

      {/* Summary Stats */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 6, md: 3 }}>
          <StatCard title="Agent Runs (24h)" value={stats.agent_runs_24h} color="#3b82f6" />
        </Grid>
        <Grid size={{ xs: 6, md: 3 }}>
          <StatCard title="Active Loads" value={stats.active_loads} color="#22c55e" />
        </Grid>
        <Grid size={{ xs: 6, md: 3 }}>
          <StatCard title="Memory Ops (24h)" value={stats.memory_operations_24h} color="#06b6d4" />
        </Grid>
        <Grid size={{ xs: 6, md: 3 }}>
          <StatCard title="Error Rate" value={`${stats.error_rate_24h}%`} color="#ef4444" />
        </Grid>
      </Grid>

      <Box sx={{ borderBottom: '1px solid #2a3a52', mb: 3 }}>
        <Tabs value={tab} onChange={(_, v) => setTab(v)} variant="scrollable" scrollButtons="auto">
          <Tab label="Agent Metrics" />
          <Tab label="Memory Metrics" />
          <Tab label="Workflow Metrics" />
          <Tab label="Error Metrics" />
          <Tab label="Token Usage" />
          <Tab label="Sankey Flow" />
          <Tab label="Tool Heatmap" />
          <Tab label="Latency" />
        </Tabs>
      </Box>

      <TabPanel value={tab} index={0}>
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 6 }}>
            <Card sx={{ bgcolor: '#1a2235' }}>
              <CardContent>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>Agent Run Status Distribution</Typography>
                <ReactEChartsCore
                  echarts={echarts}
                  option={{
                    ...chartTheme,
                    tooltip: { trigger: 'item' },
                    series: [{
                      type: 'pie',
                      radius: ['40%', '70%'],
                      data: agentStatusData,
                      label: { color: '#94a3b8' },
                    }],
                  }}
                  style={{ height: 300 }}
                />
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <Card sx={{ bgcolor: '#1a2235' }}>
              <CardContent>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>Runs by Workflow</Typography>
                <ReactEChartsCore
                  echarts={echarts}
                  option={{
                    ...chartTheme,
                    tooltip: { trigger: 'axis' },
                    xAxis: {
                      type: 'category',
                      data: Object.keys(workflowData).map((w) => w.replace(/_/g, ' ')),
                      axisLabel: { color: '#94a3b8' },
                    },
                    yAxis: { type: 'value', axisLabel: { color: '#94a3b8' } },
                    series: [{
                      type: 'bar',
                      data: Object.values(workflowData),
                      itemStyle: { color: '#3b82f6', borderRadius: [4, 4, 0, 0] },
                    }],
                    grid: { left: 40, right: 20, bottom: 40, top: 20 },
                  }}
                  style={{ height: 300 }}
                />
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tab} index={1}>
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 6 }}>
            <Card sx={{ bgcolor: '#1a2235' }}>
              <CardContent>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>Memory Type Distribution</Typography>
                <ReactEChartsCore
                  echarts={echarts}
                  option={{
                    ...chartTheme,
                    tooltip: { trigger: 'item' },
                    series: [{
                      type: 'pie',
                      radius: ['40%', '70%'],
                      data: memoryTypeData,
                      label: { color: '#94a3b8' },
                    }],
                  }}
                  style={{ height: 300 }}
                />
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <Card sx={{ bgcolor: '#1a2235' }}>
              <CardContent>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>Memory Operations (24h)</Typography>
                <ReactEChartsCore
                  echarts={echarts}
                  option={{
                    ...chartTheme,
                    tooltip: { trigger: 'axis' },
                    xAxis: {
                      type: 'category',
                      data: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', 'Now'],
                      axisLabel: { color: '#94a3b8' },
                    },
                    yAxis: { type: 'value', axisLabel: { color: '#94a3b8' } },
                    series: [
                      {
                        name: 'Store', type: 'line', smooth: true,
                        data: [12, 8, 24, 32, 28, 16, 21],
                        itemStyle: { color: '#06b6d4' },
                      },
                      {
                        name: 'Retrieve', type: 'line', smooth: true,
                        data: [45, 38, 67, 89, 72, 55, 63],
                        itemStyle: { color: '#3b82f6' },
                      },
                    ],
                    legend: { bottom: 0, textStyle: { color: '#94a3b8' } },
                    grid: { left: 40, right: 20, bottom: 40, top: 20 },
                  }}
                  style={{ height: 300 }}
                />
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tab} index={2}>
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 6 }}>
            <Card sx={{ bgcolor: '#1a2235' }}>
              <CardContent>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>Workflow Execution Count</Typography>
                <ReactEChartsCore
                  echarts={echarts}
                  option={{
                    ...chartTheme,
                    tooltip: { trigger: 'axis' },
                    xAxis: {
                      type: 'category',
                      data: Object.keys(workflowData).map((w) => w.replace(/_/g, ' ')),
                      axisLabel: { color: '#94a3b8', rotate: 30 },
                    },
                    yAxis: { type: 'value', axisLabel: { color: '#94a3b8' } },
                    series: [{
                      type: 'bar',
                      data: Object.values(workflowData),
                      itemStyle: {
                        color: (params: { dataIndex: number }) => {
                          const colors = ['#3b82f6', '#22c55e', '#f59e0b', '#8b5cf6'];
                          return colors[params.dataIndex % colors.length];
                        },
                        borderRadius: [4, 4, 0, 0],
                      },
                    }],
                    grid: { left: 40, right: 20, bottom: 60, top: 20 },
                  }}
                  style={{ height: 300 }}
                />
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <Card sx={{ bgcolor: '#1a2235' }}>
              <CardContent>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>Avg Duration by Workflow</Typography>
                <ReactEChartsCore
                  echarts={echarts}
                  option={{
                    ...chartTheme,
                    tooltip: { trigger: 'axis' },
                    xAxis: {
                      type: 'category',
                      data: Object.keys(workflowData).map((w) => w.replace(/_/g, ' ')),
                      axisLabel: { color: '#94a3b8', rotate: 30 },
                    },
                    yAxis: { type: 'value', axisLabel: { color: '#94a3b8' }, name: 'ms', nameTextStyle: { color: '#94a3b8' } },
                    series: [{
                      type: 'bar',
                      data: Object.keys(workflowData).map((_, i) => 800 + Math.random() * 2200),
                      itemStyle: { color: '#f59e0b', borderRadius: [4, 4, 0, 0] },
                    }],
                    grid: { left: 50, right: 20, bottom: 60, top: 20 },
                  }}
                  style={{ height: 300 }}
                />
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tab} index={3}>
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 6 }}>
            <Card sx={{ bgcolor: '#1a2235' }}>
              <CardContent>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>Error Rate Gauge</Typography>
                <ReactEChartsCore
                  echarts={echarts}
                  option={{
                    ...chartTheme,
                    series: [{
                      type: 'gauge',
                      startAngle: 200,
                      endAngle: -20,
                      min: 0,
                      max: 100,
                      data: [{ value: stats.error_rate_24h, name: 'Error Rate %' }],
                      axisLine: { lineStyle: { width: 20, color: [[0.3, '#22c55e'], [0.7, '#f59e0b'], [1, '#ef4444']] } },
                      axisTick: { lineStyle: { color: '#64748b' } },
                      axisLabel: { color: '#94a3b8' },
                      pointer: { itemStyle: { color: '#e2e8f0' } },
                      detail: { formatter: '{value}%', color: '#e2e8f0', fontSize: 24 },
                      title: { color: '#94a3b8', fontSize: 14 },
                    }],
                  }}
                  style={{ height: 300 }}
                />
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <Card sx={{ bgcolor: '#1a2235' }}>
              <CardContent>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>Recent Errors</Typography>
                {errorData.length === 0 ? (
                  <Typography variant="body2" sx={{ color: '#64748b', textAlign: 'center', py: 4 }}>
                    No errors recorded ✅
                  </Typography>
                ) : (
                  errorData.map((err, i) => (
                    <Box key={i} sx={{ p: 1.5, mb: 1, bgcolor: '#ef444410', borderRadius: 1, border: '1px solid #ef444430' }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Chip label={err.workflow.replace(/_/g, ' ')} size="small" sx={{ bgcolor: '#ef444420', color: '#ef4444' }} />
                        <Typography variant="caption" sx={{ color: '#64748b', fontFamily: 'monospace' }}>
                          {err.run_id.slice(0, 12)}
                        </Typography>
                      </Box>
                      <Typography variant="body2" sx={{ color: '#ef4444', mt: 0.5 }}>{err.error}</Typography>
                    </Box>
                  ))
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      <TabPanel value={tab} index={4}>
        <Grid container spacing={3}>
          <Grid size={{ xs: 12 }}>
            <Card sx={{ bgcolor: '#1a2235' }}>
              <CardContent>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>Token Usage Over Time</Typography>
                <ReactEChartsCore
                  echarts={echarts}
                  option={{
                    ...chartTheme,
                    tooltip: { trigger: 'axis' },
                    xAxis: {
                      type: 'category',
                      data: tokenUsageData.map((d) => d.time),
                      axisLabel: { color: '#94a3b8' },
                    },
                    yAxis: { type: 'value', axisLabel: { color: '#94a3b8' }, name: 'Tokens', nameTextStyle: { color: '#94a3b8' } },
                    series: [
                      {
                        name: 'Tokens',
                        type: 'line',
                        smooth: true,
                        data: tokenUsageData.map((d) => d.tokens),
                        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                          { offset: 0, color: 'rgba(59, 130, 246, 0.3)' },
                          { offset: 1, color: 'rgba(59, 130, 246, 0.05)' },
                        ]) },
                        itemStyle: { color: '#3b82f6' },
                      },
                    ],
                    grid: { left: 60, right: 20, bottom: 40, top: 20 },
                  }}
                  style={{ height: 350 }}
                />
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <Card sx={{ bgcolor: '#1a2235' }}>
              <CardContent>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>Token Usage by Model</Typography>
                <ReactEChartsCore
                  echarts={echarts}
                  option={{
                    ...chartTheme,
                    tooltip: { trigger: 'item' },
                    series: [{
                      type: 'pie',
                      radius: ['40%', '70%'],
                      data: [
                        { value: 65, name: 'GPT-4o', itemStyle: { color: '#3b82f6' } },
                        { value: 25, name: 'GPT-4o-mini', itemStyle: { color: '#22c55e' } },
                        { value: 10, name: 'Embeddings', itemStyle: { color: '#8b5cf6' } },
                      ],
                      label: { color: '#94a3b8' },
                    }],
                  }}
                  style={{ height: 250 }}
                />
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <Card sx={{ bgcolor: '#1a2235' }}>
              <CardContent>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>Cost Estimate (24h)</Typography>
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Typography variant="h3" sx={{ fontWeight: 700, color: '#3b82f6' }}>$12.48</Typography>
                  <Typography variant="body2" sx={{ color: '#64748b', mt: 1 }}>Total estimated cost</Typography>
                  <Box sx={{ display: 'flex', justifyContent: 'center', gap: 3, mt: 3 }}>
                    <Box>
                      <Typography variant="h6" sx={{ fontWeight: 600, color: '#22c55e' }}>142K</Typography>
                      <Typography variant="caption" sx={{ color: '#64748b' }}>Input tokens</Typography>
                    </Box>
                    <Box>
                      <Typography variant="h6" sx={{ fontWeight: 600, color: '#f59e0b' }}>38K</Typography>
                      <Typography variant="caption" sx={{ color: '#64748b' }}>Output tokens</Typography>
                    </Box>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Sankey Flow Diagram */}
      <TabPanel value={tab} index={5}>
        <Grid container spacing={3}>
          <Grid size={{ xs: 12 }}>
            <Card sx={{ bgcolor: '#1a2235' }}>
              <CardContent>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>Event → SOP Branch → Tool Calls Flow</Typography>
                <ReactEChartsCore
                  echarts={echarts}
                  option={{
                    ...chartTheme,
                    tooltip: { trigger: 'item', triggerOn: 'mousemove' },
                    series: [{
                      type: 'sankey',
                      layoutIterations: 32,
                      nodeWidth: 20,
                      nodeGap: 12,
                      left: 40,
                      right: 160,
                      top: 20,
                      bottom: 20,
                      data: [
                        { name: 'Inbound SMS', itemStyle: { color: '#3b82f6' } },
                        { name: 'Inbound Email', itemStyle: { color: '#8b5cf6' } },
                        { name: 'Tracking Ping', itemStyle: { color: '#06b6d4' } },
                        { name: 'Load Update', itemStyle: { color: '#22c55e' } },
                        { name: 'Arrival Confirm', itemStyle: { color: '#f59e0b' } },
                        { name: 'Driver ETA', itemStyle: { color: '#f59e0b' } },
                        { name: 'Load Question', itemStyle: { color: '#f59e0b' } },
                        { name: 'Operational Issue', itemStyle: { color: '#ef4444' } },
                        { name: 'Broker Message', itemStyle: { color: '#64748b' } },
                        { name: 'No Action', itemStyle: { color: '#64748b' } },
                        { name: 'send_message', itemStyle: { color: '#3b82f6' } },
                        { name: 'update_load_state', itemStyle: { color: '#22c55e' } },
                        { name: 'schedule_followup', itemStyle: { color: '#06b6d4' } },
                        { name: 'escalate_to_ops', itemStyle: { color: '#ef4444' } },
                        { name: 'classify_attachment', itemStyle: { color: '#8b5cf6' } },
                        { name: 'cancel_followup', itemStyle: { color: '#f59e0b' } },
                        { name: 'record_sop_branch', itemStyle: { color: '#94a3b8' } },
                        { name: 'no_action', itemStyle: { color: '#64748b' } },
                      ],
                      links: [
                        // Inbound SMS flows
                        { source: 'Inbound SMS', target: 'Arrival Confirm', value: 8 },
                        { source: 'Inbound SMS', target: 'Driver ETA', value: 12 },
                        { source: 'Inbound SMS', target: 'Load Question', value: 6 },
                        { source: 'Inbound SMS', target: 'Operational Issue', value: 3 },
                        // Inbound Email flows
                        { source: 'Inbound Email', target: 'Broker Message', value: 5 },
                        { source: 'Inbound Email', target: 'Load Question', value: 2 },
                        // Tracking Ping flows
                        { source: 'Tracking Ping', target: 'Arrival Confirm', value: 10 },
                        { source: 'Tracking Ping', target: 'No Action', value: 15 },
                        // Load Update flows
                        { source: 'Load Update', target: 'Driver ETA', value: 4 },
                        // SOP Branch → Tool Calls
                        { source: 'Arrival Confirm', target: 'update_load_state', value: 18 },
                        { source: 'Arrival Confirm', target: 'send_message', value: 18 },
                        { source: 'Arrival Confirm', target: 'cancel_followup', value: 18 },
                        { source: 'Driver ETA', target: 'schedule_followup', value: 16 },
                        { source: 'Driver ETA', target: 'send_message', value: 16 },
                        { source: 'Load Question', target: 'send_message', value: 8 },
                        { source: 'Load Question', target: 'escalate_to_ops', value: 2 },
                        { source: 'Operational Issue', target: 'escalate_to_ops', value: 3 },
                        { source: 'Operational Issue', target: 'send_message', value: 3 },
                        { source: 'Broker Message', target: 'no_action', value: 5 },
                        { source: 'No Action', target: 'record_sop_branch', value: 15 },
                        // All branches record SOP
                        { source: 'Arrival Confirm', target: 'record_sop_branch', value: 18 },
                        { source: 'Driver ETA', target: 'record_sop_branch', value: 16 },
                        { source: 'Load Question', target: 'record_sop_branch', value: 8 },
                        { source: 'Operational Issue', target: 'record_sop_branch', value: 3 },
                      ],
                      lineStyle: { color: 'gradient', curveness: 0.5 },
                      label: { color: '#94a3b8', fontSize: 11 },
                    }],
                  }}
                  style={{ height: 450 }}
                />
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <Card sx={{ bgcolor: '#1a2235' }}>
              <CardContent>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>Customer → Workflow Distribution</Typography>
                <ReactEChartsCore
                  echarts={echarts}
                  option={{
                    ...chartTheme,
                    tooltip: { trigger: 'item', triggerOn: 'mousemove' },
                    series: [{
                      type: 'sankey',
                      layoutIterations: 24,
                      nodeWidth: 16,
                      nodeGap: 10,
                      left: 30,
                      right: 120,
                      data: [
                        { name: 'Customer A', itemStyle: { color: '#3b82f6' } },
                        { name: 'Customer B', itemStyle: { color: '#22c55e' } },
                        { name: 'Customer C', itemStyle: { color: '#8b5cf6' } },
                        { name: 'ETA Checkpoint', itemStyle: { color: '#f59e0b' } },
                        { name: 'Confirm Delivery', itemStyle: { color: '#06b6d4' } },
                        { name: 'Email Escalation', itemStyle: { color: '#ef4444' } },
                        { name: 'Slack Notification', itemStyle: { color: '#8b5cf6' } },
                        { name: 'Auto POD', itemStyle: { color: '#22c55e' } },
                        { name: 'Human Review', itemStyle: { color: '#f59e0b' } },
                      ],
                      links: [
                        { source: 'Customer A', target: 'ETA Checkpoint', value: 15 },
                        { source: 'Customer A', target: 'Confirm Delivery', value: 8 },
                        { source: 'Customer B', target: 'ETA Checkpoint', value: 12 },
                        { source: 'Customer B', target: 'Confirm Delivery', value: 6 },
                        { source: 'Customer C', target: 'ETA Checkpoint', value: 10 },
                        { source: 'Customer C', target: 'Confirm Delivery', value: 7 },
                        { source: 'ETA Checkpoint', target: 'Email Escalation', value: 8 },
                        { source: 'ETA Checkpoint', target: 'Slack Notification', value: 12 },
                        { source: 'Confirm Delivery', target: 'Auto POD', value: 12 },
                        { source: 'Confirm Delivery', target: 'Human Review', value: 9 },
                      ],
                      lineStyle: { color: 'gradient', curveness: 0.5 },
                      label: { color: '#94a3b8', fontSize: 11 },
                    }],
                  }}
                  style={{ height: 300 }}
                />
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <Card sx={{ bgcolor: '#1a2235' }}>
              <CardContent>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>State Transition Flow</Typography>
                <ReactEChartsCore
                  echarts={echarts}
                  option={{
                    ...chartTheme,
                    tooltip: { trigger: 'item', triggerOn: 'mousemove' },
                    series: [{
                      type: 'sankey',
                      layoutIterations: 24,
                      nodeWidth: 16,
                      nodeGap: 10,
                      left: 30,
                      right: 120,
                      data: [
                        { name: 'Dispatched', itemStyle: { color: '#64748b' } },
                        { name: 'On Route', itemStyle: { color: '#3b82f6' } },
                        { name: 'At Delivery', itemStyle: { color: '#f59e0b' } },
                        { name: 'Delivered', itemStyle: { color: '#22c55e' } },
                        { name: 'POD Collected', itemStyle: { color: '#06b6d4' } },
                      ],
                      links: [
                        { source: 'Dispatched', target: 'On Route', value: 40 },
                        { source: 'On Route', target: 'At Delivery', value: 32 },
                        { source: 'At Delivery', target: 'Delivered', value: 25 },
                        { source: 'Delivered', target: 'POD Collected', value: 20 },
                      ],
                      lineStyle: { color: 'gradient', curveness: 0.5 },
                      label: { color: '#94a3b8', fontSize: 11 },
                    }],
                  }}
                  style={{ height: 300 }}
                />
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Tool Usage Heatmap */}
      <TabPanel value={tab} index={6}>
        <Grid container spacing={3}>
          <Grid size={{ xs: 12 }}>
            <Card sx={{ bgcolor: '#1a2235' }}>
              <CardContent>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>Tool Usage by Hour and Tool Type</Typography>
                <ReactEChartsCore
                  echarts={echarts}
                  option={{
                    ...chartTheme,
                    tooltip: { position: 'top' },
                    grid: { left: 120, right: 40, bottom: 40, top: 10 },
                    xAxis: {
                      type: 'category',
                      data: ['00', '02', '04', '06', '08', '10', '12', '14', '16', '18', '20', '22'],
                      splitArea: { show: true },
                      axisLabel: { color: '#94a3b8' },
                    },
                    yAxis: {
                      type: 'category',
                      data: ['send_message', 'update_load_state', 'schedule_followup', 'escalate_to_ops', 'classify_attachment', 'cancel_followup', 'record_sop_branch', 'no_action'],
                      axisLabel: { color: '#94a3b8', fontSize: 10 },
                    },
                    visualMap: {
                      min: 0,
                      max: 10,
                      calculable: true,
                      orient: 'horizontal',
                      left: 'center',
                      bottom: 0,
                      inRange: {
                        color: ['#1a2235', '#1e3a5f', '#2563eb', '#3b82f6', '#60a5fa'],
                      },
                      textStyle: { color: '#94a3b8' },
                    },
                    series: [{
                      type: 'heatmap',
                      data: [
                        // [hour, tool, count]
                        ['00', 'send_message', 2], ['02', 'send_message', 1], ['04', 'send_message', 0],
                        ['06', 'send_message', 3], ['08', 'send_message', 7], ['10', 'send_message', 9],
                        ['12', 'send_message', 8], ['14', 'send_message', 10], ['16', 'send_message', 7],
                        ['18', 'send_message', 5], ['20', 'send_message', 3], ['22', 'send_message', 2],
                        ['00', 'update_load_state', 1], ['02', 'update_load_state', 0], ['04', 'update_load_state', 0],
                        ['06', 'update_load_state', 2], ['08', 'update_load_state', 4], ['10', 'update_load_state', 5],
                        ['12', 'update_load_state', 4], ['14', 'update_load_state', 6], ['16', 'update_load_state', 4],
                        ['18', 'update_load_state', 3], ['20', 'update_load_state', 2], ['22', 'update_load_state', 1],
                        ['00', 'schedule_followup', 1], ['02', 'schedule_followup', 0], ['04', 'schedule_followup', 0],
                        ['06', 'schedule_followup', 2], ['08', 'schedule_followup', 5], ['10', 'schedule_followup', 6],
                        ['12', 'schedule_followup', 5], ['14', 'schedule_followup', 7], ['16', 'schedule_followup', 5],
                        ['18', 'schedule_followup', 3], ['20', 'schedule_followup', 2], ['22', 'schedule_followup', 1],
                        ['00', 'escalate_to_ops', 0], ['02', 'escalate_to_ops', 0], ['04', 'escalate_to_ops', 0],
                        ['06', 'escalate_to_ops', 1], ['08', 'escalate_to_ops', 2], ['10', 'escalate_to_ops', 3],
                        ['12', 'escalate_to_ops', 2], ['14', 'escalate_to_ops', 3], ['16', 'escalate_to_ops', 2],
                        ['18', 'escalate_to_ops', 1], ['20', 'escalate_to_ops', 1], ['22', 'escalate_to_ops', 0],
                        ['00', 'classify_attachment', 0], ['02', 'classify_attachment', 0], ['04', 'classify_attachment', 0],
                        ['06', 'classify_attachment', 1], ['08', 'classify_attachment', 2], ['10', 'classify_attachment', 3],
                        ['12', 'classify_attachment', 3], ['14', 'classify_attachment', 4], ['16', 'classify_attachment', 3],
                        ['18', 'classify_attachment', 2], ['20', 'classify_attachment', 1], ['22', 'classify_attachment', 0],
                        ['00', 'cancel_followup', 0], ['02', 'cancel_followup', 0], ['04', 'cancel_followup', 0],
                        ['06', 'cancel_followup', 1], ['08', 'cancel_followup', 2], ['10', 'cancel_followup', 3],
                        ['12', 'cancel_followup', 2], ['14', 'cancel_followup', 3], ['16', 'cancel_followup', 2],
                        ['18', 'cancel_followup', 1], ['20', 'cancel_followup', 1], ['22', 'cancel_followup', 0],
                        ['00', 'record_sop_branch', 2], ['02', 'record_sop_branch', 1], ['04', 'record_sop_branch', 0],
                        ['06', 'record_sop_branch', 3], ['08', 'record_sop_branch', 7], ['10', 'record_sop_branch', 9],
                        ['12', 'record_sop_branch', 8], ['14', 'record_sop_branch', 10], ['16', 'record_sop_branch', 7],
                        ['18', 'record_sop_branch', 5], ['20', 'record_sop_branch', 3], ['22', 'record_sop_branch', 2],
                        ['00', 'no_action', 1], ['02', 'no_action', 0], ['04', 'no_action', 0],
                        ['06', 'no_action', 1], ['08', 'no_action', 2], ['10', 'no_action', 3],
                        ['12', 'no_action', 2], ['14', 'no_action', 3], ['16', 'no_action', 2],
                        ['18', 'no_action', 1], ['20', 'no_action', 1], ['22', 'no_action', 0],
                      ],
                      label: { show: true, color: '#94a3b8', fontSize: 9 },
                      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0, 0, 0, 0.5)' } },
                    }],
                  }}
                  style={{ height: 400 }}
                />
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <Card sx={{ bgcolor: '#1a2235' }}>
              <CardContent>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>Tool Usage by Customer</Typography>
                <ReactEChartsCore
                  echarts={echarts}
                  option={{
                    ...chartTheme,
                    tooltip: { position: 'top' },
                    grid: { left: 120, right: 40, bottom: 40, top: 10 },
                    xAxis: {
                      type: 'category',
                      data: ['Customer A', 'Customer B', 'Customer C'],
                      axisLabel: { color: '#94a3b8' },
                    },
                    yAxis: {
                      type: 'category',
                      data: ['send_message', 'escalate_to_ops', 'schedule_followup', 'classify_attachment'],
                      axisLabel: { color: '#94a3b8', fontSize: 10 },
                    },
                    visualMap: {
                      min: 0,
                      max: 15,
                      calculable: true,
                      orient: 'horizontal',
                      left: 'center',
                      bottom: 0,
                      inRange: { color: ['#1a2235', '#1e3a5f', '#2563eb', '#3b82f6', '#60a5fa'] },
                      textStyle: { color: '#94a3b8' },
                    },
                    series: [{
                      type: 'heatmap',
                      data: [
                        ['Customer A', 'send_message', 12],
                        ['Customer A', 'escalate_to_ops', 4],
                        ['Customer A', 'schedule_followup', 8],
                        ['Customer A', 'classify_attachment', 3],
                        ['Customer B', 'send_message', 10],
                        ['Customer B', 'escalate_to_ops', 6],
                        ['Customer B', 'schedule_followup', 5],
                        ['Customer B', 'classify_attachment', 4],
                        ['Customer C', 'send_message', 14],
                        ['Customer C', 'escalate_to_ops', 3],
                        ['Customer C', 'schedule_followup', 7],
                        ['Customer C', 'classify_attachment', 5],
                      ],
                      label: { show: true, color: '#94a3b8', fontSize: 10 },
                    }],
                  }}
                  style={{ height: 280 }}
                />
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <Card sx={{ bgcolor: '#1a2235' }}>
              <CardContent>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>Tool Call Volume (24h)</Typography>
                <ReactEChartsCore
                  echarts={echarts}
                  option={{
                    ...chartTheme,
                    tooltip: { trigger: 'axis' },
                    xAxis: {
                      type: 'category',
                      data: ['send_msg', 'update_state', 'followup', 'escalate', 'classify', 'cancel', 'record', 'no_action'],
                      axisLabel: { color: '#94a3b8', rotate: 30 },
                    },
                    yAxis: { type: 'value', axisLabel: { color: '#94a3b8' } },
                    series: [{
                      type: 'bar',
                      data: [56, 28, 38, 14, 18, 12, 56, 14],
                      itemStyle: {
                        color: (params: { dataIndex: number }) => {
                          const colors = ['#3b82f6', '#22c55e', '#06b6d4', '#ef4444', '#8b5cf6', '#f59e0b', '#94a3b8', '#64748b'];
                          return colors[params.dataIndex % colors.length];
                        },
                        borderRadius: [4, 4, 0, 0],
                      },
                    }],
                    grid: { left: 40, right: 20, bottom: 60, top: 20 },
                  }}
                  style={{ height: 280 }}
                />
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Latency Charts */}
      <TabPanel value={tab} index={7}>
        <Grid container spacing={3}>
          <Grid size={{ xs: 12 }}>
            <Card sx={{ bgcolor: '#1a2235' }}>
              <CardContent>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>Agent Run Latency Over Time</Typography>
                <ReactEChartsCore
                  echarts={echarts}
                  option={{
                    ...chartTheme,
                    tooltip: { trigger: 'axis' },
                    xAxis: {
                      type: 'category',
                      data: ['00:00', '02:00', '04:00', '06:00', '08:00', '10:00', '12:00', '14:00', '16:00', '18:00', '20:00', '22:00'],
                      axisLabel: { color: '#94a3b8' },
                    },
                    yAxis: {
                      type: 'value',
                      name: 'ms',
                      nameTextStyle: { color: '#94a3b8' },
                      axisLabel: { color: '#94a3b8' },
                    },
                    series: [
                      {
                        name: 'p50',
                        type: 'line',
                        smooth: true,
                        data: [820, 780, 850, 900, 1200, 1500, 1400, 1800, 1600, 1300, 1100, 900],
                        itemStyle: { color: '#22c55e' },
                        lineStyle: { width: 2 },
                      },
                      {
                        name: 'p95',
                        type: 'line',
                        smooth: true,
                        data: [2400, 2200, 2500, 2800, 3600, 4200, 3800, 4800, 4400, 3600, 3200, 2600],
                        itemStyle: { color: '#f59e0b' },
                        lineStyle: { width: 2, type: 'dashed' },
                      },
                      {
                        name: 'p99',
                        type: 'line',
                        smooth: true,
                        data: [4800, 4500, 5200, 5800, 7200, 8500, 7800, 9600, 8800, 7200, 6400, 5200],
                        itemStyle: { color: '#ef4444' },
                        lineStyle: { width: 2, type: 'dotted' },
                      },
                    ],
                    legend: { bottom: 0, textStyle: { color: '#94a3b8' } },
                    grid: { left: 60, right: 20, bottom: 40, top: 20 },
                  }}
                  style={{ height: 350 }}
                />
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <Card sx={{ bgcolor: '#1a2235' }}>
              <CardContent>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>Latency by Workflow</Typography>
                <ReactEChartsCore
                  echarts={echarts}
                  option={{
                    ...chartTheme,
                    tooltip: { trigger: 'axis' },
                    xAxis: {
                      type: 'category',
                      data: ['ETA Checkpoint', 'Confirm Delivery'],
                      axisLabel: { color: '#94a3b8' },
                    },
                    yAxis: {
                      type: 'value',
                      name: 'ms',
                      nameTextStyle: { color: '#94a3b8' },
                      axisLabel: { color: '#94a3b8' },
                    },
                    series: [
                      {
                        name: 'p50',
                        type: 'bar',
                        data: [1100, 1800],
                        itemStyle: { color: '#22c55e', borderRadius: [4, 4, 0, 0] },
                      },
                      {
                        name: 'p95',
                        type: 'bar',
                        data: [3200, 4800],
                        itemStyle: { color: '#f59e0b', borderRadius: [4, 4, 0, 0] },
                      },
                      {
                        name: 'p99',
                        type: 'bar',
                        data: [6400, 9600],
                        itemStyle: { color: '#ef4444', borderRadius: [4, 4, 0, 0] },
                      },
                    ],
                    legend: { bottom: 0, textStyle: { color: '#94a3b8' } },
                    grid: { left: 60, right: 20, bottom: 40, top: 20 },
                  }}
                  style={{ height: 300 }}
                />
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <Card sx={{ bgcolor: '#1a2235' }}>
              <CardContent>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>Tool Call Latency Distribution</Typography>
                <ReactEChartsCore
                  echarts={echarts}
                  option={{
                    ...chartTheme,
                    tooltip: { trigger: 'axis' },
                    xAxis: {
                      type: 'category',
                      data: ['send_msg', 'update_state', 'followup', 'escalate', 'classify', 'cancel', 'memory'],
                      axisLabel: { color: '#94a3b8', rotate: 30 },
                    },
                    yAxis: {
                      type: 'value',
                      name: 'ms',
                      nameTextStyle: { color: '#94a3b8' },
                      axisLabel: { color: '#94a3b8' },
                    },
                    series: [
                      {
                        name: 'Avg',
                        type: 'bar',
                        data: [120, 85, 95, 150, 200, 60, 110],
                        itemStyle: {
                          color: (params: { dataIndex: number }) => {
                            const colors = ['#3b82f6', '#22c55e', '#06b6d4', '#ef4444', '#8b5cf6', '#f59e0b', '#94a3b8'];
                            return colors[params.dataIndex % colors.length];
                          },
                          borderRadius: [4, 4, 0, 0],
                        },
                      },
                    ],
                    grid: { left: 60, right: 20, bottom: 60, top: 20 },
                  }}
                  style={{ height: 300 }}
                />
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <Card sx={{ bgcolor: '#1a2235' }}>
              <CardContent>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>SLA Compliance</Typography>
                <ReactEChartsCore
                  echarts={echarts}
                  option={{
                    ...chartTheme,
                    series: [{
                      type: 'gauge',
                      startAngle: 200,
                      endAngle: -20,
                      min: 0,
                      max: 100,
                      data: [{ value: 94.2, name: 'SLA %' }],
                      axisLine: { lineStyle: { width: 20, color: [[0.8, '#ef4444'], [0.95, '#f59e0b'], [1, '#22c55e']] } },
                      axisTick: { lineStyle: { color: '#64748b' } },
                      axisLabel: { color: '#94a3b8' },
                      pointer: { itemStyle: { color: '#e2e8f0' } },
                      detail: { formatter: '{value}%', color: '#e2e8f0', fontSize: 24 },
                      title: { color: '#94a3b8', fontSize: 14 },
                    }],
                  }}
                  style={{ height: 280 }}
                />
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <Card sx={{ bgcolor: '#1a2235' }}>
              <CardContent>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>Latency Percentiles Summary</Typography>
                <Box sx={{ py: 2 }}>
                  {[
                    { label: 'p50', value: '1.2s', color: '#22c55e' },
                    { label: 'p95', value: '3.8s', color: '#f59e0b' },
                    { label: 'p99', value: '7.6s', color: '#ef4444' },
                    { label: 'SLA Target', value: '5s', color: '#3b82f6' },
                  ].map((item) => (
                    <Box key={item.label} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', py: 1.5, borderBottom: '1px solid #2a3a52' }}>
                      <Typography variant="body2" sx={{ color: '#94a3b8', fontWeight: 500 }}>{item.label}</Typography>
                      <Typography variant="h6" sx={{ color: item.color, fontWeight: 700, fontFamily: 'monospace' }}>{item.value}</Typography>
                    </Box>
                  ))}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>
    </Box>
  );
}