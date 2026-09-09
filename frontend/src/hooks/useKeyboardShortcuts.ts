'use client';

import { useEffect, useState } from 'react';
import { StratumType } from '../lib/wetland/types';

interface ShortcutOptions {
  onSelectStratum?: (stratum: StratumType) => void;
  onToggleVerification?: () => void;
  onToggleShortcutsModal?: () => void;
}

export function useKeyboardShortcuts({
  onSelectStratum,
  onToggleVerification,
  onToggleShortcutsModal,
}: ShortcutOptions) {
  const [wakeLockActive, setWakeLockActive] = useState(false);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const activeTag = (document.activeElement?.tagName || '').toLowerCase();
      const isInputActive = activeTag === 'input' || activeTag === 'select' || activeTag === 'textarea';

      // Alt+1..4 for strata switching
      if (e.altKey && !e.ctrlKey && !e.metaKey) {
        if (e.key === '1') {
          e.preventDefault();
          onSelectStratum?.('tree');
        } else if (e.key === '2') {
          e.preventDefault();
          onSelectStratum?.('sapling_shrub');
        } else if (e.key === '3') {
          e.preventDefault();
          onSelectStratum?.('herb');
        } else if (e.key === '4') {
          e.preventDefault();
          onSelectStratum?.('woody_vine');
        } else if (e.key.toLowerCase() === 'v') {
          e.preventDefault();
          onToggleVerification?.();
        } else if (e.key === '/' || e.key === '?') {
          e.preventDefault();
          onToggleShortcutsModal?.();
        }
      }

      // Non-input single key shortcuts
      if (!isInputActive && !e.altKey && !e.ctrlKey && !e.metaKey) {
        if (e.key === '?' || (e.shiftKey && e.key === '/')) {
          e.preventDefault();
          onToggleShortcutsModal?.();
        } else if (e.key.toLowerCase() === 'v') {
          e.preventDefault();
          onToggleVerification?.();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onSelectStratum, onToggleVerification, onToggleShortcutsModal]);

  // Screen Wake Lock API for field surveys
  const toggleWakeLock = async () => {
    if (typeof window === 'undefined' || !('wakeLock' in navigator)) return;

    if (!wakeLockActive) {
      try {
        const sentinel = await (navigator as any).wakeLock.request('screen');
        setWakeLockActive(true);
        sentinel.addEventListener('release', () => {
          setWakeLockActive(false);
        });
      } catch (err) {
        console.warn('Screen wake lock request denied:', err);
      }
    }
  };

  return {
    wakeLockActive,
    toggleWakeLock,
  };
}
