import { useState } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardActionArea from '@mui/material/CardActionArea';
import TextField from '@mui/material/TextField';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import FormControl from '@mui/material/FormControl';
import FormControlLabel from '@mui/material/FormControlLabel';
import InputLabel from '@mui/material/InputLabel';
import Switch from '@mui/material/Switch';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import Snackbar from '@mui/material/Snackbar';
import Grid from '@mui/material/Grid';
import Divider from '@mui/material/Divider';
import LocalShippingIcon from '@mui/icons-material/LocalShipping';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import AcUnitIcon from '@mui/icons-material/AcUnit';
import LocalFireDepartmentIcon from '@mui/icons-material/LocalFireDepartment';
import Inventory2Icon from '@mui/icons-material/Inventory2';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { useNavigate } from 'react-router-dom';
import { loadsApi } from '@/api/client';

const CUSTOMERS = [
  { value: 'customer_a', label: 'Customer A' },
  { value: 'customer_b', label: 'Customer B' },
  { value: 'customer_c', label: 'Customer C' },
];

const LOAD_STATES = [
  { value: 'dispatched', label: 'Dispatched' },
  { value: 'on_route_to_delivery', label: 'On Route to Delivery' },
  { value: 'at_delivery', label: 'At Delivery' },
  { value: 'confirm_delivery', label: 'Confirm Delivery' },
];

interface FormData {
  customer_id: string;
  initial_state: string;
  external_load_id: string;
  po_number: string;
  current_eta_utc: string;
  pickup_address: string;
  delivery_address: string;
  driver_name: string;
  driver_phone: string;
  trailer_number: string;
  instructions: string;
  run_pipeline: boolean;
}

const initialForm: FormData = {
  customer_id: 'customer_a',
  initial_state: 'on_route_to_delivery',
  external_load_id: '',
  po_number: '',
  current_eta_utc: '',
  pickup_address: '',
  delivery_address: '',
  driver_name: '',
  driver_phone: '',
  trailer_number: '',
  instructions: '',
  run_pipeline: true,
};

// Pre-built load profiles for quick simulation
const LOAD_PROFILES: { name: string; icon: React.ReactNode; description: string; data: FormData }[] = [
  {
    name: 'Refrigerated',
    icon: <AcUnitIcon fontSize="small" />,
    description: 'Cold chain shipment with temp requirements',
    data: {
      customer_id: 'customer_a',
      initial_state: 'on_route_to_delivery',
      external_load_id: 'FH-REF-001',
      po_number: 'PO-COLD-881',
      current_eta_utc: '',
      pickup_address: '800 Cold Storage Ln, Detroit MI 48201',
      delivery_address: '350 Fresh Foods Blvd, Nashville TN 37211',
      driver_name: 'Carlos Mendes',
      driver_phone: '+1-555-7788',
      trailer_number: 'TRL-REEF-01',
      instructions: 'Refrigerated load - maintain 35F. Call 30 min before arrival.',
      run_pipeline: true,
    },
  },
  {
    name: 'Hazmat',
    icon: <LocalFireDepartmentIcon fontSize="small" />,
    description: 'Hazardous materials with special handling',
    data: {
      customer_id: 'customer_b',
      initial_state: 'dispatched',
      external_load_id: 'FH-HAZ-002',
      po_number: 'PO-HAZ-442',
      current_eta_utc: '',
      pickup_address: '200 ChemPark Dr, Houston TX 77001',
      delivery_address: '900 Industrial Way, Phoenix AZ 85001',
      driver_name: 'Bob Tanner',
      driver_phone: '+1-555-3344',
      trailer_number: 'TRL-HAZ-03',
      instructions: 'HAZMAT Class 3 - Flammable liquids. Placard required. Emergency kit on board.',
      run_pipeline: true,
    },
  },
  {
    name: 'Dry Van',
    icon: <Inventory2Icon fontSize="small" />,
    description: 'Standard dry freight, no special requirements',
    data: {
      customer_id: 'customer_c',
      initial_state: 'on_route_to_delivery',
      external_load_id: 'FH-DRY-003',
      po_number: 'PO-DRY-553',
      current_eta_utc: '',
      pickup_address: '500 Warehouse Rd, Chicago IL 60601',
      delivery_address: '1200 Distribution Ave, Atlanta GA 30301',
      driver_name: 'Jane Rodriguez',
      driver_phone: '+1-555-5566',
      trailer_number: 'TRL-DRY-07',
      instructions: 'Standard dry freight. Deliver to dock 4. Check in with security.',
      run_pipeline: true,
    },
  },
];

interface FormErrors {
  customer_id?: string;
  driver_name?: string;
  driver_phone?: string;
}

export function NewLoad() {
  const navigate = useNavigate();
  const [form, setForm] = useState<FormData>(initialForm);
  const [errors, setErrors] = useState<FormErrors>({});
  const [activeProfile, setActiveProfile] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [snack, setSnack] = useState<{ open: boolean; severity: 'success' | 'error'; message: string }>({
    open: false,
    severity: 'success',
    message: '',
  });

  const validate = (field: keyof FormData, value: string): string | undefined => {
    if (field === 'customer_id' && !value) return 'Customer is required';
    if (field === 'driver_phone' && value && !/^\+?[\d\s\-()]{7,}$/.test(value)) return 'Invalid phone number';
    return undefined;
  };

  const handleChange = (field: keyof FormData) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement> | any) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value;
    setForm((prev) => ({ ...prev, [field]: value }));
    if (typeof value === 'string') {
      const err = validate(field, value);
      setErrors((prev) => ({ ...prev, [field]: err }));
    }
  };

  const applyProfile = (profile: typeof LOAD_PROFILES[number]) => {
    setForm(profile.data);
    setErrors({});
    setActiveProfile(profile.name);
  };

  const handleSubmit = async () => {
    const newErrors: FormErrors = {};
    if (!form.customer_id) newErrors.customer_id = 'Customer is required';
    if (form.driver_phone && !/^\+?[\d\s\-()]{7,}$/.test(form.driver_phone)) newErrors.driver_phone = 'Invalid phone number';
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setSubmitting(true);
    try {
      const payload: Record<string, unknown> = {
        customer_id: form.customer_id,
        initial_state: form.initial_state,
        run_pipeline: form.run_pipeline,
        load_data: {} as Record<string, unknown>,
      };

      if (form.external_load_id) payload.external_load_id = form.external_load_id;
      if (form.po_number) payload.po_number = form.po_number;
      if (form.current_eta_utc) payload.current_eta_utc = form.current_eta_utc;
      if (form.instructions) payload.instructions = form.instructions;

      const loadData = payload.load_data as Record<string, unknown>;

      if (form.pickup_address || form.delivery_address) {
        loadData.pickup = { address: form.pickup_address };
        loadData.delivery = { address: form.delivery_address };
      }
      if (form.driver_name || form.driver_phone) {
        loadData.driver = { name: form.driver_name, phone: form.driver_phone };
      }
      if (form.trailer_number) {
        loadData.trailer_number = form.trailer_number;
      }

      const result = await loadsApi.create(payload) as Record<string, unknown>;

      const pipelineInfo = result.pipeline_triggered
        ? ` | Pipeline: ${result.pipeline_workflow || 'N/A'} (${result.pipeline_status || 'N/A'})`
        : '';
      setSnack({
        open: true,
        severity: 'success',
        message: `Load ${result.load_id} created${pipelineInfo}`,
      });

      setTimeout(() => navigate(`/simulation?load_id=${result.load_id}`), 1500);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unknown error';
      setSnack({ open: true, severity: 'error', message: `Failed: ${msg}` });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>
        New Load
      </Typography>
      <Typography variant="body2" sx={{ color: '#64748b', mb: 3 }}>
        Create a new freight load and optionally trigger the agent pipeline
      </Typography>

      {/* Quick Profiles */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" sx={{ mb: 0.5, fontWeight: 600 }}>Quick Profiles</Typography>
        <Typography variant="body2" sx={{ color: '#64748b', mb: 2 }}>
          Click a profile to auto-fill the form with realistic test data
        </Typography>
        <Grid container spacing={2}>
          {LOAD_PROFILES.map((profile) => {
            const isActive = activeProfile === profile.name;
            return (
              <Grid key={profile.name} size={{ xs: 12, sm: 4 }}>
                <Card
                  sx={{
                    bgcolor: isActive ? '#0f2a4a' : '#1a2235',
                    border: '1px solid',
                    borderColor: isActive ? '#3b82f6' : '#2a3a52',
                    transition: 'all 0.15s',
                    '&:hover': { borderColor: '#3b82f6', bgcolor: '#0f2a4a' },
                    position: 'relative',
                  }}
                >
                  <CardActionArea onClick={() => applyProfile(profile)} sx={{ p: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                      <Box
                        sx={{
                          width: 36,
                          height: 36,
                          borderRadius: 1.5,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          bgcolor: isActive ? '#3b82f620' : '#243049',
                          color: isActive ? '#3b82f6' : '#64748b',
                          flexShrink: 0,
                        }}
                      >
                        {profile.icon}
                      </Box>
                      <Box sx={{ flex: 1, minWidth: 0 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
                          <Typography variant="body2" sx={{ fontWeight: 600, color: isActive ? '#e2e8f0' : '#94a3b8' }}>
                            {profile.name}
                          </Typography>
                          {isActive && (
                            <CheckCircleIcon sx={{ fontSize: 14, color: '#3b82f6' }} />
                          )}
                        </Box>
                        <Typography variant="caption" sx={{ color: '#475569' }}>
                          {profile.description}
                        </Typography>
                      </Box>
                    </Box>
                  </CardActionArea>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      </Box>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
            <LocalShippingIcon fontSize="small" /> Load Information
          </Typography>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 4 }}>
              <FormControl fullWidth size="small" error={!!errors.customer_id}>
                <InputLabel>Customer *</InputLabel>
                <Select value={form.customer_id} label="Customer *" onChange={handleChange('customer_id')}>
                  {CUSTOMERS.map((c) => (
                    <MenuItem key={c.value} value={c.value}>{c.label}</MenuItem>
                  ))}
                </Select>
                {errors.customer_id && (
                  <Typography variant="caption" sx={{ color: '#ef4444', mt: 0.5, display: 'block' }}>
                    {errors.customer_id}
                  </Typography>
                )}
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, md: 4 }}>
              <FormControl fullWidth size="small">
                <InputLabel>Initial State</InputLabel>
                <Select value={form.initial_state} label="Initial State" onChange={handleChange('initial_state')}>
                  {LOAD_STATES.map((s) => (
                    <MenuItem key={s.value} value={s.value}>{s.label}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid size={{ xs: 12, md: 4 }}>
              <TextField fullWidth size="small" label="External Load ID" value={form.external_load_id} onChange={handleChange('external_load_id')} />
            </Grid>
            <Grid size={{ xs: 12, md: 4 }}>
              <TextField fullWidth size="small" label="PO Number" value={form.po_number} onChange={handleChange('po_number')} />
            </Grid>
            <Grid size={{ xs: 12, md: 4 }}>
              <TextField fullWidth size="small" label="ETA (UTC)" type="datetime-local" value={form.current_eta_utc} onChange={handleChange('current_eta_utc')} slotProps={{ inputLabel: { shrink: true } }} />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>Addresses</Typography>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField fullWidth size="small" label="Pickup Address" value={form.pickup_address} onChange={handleChange('pickup_address')} />
            </Grid>
            <Grid size={{ xs: 12, md: 6 }}>
              <TextField fullWidth size="small" label="Delivery Address" value={form.delivery_address} onChange={handleChange('delivery_address')} />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>Driver & Equipment</Typography>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 4 }}>
              <TextField fullWidth size="small" label="Driver Name" value={form.driver_name} onChange={handleChange('driver_name')} />
            </Grid>
            <Grid size={{ xs: 12, md: 4 }}>
              <TextField
                fullWidth
                size="small"
                label="Driver Phone"
                value={form.driver_phone}
                onChange={handleChange('driver_phone')}
                error={!!errors.driver_phone}
                helperText={errors.driver_phone}
              />
            </Grid>
            <Grid size={{ xs: 12, md: 4 }}>
              <TextField fullWidth size="small" label="Trailer Number" value={form.trailer_number} onChange={handleChange('trailer_number')} />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" sx={{ mb: 2 }}>Instructions & Pipeline</Typography>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12 }}>
              <TextField fullWidth size="small" label="Special Instructions" multiline rows={3} value={form.instructions} onChange={handleChange('instructions')} />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <FormControlLabel
                control={<Switch checked={form.run_pipeline} onChange={handleChange('run_pipeline')} color="primary" />}
                label="Run Agent Pipeline on Creation"
                sx={{ mt: 1 }}
              />
              <Typography variant="caption" sx={{ display: 'block', color: '#64748b', ml: 6 }}>
                When enabled, the agent will automatically process this load based on its initial state.
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      <Divider sx={{ mb: 3 }} />

      <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
        <Button variant="outlined" onClick={() => navigate('/')} disabled={submitting}>
          Cancel
        </Button>
        <Button
          variant="contained"
          startIcon={<PlayArrowIcon />}
          onClick={handleSubmit}
          disabled={submitting}
          sx={{ minWidth: 160 }}
        >
          {submitting ? 'Creating...' : 'Create & Simulate'}
        </Button>
      </Box>

      <Snackbar
        open={snack.open}
        autoHideDuration={6000}
        onClose={() => setSnack((s) => ({ ...s, open: false }))}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity={snack.severity} onClose={() => setSnack((s) => ({ ...s, open: false }))} variant="filled">
          {snack.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}
