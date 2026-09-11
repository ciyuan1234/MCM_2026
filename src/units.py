"""Explicit conversions for the input, solver and output unit boundaries."""

from __future__ import annotations

CM_PER_M = 100.0
KELVIN_OFFSET = 273.15


def cm_to_m(value_cm: float) -> float:
    return value_cm / CM_PER_M


def m_to_cm(value_m: float) -> float:
    return value_m * CM_PER_M


def celsius_to_kelvin(value_c: float) -> float:
    return value_c + KELVIN_OFFSET


def kelvin_to_celsius(value_k: float) -> float:
    return value_k - KELVIN_OFFSET
