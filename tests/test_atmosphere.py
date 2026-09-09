import numpy as np

from guidance_sim.physics.atmosphere import isa_density, isa_pressure, isa_temperature, RHO0, P0, T0


def test_sea_level_matches_standard_reference_values():
    assert np.isclose(isa_density(0.0), RHO0, atol=1e-3)
    assert np.isclose(isa_pressure(0.0), P0, atol=1.0)
    assert np.isclose(isa_temperature(0.0), T0, atol=1e-6)


def test_density_decreases_monotonically_with_altitude():
    altitudes = [0, 1000, 3000, 5000, 8000, 11000, 15000, 20000]
    densities = [isa_density(h) for h in altitudes]
    assert all(densities[i] > densities[i + 1] for i in range(len(densities) - 1))


def test_temperature_isothermal_above_tropopause():
    assert np.isclose(isa_temperature(11000), isa_temperature(15000))
    assert np.isclose(isa_temperature(15000), isa_temperature(20000))


def test_negative_altitude_clamped_to_sea_level():
    # Guards against nonsensical negative-altitude inputs blowing up the model.
    assert np.isclose(isa_density(-50.0), isa_density(0.0))
