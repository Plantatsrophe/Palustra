"""NRCS Hydric Soil indicators evaluation (v8.2) for Munsell matrix & redox morphology."""

from typing import List, Optional, Sequence, Tuple
from palustra.wetland.models import (
    HydricSoilIndicatorResult,
    SoilDetermination,
    SoilHorizon,
)

GLEY_1_HUES = {"10Y", "5GY", "10GY", "5G", "10G", "5BG", "10BG", "5B", "10B", "5PB", "N"}
GLEY_2_HUES = {"5PB", "10PB", "5P", "10P", "5RP"}


def is_gleyed_matrix(horizon: SoilHorizon) -> bool:
    """Determine whether a soil horizon exhibits a Gleyed Matrix under NRCS standards.

    Criteria:
    - Munsell Gley 1 or Gley 2 charts with Value >= 4.0.
    """
    if horizon.matrix_value < 4.0:
        return False

    hue = horizon.matrix_hue.strip().upper()
    if hue == "GLEY1" or hue in GLEY_1_HUES:
        return True
    if hue == "GLEY2" or hue in GLEY_2_HUES:
        return True
    return False


def is_depleted_matrix(horizon: SoilHorizon) -> Tuple[bool, Optional[str]]:
    """Determine whether a soil horizon exhibits a Depleted Matrix under NRCS standards.

    Returns:
        (is_depleted, qualifying_category_string)

    NRCS v8.2 Categories:
    1. Matrix Value >= 5 and Chroma <= 1 (with or without redox concentrations); OR
    2. Matrix Value >= 6 and Chroma <= 2 (with or without redox concentrations); OR
    3. Matrix Value 4 or 5 and Chroma 2 with >= 2% distinct or prominent redox concentrations; OR
    4. Matrix Value 4 and Chroma 1 with >= 2% distinct or prominent redox concentrations.
    """
    val = horizon.matrix_value
    chroma = horizon.matrix_chroma
    redox_pct = horizon.redox_percent
    redox_qualifies = (
        redox_pct >= 2.0
        and horizon.redox_distinctness.lower() in ("distinct", "prominent")
    )

    # Category 1: Value >= 5, Chroma <= 1
    if val >= 5.0 and chroma <= 1.0:
        return True, "Category 1: Value >= 5, Chroma <= 1"

    # Category 2: Value >= 6, Chroma <= 2
    if val >= 6.0 and chroma <= 2.0:
        return True, "Category 2: Value >= 6, Chroma <= 2"

    # Category 3: Value in [4.0, 5.0], Chroma == 2 with >= 2% distinct/prominent redox
    if (4.0 <= val <= 5.0) and abs(chroma - 2.0) < 1e-3 and redox_qualifies:
        return True, "Category 3: Value 4 or 5, Chroma 2 with >= 2% distinct/prominent redox"

    # Category 4: Value == 4.0, Chroma == 1 with >= 2% distinct/prominent redox
    if abs(val - 4.0) < 1e-3 and abs(chroma - 1.0) < 1e-3 and redox_qualifies:
        return True, "Category 4: Value 4, Chroma 1 with >= 2% distinct/prominent redox"

    return False, None


def is_depleted_or_gleyed(horizon: SoilHorizon) -> bool:
    """Helper to check if a horizon meets either depleted or gleyed matrix criteria."""
    depleted, _ = is_depleted_matrix(horizon)
    return depleted or is_gleyed_matrix(horizon)


def check_indicator_a11(horizons: Sequence[SoilHorizon]) -> HydricSoilIndicatorResult:
    """Indicator A11: Depleted Below Dark Surface.

    Criteria:
    - All soils (independent of texture).
    - A depleted or gleyed matrix layer >= 15 cm thick starting within 30 cm of the surface,
      beneath a dark mineral surface layer (Value <= 3, Chroma <= 2).
    """
    if not horizons:
        return HydricSoilIndicatorResult(
            code="A11",
            name="Depleted Below Dark Surface",
            confirmed=False,
            rationale="No horizons provided.",
        )

    # First layer must start at 0 and have Value <= 3, Chroma <= 2
    surface = horizons[0]
    if surface.top_depth_cm > 0.0 or surface.matrix_value > 3.0 or surface.matrix_chroma > 2.0:
        return HydricSoilIndicatorResult(
            code="A11",
            name="Depleted Below Dark Surface",
            confirmed=False,
            rationale=f"Surface horizon {surface.name} is not dark (Value={surface.matrix_value}, Chroma={surface.matrix_chroma}).",
        )

    dark_surface_bottom = surface.bottom_depth_cm

    # Check for depleted or gleyed layer underneath starting within 30 cm
    for h in horizons[1:]:
        if h.top_depth_cm >= dark_surface_bottom and h.top_depth_cm <= 30.0:
            if is_depleted_or_gleyed(h) and h.thickness_cm >= 15.0:
                return HydricSoilIndicatorResult(
                    code="A11",
                    name="Depleted Below Dark Surface",
                    confirmed=True,
                    qualifying_layers=[surface.name, h.name],
                    rationale=(
                        f"Dark surface {surface.name} (0-{surface.bottom_depth_cm} cm) underlain by "
                        f"depleted/gleyed layer {h.name} ({h.top_depth_cm}-{h.bottom_depth_cm} cm, "
                        f"thickness={h.thickness_cm} cm >= 15 cm)."
                    ),
                )

    return HydricSoilIndicatorResult(
        code="A11",
        name="Depleted Below Dark Surface",
        confirmed=False,
        rationale="No depleted/gleyed layer >= 15 cm thick starting within 30 cm beneath dark surface.",
    )


def check_indicator_a12(horizons: Sequence[SoilHorizon]) -> HydricSoilIndicatorResult:
    """Indicator A12: Thick Dark Surface.

    Criteria:
    - All soils.
    - A thick dark mineral surface layer >= 30 cm thick with Value <= 3.5, Chroma <= 1.
    - Underlain by a depleted or gleyed matrix starting within 30 or 35 cm.
    """
    if not horizons:
        return HydricSoilIndicatorResult(
            code="A12",
            name="Thick Dark Surface",
            confirmed=False,
            rationale="No horizons provided.",
        )

    # Check for dark surface >= 30 cm thick starting at 0 cm
    dark_layers: List[SoilHorizon] = []
    cumulative_dark_thickness = 0.0

    for h in horizons:
        if (
            h.matrix_value <= 3.5
            and h.matrix_chroma <= 1.0
            and not h.is_organic
        ):
            dark_layers.append(h)
            cumulative_dark_thickness += h.thickness_cm
        else:
            break

    if cumulative_dark_thickness < 30.0:
        return HydricSoilIndicatorResult(
            code="A12",
            name="Thick Dark Surface",
            confirmed=False,
            rationale=f"Dark surface layer thickness ({cumulative_dark_thickness} cm) is < 30 cm.",
        )

    dark_bottom = dark_layers[-1].bottom_depth_cm

    # Look for depleted/gleyed matrix directly beneath starting within 35 cm
    for h in horizons[len(dark_layers):]:
        if h.top_depth_cm <= 35.0 and is_depleted_or_gleyed(h):
            return HydricSoilIndicatorResult(
                code="A12",
                name="Thick Dark Surface",
                confirmed=True,
                qualifying_layers=[d.name for d in dark_layers] + [h.name],
                rationale=(
                    f"Thick dark surface ({cumulative_dark_thickness} cm >= 30 cm) underlain by "
                    f"depleted/gleyed layer {h.name} starting at {h.top_depth_cm} cm."
                ),
            )

    return HydricSoilIndicatorResult(
        code="A12",
        name="Thick Dark Surface",
        confirmed=False,
        rationale="Thick dark surface present, but underlain layer is not depleted or gleyed within 35 cm.",
    )


def check_indicator_f3(horizons: Sequence[SoilHorizon]) -> HydricSoilIndicatorResult:
    """Indicator F3: Depleted Matrix.

    Criteria:
    - Loamy and clayey soils.
    - A depleted matrix layer:
      1. >= 5 cm thick starting within 10 cm of the mineral surface; OR
      2. >= 15 cm thick starting within 25 cm of the mineral surface.
    """
    for h in horizons:
        if not h.is_loamy_clayey:
            continue
        is_dep, category = is_depleted_matrix(h)
        if not is_dep:
            continue

        # Condition 1: >= 5 cm thick within 10 cm
        if h.top_depth_cm <= 10.0 and h.thickness_cm >= 5.0:
            return HydricSoilIndicatorResult(
                code="F3",
                name="Depleted Matrix",
                confirmed=True,
                qualifying_layers=[h.name],
                rationale=(
                    f"Horizon {h.name} is depleted ({category}) with thickness {h.thickness_cm} cm >= 5 cm "
                    f"starting at {h.top_depth_cm} cm <= 10 cm."
                ),
            )

        # Condition 2: >= 15 cm thick within 25 cm
        if h.top_depth_cm <= 25.0 and h.thickness_cm >= 15.0:
            return HydricSoilIndicatorResult(
                code="F3",
                name="Depleted Matrix",
                confirmed=True,
                qualifying_layers=[h.name],
                rationale=(
                    f"Horizon {h.name} is depleted ({category}) with thickness {h.thickness_cm} cm >= 15 cm "
                    f"starting at {h.top_depth_cm} cm <= 25 cm."
                ),
            )

    return HydricSoilIndicatorResult(
        code="F3",
        name="Depleted Matrix",
        confirmed=False,
        rationale="No loamy/clayey horizon satisfies the F3 thickness and depth requirements.",
    )


def check_indicator_f6(horizons: Sequence[SoilHorizon]) -> HydricSoilIndicatorResult:
    """Indicator F6: Redox Dark Surface.

    Criteria:
    - Loamy and clayey soils.
    - A layer >= 10 cm thick starting within 20 cm of the mineral surface with:
      1. Dark matrix: Value <= 3, Chroma <= 1; AND
      2. >= 2% distinct or prominent redox concentrations.
    """
    for h in horizons:
        if not h.is_loamy_clayey:
            continue

        if h.top_depth_cm <= 20.0 and h.thickness_cm >= 10.0:
            val_ok = h.matrix_value <= 3.0
            chroma_ok = h.matrix_chroma <= 1.0
            redox_ok = (
                h.redox_percent >= 2.0
                and h.redox_distinctness.lower() in ("distinct", "prominent")
            )
            if val_ok and chroma_ok and redox_ok:
                return HydricSoilIndicatorResult(
                    code="F6",
                    name="Redox Dark Surface",
                    confirmed=True,
                    qualifying_layers=[h.name],
                    rationale=(
                        f"Horizon {h.name} ({h.top_depth_cm}-{h.bottom_depth_cm} cm, thickness={h.thickness_cm} cm) "
                        f"has Value={h.matrix_value} <= 3, Chroma={h.matrix_chroma} <= 1, and "
                        f"{h.redox_percent}% {h.redox_distinctness} redox concentrations."
                    ),
                )

    return HydricSoilIndicatorResult(
        code="F6",
        name="Redox Dark Surface",
        confirmed=False,
        rationale="No loamy/clayey horizon satisfies F6 criteria (Value <= 3, Chroma <= 1, >= 2% redox).",
    )


def check_indicator_s5(horizons: Sequence[SoilHorizon]) -> HydricSoilIndicatorResult:
    """Indicator S5: Sandy Redox.

    Criteria:
    - Sandy soils (texture is sand or loamy sand).
    - A layer starting within 15 cm of the mineral soil surface with:
      1. Matrix Chroma <= 2; AND
      2. >= 2% distinct or prominent redox concentrations.
      3. Thickness >= 5 cm.
    """
    for h in horizons:
        if not h.is_sandy:
            continue

        if h.top_depth_cm <= 15.0 and h.thickness_cm >= 5.0:
            chroma_ok = h.matrix_chroma <= 2.0
            redox_ok = (
                h.redox_percent >= 2.0
                and h.redox_distinctness.lower() in ("distinct", "prominent")
            )
            if chroma_ok and redox_ok:
                return HydricSoilIndicatorResult(
                    code="S5",
                    name="Sandy Redox",
                    confirmed=True,
                    qualifying_layers=[h.name],
                    rationale=(
                        f"Sandy horizon {h.name} ({h.top_depth_cm}-{h.bottom_depth_cm} cm) starting at "
                        f"{h.top_depth_cm} cm <= 15 cm has Chroma={h.matrix_chroma} <= 2 and "
                        f"{h.redox_percent}% {h.redox_distinctness} redox concentrations."
                    ),
                )

    return HydricSoilIndicatorResult(
        code="S5",
        name="Sandy Redox",
        confirmed=False,
        rationale="No sandy horizon satisfies S5 criteria (starting <= 15 cm, Chroma <= 2, >= 2% redox).",
    )


def evaluate_hydric_soils(horizons: Sequence[SoilHorizon]) -> SoilDetermination:
    """Evaluate soil pit profile against NRCS indicators A11, A12, F3, F6, and S5."""
    checkers = [
        check_indicator_a11,
        check_indicator_a12,
        check_indicator_f3,
        check_indicator_f6,
        check_indicator_s5,
    ]

    evaluated: List[HydricSoilIndicatorResult] = []
    confirmed_codes: List[str] = []
    depleted_layers: List[str] = []
    gleyed_layers: List[str] = []

    for h in horizons:
        is_dep, _ = is_depleted_matrix(h)
        if is_dep and h.name not in depleted_layers:
            depleted_layers.append(h.name)
        if is_gleyed_matrix(h) and h.name not in gleyed_layers:
            gleyed_layers.append(h.name)

    for check in checkers:
        res = check(horizons)
        evaluated.append(res)
        if res.confirmed:
            confirmed_codes.append(res.code)

    hydric_present = len(confirmed_codes) > 0
    remarks = [
        f"Hydric Soil Status: {'CONFIRMED' if hydric_present else 'NOT MET'}.",
        f"Confirmed Indicators: {', '.join(confirmed_codes) if confirmed_codes else 'None'}.",
    ]

    return SoilDetermination(
        hydric_soil_present=hydric_present,
        indicators_evaluated=evaluated,
        confirmed_indicators=confirmed_codes,
        depleted_layers=depleted_layers,
        gleyed_layers=gleyed_layers,
        remarks=remarks,
    )
