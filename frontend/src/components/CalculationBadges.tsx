'use client';

import React from 'react';
import { VegetationDetermination } from '../lib/wetland/types';
import { AlertCircle, CheckCircle2, ShieldAlert, ShieldCheck, Zap } from 'lucide-react';

interface CalculationBadgesProps {
  determination: VegetationDetermination;
}

export const CalculationBadges: React.FC<CalculationBadgesProps> = ({ determination }) => {
  const {
    rapid_test_passed,
    dominance_test_a,
    dominance_test_b,
    dominance_test_percent,
    dominance_test_passed,
    prevalence_index,
    prevalence_index_passed,
    hydrophytic_vegetation_present,
  } = determination;

  return (
    <div className="w-full bg-field-surface border-b border-field-border p-3 transition-colors">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3">
        {/* Real-time Reactive Badges */}
        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          {/* Dominance % Badge */}
          <div
            id="dominance-badge"
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs sm:text-sm font-medium transition-all shadow-sm ${
              dominance_test_passed
                ? 'bg-emerald-950/70 border-emerald-500/60 text-emerald-200'
                : dominance_test_b === 0
                ? 'bg-field-card border-field-border text-slate-400'
                : 'bg-rose-950/70 border-rose-500/60 text-rose-200'
            }`}
          >
            <div className="flex items-center gap-1.5">
              <span
                className={`w-2 h-2 rounded-full ${
                  dominance_test_passed
                    ? 'bg-emerald-400 animate-pulse'
                    : dominance_test_b === 0
                    ? 'bg-slate-500'
                    : 'bg-rose-400'
                }`}
              />
              <span className="text-slate-400 font-semibold tracking-wider uppercase text-[10px] sm:text-xs">
                Dominance Test:
              </span>
            </div>
            <span className="font-mono font-bold text-sm sm:text-base">
              {dominance_test_b > 0 ? `${dominance_test_percent.toFixed(1)}%` : '0.0%'}
            </span>
            <span className="text-[11px] text-slate-400 font-mono">
              ({dominance_test_a}/{dominance_test_b})
            </span>
            <span
              className={`text-[10px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider ${
                dominance_test_passed
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                  : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
              }`}
            >
              {dominance_test_passed ? 'PASS (>50%)' : 'FAIL (≤50%)'}
            </span>
          </div>

          {/* Prevalence Score Badge */}
          <div
            id="prevalence-badge"
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs sm:text-sm font-medium transition-all shadow-sm ${
              prevalence_index_passed
                ? 'bg-emerald-950/70 border-emerald-500/60 text-emerald-200'
                : prevalence_index === null
                ? 'bg-field-card border-field-border text-slate-400'
                : 'bg-amber-950/70 border-amber-500/60 text-amber-200'
            }`}
          >
            <div className="flex items-center gap-1.5">
              <span
                className={`w-2 h-2 rounded-full ${
                  prevalence_index_passed
                    ? 'bg-emerald-400 animate-pulse'
                    : prevalence_index === null
                    ? 'bg-slate-500'
                    : 'bg-amber-400'
                }`}
              />
              <span className="text-slate-400 font-semibold tracking-wider uppercase text-[10px] sm:text-xs">
                Prevalence Index:
              </span>
            </div>
            <span className="font-mono font-bold text-sm sm:text-base">
              {prevalence_index !== null ? prevalence_index.toFixed(2) : 'N/A'}
            </span>
            <span
              className={`text-[10px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider ${
                prevalence_index_passed
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                  : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
              }`}
            >
              {prevalence_index !== null
                ? prevalence_index_passed
                  ? 'PASS (≤3.00)'
                  : 'FAIL (>3.00)'
                : 'NO DATA'}
            </span>
          </div>

          {/* Rapid Test Badge */}
          <div
            id="rapid-badge"
            className={`hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-xs font-mono ${
              rapid_test_passed
                ? 'bg-teal-950/80 border-teal-500/60 text-teal-200'
                : 'bg-field-card/80 border-field-border text-slate-400'
            }`}
          >
            <Zap className={`w-3.5 h-3.5 ${rapid_test_passed ? 'text-teal-300' : 'text-slate-500'}`} />
            <span>Rapid Test:</span>
            <span className="font-bold">{rapid_test_passed ? 'MET (100% OBL/FACW)' : 'NOT MET'}</span>
          </div>
        </div>

        {/* Master Overall Hydrophytic Status Banner */}
        <div
          id="hydrophytic-status-banner"
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs sm:text-sm font-semibold tracking-wide transition-all shadow-md ${
            hydrophytic_vegetation_present
              ? 'bg-emerald-900/80 border-emerald-400 text-emerald-100 ring-1 ring-emerald-500/30'
              : 'bg-rose-950/80 border-rose-500 text-rose-100 ring-1 ring-rose-500/30'
          }`}
        >
          {hydrophytic_vegetation_present ? (
            <>
              <ShieldCheck className="w-4 h-4 text-emerald-300" />
              <span>HYDROPHYTIC VEGETATION: PRESENT</span>
            </>
          ) : (
            <>
              <ShieldAlert className="w-4 h-4 text-rose-300" />
              <span>HYDROPHYTIC VEGETATION: ABSENT</span>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
