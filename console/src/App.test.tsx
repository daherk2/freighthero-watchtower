import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ThemeProvider } from '@mui/material/styles';
import { darkTheme } from '@/theme';
import type { ReactNode } from 'react';

// Mock BrowserRouter to just render children (we'll wrap with MemoryRouter in the test)
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    BrowserRouter: ({ children }: { children: ReactNode }) => <>{children}</>,
  };
});

import App from '@/App';
import { MemoryRouter } from 'react-router-dom';

describe('App routing', () => {
  it('should render Dashboard on root route', () => {
    render(
      <ThemeProvider theme={darkTheme}>
        <MemoryRouter initialEntries={['/']}>
          <App />
        </MemoryRouter>
      </ThemeProvider>
    );
    // Dashboard renders with title "Operations Dashboard"
    expect(screen.getByText('Operations Dashboard')).toBeInTheDocument();
  });
});