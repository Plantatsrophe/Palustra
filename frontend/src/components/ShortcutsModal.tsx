'use client';

import React from 'react';
import { Keyboard, X, Sparkles, Zap, Smartphone, Check } from 'lucide-react';

interface ShortcutsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ShortcutsModal: React.FC<ShortcutsModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
      <div className="bg-field-surface border border-field-border rounded-2xl shadow-2xl max-w-lg w-full p-5 space-y-4 text-slate-200">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-field-border/80 pb-3">
          <div className="flex items-center gap-2">
            <Keyboard className="w-5 h-5 text-emerald-400" />
            <h2 className="text-base font-bold text-slate-100">Field Speed Shortcuts & Commands</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-field-card transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Shortcuts List */}
        <div className="space-y-4 text-xs font-mono">
          <div>
            <h3 className="text-emerald-400 font-bold uppercase tracking-wider mb-2 text-[11px]">
              Stratum Quick Navigation
            </h3>
            <div className="grid grid-cols-2 gap-2">
              <div className="bg-field-card p-2 rounded-lg border border-field-border flex items-center justify-between">
                <span>Tree Stratum</span>
                <kbd className="px-1.5 py-0.5 bg-field-surface rounded border border-field-border text-emerald-300 font-bold">
                  Alt+1
                </kbd>
              </div>
              <div className="bg-field-card p-2 rounded-lg border border-field-border flex items-center justify-between">
                <span>Sapling/Shrub</span>
                <kbd className="px-1.5 py-0.5 bg-field-surface rounded border border-field-border text-emerald-300 font-bold">
                  Alt+2
                </kbd>
              </div>
              <div className="bg-field-card p-2 rounded-lg border border-field-border flex items-center justify-between">
                <span>Herb Stratum</span>
                <kbd className="px-1.5 py-0.5 bg-field-surface rounded border border-field-border text-emerald-300 font-bold">
                  Alt+3
                </kbd>
              </div>
              <div className="bg-field-card p-2 rounded-lg border border-field-border flex items-center justify-between">
                <span>Woody Vine</span>
                <kbd className="px-1.5 py-0.5 bg-field-surface rounded border border-field-border text-emerald-300 font-bold">
                  Alt+4
                </kbd>
              </div>
            </div>
          </div>

          <div>
            <h3 className="text-emerald-400 font-bold uppercase tracking-wider mb-2 text-[11px]">
              Data Entry & Verification
            </h3>
            <div className="space-y-1.5">
              <div className="bg-field-card p-2 rounded-lg border border-field-border flex items-center justify-between">
                <span className="font-sans text-slate-300">Submit Taxon & Focus Next</span>
                <kbd className="px-1.5 py-0.5 bg-field-surface rounded border border-field-border text-slate-200">
                  Enter
                </kbd>
              </div>
              <div className="bg-field-card p-2 rounded-lg border border-field-border flex items-center justify-between">
                <span className="font-sans text-slate-300">Toggle Split-Screen Audit UI</span>
                <kbd className="px-1.5 py-0.5 bg-field-surface rounded border border-field-border text-slate-200">
                  Alt+V / v
                </kbd>
              </div>
              <div className="bg-field-card p-2 rounded-lg border border-field-border flex items-center justify-between">
                <span className="font-sans text-slate-300">Navigate Dropdown Suggestions</span>
                <span className="text-slate-400">ArrowUp / ArrowDown</span>
              </div>
              <div className="bg-field-card p-2 rounded-lg border border-field-border flex items-center justify-between">
                <span className="font-sans text-slate-300">Dismiss Dropdown / Modal</span>
                <kbd className="px-1.5 py-0.5 bg-field-surface rounded border border-field-border text-slate-200">
                  Escape
                </kbd>
              </div>
            </div>
          </div>

          {/* Zero-Connectivity Guarantee Banner */}
          <div className="bg-emerald-950/60 border border-emerald-500/40 rounded-xl p-3 space-y-1">
            <div className="flex items-center gap-1.5 text-emerald-300 font-bold text-xs">
              <Sparkles className="w-4 h-4" />
              <span>Offline-First Field Guarantee</span>
            </div>
            <p className="text-[11px] font-sans text-slate-300 leading-relaxed">
              Every keystroke saves synchronously to local browser IndexedDB storage via Dexie.js. You can safely operate in deep wilderness or airplane mode with 100% functionality.
            </p>
          </div>
        </div>

        <div className="pt-2 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
