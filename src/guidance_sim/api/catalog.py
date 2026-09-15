"""Generic visualization scenarios backed by public reference ranges.

Picker labels use the RL-track taxonomy (NoManeuver / ConstantTurn /
SinusoidalWeave); each drives a distinct, randomized target maneuver in
``guidance_sim.api.live_stream``. ``source_ids`` map to the review table
in ``docs/scenario-parameter-sources.md``.
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
    data_source="rollout",
    scenarios=[
        ScenarioOption(
            id="crossing-intercept",
            label="NoManeuver",
            description="Live NoManeuver engagement (non-maneuvering target).",
            initial_range_m=6_000.0,
            altitude_m=3_300.0,
            duration_s=10.0,
        ),
        ScenarioOption(
            id="head-on-intercept",
            label="ConstantTurn",
            description="Live ConstantTurn engagement (randomized turn g/direction).",
            initial_range_m=6_000.0,
            altitude_m=3_300.0,
            duration_s=7.0,
        ),
        ScenarioOption(
            id="evasive-climb",
            label="SinusoidalWeave",
            description="Live SinusoidalWeave engagement (randomized amplitude/frequency).",
            initial_range_m=6_000.0,
            altitude_m=3_300.0,
            duration_s=12.0,
        ),
        ScenarioOption(
            id="g-limited-turn",
            label="ConstantTurn vs 10 g",
            description=(
                "An 8 g turning target against an interceptor that can only "
                "pull 10 g: Proportional Navigation reacts too late and "
                "misses, while Augmented PN and Optimal Guidance anticipate "
                "the turn and hit."
            ),
            initial_range_m=7_000.0,
            altitude_m=3_300.0,
            duration_s=8.0,
            parameter_defaults={"engagement.target_maneuver_g": 8.0},
            pursuer_g_limit=10.0,
        ),
        ScenarioOption(
            id="cobra-evasion",
            label="Cobra",
            description=(
                "Tail chase: the interceptor closes from behind on a target "
                "cruising level at 240 m/s. At 1.5 s time-to-go the target "
                "cuts throttle and snaps its nose to near-vertical; lift "
                "zooms it up while drag bleeds airspeed, and the slowed "
                "interceptor overshoots. It then falls into a banked spiral. "
                "3-DOF + attitude model, not 6-DOF."
            ),
            initial_range_m=3_000.0,
            altitude_m=3_000.0,
            duration_s=25.0,
            parameter_defaults={
                "engagement.initial_range": 3_000.0,
                "engagement.lateral_offset": 0.0,
                "engagement.altitude_delta": 0.0,
                "engagement.target_heading": 0.0,  # flying away: tail chase
                "interceptor.speed": 700.0,
                # Entry speed matters: at 150 m/s the pitch-up has too little
                # dynamic pressure to zoom, and every law still hits.
                "target.speed": 240.0,
            },
        ),
    ],
    guidance_laws=[
        GuidanceOption(
            id="pn",
            label="Proportional Navigation",
            description=(
                "Steers toward where the target will be by watching how fast "
                "the sightline to it is swinging, and turning to stop that "
                "swing. Simple and effective, but reacts late to a hard turn."
            ),
        ),
        GuidanceOption(
            id="apn",
            label="Augmented PN",
            description=(
                "Same idea as Proportional Navigation, but also factors in the "
                "target's own turning to lead it better, so it handles a "
                "maneuvering target more accurately."
            ),
        ),
        GuidanceOption(
            id="ogl",
            label="Optimal Guidance",
            description=(
                "Plans the interceptor's path to minimize the predicted miss "
                "distance at intercept, instead of just reacting turn by turn."
            ),
        ),
        GuidanceOption(
            id="rl",
            label="RL Policy",
            description=(
                "A neural network trained by trial and error (reinforcement "
                "learning) to steer the interceptor, instead of the classical "
                "formulas above. Uses a frozen, pre-trained checkpoint."
            ),
        ),
    ],
    # Operator-set geometry, not reference data: no source_ids.
    engagement_parameters={
        "initial_range": _parameter(
            7_000.0, "m", 2_000.0, 15_000.0, "illustrative",
            live_control=True, control_step=250.0,
        ),
        "lateral_offset": _parameter(
            0.0, "m", -4_000.0, 4_000.0, "illustrative",
            live_control=True, control_step=100.0,
        ),
        "altitude_delta": _parameter(
            300.0, "m", -1_500.0, 1_500.0, "illustrative",
            live_control=True, control_step=50.0,
        ),
        # 180 = flying straight at the interceptor, 90/270 = crossing.
        "target_heading": _parameter(
            180.0, "deg", 0.0, 360.0, "illustrative",
            live_control=True, control_step=5.0,
        ),
        "target_maneuver_g": _parameter(
            5.0, "g", 0.0, 9.0, "illustrative",
            live_control=True, control_step=0.5,
        ),
    },
    vehicle_profiles=[
        VehicleProfile(
            name="Interceptor A",
            role="interceptor",
            parameters={
                "speed": _parameter(
                    700.0,
                    "m/s",
                    400.0,
                    1_200.0,
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
                    240.0,
                    "m/s",
                    150.0,
                    450.0,
                    "synthesized",
                    "FOI-ADMIRE-2005",
                    "AIAA-CLIMB-2024",
                    "GENERIC-MISSILE-1994",
                    "PN-FUZZY-2020",
                    live_control=True,
                    control_step=5.0,
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
    for parameter_name, parameter in CATALOG.engagement_parameters.items():
        controls[f"engagement.{parameter_name}"] = parameter
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
