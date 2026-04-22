import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import SettingsPanel from './SettingsPanel';
import React from 'react';

// Mock fetch to prevent actual network calls during tests
global.fetch = vi.fn(() =>
  Promise.resolve({
    json: () => Promise.resolve({ status: 'ok' }),
  })
);

describe('SettingsPanel Component', () => {
  it('renders routing and DIL sections', () => {
    render(<SettingsPanel />);
    expect(screen.getByText('Control Panel')).toBeInTheDocument();
    expect(screen.getByText('Routing Algorithm (F2/F3)')).toBeInTheDocument();
    expect(screen.getByText('DIL Adversarial Settings (R6)')).toBeInTheDocument();
  });

  it('allows selecting routing algorithms', async () => {
    render(<SettingsPanel />);
    
    const sptBtn = screen.getByText('Shortest Processing Time (SPT)');
    const eddBtn = screen.getByText('Earliest Due Date (EDD)');
    
    // Test selecting EDD
    fireEvent.click(eddBtn);
    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/settings/routing',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ algorithm: 'EDD' }),
      })
    );

    // Test selecting SPT
    fireEvent.click(sptBtn);
    expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/settings/routing',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ algorithm: 'SPT' }),
        })
      );
  });
  
  it('allows applying DIL profile', async () => {
      render(<SettingsPanel />);
      const applyBtn = screen.getByText('Apply DIL Profile');
      fireEvent.click(applyBtn);
      
      expect(global.fetch).toHaveBeenCalledWith(
          'http://localhost:8000/settings/dil',
          expect.objectContaining({
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: expect.stringContaining('"r6_offline":false')
          })
      );
  });
});
