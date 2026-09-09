'use client';

import React from 'react';
import {
  Columns2,
  HardDrive,
  HelpCircle,
  Lock,
  Moon,
  Sun,
  RefreshCw,
  SunMedium,
  Wifi,
  WifiOff,
} from 'lucide-react';
import { StorageAudit } from '../hooks/useServiceWorker';

interface AppHeaderProps {
  projectName: string;
  plotName: string;
  region: 'EMP' | 'AGCP';
  onToggleRegion: () => void;
  isOnline: boolean;
  outboxCount: number;
  isSyncing: boolean;
  onTriggerSync: () => void;
  storageInfo: StorageAudit | null;
  wakeLockActive: boolean;
  onToggleWakeLock: () => void;
  isVerificationOpen: boolean;
  onToggleVerification: () => void;
  onOpenShortcuts: () => void;
  isSunlightMode: boolean;
  onToggleSunlightMode: () => void;
}

export const AppHeader: React.FC<AppHeaderProps> = ({
  projectName,
  plotName,
  region,
  onToggleRegion,
  isOnline,
  outboxCount,
  isSyncing,
  onTriggerSync,
  storageInfo,
  wakeLockActive,
  onToggleWakeLock,
  isVerificationOpen,
  onToggleVerification,
  onOpenShortcuts,
  isSunlightMode,
  onToggleSunlightMode,
}) => {
  return (
    <header className="bg-field-surface border-b border-field-border px-3 py-2 text-slate-200">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-3">
        {/* Left: Branding & Current Plot */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400 font-bold">
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                <path d="M12 8v8" />
                <path d="M8 12h8" />
              </svg>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-sm font-bold text-slate-100 tracking-tight">PALUSTRA PWA</h1>
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-950 text-emerald-300 border border-emerald-600/40 font-mono">
                  OFFLINE-FIRST
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-mono truncate max-w-[180px] sm:max-w-xs">
                {plotName}
              </p>
            </div>
          </div>

          {/* Region Switcher Badge */}
          <button
            onClick={onToggleRegion}
            className="hidden sm:flex items-center gap-1.5 px-2 py-1 rounded bg-field-card border border-field-border hover:border-slate-500 text-xs font-mono font-bold text-slate-300 transition-colors"
            title="Click to toggle Regional Supplement (EMP / AGCP)"
          >
            <span className="text-slate-500 text-[10px]">REGION:</span>
            <span className="text-emerald-400">{region}</span>
          </button>
        </div>

        {/* Right: Actions, Storage, Sync, and Shortcuts */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Storage Quota & Persistence Indicator */}
          {storageInfo && (
            <div
              className="hidden md:flex items-center gap-1.5 px-2 py-1 rounded bg-field-card border border-field-border text-[11px] font-mono text-slate-400"
              title={`Persistent Storage: ${storageInfo.persisted ? 'Granted' : 'Best-Effort'} | Storage Used: ${(
                storageInfo.usageBytes / (1024 * 1024)
              ).toFixed(1)} MB`}
            >
              <HardDrive className={`w-3.5 h-3.5 ${storageInfo.persisted ? 'text-emerald-400' : 'text-amber-400'}`} />
              <span>{storageInfo.persisted ? 'PERSISTED' : 'STORAGE'}</span>
            </div>
          )}

          {/* Wake Lock Button */}
          <button
            onClick={onToggleWakeLock}
            className={`p-1.5 rounded-lg border text-xs flex items-center gap-1 transition-colors ${
              wakeLockActive
                ? 'bg-amber-950/80 border-amber-500 text-amber-300'
                : 'bg-field-card border-field-border text-slate-400 hover:text-slate-200'
            }`}
            title="Screen Wake Lock (prevents tablet display from sleeping while recording)"
          >
            <SunMedium className="w-4 h-4" />
            <span className="hidden xl:inline text-[10px] font-mono">
              {wakeLockActive ? 'AWAKE' : 'SLEEP OK'}
            </span>
          </button>

          {/* Sunlight Mode Toggle */}
          <button
            onClick={onToggleSunlightMode}
            className={`p-1.5 rounded-lg border text-xs transition-colors ${
              isSunlightMode
                ? 'bg-amber-400 text-slate-900 border-amber-500 font-bold'
                : 'bg-field-card border-field-border text-slate-400 hover:text-slate-200'
            }`}
            title="Toggle High-Contrast Outdoor Sunlight Mode"
          >
            {isSunlightMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>

          {/* Sync Outbox Button & Network Status */}
          <div className="flex items-center gap-1.5">
            <button
              onClick={onTriggerSync}
              disabled={isSyncing || !isOnline}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs font-mono transition-all ${
                outboxCount > 0
                  ? 'bg-amber-950/80 border-amber-500 text-amber-300 animate-pulse'
                  : 'bg-field-card border-field-border text-slate-300 hover:bg-field-card/80'
              }`}
              title="Sync Outbox Queue"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin text-emerald-400' : ''}`} />
              <span>{outboxCount > 0 ? `${outboxCount} Pending` : 'Synced'}</span>
            </button>

            {/* Network Indicator */}
            <div
              className={`p-1.5 rounded-lg border ${
                isOnline
                  ? 'bg-emerald-950/80 border-emerald-600/50 text-emerald-400'
                  : 'bg-rose-950/80 border-rose-600/50 text-rose-400'
              }`}
              title={isOnline ? 'Network Connected (Online)' : 'No Network (Zero-Connectivity Mode)'}
            >
              {isOnline ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
            </div>
          </div>

          {/* Split-Screen Verification Toggle (Alt+V) */}
          <button
            onClick={onToggleVerification}
            className={`hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs font-semibold transition-all ${
              isVerificationOpen
                ? 'bg-emerald-950/80 border-emerald-500 text-emerald-300 ring-1 ring-emerald-500/40'
                : 'bg-field-card border-field-border text-slate-300 hover:border-slate-500'
            }`}
            title="Toggle Split-Screen Verification Panel (Alt+V)"
          >
            <Columns2 className="w-4 h-4" />
            <span>Split View</span>
            <kbd className="text-[10px] font-mono px-1 py-0.2 bg-field-surface rounded border border-field-border text-slate-400">
              Alt+V
            </kbd>
          </button>

          {/* Keyboard Shortcuts Help Button */}
          <button
            onClick={onOpenShortcuts}
            className="p-1.5 rounded-lg bg-field-card border border-field-border hover:border-slate-500 text-slate-400 hover:text-slate-200 transition-colors"
            title="Keyboard Shortcuts Cheatsheet (Press ?)"
          >
            <HelpCircle className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
};
