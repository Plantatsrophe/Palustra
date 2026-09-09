#!/usr/bin/env python3
"""USACE Wetland Standards Mathematical Helper Script.

Executable calculation engine for 50/20 dominance, Prevalence Index,
NRCS hydric soil indicators, and regional hydrology logic.
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from palustra.wetland import (
    RegionEnum,
    SoilHorizon,
    SpeciesCover,
    calculate_prevalence_index,
    calculate_stratum_50_20,
    evaluate_hydric_soils,
    evaluate_hydrophytic_vegetation,
    evaluate_wetland_hydrology,
    perform_jurisdictional_wetland_determination,
)


def main():
    print("=== Palustra USACE Wetland Mathematical Engine ===")
    print("Version: 1.0.0 (EMP & AGCP Regional Supplements)")
    print("Deterministic calculation routines loaded successfully.")


if __name__ == "__main__":
    main()
