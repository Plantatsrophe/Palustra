'use client';

import { useEffect, useState } from 'react';
import { db, initializeStoragePersistence } from '../lib/db';

export interface StorageAudit {
  persisted: boolean;
  quotaBytes: number;
  usageBytes: number;
  percentUsed: number;
}

export function useServiceWorker() {
  const [isOnline, setIsOnline] = useState<boolean>(true);
  const [swRegistered, setSwRegistered] = useState<boolean>(false);
  const [outboxCount, setOutboxCount] = useState<number>(0);
  const [storageInfo, setStorageInfo] = useState<StorageAudit | null>(null);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    setIsOnline(navigator.onLine);

    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Register Service Worker
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker
        .register('/sw.js')
        .then((reg) => {
          setSwRegistered(true);
          console.log('Palustra Service Worker registered with scope:', reg.scope);
        })
        .catch((err) => {
          console.warn('Palustra Service Worker registration error:', err);
        });

      navigator.serviceWorker.addEventListener('message', (event) => {
        if (event.data?.type === 'TRIGGER_OUTBOX_SYNC') {
          triggerSync();
        }
      });
    }

    // Storage persistence audit
    initializeStoragePersistence().then((audit) => {
      setStorageInfo(audit);
    });

    // Outbox count monitor
    const updateOutboxCount = async () => {
      try {
        const count = await db.sync_outbox.count();
        setOutboxCount(count);
      } catch (e) {
        console.warn('Error reading outbox count:', e);
      }
    };

    updateOutboxCount();
    const interval = setInterval(updateOutboxCount, 3000);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      clearInterval(interval);
    };
  }, []);

  const triggerSync = async () => {
    if (!navigator.onLine || isSyncing) return;
    setIsSyncing(true);
    try {
      // Simulate draining outbox queue or posting to /api/sync
      const pendingRecords = await db.sync_outbox.toArray();
      if (pendingRecords.length > 0) {
        // Clear drained outbox in local db
        await db.sync_outbox.clear();
        setOutboxCount(0);
      }
    } catch (err) {
      console.warn('Sync failed:', err);
    } finally {
      setIsSyncing(false);
    }
  };

  return {
    isOnline,
    swRegistered,
    outboxCount,
    storageInfo,
    isSyncing,
    triggerSync,
  };
}
