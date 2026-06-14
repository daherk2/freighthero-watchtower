import { useState, useEffect } from 'react';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Chip from '@mui/material/Chip';
import TextField from '@mui/material/TextField';
import InputAdornment from '@mui/material/InputAdornment';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import LinearProgress from '@mui/material/LinearProgress';
import SearchIcon from '@mui/icons-material/Search';
import { SectionHeader, LoadSelector } from '@/components/shared';
import { useMemoryState } from '@/api/hooks';
import { authFetch } from '@/api/client';
import { mockMemories } from '@/api/mockData';
import type { MemoryEntry, Load, AgentRun } from '@/types';
import { memoryTypeColors } from '@/theme';

function TabPanel({ children, value, index }: { children: React.ReactNode; value: number; index: number }) {
  return value === index ? <Box sx={{ pt: 3 }}>{children}</Box> : null;
}

export function MemoryExplorer() {
  const [tab, setTab] = useState(0);
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState<string | null>(null);
  const [selectedLoadId, setSelectedLoadId] = useState<string | null>(null);
  const [loadMemories, setLoadMemories] = useState<MemoryEntry[]>([]);
  const { data: memoryState } = useMemoryState(
    selectedLoadId ? 'load' : 'global',
    selectedLoadId || 'all'
  );
  const apiMemories = ((memoryState as { memories?: MemoryEntry[] })?.memories as MemoryEntry[]) || [];
  const memories = apiMemories.length > 0 ? apiMemories : (selectedLoadId ? loadMemories : mockMemories);

  // Fetch memories for selected load from debugger API, falling back to agent run memory operations
  useEffect(() => {
    if (!selectedLoadId) {
      setLoadMemories([]);
      return;
    }
    authFetch(`/api/v1/debugger/memory/load/${selectedLoadId}`)
      .then((res) => res.json())
      .then(async (data) => {
        const mems = (data.memories || []) as MemoryEntry[];
        if (mems.length > 0) {
          setLoadMemories(mems);
          return;
        }
        // Fallback: extract memory operations from agent runs
        try {
          const runsRes = await authFetch(`/api/v1/monitoring/agent-runs?load_id=${selectedLoadId}`);
          const runs = await runsRes.json();
          const runsWithMemOps = runs.filter((r: AgentRun) => (r.memory_operations_count ?? 0) > 0);
          const detailedMems: MemoryEntry[] = [];
          for (const run of runsWithMemOps) {
            try {
              const detailRes = await authFetch(`/api/v1/debugger/agent-runs/${run.run_id}`);
              const detail = await detailRes.json();
              for (const op of (detail.memory_operations || [])) {
                detailedMems.push({
                  id: op.operation_id || `${run.run_id}-${op.memory_type}-${op.operation}`,
                  memory_type: op.memory_type || 'semantic',
                  scope: op.scope || 'load',
                  scope_id: op.scope_id || selectedLoadId,
                  content: op.content || '',
                  tags: op.tags || [],
                  confidence: op.confidence || 1.0,
                  created_at: op.created_at || run.started_at,
                  updated_at: op.updated_at || run.started_at,
                } as MemoryEntry);
              }
            } catch { /* skip failed detail fetches */ }
          }
          setLoadMemories(detailedMems);
        } catch {
          setLoadMemories([]);
        }
      })
      .catch(() => setLoadMemories([]));
  }, [selectedLoadId]);

  const memoryTypes = ['STM', 'LTM', 'semantic', 'procedural', 'episodic'];

  const filtered = memories.filter((m) => {
    const matchesSearch = !search || m.content.toLowerCase().includes(search.toLowerCase()) || m.tags.some((t) => t.toLowerCase().includes(search.toLowerCase()));
    const matchesType = !typeFilter || m.memory_type === typeFilter;
    return matchesSearch && matchesType;
  });

  const typeCounts = memoryTypes.reduce<Record<string, number>>((acc, type) => {
    acc[type] = memories.filter((m) => m.memory_type === type).length;
    return acc;
  }, {});

  return (
    <Box>
      <SectionHeader title="Memory Explorer" subtitle="Inspect LTM, STM, semantic, procedural, and episodic memory" />

      <LoadSelector
        onLoadChange={(loadId) => setSelectedLoadId(loadId)}
        showViewDetails
        navigate={(path) => window.location.href = path}
      />

      <Grid container spacing={3}>
        {/* Sidebar - Memory Type Filter */}
        <Grid size={{ xs: 12, sm: 6, md: 4, lg: 3 }}>
          <Card sx={{ bgcolor: '#1a2235', mb: 2 }}>
            <CardContent>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>Memory Types</Typography>
              {memoryTypes.map((type) => (
                <Box
                  key={type}
                  onClick={() => setTypeFilter(typeFilter === type ? null : type)}
                  sx={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    p: 1.5, mb: 0.5, borderRadius: 1, cursor: 'pointer',
                    bgcolor: typeFilter === type ? `${memoryTypeColors[type]}15` : 'transparent',
                    border: typeFilter === type ? `1px solid ${memoryTypeColors[type]}` : '1px solid transparent',
                    '&:hover': { bgcolor: '#0a0e17' },
                  }}
                >
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: memoryTypeColors[type] }} />
                    <Typography variant="body2" sx={{ color: typeFilter === type ? memoryTypeColors[type] : '#e2e8f0' }}>
                      {type}
                    </Typography>
                  </Box>
                  <Typography variant="caption" sx={{ color: '#64748b' }}>{typeCounts[type] || 0}</Typography>
                </Box>
              ))}
            </CardContent>
          </Card>

          <Card sx={{ bgcolor: '#1a2235' }}>
            <CardContent>
              <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>Memory Stats</Typography>
              {memoryTypes.map((type) => (
                <Box key={type} sx={{ mb: 1.5 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                    <Typography variant="caption" sx={{ color: '#94a3b8' }}>{type}</Typography>
                    <Typography variant="caption" sx={{ color: memoryTypeColors[type] }}>
                      {typeCounts[type] || 0}
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={((typeCounts[type] || 0) / memories.length) * 100}
                    sx={{
                      height: 4, borderRadius: 2, bgcolor: '#0a0e17',
                      '& .MuiLinearProgress-bar': { bgcolor: memoryTypeColors[type], borderRadius: 2 },
                    }}
                  />
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>

        {/* Main Content */}
        <Grid size={{ xs: 12, md: 9 }}>
          <Box sx={{ mb: 2 }}>
            <TextField
              fullWidth
              size="small"
              placeholder="Search memories by content or tags..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start"><SearchIcon sx={{ color: '#64748b' }} /></InputAdornment>
                  ),
                },
              }}
              sx={{
                '& .MuiOutlinedInput-root': { bgcolor: '#1a2235', color: '#e2e8f0' },
                '& .MuiOutlinedInput-notchedOutline': { borderColor: '#2a3a52' },
              }}
            />
          </Box>

          <Box sx={{ borderBottom: '1px solid #2a3a52', mb: 2 }}>
            <Tabs value={tab} onChange={(_, v) => setTab(v)}>
              <Tab label="All" />
              <Tab label="Recent" />
              <Tab label="High Confidence" />
            </Tabs>
          </Box>

          <TabPanel value={tab} index={0}>
            {filtered.map((mem) => (
              <MemoryCard key={mem.id} memory={mem} />
            ))}
            {filtered.length === 0 && (
              <Typography variant="body2" sx={{ color: '#64748b', textAlign: 'center', py: 4 }}>
                No memories match your search
              </Typography>
            )}
          </TabPanel>

          <TabPanel value={tab} index={1}>
            {[...filtered].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()).map((mem) => (
              <MemoryCard key={mem.id} memory={mem} />
            ))}
          </TabPanel>

          <TabPanel value={tab} index={2}>
            {filtered.filter((m) => m.confidence >= 0.8).map((mem) => (
              <MemoryCard key={mem.id} memory={mem} />
            ))}
          </TabPanel>
        </Grid>
      </Grid>
    </Box>
  );
}

function MemoryCard({ memory }: { memory: MemoryEntry }) {
  return (
    <Card sx={{ bgcolor: '#1a2235', mb: 1.5, '&:hover': { borderColor: '#3b82f6' } }}>
      <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <Chip
              label={memory.memory_type}
              size="small"
              sx={{ bgcolor: `${memoryTypeColors[memory.memory_type]}20`, color: memoryTypeColors[memory.memory_type] }}
            />
            <Chip label={`${memory.scope}:${memory.scope_id}`} size="small" variant="outlined" sx={{ fontSize: '0.625rem' }} />
          </Box>
          <Box sx={{ display: 'flex', gap: 1.5 }}>
            <Typography variant="caption" sx={{ color: '#64748b' }}>
              conf: {(memory.confidence ?? 0).toFixed(2)}
            </Typography>
            <Typography variant="caption" sx={{ color: '#64748b' }}>
              rel: {(memory.relevance_score ?? 0).toFixed(2)}
            </Typography>
          </Box>
        </Box>
        <Typography variant="body2" sx={{ color: '#e2e8f0', mb: 1 }}>{memory.content}</Typography>
        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
          {memory.tags.map((tag) => (
            <Chip key={tag} label={tag} size="small" variant="outlined" sx={{ fontSize: '0.625rem', height: 20 }} />
          ))}
        </Box>
        <Typography variant="caption" sx={{ color: '#475569', mt: 0.5, display: 'block' }}>
          {new Date(memory.created_at).toLocaleString()} · accessed {memory.access_count ?? 0} times
        </Typography>
      </CardContent>
    </Card>
  );
}