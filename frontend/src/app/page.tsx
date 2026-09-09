'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { db, seedInitialDatabase } from '../lib/db';
import { SpeciesEntry, StratumType } from '../lib/wetland/types';
import { evaluateHydrophyticVegetation } from '../lib/wetland/calculations';
import { useServiceWorker } from '../hooks/useServiceWorker';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';
import { AppHeader } from '../components/AppHeader';
import { CalculationBadges } from '../components/CalculationBadges';
import { SplitScreenLayout } from '../components/SplitScreenLayout';
import { KeyboardDataEntry } from '../components/KeyboardDataEntry';
import { VerificationPanel } from '../components/VerificationPanel';
import { ShortcutsModal } from '../components/ShortcutsModal';

export default function Home() {
  const [activePlotId, setActivePlotId] = useState<string>('plot-demo-1');
  const [activeStratum, setActiveStratum] = useState<StratumType>('herb');
  const [isVerificationOpen, setIsVerificationOpen] = useState<boolean>(true);
  const [isShortcutsOpen, setIsShortcutsOpen] = useState<boolean>(false);
  const [isSunlightMode, setIsSunlightMode] = useState<boolean>(false);
  const [region, setRegion] = useState<'EMP' | 'AGCP'>('EMP');

  // Service Worker and storage persistence
  const { isOnline, outboxCount, isSyncing, triggerSync, storageInfo } = useServiceWorker();

  // Seed database on initial mount
  useEffect(() => {
    seedInitialDatabase();
  }, []);

  // Keyboard navigation & Screen Wake Lock
  const { wakeLockActive, toggleWakeLock } = useKeyboardShortcuts({
    onSelectStratum: (stratum) => setActiveStratum(stratum),
    onToggleVerification: () => setIsVerificationOpen((prev) => !prev),
    onToggleShortcutsModal: () => setIsShortcutsOpen((prev) => !prev),
  });

  // Dexie live queries for active plot, taxa, and reference plants
  const plot = useLiveQuery(() => db.plots.get(activePlotId), [activePlotId]);
  const taxaRecords = useLiveQuery(
    () =>
      db.vegetation_taxa
        .where('plot_id')
        .equals(activePlotId)
        .and((item) => !item.is_deleted)
        .toArray(),
    [activePlotId]
  );
  const referencePlants = useLiveQuery(() => db.reference_taxa.toArray(), []);

  // Map Dexie taxa to SpeciesEntry models
  const speciesList: SpeciesEntry[] = useMemo(() => {
    if (!taxaRecords) return [];
    return taxaRecords.map((t) => ({
      id: t.id,
      plot_id: t.plot_id,
      stratum: t.stratum_id,
      taxon: t.taxon,
      common_name: t.common_name,
      usda_symbol: t.usda_symbol,
      percent_cover: t.percent_cover,
      indicator_status: t.indicator_status,
      has_morphological_adaptations: t.has_morphological_adaptations,
    }));
  }, [taxaRecords]);

  // Group taxa by stratum
  const strataData = useMemo(() => {
    const data: Record<StratumType, SpeciesEntry[]> = {
      tree: [],
      sapling_shrub: [],
      herb: [],
      woody_vine: [],
    };
    speciesList.forEach((s) => {
      if (data[s.stratum]) {
        data[s.stratum].push(s);
      }
    });
    return data;
  }, [speciesList]);

  // Real-time reactive USACE calculations
  const determination = useMemo(() => {
    return evaluateHydrophyticVegetation(strataData);
  }, [strataData]);

  // Active stratum species
  const activeStratumSpecies = useMemo(() => {
    return strataData[activeStratum] || [];
  }, [strataData, activeStratum]);

  // Taxon database operations
  const handleAddSpecies = async (entry: Omit<SpeciesEntry, 'id'>) => {
    const newRecord = {
      id: crypto.randomUUID(),
      plot_id: activePlotId,
      stratum_id: entry.stratum,
      usda_symbol: entry.usda_symbol,
      taxon: entry.taxon,
      common_name: entry.common_name || '',
      percent_cover: entry.percent_cover,
      indicator_status: entry.indicator_status,
      has_morphological_adaptations: false,
      is_deleted: false,
      sync_status: 'pending_insert' as const,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    await db.saveVegetationTaxon(newRecord);
  };

  const handleUpdateSpecies = async (id: string, updates: Partial<SpeciesEntry>) => {
    const existing = await db.vegetation_taxa.get(id);
    if (!existing) return;

    const updatedRecord = {
      ...existing,
      ...updates,
      stratum_id: updates.stratum || existing.stratum_id,
      updated_at: new Date().toISOString(),
      sync_status: 'pending_update' as const,
    };

    await db.saveVegetationTaxon(updatedRecord);
  };

  const handleDeleteSpecies = async (id: string) => {
    await db.softDeleteTaxon(id, activePlotId);
  };

  const handleToggleRegion = () => {
    setRegion((prev) => (prev === 'EMP' ? 'AGCP' : 'EMP'));
  };

  return (
    <div
      className={`h-screen flex flex-col overflow-hidden select-none sm:select-text ${
        isSunlightMode ? 'sunlight-mode' : ''
      }`}
    >
      {/* 1. App Header */}
      <AppHeader
        projectName="Neuse River Basin Delineation"
        plotName={plot?.plot_name || 'SP-01-WETLAND-FOREST'}
        region={region}
        onToggleRegion={handleToggleRegion}
        isOnline={isOnline}
        outboxCount={outboxCount}
        isSyncing={isSyncing}
        onTriggerSync={triggerSync}
        storageInfo={storageInfo}
        wakeLockActive={wakeLockActive}
        onToggleWakeLock={toggleWakeLock}
        isVerificationOpen={isVerificationOpen}
        onToggleVerification={() => setIsVerificationOpen((prev) => !prev)}
        onOpenShortcuts={() => setIsShortcutsOpen(true)}
        isSunlightMode={isSunlightMode}
        onToggleSunlightMode={() => setIsSunlightMode((prev) => !prev)}
      />

      {/* 2. Real-Time Reactive Calculation Badges */}
      <CalculationBadges determination={determination} />

      {/* 3. Split-Screen Verification UI & Keyboard Entry */}
      <SplitScreenLayout
        isVerificationOpen={isVerificationOpen}
        onToggleVerification={() => setIsVerificationOpen((prev) => !prev)}
        leftPane={
          <KeyboardDataEntry
            activeStratum={activeStratum}
            onSelectStratum={setActiveStratum}
            stratumResult={determination.strata_results[activeStratum]}
            speciesList={activeStratumSpecies}
            referencePlants={referencePlants || []}
            region={region}
            onAddSpecies={handleAddSpecies}
            onUpdateSpecies={handleUpdateSpecies}
            onDeleteSpecies={handleDeleteSpecies}
          />
        }
        rightPane={
          <VerificationPanel
            determination={determination}
            activeStratum={activeStratum}
            onSelectStratum={setActiveStratum}
            plotName={plot?.plot_name || 'SP-01-WETLAND-FOREST'}
            region={region}
          />
        }
      />

      {/* 4. Keyboard Shortcuts Modal */}
      <ShortcutsModal isOpen={isShortcutsOpen} onClose={() => setIsShortcutsOpen(false)} />
    </div>
  );
}
