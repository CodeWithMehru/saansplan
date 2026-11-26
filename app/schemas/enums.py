"""Centralized domain enumerations for air quality categories and budget tiers."""

from __future__ import annotations

from enum import Enum


class CPCBCategory(str, Enum):
    """CPCB Indian National Air Quality Index categories."""

    GOOD = "Good"
    SATISFACTORY = "Satisfactory"
    MODERATE = "Moderate"
    POOR = "Poor"
    VERY_POOR = "Very Poor"
    SEVERE = "Severe"


class BudgetTier(str, Enum):
    """Household intervention economic budget tiers."""

    LOW = "low"
    MODERATE = "moderate"
    BALANCED = "balanced"


__all__ = ["BudgetTier", "CPCBCategory"]
