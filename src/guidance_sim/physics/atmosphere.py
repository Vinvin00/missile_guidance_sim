"""
Simplified International Standard Atmosphere (ISA) model.

Covers the troposphere (0-11 km) and lower stratosphere (11-20 km),
which is more than enough altitude range for the drone/missile
engagement envelopes this simulation targets. This is the same
standard atmosphere model used in any introductory aerodynamics or
flight-dynamics course -- there is nothing weapon-specific about it.

Reference: ICAO Standard Atmosphere / U.S. Standard Atmosphere 1976.
"""

from __future__ import annotations

import numpy as np

G0 = 9.80665  # m/s^2, standard gravity
R_AIR = 287.05287  # J/(kg*K), specific gas constant for dry air

# Sea-level reference conditions
T0 = 288.15  # K
P0 = 101325.0  # Pa
RHO0 = 1.225  # kg/m^3

# Troposphere lapse rate
LAPSE_RATE = 0.0065  # K/m
TROPOPAUSE_ALT = 11000.0  # m
TROPOPAUSE_TEMP = T0 - LAPSE_RATE * TROPOPAUSE_ALT  # 216.65 K

# Pressure at the tropopause, from the troposphere formula evaluated at 11 km
_P_TROPOPAUSE = P0 * (TROPOPAUSE_TEMP / T0) ** (G0 / (LAPSE_RATE * R_AIR))


def isa_temperature(altitude_m: float) -> float:
    """Air temperature (K) at the given geometric altitude (m)."""
    h = max(altitude_m, 0.0)
    if h <= TROPOPAUSE_ALT:
        return T0 - LAPSE_RATE * h
    return TROPOPAUSE_TEMP  # isothermal in the lower stratosphere (11-20 km)


def isa_pressure(altitude_m: float) -> float:
    """Static pressure (Pa) at the given geometric altitude (m)."""
    h = max(altitude_m, 0.0)
    if h <= TROPOPAUSE_ALT:
        temp = isa_temperature(h)
        return P0 * (temp / T0) ** (G0 / (LAPSE_RATE * R_AIR))
    # Isothermal layer: exponential pressure decay
    return _P_TROPOPAUSE * np.exp(-G0 * (h - TROPOPAUSE_ALT) / (R_AIR * TROPOPAUSE_TEMP))


def isa_density(altitude_m: float) -> float:
    """Air density (kg/m^3) at the given geometric altitude (m)."""
    temp = isa_temperature(altitude_m)
    pressure = isa_pressure(altitude_m)
    return pressure / (R_AIR * temp)


def speed_of_sound(altitude_m: float) -> float:
    """Local speed of sound (m/s), for Mach-number bookkeeping."""
    gamma = 1.4  # ratio of specific heats for air
    temp = isa_temperature(altitude_m)
    return float(np.sqrt(gamma * R_AIR * temp))
