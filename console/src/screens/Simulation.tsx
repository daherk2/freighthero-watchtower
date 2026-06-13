import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Button from '@mui/material/Button';
import Chip from '@mui/material/Chip';
import Grid from '@mui/material/Grid';
import Divider from '@mui/material/Divider';
import LinearProgress from '@mui/material/LinearProgress';
import Alert from '@mui/material/Alert';
import Snackbar from '@mui/material/Snackbar';
import TextField from '@mui/material/TextField';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import LocalShippingIcon from '@mui/icons-material/LocalShipping';
import SmsIcon from '@mui/icons-material/Sms';
import GpsFixedIcon from '@mui/icons-material/GpsFixed';
import UpdateIcon from '@mui/icons-material/Update';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import TimerIcon from '@mui/icons-material/Timer';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import AddIcon from '@mui/icons-material/Add';
import RefreshIcon from '@mui/icons-material/Refresh';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import BuildIcon from '@mui/icons-material/Build';
import TimelineIcon from '@mui/icons-material/Timeline';
import BugReportIcon from '@mui/icons-material/BugReport';
import MonitorHeartIcon from '@mui/icons-material/MonitorHeart';
import { loadsApi, eventsApi, monitoringApi } from '@/api/client';
import { StateChip } from '@/components/shared';
import { stateColors } from '@/theme';

// Event scenarios the user can trigger
interface EventScenario {
  id: string;
  label: string;
  icon: React.ReactNode;
  description: string;
  eventType: 'inbound_communication' | 'tracking' | 'load_update';
  color: string;
  buildPayload: (loadId: string, customerId: string) => Record<string, unknown>;
}

const SCENARIOS: EventScenario[] = [
  {
    id: 'driver_eta_sms',
    label: 'Driver SMS: "I\'ll be there in 30 min"',
    icon: <SmsIcon />,
    description: 'Driver sends ETA via SMS',
    eventType: 'inbound_communication',
    color: '#3b82f6',
    buildPayload: (loadId, customerId) => ({
      event_id: `sim-evt-${Date.now()}`,
      event_type: 'inbound_communication',
      load_id: loadId,
      customer_id: customerId,
      occurred_at: new Date().toISOString(),
      inbound_communication: {
        sender_type: 'driver',
        channel: 'sms',
        message: 'I will be there in about 30 minutes',
        attachments: [],
      },
    }),
  },
  {
    id: 'driver_breakdown',
    label: 'Driver SMS: "Truck broke down"',
    icon: <SmsIcon />,
    description: 'Driver reports breakdown',
    eventType: 'inbound_communication',
    color: '#ef4444',
    buildPayload: (loadId, customerId) => ({
      event_id: `sim-evt-${Date.now()}`,
      event_type: 'inbound_communication',
      load_id: loadId,
      customer_id: customerId,
      occurred_at: new Date().toISOString(),
      inbound_communication: {
        sender_type: 'driver',
        channel: 'sms',
        message: 'Truck broke down on the highway. Need assistance.',
        attachments: [],
      },
    }),
  },
  {
    id: 'tracking_nearby',
    label: 'GPS: 2 miles from delivery',
    icon: <GpsFixedIcon />,
    description: 'Tracking ping near destination',
    eventType: 'tracking',
    color: '#22c55e',
    buildPayload: (loadId, customerId) => ({
      event_id: `sim-evt-${Date.now()}`,
      event_type: 'tracking',
      load_id: loadId,
      customer_id: customerId,
      occurred_at: new Date().toISOString(),
      tracking: {
        latitude: 36.1627,
        longitude: -86.7816,
        distance_to_delivery: 2.0,
        timestamp: new Date().toISOString(),
      },
    }),
  },
  {
    id: 'tracking_arrived',
    label: 'GPS: Arrived at delivery',
    icon: <GpsFixedIcon />,
    description: 'Driver arrived at delivery location',
    eventType: 'tracking',
    color: '#10b981',
    buildPayload: (loadId, customerId) => ({
      event_id: `sim-evt-${Date.now()}`,
      event_type: 'tracking',
      load_id: loadId,
      customer_id: customerId,
      occurred_at: new Date().toISOString(),
      tracking: {
        latitude: 36.1627,
        longitude: -86.7816,
        distance_to_delivery: 0.1,
        timestamp: new Date().toISOString(),
      },
    }),
  },
  {
    id: 'pod_received',
    label: 'Driver sends POD document',
    icon: <SmsIcon />,
    description: 'Proof of delivery received',
    eventType: 'inbound_communication',
    color: '#8b5cf6',
    buildPayload: (loadId, customerId) => ({
      event_id: `sim-evt-${Date.now()}`,
      event_type: 'inbound_communication',
      load_id: loadId,
      customer_id: customerId,
      occurred_at: new Date().toISOString(),
      inbound_communication: {
        sender_type: 'driver',
        channel: 'sms',
        message: 'Here is the POD',
        attachments: [{ url: 'https://example.com/pod.pdf', classification: 'pod' }],
      },
    }),
  },
  {
    id: 'eta_update',
    label: 'ETA Update: +45 min delay',
    icon: <UpdateIcon />,
    description: 'Load ETA pushed back',
    eventType: 'load_update',
    color: '#f59e0b',
    buildPayload: (loadId, customerId) => {
      const newEta = new Date();
      newEta.setMinutes(newEta.getMinutes() + 45);
      return {
        event_id: `sim-evt-${Date.now()}`,
        event_type: 'load_update',
        load_id: loadId,
        customer_id: customerId,
        occurred_at: new Date().toISOString(),
        load_update: {
          update_type: 'eta_change',
          new_value: newEta.toISOString(),
        },
      };
    },
  },
  {
    id: 'broker_message',
    label: 'Broker: "Any update on load?"',
    icon: <SmsIcon />,
    description: 'Broker asks for status',
    eventType: 'inbound_communication',
    color: '#06b6d4',
    buildPayload: (loadId, customerId) => ({
      event_id: `sim-evt-${Date.now()}`,
      event_type: 'inbound_communication',
      load_id: loadId,
      customer_id: customerId,
      occurred_at: new Date().toISOString(),
      inbound_communication: {
        sender_type: 'broker',
        channel: 'email',
        message: 'Can I get an update on this load? Customer is asking.',
        attachments: [],
      },
    }),
  },
  {
    id: 'timer_callback',
    label: 'Timer: ETA follow-up expired',
    icon: <TimerIcon />,
    description: 'ETA follow-up timer fired',
    eventType: 'load_update',
    color: '#f97316',
    buildPayload: (loadId, customerId) => ({
      event_id: `sim-evt-${Date.now()}`,
      event_type: 'load_update',
      load_id: loadId,
      customer_id: customerId,
      occurred_at: new Date().toISOString(),
      load_update: {
        update_type: 'timer_callback',
        new_value: 'eta_followup',
      },
    }),
  },
];

interface EventLog {
  id: string;
  scenario: string;
  timestamp: string;
  status: 'sending' | 'success' | 'error';
  workflow?: string;
  message?: string;
}

interface LoadOption {
  load_id: string;
  customer_id: string;
  current_state: string;
  external_load_id?: string;
  po_number?: string;
  updated_at?: string;
}

const STORAGE_KEY = 'freighthero_selected_load';

export function Simulation() {
  const navigate = useNavigate();
  const [selectedLoadId, setSelectedLoadId] = useState<string>('');
  const [loads, setLoads] = useState<LoadOption[]>([]);
  const [loadsLoading, setLoadsLoading] = useState(true);
  const [customerId, setCustomerId] = useState('customer_a');
  const [loadState, setLoadState] = useState<string>('');
  const [eventLog, setEventLog] = useState<EventLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [snack, setSnack] = useState<{ open: boolean; severity: 'success' | 'error'; message: string }>({
    open: false, severity: 'success', message: '',
  });
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [newLoadForm, setNewLoadForm] = useState({
    customer_id: 'customer_a',
    initial_state: 'on_route_to_delivery',
    external_load_id: '',
    po_number: '',
    driver_name: '',
    driver_phone: '',
    instructions: '',
  });

  // Load persisted load ID from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      setSelectedLoadId(saved);
    }
  }, []);

  // Fetch available loads
  const fetchLoads = useCallback(async () => {
    setLoadsLoading(true);
    try {
      const data = await loadsApi.list() as LoadOption[];
      setLoads(data);
    } catch (err) {
      console.error('Failed to fetch loads:', err);
    } finally {
      setLoadsLoading(false);
    }
  }, []);

  useEffect(() => { fetchLoads(); }, [fetchLoads]);

  // Fetch load details when selected
  const fetchLoadState = useCallback(async () => {
    if (!selectedLoadId) {
      setLoadState('');
      setCustomerId('customer_a');
      return;
    }
    try {
      const res = await loadsApi.get(selectedLoadId) as Record<string, unknown>;
      setCustomerId((res.customer_id as string) || 'customer_a');
      setLoadState((res.current_state as string) || '');
    } catch {
      // Load might have been deleted
      setLoadState('');
    }
  }, [selectedLoadId]);

  useEffect(() => { fetchLoadState(); }, [fetchLoadState]);

  // Save selected load to localStorage
  const selectLoad = (loadId: string) => {
    setSelectedLoadId(loadId);
    if (loadId) {
      localStorage.setItem(STORAGE_KEY, loadId);
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  };

  const fireEvent = async (scenario: EventScenario) => {
    if (!selectedLoadId) {
      setSnack({ open: true, severity: 'error', message: 'No load selected. Pick or create a load first.' });
      return;
    }

    const logId = `log-${Date.now()}`;
    setEventLog((prev) => [
      { id: logId, scenario: scenario.label, timestamp: new Date().toISOString(), status: 'sending' },
      ...prev,
    ]);
    setLoading(true);

    try {
      const payload = scenario.buildPayload(selectedLoadId, customerId);
      let result: Record<string, unknown>;

      if (scenario.eventType === 'inbound_communication') {
        result = (await eventsApi.inboundCommunication(payload)) as Record<string, unknown>;
      } else if (scenario.eventType === 'tracking') {
        result = (await eventsApi.tracking(payload)) as Record<string, unknown>;
      } else {
        result = (await eventsApi.loadUpdate(payload)) as Record<string, unknown>;
      }

      setEventLog((prev) =>
        prev.map((l) =>
          l.id === logId
            ? { ...l, status: 'success', workflow: (result.workflow as string) || 'N/A', message: `Event processed → ${result.workflow || 'routed'}` }
            : l
        )
      );

      // Refresh load state after event
      setTimeout(() => fetchLoadState(), 1000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unknown error';
      setEventLog((prev) =>
        prev.map((l) => (l.id === logId ? { ...l, status: 'error', message: msg } : l))
      );
    } finally {
      setLoading(false);
    }
  };

  // State transition helper
  const transitionState = async (newState: string) => {
    if (!selectedLoadId) return;
    try {
      await loadsApi.transition(selectedLoadId, newState);
      setSnack({ open: true, severity: 'success', message: `State → ${newState}` });
      setTimeout(() => fetchLoadState(), 500);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unknown error';
      setSnack({ open: true, severity: 'error', message: `Transition failed: ${msg}` });
    }
  };

  // Create new load
  const createLoad = async () => {
    try {
      const payload: Record<string, unknown> = {
        customer_id: newLoadForm.customer_id,
        initial_state: newLoadForm.initial_state,
        run_pipeline: true,
        load_data: {} as Record<string, unknown>,
      };
      if (newLoadForm.external_load_id) payload.external_load_id = newLoadForm.external_load_id;
      if (newLoadForm.po_number) payload.po_number = newLoadForm.po_number;
      if (newLoadForm.instructions) payload.instructions = newLoadForm.instructions;
      const loadData = payload.load_data as Record<string, unknown>;
      if (newLoadForm.driver_name || newLoadForm.driver_phone) {
        loadData.driver = { name: newLoadForm.driver_name, phone: newLoadForm.driver_phone };
      }

      const result = (await loadsApi.create(payload)) as Record<string, unknown>;
      setCreateDialogOpen(false);
      selectLoad(result.load_id as string);
      await fetchLoads();
      setSnack({ open: true, severity: 'success', message: `Load ${result.load_id} created` });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unknown error';
      setSnack({ open: true, severity: 'error', message: `Failed: ${msg}` });
    }
  };

  const selectedLoad = loads.find((l) => l.load_id === selectedLoadId);

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>
        Simulation
      </Typography>
      <Typography variant="body2" sx={{ color: '#64748b', mb: 3 }}>
        Select a load and fire events to test the agent pipeline
      </Typography>

      {/* Load Selector */}
      <Card sx={{ mb: 3, bgcolor: '#1a2235' }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <LocalShippingIcon fontSize="small" /> Select Load
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Tooltip title="Refresh loads">
                <IconButton size="small" onClick={fetchLoads} disabled={loadsLoading}>
                  <RefreshIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              <Button
                size="small"
                variant="outlined"
                startIcon={<AddIcon />}
                onClick={() => setCreateDialogOpen(true)}
              >
                New Load
              </Button>
            </Box>
          </Box>

          <FormControl fullWidth size="small" sx={{ mb: 2 }}>
            <InputLabel>Choose a load to simulate</InputLabel>
            <Select
              value={selectedLoadId}
              label="Choose a load to simulate"
              onChange={(e) => selectLoad(e.target.value)}
              sx={{ bgcolor: '#0a0e17', borderRadius: 1 }}
            >
              <MenuItem value="">
                <em>No load selected</em>
              </MenuItem>
              {loads.map((load) => (
                <MenuItem key={load.load_id} value={load.load_id}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                    <Chip
                      label={load.current_state?.replace(/_/g, ' ')}
                      size="small"
                      sx={{ bgcolor: stateColors[load.current_state] || '#64748b', color: '#fff', fontSize: '0.7rem', height: 20 }}
                    />
                    <Typography variant="body2" sx={{ fontFamily: 'monospace', color: '#3b82f6', flex: 1 }} noWrap>
                      {load.external_load_id || load.load_id.slice(0, 16)}...
                    </Typography>
                    <Typography variant="caption" sx={{ color: '#64748b' }}>
                      {load.customer_id}
                    </Typography>
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {selectedLoadId && (
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', flexWrap: 'wrap' }}>
              <Chip label={selectedLoadId} size="small" sx={{ fontFamily: 'monospace', color: '#3b82f6' }} />
              {loadState && (
                <Chip
                  label={loadState.replace(/_/g, ' ')}
                  size="small"
                  sx={{ bgcolor: stateColors[loadState] || '#64748b', color: '#fff' }}
                />
              )}
              <Chip label={customerId} size="small" variant="outlined" />
              <Button size="small" variant="text" onClick={() => navigate(`/loads/${selectedLoadId}`)}>
                View Details →
              </Button>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* State Transitions */}
      {selectedLoadId && (
        <Card sx={{ mb: 3, bgcolor: '#1a2235' }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 1 }}>State Transitions</Typography>
            <Typography variant="body2" sx={{ color: '#64748b', mb: 2 }}>
              Manually transition the load state
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              <Button
                size="small"
                variant="outlined"
                startIcon={<ArrowForwardIcon />}
                onClick={() => transitionState('on_route_to_delivery')}
                disabled={loadState === 'on_route_to_delivery'}
                sx={{ borderColor: '#3b82f655', color: '#3b82f6', '&:hover': { borderColor: '#3b82f6', bgcolor: '#3b82f615' } }}
              >
                → On Route
              </Button>
              <Button
                size="small"
                variant="outlined"
                startIcon={<ArrowForwardIcon />}
                onClick={() => transitionState('at_delivery')}
                disabled={loadState === 'at_delivery'}
                sx={{ borderColor: '#f59e0b55', color: '#f59e0b', '&:hover': { borderColor: '#f59e0b', bgcolor: '#f59e0b15' } }}
              >
                → At Delivery
              </Button>
              <Button
                size="small"
                variant="outlined"
                startIcon={<ArrowForwardIcon />}
                onClick={() => transitionState('confirm_delivery')}
                disabled={loadState === 'confirm_delivery'}
                sx={{ borderColor: '#8b5cf655', color: '#8b5cf6', '&:hover': { borderColor: '#8b5cf6', bgcolor: '#8b5cf615' } }}
              >
                → Confirm
              </Button>
              <Button
                size="small"
                variant="outlined"
                color="success"
                startIcon={<CheckCircleIcon />}
                onClick={() => transitionState('delivered')}
              >
                → Delivered
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Event Buttons */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 1 }}>Fire Events</Typography>
          <Typography variant="body2" sx={{ color: '#64748b', mb: 2 }}>
            Click an event to simulate it hitting the agent pipeline
          </Typography>
          <Grid container spacing={1.5}>
            {SCENARIOS.map((scenario) => (
              <Grid size={{ xs: 12, sm: 6, md: 4 }} key={scenario.id}>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={scenario.icon}
                  onClick={() => fireEvent(scenario)}
                  disabled={!selectedLoadId || loading}
                  sx={{
                    justifyContent: 'flex-start',
                    textTransform: 'none',
                    borderColor: scenario.color + '55',
                    color: scenario.color,
                    '&:hover': { borderColor: scenario.color, bgcolor: scenario.color + '15' },
                    py: 1.5,
                    px: 2,
                  }}
                >
                  <Box sx={{ textAlign: 'left' }}>
                    <Box sx={{ fontSize: '0.85rem', fontWeight: 600 }}>{scenario.label}</Box>
                    <Box sx={{ fontSize: '0.7rem', color: '#64748b' }}>{scenario.description}</Box>
                  </Box>
                </Button>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>

      {/* Custom Message */}
      {selectedLoadId && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>Custom Driver Message</Typography>
            <CustomMessageSender
              loadId={selectedLoadId}
              customerId={customerId}
              disabled={!selectedLoadId || loading}
              onSent={(msg, workflow) => {
                setEventLog((prev) => [
                  { id: `log-${Date.now()}`, scenario: `Custom: "${msg}"`, timestamp: new Date().toISOString(), status: 'success', workflow: workflow || 'N/A', message: 'Sent' },
                  ...prev,
                ]);
                setTimeout(() => fetchLoadState(), 1000);
              }}
            />
          </CardContent>
        </Card>
      )}

      {/* Pipeline Inspection Links */}
      {selectedLoadId && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 1 }}>Pipeline Inspection</Typography>
            <Typography variant="body2" sx={{ color: '#64748b', mb: 2 }}>
              Inspect the agent pipeline for this load
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              <Button
                size="small"
                variant="outlined"
                startIcon={<SmartToyIcon />}
                onClick={() => navigate(`/agent?load_id=${selectedLoadId}`)}
                sx={{ borderColor: '#3b82f655', color: '#3b82f6', '&:hover': { borderColor: '#3b82f6', bgcolor: '#3b82f615' } }}
              >
                Agent Runs
              </Button>
              <Button
                size="small"
                variant="outlined"
                startIcon={<MonitorHeartIcon />}
                onClick={() => navigate(`/monitoring?load_id=${selectedLoadId}`)}
                sx={{ borderColor: '#22c55e55', color: '#22c55e', '&:hover': { borderColor: '#22c55e', bgcolor: '#22c55e15' } }}
              >
                Monitoring
              </Button>
              <Button
                size="small"
                variant="outlined"
                startIcon={<AccountTreeIcon />}
                onClick={() => navigate(`/workflow?load_id=${selectedLoadId}`)}
                sx={{ borderColor: '#f59e0b55', color: '#f59e0b', '&:hover': { borderColor: '#f59e0b', bgcolor: '#f59e0b15' } }}
              >
                Workflow
              </Button>
              <Button
                size="small"
                variant="outlined"
                startIcon={<BuildIcon />}
                onClick={() => navigate(`/tools?load_id=${selectedLoadId}`)}
                sx={{ borderColor: '#8b5cf655', color: '#8b5cf6', '&:hover': { borderColor: '#8b5cf6', bgcolor: '#8b5cf615' } }}
              >
                Tool Calls
              </Button>
              <Button
                size="small"
                variant="outlined"
                startIcon={<TimelineIcon />}
                onClick={() => navigate(`/traces?load_id=${selectedLoadId}`)}
                sx={{ borderColor: '#06b6d455', color: '#06b6d4', '&:hover': { borderColor: '#06b6d4', bgcolor: '#06b6d415' } }}
              >
                Traces
              </Button>
              <Button
                size="small"
                variant="outlined"
                startIcon={<BugReportIcon />}
                onClick={() => navigate(`/debugger?load_id=${selectedLoadId}`)}
                sx={{ borderColor: '#ef444455', color: '#ef4444', '&:hover': { borderColor: '#ef4444', bgcolor: '#ef444415' } }}
              >
                Debugger
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Event Log */}
      <Card sx={{ mb: 3 }}>
        <CardContent sx={{ p: 0 }}>
          <Box sx={{ px: 2.5, pt: 2, pb: loading ? 0 : 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
              <Typography variant="h6">Event Log</Typography>
              {eventLog.length > 0 && (
                <Chip label={eventLog.length} size="small" sx={{ bgcolor: '#243049', color: '#64748b', height: 18, fontSize: '0.65rem' }} />
              )}
            </Box>
            {eventLog.length > 0 && (
              <Button
                size="small"
                sx={{ fontSize: '0.7rem', color: '#64748b', '&:hover': { color: '#94a3b8' } }}
                onClick={() => setEventLog([])}
              >
                Clear
              </Button>
            )}
          </Box>

          {loading && <LinearProgress sx={{ mx: 0, height: 2, bgcolor: '#243049', '& .MuiLinearProgress-bar': { bgcolor: '#3b82f6' } }} />}

          <Box sx={{ px: 2.5, pb: 2, pt: loading ? 1 : 0 }}>
            {eventLog.length === 0 ? (
              <Typography variant="body2" sx={{ color: '#64748b', textAlign: 'center', py: 4 }}>
                No events fired yet. Select a load and click an event button to start.
              </Typography>
            ) : (
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, maxHeight: 400, overflowY: 'auto', pr: 0.5 }}>
                {eventLog.map((log) => (
                  <Box
                    key={log.id}
                    sx={{
                      p: 1.5,
                      borderRadius: 1,
                      bgcolor: log.status === 'success' ? '#0f2a1a' : log.status === 'error' ? '#2a0f0f' : '#1a1a2a',
                      border: '1px solid',
                      borderColor: log.status === 'success' ? '#22c55e44' : log.status === 'error' ? '#ef444444' : '#3b82f644',
                    }}
                  >
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 1 }}>
                      <Typography variant="body2" sx={{ fontWeight: 600, flex: 1 }}>
                        {log.scenario}
                      </Typography>
                      <Chip
                        size="small"
                        label={log.status}
                        color={log.status === 'success' ? 'success' : log.status === 'error' ? 'error' : 'info'}
                        sx={{ fontSize: '0.7rem', flexShrink: 0 }}
                      />
                    </Box>
                    {log.workflow && (
                      <Typography variant="caption" sx={{ color: '#22c55e' }}>
                        → Workflow: {log.workflow}
                      </Typography>
                    )}
                    {log.message && log.status === 'error' && (
                      <Typography variant="caption" sx={{ color: '#ef4444', display: 'block' }}>
                        {log.message}
                      </Typography>
                    )}
                    <Typography variant="caption" sx={{ color: '#64748b', display: 'block', mt: 0.5 }}>
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </Typography>
                  </Box>
                ))}
              </Box>
            )}
          </Box>
        </CardContent>
      </Card>

      {/* Create Load Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Load</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <FormControl fullWidth size="small">
              <InputLabel>Customer</InputLabel>
              <Select
                value={newLoadForm.customer_id}
                label="Customer"
                onChange={(e) => setNewLoadForm((prev) => ({ ...prev, customer_id: e.target.value }))}
              >
                <MenuItem value="customer_a">Customer A</MenuItem>
                <MenuItem value="customer_b">Customer B</MenuItem>
                <MenuItem value="customer_c">Customer C</MenuItem>
              </Select>
            </FormControl>
            <FormControl fullWidth size="small">
              <InputLabel>Initial State</InputLabel>
              <Select
                value={newLoadForm.initial_state}
                label="Initial State"
                onChange={(e) => setNewLoadForm((prev) => ({ ...prev, initial_state: e.target.value }))}
              >
                <MenuItem value="dispatched">Dispatched</MenuItem>
                <MenuItem value="on_route_to_delivery">On Route to Delivery</MenuItem>
                <MenuItem value="at_delivery">At Delivery</MenuItem>
              </Select>
            </FormControl>
            <TextField
              fullWidth
              size="small"
              label="External Load ID (optional)"
              value={newLoadForm.external_load_id}
              onChange={(e) => setNewLoadForm((prev) => ({ ...prev, external_load_id: e.target.value }))}
            />
            <TextField
              fullWidth
              size="small"
              label="PO Number (optional)"
              value={newLoadForm.po_number}
              onChange={(e) => setNewLoadForm((prev) => ({ ...prev, po_number: e.target.value }))}
            />
            <TextField
              fullWidth
              size="small"
              label="Driver Name"
              value={newLoadForm.driver_name}
              onChange={(e) => setNewLoadForm((prev) => ({ ...prev, driver_name: e.target.value }))}
            />
            <TextField
              fullWidth
              size="small"
              label="Driver Phone"
              value={newLoadForm.driver_phone}
              onChange={(e) => setNewLoadForm((prev) => ({ ...prev, driver_phone: e.target.value }))}
            />
            <TextField
              fullWidth
              size="small"
              label="Instructions"
              multiline
              rows={2}
              value={newLoadForm.instructions}
              onChange={(e) => setNewLoadForm((prev) => ({ ...prev, instructions: e.target.value }))}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={createLoad} startIcon={<PlayArrowIcon />}>
            Create & Select
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snack.open}
        autoHideDuration={4000}
        onClose={() => setSnack((s) => ({ ...s, open: false }))}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity={snack.severity} onClose={() => setSnack((s) => ({ ...s, open: false }))}>
          {snack.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}

// Sub-component for custom message
function CustomMessageSender({
  loadId,
  customerId,
  disabled,
  onSent,
}: {
  loadId: string;
  customerId: string;
  disabled: boolean;
  onSent: (msg: string, workflow?: string) => void;
}) {
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);

  const send = async () => {
    if (!message.trim()) return;
    setSending(true);
    try {
      const payload = {
        event_id: `sim-evt-${Date.now()}`,
        event_type: 'inbound_communication',
        load_id: loadId,
        customer_id: customerId,
        occurred_at: new Date().toISOString(),
        inbound_communication: {
          sender_type: 'driver',
          channel: 'sms',
          message: message.trim(),
          attachments: [],
        },
      };
      const result = (await eventsApi.inboundCommunication(payload)) as Record<string, unknown>;
      onSent(message.trim(), result.workflow as string | undefined);
      setMessage('');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unknown error';
      onSent(msg);
    } finally {
      setSending(false);
    }
  };

  return (
    <Box sx={{ display: 'flex', gap: 1 }}>
      <TextField
        fullWidth
        size="small"
        placeholder="Type a driver message..."
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={(e) => { if (e.key === 'Enter' && !disabled && !sending) send(); }}
        disabled={disabled || sending}
      />
      <Button
        variant="contained"
        onClick={send}
        disabled={disabled || sending || !message.trim()}
        startIcon={<PlayArrowIcon />}
      >
        Send
      </Button>
    </Box>
  );
}
