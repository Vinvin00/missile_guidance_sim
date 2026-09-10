"""Generic visualization scenarios backed by public reference ranges.

Picker labels use the RL-track taxonomy (NoManeuver / ConstantTurn /
SinusoidalWeave). Scenario ids remain stable so mock geometries stay
unchanged. ``source_ids`` map to the review table in
``docs/scenario-parameter-sources.md``.
"""

from __future__ import annotations

import math
from typing import Literal

from guidance_sim.api.schemas import (
    CatalogResponse,
    GuidanceOption,
    ParameterValue,
    ScenarioOption,
    VehicleProfile,
)


def _parameter(
    value: float,
    unit: str,
    reference_min: float,
    reference_max: float,
    basis: Literal["direct", "synthesized", "illustrative"],
    *source_ids: str,
    live_control: bool = False,
    control_step: float | None = None,
) -> ParameterValue:
    return ParameterValue(
        value=value,
        unit=unit,
        reference_min=reference_min,
        reference_max=reference_max,
        basis=basis,
        source_ids=list(source_ids),
        live_control=live_control,
        control_step=control_step,
    )


CATALOG = CatalogResponse(
    scenarios=[
        ScenarioOption(
            id="crossing-intercept",
            label="NoManeuver",
            description="RL-track NoManeuver preview (non-maneuvering target).",
            initial_range_m=6_000.0,
            altitude_m=3_300.0,
            duration_s=10.0,
        ),
        ScenarioOption(
            id="head-on-intercept",
            label="ConstantTurn",
            description="RL-track ConstantTurn preview (label only; mock path unchanged).",
            initial_range_m=6_000.0,
            altitude_m=3_300.0,
            duration_s=7.0,
        ),
        ScenarioOption(
            id="evasive-climb",
            label="SinusoidalWeave",
            description="RL-track SinusoidalWeave preview (bounded climbing weave).",
            initial_range_m=6_000.0,
            altitude_m=3_300.0,
            duration_s=12.0,
        ),
    ],
    guidance_laws=[
        GuidanceOption(
            id="pn",
            label="Proportional Navigation",
            description="Synthetic trajectory shaped like the classical PN baseline.",
        ),
        GuidanceOption(
            id="apn",
            label="Augmented PN",
            description="Synthetic preview only; no live guidance evaluation yet.",
        ),
        GuidanceOption(
            id="ogl",
            label="Optimal Guidance",
            description="Synthetic preview only; no live guidance evaluation yet.",
        ),
    ],
    vehicle_profiles=[
        VehicleProfile(
            name="Interceptor A",
            role="interceptor",
            parameters={
                "speed": _parameter(
                    700.0,
                    "m/s",
                    600.0,
                    1_000.0,
                    "synthesized",
                    "GENERIC-MISSILE-1994",
                    "NPS-GUIDANCE-2000",
                    "PN-FUZZY-2020",
                    "PN-TRAJECTORY-2022",
                    live_control=True,
                    control_step=10.0,
                ),
                "mass": _parameter(
                    200.0,
                    "kg",
                    50.0,
                    300.0,
                    "synthesized",
                    "GENERIC-MISSILE-1994",
                    "NPS-GUIDANCE-2000",
                    "PN-FUZZY-2020",
                ),
                "reference_area": _parameter(
                    0.05,
                    "m^2",
                    0.04,
                    0.08,
                    "synthesized",
                    "NPS-GUIDANCE-2000",
                    "PN-FUZZY-2020",
                ),
                "drag_coefficient": _parameter(
                    0.3,
                    "dimensionless",
                    0.2,
                    0.4,
                    "synthesized",
                    "NPS-GUIDANCE-2000",
                    "PN-FUZZY-2020",
                    "ARL-GRID-FIN-2000",
                ),
                "max_normal_force_coefficient": _parameter(
                    5.0,
                    "dimensionless",
                    4.0,
                    6.0,
                    "illustrative",
                    "ARL-GRID-FIN-2000",
                ),
                "maneuver_limit": _parameter(
                    25.0,
                    "g",
                    20.0,
                    30.0,
                    "synthesized",
                    "GENERIC-MISSILE-1994",
                    "NPS-GUIDANCE-2000",
                    "PN-FUZZY-2020",
                ),
            },
        ),
        VehicleProfile(
            name="Target B",
            role="target",
            parameters={
                "speed": _parameter(
                    500.0,
                    "m/s",
                    300.0,
                    600.0,
                    "synthesized",
                    "NPS-GUIDANCE-2000",
                    "PN-FUZZY-2020",
                    "PN-TRAJECTORY-2022",
                    live_control=True,
                    control_step=10.0,
                ),
                "mass": _parameter(
                    9_100.0,
                    "kg",
                    9_000.0,
                    27_200.0,
                    "synthesized",
                    "FOI-ADMIRE-2005",
                    "AIAA-CLIMB-2024",
                ),
                "reference_area": _parameter(
                    45.0,
                    "m^2",
                    45.0,
                    50.0,
                    "synthesized",
                    "FOI-ADMIRE-2005",
                    "AIAA-CLIMB-2024",
                ),
                "drag_coefficient": _parameter(
                    0.035,
                    "dimensionless",
                    0.03,
                    0.05,
                    "illustrative",
                    "AIAA-CLIMB-2024",
                ),
                "max_normal_force_coefficient": _parameter(
                    1.1,
                    "dimensionless",
                    1.0,
                    1.2,
                    "illustrative",
                    "GENERIC-TRANSPORT-CN-2017",
                ),
                "maneuver_limit": _parameter(
                    9.0,
                    "g",
                    3.0,
                    9.0,
                    "synthesized",
                    "FOI-ADMIRE-2005",
                    "NPS-GUIDANCE-2000",
                    "PN-FUZZY-2020",
                ),
            },
        ),
    ],
)


def get_catalog() -> CatalogResponse:
    """Return an isolated catalog object for request-safe serialization."""

    return CATALOG.model_copy(deep=True)


def get_live_parameters() -> dict[str, ParameterValue]:
    """Flatten catalog-marked controls without hardcoding vehicle fields."""

    controls: dict[str, ParameterValue] = {}
    for profile in CATALOG.vehicle_profiles:
        for parameter_name, parameter in profile.parameters.items():
            if parameter.live_control:
                controls[f"{profile.role}.{parameter_name}"] = parameter
    return controls


def resolve_live_parameters(overrides: dict[str, float]) -> dict[str, float]:
    """Apply bounded client overrides to catalog defaults."""

    controls = get_live_parameters()
    unknown = sorted(set(overrides) - set(controls))
    if unknown:
        raise ValueError(f"unknown live parameter: {unknown[0]}")

    resolved = {name: parameter.value for name, parameter in controls.items()}
    for name, value in overrides.items():
        parameter = controls[name]
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite")
        if not parameter.reference_min <= value <= parameter.reference_max:
            raise ValueError(
                f"{name} must be between {parameter.reference_min:g} "
                f"and {parameter.reference_max:g}"
            )
        resolved[name] = value
    return resolved
