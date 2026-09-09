'use client';

import React, { useState, useRef, useEffect } from 'react';
import { IndicatorStatus, SpeciesEntry, StratumDominanceResult, StratumType, STRATA_CONFIG } from '../lib/wetland/types';
import { ReferenceTaxonRecord } from '../lib/db/schema';
import { Plus, Trash2, Check, AlertCircle, Sparkles, ChevronRight, HelpCircle } from 'lucide-react';

interface KeyboardDataEntryProps {
  activeStratum: StratumType;
  onSelectStratum: (stratum: StratumType) => void;
  stratumResult: StratumDominanceResult;
  speciesList: SpeciesEntry[];
  referencePlants: ReferenceTaxonRecord[];
  region: 'EMP' | 'AGCP';
  onAddSpecies: (entry: Omit<SpeciesEntry, 'id'>) => Promise<void>;
  onUpdateSpecies: (id: string, updates: Partial<SpeciesEntry>) => Promise<void>;
  onDeleteSpecies: (id: string) => Promise<void>;
}

const COVER_PRESETS = [1, 5, 10, 15, 20, 25, 35, 50, 75, 90];

export const KeyboardDataEntry: React.FC<KeyboardDataEntryProps> = ({
  activeStratum,
  onSelectStratum,
  stratumResult,
  speciesList,
  referencePlants,
  region,
  onAddSpecies,
  onUpdateSpecies,
  onDeleteSpecies,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPlant, setSelectedPlant] = useState<ReferenceTaxonRecord | null>(null);
  const [coverInput, setCoverInput] = useState('');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [focusedIndex, setFocusedIndex] = useState(0);

  const searchInputRef = useRef<HTMLInputElement>(null);
  const coverInputRef = useRef<HTMLInputElement>(null);

  // Filter reference plants by symbol, scientific name, or common name
  const filteredPlants = searchQuery.trim().length > 0
    ? referencePlants
        .filter(
          (p) =>
            p.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
            p.scientific_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            p.common_name.toLowerCase().includes(searchQuery.toLowerCase())
        )
        .slice(0, 8)
    : [];

  // Reset dropdown focus on query change
  useEffect(() => {
    setFocusedIndex(0);
    setIsDropdownOpen(filteredPlants.length > 0 && !selectedPlant);
  }, [searchQuery, selectedPlant]);

  const handleSelectPlant = (plant: ReferenceTaxonRecord) => {
    setSelectedPlant(plant);
    setSearchQuery(`${plant.symbol} - ${plant.scientific_name}`);
    setIsDropdownOpen(false);
    // Move focus to cover input immediately
    setTimeout(() => coverInputRef.current?.focus(), 50);
  };

  const handleAddSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    const coverNum = parseFloat(coverInput);
    if (!coverNum || coverNum <= 0) {
      coverInputRef.current?.focus();
      return;
    }

    if (selectedPlant) {
      const indicator = region === 'EMP' ? selectedPlant.emp_indicator : selectedPlant.agcp_indicator;
      await onAddSpecies({
        plot_id: '',
        stratum: activeStratum,
        taxon: selectedPlant.scientific_name,
        common_name: selectedPlant.common_name,
        usda_symbol: selectedPlant.symbol,
        percent_cover: coverNum,
        indicator_status: indicator,
      });
    } else if (searchQuery.trim().length > 0) {
      // Custom taxon entry
      await onAddSpecies({
        plot_id: '',
        stratum: activeStratum,
        taxon: searchQuery.trim(),
        common_name: '',
        usda_symbol: searchQuery.trim().slice(0, 5).toUpperCase(),
        percent_cover: coverNum,
        indicator_status: 'FAC', // Default fallback
      });
    }

    // Reset inputs and refocus search for rapid chaining
    setSearchQuery('');
    setSelectedPlant(null);
    setCoverInput('');
    setIsDropdownOpen(false);
    searchInputRef.current?.focus();
  };

  const handleSearchKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (isDropdownOpen && filteredPlants.length > 0) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setFocusedIndex((prev) => (prev + 1) % filteredPlants.length);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setFocusedIndex((prev) => (prev - 1 + filteredPlants.length) % filteredPlants.length);
      } else if (e.key === 'Enter') {
        e.preventDefault();
        handleSelectPlant(filteredPlants[focusedIndex]);
      } else if (e.key === 'Escape') {
        setIsDropdownOpen(false);
      }
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (selectedPlant) {
        coverInputRef.current?.focus();
      } else {
        handleAddSubmit();
      }
    }
  };

  const strataKeys: StratumType[] = ['tree', 'sapling_shrub', 'herb', 'woody_vine'];

  return (
    <div className="flex flex-col h-full bg-field-dark border-r border-field-border overflow-y-auto">
      {/* Stratum Tabs with Hotkey Badges */}
      <div className="bg-field-surface border-b border-field-border p-2 sticky top-0 z-20 shadow-sm">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5">
          {strataKeys.map((strat) => {
            const config = STRATA_CONFIG[strat];
            const isActive = strat === activeStratum;
            return (
              <button
                key={strat}
                id={`tab-${strat}`}
                onClick={() => onSelectStratum(strat)}
                className={`flex flex-col items-start px-2.5 py-2 rounded-lg border text-left transition-all ${
                  isActive
                    ? 'bg-emerald-950/80 border-emerald-500 text-emerald-100 shadow-md ring-1 ring-emerald-500/40'
                    : 'bg-field-card border-field-border text-slate-300 hover:bg-field-card/80 hover:border-slate-600'
                }`}
              >
                <div className="flex items-center justify-between w-full">
                  <span className="text-xs font-semibold">{config.label}</span>
                  <span
                    className={`text-[10px] font-mono px-1 py-0.5 rounded border ${
                      isActive
                        ? 'bg-emerald-800/80 border-emerald-400 text-emerald-100'
                        : 'bg-field-surface border-field-border text-slate-400'
                    }`}
                  >
                    {config.altKey}
                  </span>
                </div>
                <span className="text-[10px] text-slate-400 truncate mt-0.5">
                  {strat === activeStratum ? `${stratumResult.dominants.length} Dominants` : ''}
                </span>
              </button>
            );
          })}
        </div>

        {/* Stratum Summary Line */}
        <div className="mt-2.5 px-1 flex items-center justify-between text-xs font-mono text-slate-300">
          <div className="flex items-center gap-2">
            <span className="text-slate-400">Total Cover:</span>
            <span className="font-bold text-emerald-400 text-sm">{stratumResult.total_cover}%</span>
          </div>
          <div className="flex items-center gap-3 text-[11px] text-slate-400">
            <span>
              50% Cutoff: <strong className="text-slate-200">{stratumResult.threshold_50}%</strong>
            </span>
            <span>
              20% Cutoff: <strong className="text-slate-200">{stratumResult.threshold_20}%</strong>
            </span>
          </div>
        </div>
      </div>

      {/* Fast Quick-Add Entry Bar */}
      <div className="p-3 bg-field-surface/60 border-b border-field-border">
        <form onSubmit={handleAddSubmit} className="space-y-2.5">
          <div className="flex items-center justify-between text-xs font-semibold text-slate-300">
            <span className="flex items-center gap-1.5 text-emerald-400">
              <Plus className="w-3.5 h-3.5" />
              Quick Taxon Entry (Keyboard-First)
            </span>
            <span className="text-[10px] text-slate-400 font-mono">Press [Enter] to submit</span>
          </div>

          <div className="flex flex-col sm:flex-row gap-2 relative">
            {/* Taxon / Symbol Input with Typeahead Dropdown */}
            <div className="flex-1 relative">
              <input
                ref={searchInputRef}
                id="taxon-search-input"
                type="text"
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setSelectedPlant(null);
                }}
                onKeyDown={handleSearchKeyDown}
                placeholder="Type USDA Symbol or species name (e.g. ACRU, Carex)..."
                className="w-full bg-field-card border border-field-border rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono"
                autoComplete="off"
              />

              {/* Autocomplete Dropdown */}
              {isDropdownOpen && filteredPlants.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-field-card border border-field-border rounded-lg shadow-2xl z-50 max-h-60 overflow-y-auto">
                  {filteredPlants.map((plant, idx) => {
                    const isFocused = idx === focusedIndex;
                    const indicator = region === 'EMP' ? plant.emp_indicator : plant.agcp_indicator;
                    return (
                      <div
                        key={plant.id}
                        onClick={() => handleSelectPlant(plant)}
                        className={`px-3 py-2 text-xs flex items-center justify-between cursor-pointer border-b border-field-border/50 last:border-b-0 ${
                          isFocused ? 'bg-emerald-950/80 text-emerald-200' : 'hover:bg-field-surface text-slate-200'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-bold text-emerald-400 w-12">{plant.symbol}</span>
                          <span className="italic font-medium">{plant.scientific_name}</span>
                          <span className="text-slate-400">({plant.common_name})</span>
                        </div>
                        <span className="font-mono px-1.5 py-0.5 rounded bg-field-surface border border-field-border font-bold text-[10px]">
                          {indicator}
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Percent Cover Input */}
            <div className="w-full sm:w-28 relative">
              <input
                ref={coverInputRef}
                id="cover-input"
                type="number"
                min="0.1"
                max="100"
                step="any"
                value={coverInput}
                onChange={(e) => setCoverInput(e.target.value)}
                placeholder="Cover %"
                className="w-full bg-field-card border border-field-border rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono text-center font-bold"
              />
              <span className="absolute right-3 top-2.5 text-xs text-slate-400 font-mono">%</span>
            </div>

            {/* Submit Button */}
            <button
              id="submit-taxon-btn"
              type="submit"
              className="bg-emerald-600 hover:bg-emerald-500 active:bg-emerald-700 text-white font-semibold text-xs px-4 py-2 rounded-lg flex items-center justify-center gap-1.5 shadow-md transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>Add</span>
            </button>
          </div>

          {/* Quick Cover Preset Chips */}
          <div className="flex items-center gap-1.5 flex-wrap pt-0.5">
            <span className="text-[10px] text-slate-400 font-mono mr-1">Presets:</span>
            {COVER_PRESETS.map((val) => (
              <button
                key={val}
                type="button"
                onClick={() => {
                  setCoverInput(val.toString());
                  setTimeout(() => coverInputRef.current?.focus(), 20);
                }}
                className={`text-[10px] font-mono px-2 py-0.5 rounded border transition-colors ${
                  coverInput === val.toString()
                    ? 'bg-emerald-800 text-emerald-100 border-emerald-400 font-bold'
                    : 'bg-field-card border-field-border text-slate-300 hover:bg-field-surface'
                }`}
              >
                {val}%
              </button>
            ))}
          </div>
        </form>
      </div>

      {/* Taxon Table for Current Stratum */}
      <div className="flex-1 p-3 space-y-2">
        <div className="flex items-center justify-between text-xs text-slate-400 font-semibold px-1">
          <span>Species ({speciesList.length})</span>
          <span className="text-[10px] font-mono">Live Dexie DB</span>
        </div>

        {speciesList.length === 0 ? (
          <div className="p-8 text-center border-2 border-dashed border-field-border rounded-xl bg-field-card/30 text-slate-400">
            <p className="text-sm font-medium">No species logged in {STRATA_CONFIG[activeStratum].label}.</p>
            <p className="text-xs text-slate-500 mt-1">
              Use the quick-add bar above or press <kbd className="px-1 bg-field-surface rounded border border-field-border font-mono text-[10px]">Enter</kbd> to add plants.
            </p>
          </div>
        ) : (
          <div className="space-y-1.5">
            {speciesList.map((species) => {
              const isDominant = stratumResult.dominants.some((d) => d.id === species.id);
              return (
                <div
                  key={species.id}
                  className={`p-2.5 rounded-lg border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2.5 transition-all ${
                    isDominant
                      ? 'bg-field-card border-emerald-500/40 shadow-sm'
                      : 'bg-field-card/60 border-field-border'
                  }`}
                >
                  {/* Plant Info */}
                  <div className="flex items-center gap-2.5 flex-1 min-w-0">
                    <span className="font-mono text-xs font-bold text-emerald-400 w-14 truncate">
                      {species.usda_symbol}
                    </span>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-slate-100 italic truncate">
                          {species.taxon}
                        </span>
                        {isDominant && (
                          <span className="bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-[9px] font-bold px-1.5 py-0.2 rounded uppercase tracking-wider">
                            Dominant
                          </span>
                        )}
                      </div>
                      {species.common_name && (
                        <p className="text-xs text-slate-400 truncate">{species.common_name}</p>
                      )}
                    </div>
                  </div>

                  {/* Indicator Status & Cover Input */}
                  <div className="flex items-center gap-2 self-end sm:self-center">
                    {/* Indicator Dropdown */}
                    <select
                      value={species.indicator_status}
                      onChange={(e) =>
                        onUpdateSpecies(species.id, {
                          indicator_status: e.target.value as IndicatorStatus,
                        })
                      }
                      className="bg-field-surface border border-field-border rounded px-2 py-1 text-xs font-mono font-bold text-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                    >
                      <option value="OBL">OBL</option>
                      <option value="FACW">FACW</option>
                      <option value="FAC">FAC</option>
                      <option value="FACU">FACU</option>
                      <option value="UPL">UPL</option>
                      <option value="NL">NL</option>
                    </select>

                    {/* Interactive Cover Input */}
                    <div className="relative w-20">
                      <input
                        type="number"
                        min="0"
                        max="100"
                        step="any"
                        value={species.percent_cover}
                        onChange={(e) => {
                          const val = parseFloat(e.target.value);
                          if (!isNaN(val)) {
                            onUpdateSpecies(species.id, { percent_cover: val });
                          }
                        }}
                        className="w-full bg-field-surface border border-field-border rounded px-2 py-1 text-xs font-mono font-bold text-right text-emerald-300 focus:outline-none focus:ring-1 focus:ring-emerald-500 pr-5"
                      />
                      <span className="absolute right-1.5 top-1 text-[10px] text-slate-400 font-mono">%</span>
                    </div>

                    {/* Morphological Adaptation Checkbox (for FACU) */}
                    {species.indicator_status === 'FACU' && (
                      <label
                        className="flex items-center gap-1 text-[10px] font-mono text-slate-400 cursor-pointer"
                        title="Morphological adaptations observed in ≥50% of individuals"
                      >
                        <input
                          type="checkbox"
                          checked={species.has_morphological_adaptations || false}
                          onChange={(e) =>
                            onUpdateSpecies(species.id, {
                              has_morphological_adaptations: e.target.checked,
                            })
                          }
                          className="rounded border-field-border bg-field-surface text-emerald-500 focus:ring-0"
                        />
                        <span>Adapt.</span>
                      </label>
                    )}

                    {/* Delete Species Button */}
                    <button
                      onClick={() => onDeleteSpecies(species.id)}
                      title="Remove taxon entry"
                      className="p-1 text-slate-500 hover:text-rose-400 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
