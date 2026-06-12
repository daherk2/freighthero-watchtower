import { describe, it, expect } from 'vitest';
import { stateColors, statusColors, memoryTypeColors, darkTheme } from '@/theme';

describe('theme', () => {
  describe('darkTheme', () => {
    it('should be a valid MUI theme', () => {
      expect(darkTheme).toBeDefined();
      expect(darkTheme.palette.mode).toBe('dark');
    });

    it('should have primary color', () => {
      expect(darkTheme.palette.primary.main).toBe('#3b82f6');
    });

    it('should have correct background colors', () => {
      expect(darkTheme.palette.background.default).toBe('#0a0e17');
      expect(darkTheme.palette.background.paper).toBe('#1a2235');
    });

    it('should have Inter font family', () => {
      expect(darkTheme.typography.fontFamily).toContain('Inter');
    });

    it('should have custom border radius', () => {
      expect(darkTheme.shape.borderRadius).toBe(8);
    });

    it('should have MuiCard overrides', () => {
      expect(darkTheme.components.MuiCard).toBeDefined();
      expect(darkTheme.components.MuiCard.styleOverrides.root.backgroundImage).toBe('none');
    });

    it('should have MuiButton overrides', () => {
      expect(darkTheme.components.MuiButton).toBeDefined();
      expect(darkTheme.components.MuiButton.styleOverrides.root.textTransform).toBe('none');
    });
  });

  describe('stateColors', () => {
    it('should have all load states', () => {
      expect(stateColors).toHaveProperty('dispatched');
      expect(stateColors).toHaveProperty('on_route_to_delivery');
      expect(stateColors).toHaveProperty('at_delivery');
      expect(stateColors).toHaveProperty('confirm_delivery');
      expect(stateColors).toHaveProperty('delivered');
    });

    it('should have valid CSS colors', () => {
      Object.values(stateColors).forEach((color) => {
        expect(color).toMatch(/^#[0-9a-f]{6}$/i);
      });
    });
  });

  describe('statusColors', () => {
    it('should have all agent statuses', () => {
      expect(statusColors).toHaveProperty('pending');
      expect(statusColors).toHaveProperty('running');
      expect(statusColors).toHaveProperty('completed');
      expect(statusColors).toHaveProperty('failed');
    });
  });

  describe('memoryTypeColors', () => {
    it('should have episodic, semantic, procedural, STM, LTM', () => {
      expect(memoryTypeColors).toHaveProperty('episodic');
      expect(memoryTypeColors).toHaveProperty('semantic');
      expect(memoryTypeColors).toHaveProperty('procedural');
      expect(memoryTypeColors).toHaveProperty('STM');
      expect(memoryTypeColors).toHaveProperty('LTM');
    });
  });
});