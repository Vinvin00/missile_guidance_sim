"""Shared PN/APN/OGL factory builders for scripts/evaluation that need all three."""

from __future__ import annotations

from typing import Callable, TypeVar

from guidance_sim.guidance.augmented_pn import AugmentedProportionalNavigation
from guidance_sim.guidance.base import GuidanceLaw
from guidance_sim.guidance.optimal_guidance import OptimalGuidance
from guidance_sim.guidance.proportional_navigation import ProportionalNavigation
from guidance_sim.physics.entities import PointMassEntity

T = TypeVar("T")


def classical_law_factories(
    get_target: Callable[[T], PointMassEntity],
    *,
    pn_n: float,
    apn_n: float | None = None,
    ogl_n: float | None = None,
) -> dict[str, Callable[[T], GuidanceLaw]]:
    """PN/APN/OGL factories parameterized by navigation constant and a target getter.

    ``get_target`` extracts the target entity (whose achieved lateral accel
    APN/OGL need) from whatever context object each caller threads through --
    a bare entity, or an env with a ``.target`` attribute.
    """

    apn_n = pn_n if apn_n is None else apn_n
    ogl_n = pn_n if ogl_n is None else ogl_n

    def pn_factory(_context: T) -> GuidanceLaw:
        return ProportionalNavigation(pn_n)

    def apn_factory(context: T) -> GuidanceLaw:
        target = get_target(context)
        return AugmentedProportionalNavigation(
            apn_n, a_target_est=lambda: target.last_achieved_lateral_accel.copy()
        )

    def ogl_factory(context: T) -> GuidanceLaw:
        target = get_target(context)
        return OptimalGuidance(
            ogl_n, a_target_est=lambda: target.last_achieved_lateral_accel.copy()
        )

    return {"PN": pn_factory, "APN": apn_factory, "OGL": ogl_factory}
