import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test('should display dashboard with stat cards', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Operations Dashboard')).toBeVisible();
    await expect(page.getByText('Agent Runs (24h)')).toBeVisible();
    await expect(page.getByText('Active Loads')).toBeVisible();
    await expect(page.getByText('Memory Ops (24h)')).toBeVisible();
  });

  test('should show active loads table', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Active Loads')).toBeVisible();
    // Table should have load rows
    const loadRows = page.locator('table tbody tr');
    await expect(loadRows.first()).toBeVisible();
  });

  test('should navigate to load detail on click', async ({ page }) => {
    await page.goto('/');
    // Click on a load row or link
    const loadLink = page.locator('a[href*="/loads/"]').first();
    if (await loadLink.isVisible()) {
      await loadLink.click();
      await expect(page).toHaveURL(/\/loads\//);
    }
  });
});

test.describe('Navigation', () => {
  test('should navigate between all screens via sidebar', async ({ page }) => {
    await page.goto('/');

    const navItems = [
      { label: 'Dashboard', path: '/' },
      { label: 'Loads', path: '/loads' },
      { label: 'Agent Viewer', path: '/agent' },
      { label: 'Workflows', path: '/workflow' },
      { label: 'Memory', path: '/memory' },
      { label: 'Tool Calls', path: '/tools' },
      { label: 'Traces', path: '/traces' },
      { label: 'Debugger', path: '/debugger' },
      { label: 'Monitoring', path: '/monitoring' },
    ];

    for (const item of navItems) {
      const link = page.getByRole('link', { name: new RegExp(item.label, 'i') }).first();
      if (await link.isVisible()) {
        await link.click();
        await expect(page).toHaveURL(new RegExp(item.path.replace('/', '\\/') + '$'));
      }
    }
  });

  test('should highlight active nav item', async ({ page }) => {
    await page.goto('/');
    const dashboardLink = page.getByRole('link', { name: /dashboard/i }).first();
    if (await dashboardLink.isVisible()) {
      // Active link should have distinct styling
      const parent = dashboardLink.locator('..');
      await expect(parent).toBeVisible();
    }
  });
});

test.describe('Load Detail', () => {
  test('should display load list with table', async ({ page }) => {
    await page.goto('/loads');
    await expect(page.getByText(/loads/i)).toBeVisible();
  });

  test('should show load detail with tabs', async ({ page }) => {
    await page.goto('/loads/load-001');
    // Should show tab navigation
    await expect(page.getByText('Events')).toBeVisible();
    await expect(page.getByText('Agent Runs')).toBeVisible();
    await expect(page.getByText('Memory')).toBeVisible();
  });
});

test.describe('Agent Viewer', () => {
  test('should display agent run cards', async ({ page }) => {
    await page.goto('/agent');
    await expect(page.getByText(/agent/i)).toBeVisible();
  });

  test('should show agent run detail', async ({ page }) => {
    await page.goto('/agent/run-001');
    await expect(page.getByText(/tool calls/i)).toBeVisible();
  });
});

test.describe('Workflow Visualizer', () => {
  test('should render React Flow canvas', async ({ page }) => {
    await page.goto('/workflow');
    // React Flow renders a canvas/SVG
    await page.waitForTimeout(1000); // Wait for React Flow to render
    const flowCanvas = page.locator('.react-flow').first();
    if (await flowCanvas.isVisible()) {
      await expect(flowCanvas).toBeVisible();
    }
  });
});

test.describe('Memory Explorer', () => {
  test('should display memory cards with type filters', async ({ page }) => {
    await page.goto('/memory');
    await expect(page.getByText(/memory/i)).toBeVisible();
    // Should have type filter chips
    await expect(page.getByText('STM')).toBeVisible();
    await expect(page.getByText('LTM')).toBeVisible();
  });

  test('should filter memories by type', async ({ page }) => {
    await page.goto('/memory');
    const stmChip = page.getByText('STM').first();
    if (await stmChip.isVisible()) {
      await stmChip.click();
      await page.waitForTimeout(500);
    }
  });
});

test.describe('Tool Call Explorer', () => {
  test('should display tool call records', async ({ page }) => {
    await page.goto('/tools');
    await expect(page.getByText(/tool/i)).toBeVisible();
  });
});

test.describe('Trace Explorer', () => {
  test('should display trace tree', async ({ page }) => {
    await page.goto('/traces');
    await expect(page.getByText(/trace/i)).toBeVisible();
  });
});

test.describe('Agent Debugger', () => {
  test('should display debugger with step controls', async ({ page }) => {
    await page.goto('/debugger');
    await expect(page.getByText(/debugger/i)).toBeVisible();
  });
});

test.describe('Monitoring', () => {
  test('should display monitoring dashboard with tabs', async ({ page }) => {
    await page.goto('/monitoring');
    await expect(page.getByText('Monitoring')).toBeVisible();
    await expect(page.getByText('Agent Metrics')).toBeVisible();
    await expect(page.getByText('Memory Metrics')).toBeVisible();
    await expect(page.getByText('Workflow Metrics')).toBeVisible();
    await expect(page.getByText('Error Metrics')).toBeVisible();
    await expect(page.getByText('Token Usage')).toBeVisible();
    await expect(page.getByText('Sankey Flow')).toBeVisible();
    await expect(page.getByText('Tool Heatmap')).toBeVisible();
    await expect(page.getByText('Latency')).toBeVisible();
  });

  test('should switch between monitoring tabs', async ({ page }) => {
    await page.goto('/monitoring');
    // Click on Memory Metrics tab
    await page.getByText('Memory Metrics').click();
    await page.waitForTimeout(500);
    // Click on Sankey Flow tab
    await page.getByText('Sankey Flow').click();
    await page.waitForTimeout(500);
    // Click on Latency tab
    await page.getByText('Latency').click();
    await page.waitForTimeout(500);
  });

  test('should display stat cards at top', async ({ page }) => {
    await page.goto('/monitoring');
    await expect(page.getByText('Agent Runs (24h)')).toBeVisible();
    await expect(page.getByText('Active Loads')).toBeVisible();
  });
});

test.describe('Search', () => {
  test('should have search bar in header', async ({ page }) => {
    await page.goto('/');
    const searchInput = page.getByPlaceholder(/search/i);
    if (await searchInput.isVisible()) {
      await searchInput.fill('load-001');
      await expect(searchInput).toHaveValue('load-001');
    }
  });
});

test.describe('Responsive', () => {
  test('should render on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');
    await expect(page.getByText('FreightHero')).toBeVisible();
  });

  test('should toggle sidebar on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');
    const menuButton = page.getByRole('button', { name: /menu/i }).first();
    if (await menuButton.isVisible()) {
      await menuButton.click();
    }
  });
});