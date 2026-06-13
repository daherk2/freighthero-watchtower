import { useState } from 'react';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Skeleton from '@mui/material/Skeleton';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CheckIcon from '@mui/icons-material/Check';
import { stateColors, statusColors } from '@/theme';

export { LoadSelector } from './LoadSelector';

// --- CopyButton ---

interface CopyButtonProps {
  value: string;
  size?: number;
}

export function CopyButton({ value, size = 13 }: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(value).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  };

  return (
    <Tooltip title={copied ? 'Copied!' : 'Copy'} placement="top">
      <IconButton
        size="small"
        onClick={handleCopy}
        aria-label="copy to clipboard"
        sx={{
          p: 0.25,
          color: copied ? '#22c55e' : '#475569',
          '&:hover': { color: copied ? '#22c55e' : '#94a3b8', bgcolor: 'transparent' },
          transition: 'color 0.15s',
        }}
      >
        {copied
          ? <CheckIcon sx={{ fontSize: size }} />
          : <ContentCopyIcon sx={{ fontSize: size }} />
        }
      </IconButton>
    </Tooltip>
  );
}

// --- TruncatedId ---

interface TruncatedIdProps {
  id: string;
  chars?: number;
  color?: string;
}

export function TruncatedId({ id, chars = 12, color = '#3b82f6' }: TruncatedIdProps) {
  return (
    <Box sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.25 }}>
      <Typography
        component="span"
        sx={{
          fontFamily: 'monospace',
          fontSize: '0.8rem',
          color,
          letterSpacing: '-0.3px',
        }}
      >
        {id.slice(0, chars)}…
      </Typography>
      <CopyButton value={id} />
    </Box>
  );
}

// --- StatCard ---

interface StatCardProps {
  title: string;
  value: number | string;
  subtitle?: string;
  icon?: React.ReactNode;
  trend?: 'up' | 'down' | 'flat';
  trendValue?: string;
  color?: string;
  loading?: boolean;
}

export function StatCard({ title, value, subtitle, icon, trend, trendValue, color, loading }: StatCardProps) {
  if (loading) return <SkeletonStatCard />;

  return (
    <Card sx={{ height: '100%', bgcolor: '#1a2235' }}>
      <CardContent sx={{ p: 2.5, '&:last-child': { pb: 2.5 } }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1.5 }}>
          <Typography
            variant="caption"
            sx={{ color: '#64748b', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}
          >
            {title}
          </Typography>
          {icon && <Box sx={{ color: color || '#3b82f6', opacity: 0.8 }}>{icon}</Box>}
        </Box>
        <Typography variant="h4" sx={{ fontWeight: 700, color: color || '#e2e8f0', mb: 0.5, fontSize: '1.75rem' }}>
          {value}
        </Typography>
        {(subtitle || trendValue) && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            {trend && (
              <Typography
                variant="caption"
                sx={{
                  color: trend === 'up' ? '#22c55e' : trend === 'down' ? '#ef4444' : '#94a3b8',
                  fontWeight: 600,
                }}
              >
                {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'} {trendValue}
              </Typography>
            )}
            {subtitle && (
              <Typography variant="caption" sx={{ color: '#64748b' }}>
                {subtitle}
              </Typography>
            )}
          </Box>
        )}
      </CardContent>
    </Card>
  );
}

export function SkeletonStatCard() {
  return (
    <Card sx={{ height: '100%', bgcolor: '#1a2235' }}>
      <CardContent sx={{ p: 2.5, '&:last-child': { pb: 2.5 } }}>
        <Skeleton variant="text" width="60%" height={16} sx={{ mb: 1.5, bgcolor: '#243049' }} />
        <Skeleton variant="text" width="40%" height={40} sx={{ mb: 0.5, bgcolor: '#243049' }} />
        <Skeleton variant="text" width="50%" height={14} sx={{ bgcolor: '#243049' }} />
      </CardContent>
    </Card>
  );
}

// --- StatusChip ---

interface StatusChipProps {
  status: string;
  size?: 'small' | 'medium';
}

export function StatusChip({ status, size = 'small' }: StatusChipProps) {
  const color = statusColors[status] || '#94a3b8';
  return (
    <Chip
      label={status.replace(/_/g, ' ')}
      size={size}
      sx={{
        bgcolor: `${color}20`,
        color,
        fontWeight: 600,
        fontSize: size === 'small' ? '0.6875rem' : '0.75rem',
        textTransform: 'capitalize',
        border: `1px solid ${color}40`,
      }}
    />
  );
}

// --- StateChip ---

interface StateChipProps {
  state: string;
}

export function StateChip({ state }: StateChipProps) {
  const color = stateColors[state] || '#94a3b8';
  return (
    <Chip
      label={state.replace(/_/g, ' ')}
      size="small"
      sx={{
        bgcolor: `${color}20`,
        color,
        fontWeight: 600,
        fontSize: '0.6875rem',
        textTransform: 'capitalize',
        border: `1px solid ${color}40`,
      }}
    />
  );
}

// --- SectionHeader ---

interface SectionHeaderProps {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}

export function SectionHeader({ title, subtitle, action }: SectionHeaderProps) {
  return (
    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
      <Box>
        <Typography variant="h6" sx={{ fontWeight: 600, color: '#e2e8f0' }}>
          {title}
        </Typography>
        {subtitle && (
          <Typography variant="caption" sx={{ color: '#64748b' }}>
            {subtitle}
          </Typography>
        )}
      </Box>
      {action}
    </Box>
  );
}

// --- EmptyState ---

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        py: 8,
        px: 4,
      }}
    >
      {icon && <Box sx={{ color: '#334155', mb: 2 }}>{icon}</Box>}
      <Typography variant="h6" sx={{ color: '#64748b', mb: 1 }}>
        {title}
      </Typography>
      {description && (
        <Typography variant="body2" sx={{ color: '#475569', textAlign: 'center', maxWidth: 400 }}>
          {description}
        </Typography>
      )}
      {action && <Box sx={{ mt: 2 }}>{action}</Box>}
    </Box>
  );
}
