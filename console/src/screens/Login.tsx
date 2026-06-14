import React from 'react';
import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import TextField from '@mui/material/TextField';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import { AUTH_KEY } from '@/api/client';

interface LoginProps {
  onAuth: () => void;
}

export function Login({ onAuth }: LoginProps) {
  const [token, setToken] = React.useState('');
  const [error, setError] = React.useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const res = await fetch('/api/v1/monitoring/dashboard', {
      headers: { 'X-API-Key': token },
    });
    if (res.ok) {
      localStorage.setItem(AUTH_KEY, token);
      onAuth();
    } else {
      setError(true);
    }
  };

  return (
    <Box sx={{
      minHeight: '100vh', display: 'flex', alignItems: 'center',
      justifyContent: 'center', bgcolor: '#0a0e17',
    }}>
      <Card sx={{ bgcolor: '#1a2235', width: 360 }}>
        <CardContent sx={{ p: 4 }}>
          <Typography variant="h5" sx={{ fontWeight: 700, mb: 0.5, color: '#e2e8f0' }}>
            FreightHero Watchtower
          </Typography>
          <Typography variant="body2" sx={{ color: '#64748b', mb: 3 }}>
            Enter your access token to continue
          </Typography>
          <form onSubmit={handleSubmit}>
            <TextField
              fullWidth
              type="password"
              label="Token"
              value={token}
              onChange={(e) => { setToken(e.target.value); setError(false); }}
              error={error}
              helperText={error ? 'Invalid token' : ''}
              sx={{
                mb: 2,
                '& .MuiOutlinedInput-root': { color: '#e2e8f0', '& fieldset': { borderColor: '#2a3a52' } },
                '& .MuiInputLabel-root': { color: '#64748b' },
              }}
              autoFocus
            />
            <Button
              type="submit"
              variant="contained"
              fullWidth
              disabled={!token}
              sx={{ bgcolor: '#3b82f6', '&:hover': { bgcolor: '#2563eb' }, py: 1.25 }}
            >
              Sign in
            </Button>
          </form>
        </CardContent>
      </Card>
    </Box>
  );
}
