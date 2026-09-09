'use client';

import React, { useState } from 'react';
import {
  StratumType,
  STRATA_CONFIG,
  VegetationDetermination,
} from '../lib/wetland/types';
import {
  Calculator,
  CheckCircle2,
  Copy,
  Info,
  Scale,
  XCircle,
  FileCheck,
  Check,
} from 'lucide-react';

interface VerificationPanelProps {
  determination: VegetationDetermination;
  activeStratum: StratumType;
  onSelectStratum: (stratum: StratumType) => void;
  plotName: string;
  region: 'EMP' | 'AGCP';
}

export const VerificationPanel: React.FC<VerificationPanelProps> = ({
  determination,
  activeStratum,
  onSelectStratum,
  plotName,
  region,
}) => {
  const [copied, setCopied] = useState(false);
  const activeStratumResult = determination.strata_results[activeStratum];
  const {
    rapid_test_passed,
    dominance_test_a,
    dominance_test_b,
    dominance_test_percent,
    dominance_test_passed,
    prevalence_index,
    prevalence_index_passed,
    prevalence_breakdown,
    hydrophytic_vegetation_present,
    remarks,
  } = determination;

  const handleCopySummary = () => {
    const text = `USACE WETLAND DETERMINATION VEGETATION AUDIT
Plot: ${plotName} | Region: ${region}
Determination: ${hydrophytic_vegetation_present ? 'HYDROPHYTIC PRESENT' : 'HYDROPHYTIC ABSENT'}

1. RAPID TEST: ${rapid_test_passed ? 'PASSED (100% OBL/FACW)' : 'FAILED'}
2. DOMINANCE TEST (50/20 Rule):
   - Hydrophytic Dominants (A): ${dominance_test_a}
   - Total Dominants (B): ${dominance_test_b}
   - Dominance %: ${dominance_test_percent.toFixed(1)}% (Passing criterion > 50.0%)
   - Result: ${dominance_test_passed ? 'PASSED' : 'FAILED'}
3. PREVALENCE INDEX:
   - OBL: ${prevalence_breakdown.obl_cover}% (x1 = ${prevalence_breakdown.obl_cover * 1})
   - FACW: ${prevalence_breakdown.facw_cover}% (x2 = ${prevalence_breakdown.facw_cover * 2})
   - FAC: ${prevalence_breakdown.fac_cover}% (x3 = ${prevalence_breakdown.fac_cover * 3})
   - FACU: ${prevalence_breakdown.facu_cover}% (x4 = ${prevalence_breakdown.facu_cover * 4})
   - UPL: ${prevalence_breakdown.upl_cover}% (x5 = ${prevalence_breakdown.upl_cover * 5})
   - Total Cover: ${prevalence_breakdown.total_cover}% | Weighted Sum: ${prevalence_breakdown.weighted_sum}
   - Score: ${prevalence_index !== null ? prevalence_index.toFixed(2) : 'N/A'} (Passing criterion <= 3.00)
   - Result: ${prevalence_index_passed ? 'PASSED' : 'FAILED'}

Remarks:
${remarks.join('\n')}`;

    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col h-full bg-field-surface overflow-y-auto">
      {/* Verification Header */}
      <div className="p-3 bg-field-card border-b border-field-border flex items-center justify-between sticky top-0 z-20 shadow-sm">
        <div className="flex items-center gap-2">
          <Scale className="w-5 h-5 text-emerald-400" />
          <div>
            <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
              USACE Verification Audit
            </h2>
            <p className="text-[11px] text-slate-400 font-mono">
              Plot: {plotName} | Supplement: {region}
            </p>
          </div>
        </div>

        <button
          onClick={handleCopySummary}
          className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-field-surface border border-field-border hover:border-slate-500 text-xs text-slate-200 font-medium transition-colors"
          title="Copy full USACE determination audit text to clipboard"
        >
          {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          <span>{copied ? 'Copied!' : 'Copy Form Audit'}</span>
        </button>
      </div>

      <div className="p-4 space-y-5 flex-1">
        {/* Section 1: Active Stratum 50/20 Audit */}
        <div className="bg-field-card rounded-xl border border-field-border p-3.5 shadow-sm space-y-3">
          <div className="flex items-center justify-between border-b border-field-border/60 pb-2">
            <div className="flex items-center gap-2">
              <Calculator className="w-4 h-4 text-emerald-400" />
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wide">
                50/20 Rule Ledger: {STRATA_CONFIG[activeStratum].label}
              </h3>
            </div>
            <span className="text-[11px] font-mono text-slate-400">
              Total Cover: <strong className="text-emerald-400">{activeStratumResult.total_cover}%</strong>
            </span>
          </div>

          {/* Mathematical Thresholds */}
          <div className="grid grid-cols-2 gap-2 text-xs font-mono bg-field-surface/70 p-2 rounded-lg border border-field-border">
            <div>
              <span className="text-slate-400">50% Threshold (Strict &gt;):</span>
              <p className="text-slate-200 font-bold">{activeStratumResult.threshold_50}%</p>
            </div>
            <div>
              <span className="text-slate-400">20% Threshold (≥):</span>
              <p className="text-slate-200 font-bold">{activeStratumResult.threshold_20}%</p>
            </div>
          </div>

          {/* Ranked Species Table */}
          {activeStratumResult.ranked_species.length === 0 ? (
            <p className="text-xs text-slate-500 text-center py-4">No species recorded in this stratum.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-field-border text-slate-400 text-[10px] uppercase">
                    <th className="py-1 px-1.5 w-6">#</th>
                    <th className="py-1 px-1.5">Taxon</th>
                    <th className="py-1 px-1.5 w-12">Ind.</th>
                    <th className="py-1 px-1.5 w-14 text-right">Cover</th>
                    <th className="py-1 px-1.5 w-14 text-right">Cumul.</th>
                    <th className="py-1 px-1.5 text-center">Rule</th>
                    <th className="py-1 px-1.5 text-center w-16">Dominant</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-field-border/40">
                  {activeStratumResult.ranked_species.map((row) => (
                    <tr
                      key={row.id}
                      className={row.is_dominant ? 'bg-emerald-950/20 text-emerald-200' : 'text-slate-300'}
                    >
                      <td className="py-1.5 px-1.5 text-slate-500">{row.rank}</td>
                      <td className="py-1.5 px-1.5 font-sans font-medium text-slate-100 italic truncate max-w-[120px]">
                        {row.taxon}
                      </td>
                      <td className="py-1.5 px-1.5 font-bold">{row.indicator_status}</td>
                      <td className="py-1.5 px-1.5 text-right font-bold">{row.percent_cover}%</td>
                      <td className="py-1.5 px-1.5 text-right text-slate-400">{row.cumulative_percent}%</td>
                      <td className="py-1.5 px-1.5 text-center text-[10px]">
                        {row.is_d50 && <span className="text-emerald-400 font-bold mr-1">50%</span>}
                        {row.is_tied50 && <span className="text-amber-400 font-bold mr-1">TIED</span>}
                        {row.is_d20 && <span className="text-teal-400 font-bold">20%</span>}
                        {!row.is_d50 && !row.is_tied50 && !row.is_d20 && (
                          <span className="text-slate-600">—</span>
                        )}
                      </td>
                      <td className="py-1.5 px-1.5 text-center">
                        {row.is_dominant ? (
                          <span className="inline-flex items-center px-1.5 py-0.2 rounded text-[9px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 uppercase">
                            YES
                          </span>
                        ) : (
                          <span className="text-slate-500 text-[10px]">NO</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Section 2: Dominance Test Verification Ledger */}
        <div className="bg-field-card rounded-xl border border-field-border p-3.5 shadow-sm space-y-3">
          <div className="flex items-center justify-between border-b border-field-border/60 pb-2">
            <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wide">
              Dominance Test Criterion (Across All Strata)
            </h3>
            <span
              className={`text-xs font-bold font-mono px-2 py-0.5 rounded ${
                dominance_test_passed
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                  : 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
              }`}
            >
              {dominance_test_passed ? 'PASSED (> 50.0%)' : 'FAILED (≤ 50.0%)'}
            </span>
          </div>

          <div className="bg-field-surface/70 p-3 rounded-lg border border-field-border space-y-2 text-xs font-mono">
            <div className="flex items-center justify-between text-slate-300">
              <span>(A) Hydrophytic Dominants (OBL, FACW, FAC):</span>
              <strong className="text-emerald-400 text-sm">{dominance_test_a}</strong>
            </div>
            <div className="flex items-center justify-between text-slate-300">
              <span>(B) Total Dominant Occurrences:</span>
              <strong className="text-slate-200 text-sm">{dominance_test_b}</strong>
            </div>
            <div className="border-t border-field-border pt-2 flex items-center justify-between text-slate-100 font-bold">
              <span>Dominance Ratio (A / B × 100):</span>
              <span className="text-base text-emerald-400">
                {dominance_test_b > 0 ? `${dominance_test_percent.toFixed(1)}%` : '0.0%'}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 italic pt-1">
              *USACE Standard: Dominance test requires strict inequality (&gt; 50.0%). Exactly 50.00% is a regulatory failure.
            </p>
          </div>
        </div>

        {/* Section 3: Prevalence Index (PI) Matrix */}
        <div className="bg-field-card rounded-xl border border-field-border p-3.5 shadow-sm space-y-3">
          <div className="flex items-center justify-between border-b border-field-border/60 pb-2">
            <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wide">
              Prevalence Index Matrix (Weight 1..5)
            </h3>
            <span
              className={`text-xs font-bold font-mono px-2 py-0.5 rounded ${
                prevalence_index_passed
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                  : 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
              }`}
            >
              {prevalence_index !== null
                ? prevalence_index_passed
                  ? `PASSED (${prevalence_index.toFixed(2)} ≤ 3.00)`
                  : `FAILED (${prevalence_index.toFixed(2)} > 3.00)`
                : 'NO DATA'}
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-field-border text-slate-400 text-[10px] uppercase">
                  <th className="py-1 px-1.5">Indicator Group</th>
                  <th className="py-1 px-1.5 text-center">Weight</th>
                  <th className="py-1 px-1.5 text-right">Cover Sum</th>
                  <th className="py-1 px-1.5 text-right">Weighted Product</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-field-border/40 text-slate-300">
                <tr>
                  <td className="py-1.5 px-1.5 font-bold text-emerald-400">OBL</td>
                  <td className="py-1.5 px-1.5 text-center">1</td>
                  <td className="py-1.5 px-1.5 text-right">{prevalence_breakdown.obl_cover}%</td>
                  <td className="py-1.5 px-1.5 text-right font-bold">
                    {(prevalence_breakdown.obl_cover * 1).toFixed(1)}
                  </td>
                </tr>
                <tr>
                  <td className="py-1.5 px-1.5 font-bold text-emerald-300">FACW</td>
                  <td className="py-1.5 px-1.5 text-center">2</td>
                  <td className="py-1.5 px-1.5 text-right">{prevalence_breakdown.facw_cover}%</td>
                  <td className="py-1.5 px-1.5 text-right font-bold">
                    {(prevalence_breakdown.facw_cover * 2).toFixed(1)}
                  </td>
                </tr>
                <tr>
                  <td className="py-1.5 px-1.5 font-bold text-teal-300">FAC</td>
                  <td className="py-1.5 px-1.5 text-center">3</td>
                  <td className="py-1.5 px-1.5 text-right">{prevalence_breakdown.fac_cover}%</td>
                  <td className="py-1.5 px-1.5 text-right font-bold">
                    {(prevalence_breakdown.fac_cover * 3).toFixed(1)}
                  </td>
                </tr>
                <tr>
                  <td className="py-1.5 px-1.5 font-bold text-amber-300">FACU</td>
                  <td className="py-1.5 px-1.5 text-center">4</td>
                  <td className="py-1.5 px-1.5 text-right">{prevalence_breakdown.facu_cover}%</td>
                  <td className="py-1.5 px-1.5 text-right font-bold">
                    {(prevalence_breakdown.facu_cover * 4).toFixed(1)}
                  </td>
                </tr>
                <tr>
                  <td className="py-1.5 px-1.5 font-bold text-rose-300">UPL / NL</td>
                  <td className="py-1.5 px-1.5 text-center">5</td>
                  <td className="py-1.5 px-1.5 text-right">{prevalence_breakdown.upl_cover}%</td>
                  <td className="py-1.5 px-1.5 text-right font-bold">
                    {(prevalence_breakdown.upl_cover * 5).toFixed(1)}
                  </td>
                </tr>
                <tr className="bg-field-surface font-bold text-slate-100 border-t border-field-border">
                  <td className="py-1.5 px-1.5">Total Community</td>
                  <td className="py-1.5 px-1.5 text-center">—</td>
                  <td className="py-1.5 px-1.5 text-right text-emerald-400">
                    {prevalence_breakdown.total_cover}%
                  </td>
                  <td className="py-1.5 px-1.5 text-right text-emerald-400">
                    {prevalence_breakdown.weighted_sum.toFixed(1)}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="bg-field-surface/70 p-2.5 rounded-lg border border-field-border text-xs font-mono flex items-center justify-between">
            <span className="text-slate-300">Calculated Prevalence Index:</span>
            <span className="font-bold text-emerald-400 text-sm">
              {prevalence_breakdown.raw_pi !== null
                ? `${prevalence_breakdown.raw_pi.toFixed(4)} → Rounded: ${prevalence_index?.toFixed(2)}`
                : 'N/A'}
            </span>
          </div>
        </div>

        {/* Section 4: Regulatory Remarks & Three-Parameter Context */}
        <div className="bg-field-card rounded-xl border border-field-border p-3.5 shadow-sm space-y-2 text-xs">
          <div className="flex items-center gap-2 border-b border-field-border/60 pb-2">
            <Info className="w-4 h-4 text-slate-400" />
            <h3 className="font-bold text-slate-200 uppercase tracking-wide">
              Official Determination Remarks
            </h3>
          </div>
          <ul className="space-y-1.5 text-slate-300 list-disc list-inside">
            {remarks.map((rem, i) => (
              <li key={i} className="leading-relaxed">
                {rem}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};
