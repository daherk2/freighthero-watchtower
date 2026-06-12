import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import { stateColors, statusColors } from '@/theme';

// Re-export LoadSelector
export { LoadSelector } from './LoadSelector';

interface StatCardProps {
  title: string;
  value: number | string;
  subtitle?: string;
  icon?: React.ReactNode;
  trend?: 'up' | 'down' | 'flat';
  trendValue?: string;
  color?: string;
}

export function StatCard({ title, value, subtitle, icon, trend, trendValue, color }: StatCardProps) {
  return (
    <Card sx={{ height: '100%', bgcolor: '#1a2235' }}>
      <CardContent sx={{ p: 2.5, '&:last-child': { pb: 2.5 } }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1.5 }}>
          <Typography variant="caption" sx={{ color: '#64748b', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            {title}
          </Typography>
          {icon && <Box sx={{ color: color || '#3b82f6', opacity: 0.8 }}>{icon}</Box>}
        </Box>
        <Typography variant="h4" sx={{ fontWeight: 700, color: color || '#e2e8f0', mb: 0.5 }}>
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

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', py: 8, px: 4 }}>
      {icon && <Box sx={{ color: '#475569', mb: 2, fontSize: 48 }}>{icon}</Box>}
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