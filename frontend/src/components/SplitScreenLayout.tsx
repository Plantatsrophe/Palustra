'use client';

import React, { useState } from 'react';
import { Columns2, Edit3, Eye } from 'lucide-react';

interface SplitScreenLayoutProps {
  leftPane: React.ReactNode;
  rightPane: React.ReactNode;
  isVerificationOpen: boolean;
  onToggleVerification: () => void;
}

export const SplitScreenLayout: React.FC<SplitScreenLayoutProps> = ({
  leftPane,
  rightPane,
  isVerificationOpen,
  onToggleVerification,
}) => {
  // Mobile active tab: 'entry' or 'verification'
  const [mobileTab, setMobileTab] = useState<'entry' | 'verification'>('entry');

  return (
    <div className="flex-1 flex flex-col min-h-0 overflow-hidden relative">
      {/* Mobile Tab Switcher (visible only on small screens) */}
      <div className="lg:hidden flex items-center border-b border-field-border bg-field-surface px-3 py-1.5 gap-2 z-10">
        <button
          onClick={() => setMobileTab('entry')}
          className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors ${
            mobileTab === 'entry'
              ? 'bg-emerald-950/80 text-emerald-200 border border-emerald-500/50 shadow-sm'
              : 'bg-field-card text-slate-400 hover:text-slate-200'
          }`}
        >
          <Edit3 className="w-3.5 h-3.5" />
          <span>Data Entry</span>
        </button>
        <button
          onClick={() => setMobileTab('verification')}
          className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors ${
            mobileTab === 'verification'
              ? 'bg-emerald-950/80 text-emerald-200 border border-emerald-500/50 shadow-sm'
              : 'bg-field-card text-slate-400 hover:text-slate-200'
          }`}
        >
          <Eye className="w-3.5 h-3.5" />
          <span>Verification Audit</span>
        </button>
      </div>

      {/* Main Workspace Layout */}
      <div className="flex-1 flex min-h-0 overflow-hidden">
        {/* Left Pane: Data Entry */}
        <div
          className={`h-full flex-col min-h-0 transition-all ${
            // On desktop: takes 1/2 or full width depending on verification panel toggle
            isVerificationOpen ? 'w-full lg:w-1/2 flex' : 'w-full flex'
          } ${
            // On mobile: toggle display via mobileTab
            mobileTab === 'entry' ? 'flex' : 'hidden lg:flex'
          }`}
        >
          {leftPane}
        </div>

        {/* Right Pane: Split-Screen Verification UI */}
        {isVerificationOpen && (
          <div
            className={`h-full flex-col min-h-0 border-l border-field-border bg-field-surface transition-all ${
              'w-full lg:w-1/2 flex'
            } ${
              mobileTab === 'verification' ? 'flex' : 'hidden lg:flex'
            }`}
          >
            {rightPane}
          </div>
        )}
      </div>
    </div>
  );
};
