"""
budget_tool.py
---------------
Lightweight trip-budget planner. Google Places only exposes a 0-4
`price_level`, not real prices, so we translate that into a per-person,
per-day cost band and let the agent build a day-by-day estimate against
the traveler's stated total budget.
"""

from typing import List, Optional

from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

from src.config import settings

# Rough USD cost bands per person, per activity/meal, by Google price_level.
# These are intentionally conservative defaults — meant for ballpark planning,
# not financial precision. Tune PRICE_BAND_USD for your target destination.
PRICE_BAND_USD = {
    "free": (0, 0),
    "budget": (3, 10),
    "moderate": (10, 25),
    "expensive": (25, 60),
    "very_expensive": (60, 150),
}

TIER_ALIASES = {
    "free": "free",
    "$": "budget",
    "budget": "budget",
    "$$": "moderate",
    "moderate": "moderate",
    "$$$": "expensive",
    "expensive": "expensive",
    "$$$$": "very_expensive",
    "very expensive": "very_expensive",
    "very_expensive": "very_expensive",
}


class DailyBudgetInput(BaseModel):
    total_budget: float = Field(..., description="Total trip budget the traveler has, in their stated currency")
    num_days: int = Field(..., description="Number of days the budget must cover")
    num_travelers: int = Field(default=1, description="Number of people sharing the budget")
    currency: str = Field(default=settings.DEFAULT_CURRENCY, description="Currency code, e.g. USD, EUR, INR")


def plan_daily_budget(total_budget: float, num_days: int, num_travelers: int = 1, currency: str = None) -> str:
    """Split a total trip budget into a per-day, per-person spending allowance."""
    currency = currency or settings.DEFAULT_CURRENCY
    if num_days <= 0 or num_travelers <= 0:
        return "num_days and num_travelers must both be greater than zero."

    per_day_total = total_budget / num_days
    per_day_per_person = per_day_total / num_travelers

    # A simple, commonly-used split for a day of sightseeing.
    breakdown = {
        "Food (meals + snacks)": 0.40,
        "Attractions / activities": 0.30,
        "Local transport": 0.15,
        "Buffer / misc": 0.15,
    }
    lines = [
        f"Total budget: {total_budget:.2f} {currency} across {num_days} day(s), {num_travelers} traveler(s).",
        f"→ Per day (all travelers): {per_day_total:.2f} {currency}",
        f"→ Per day, per person: {per_day_per_person:.2f} {currency}",
        "",
        "Suggested daily split per person:",
    ]
    for category, share in breakdown.items():
        lines.append(f"  - {category}: ~{per_day_per_person * share:.2f} {currency}")
    return "\n".join(lines)


class EstimateCostInput(BaseModel):
    price_tiers: List[str] = Field(
        ...,
        description=(
            "List of price tiers for planned stops, one per stop. "
            "Use Google-style values: 'free', 'budget'/'$', 'moderate'/'$$', "
            "'expensive'/'$$$', or 'very_expensive'/'$$$$'."
        ),
    )
    num_travelers: int = Field(default=1, description="Number of people the cost applies to")
    currency: str = Field(default=settings.DEFAULT_CURRENCY, description="Currency code for the estimate")


def estimate_itinerary_cost(price_tiers: List[str], num_travelers: int = 1, currency: str = None) -> str:
    """Estimate a low/high cost range for a list of planned stops (attractions/restaurants) based on their price tier."""
    currency = currency or settings.DEFAULT_CURRENCY
    low_total, high_total = 0.0, 0.0
    unresolved = []

    for raw_tier in price_tiers:
        key = TIER_ALIASES.get(raw_tier.strip().lower())
        if not key:
            unresolved.append(raw_tier)
            continue
        low, high = PRICE_BAND_USD[key]
        low_total += low
        high_total += high

    low_total *= num_travelers
    high_total *= num_travelers

    result = (
        f"Estimated cost for {len(price_tiers)} stop(s), {num_travelers} traveler(s): "
        f"{low_total:.2f}–{high_total:.2f} {currency} "
        f"(figures are USD-based ballpark bands; convert if your currency differs)."
    )
    if unresolved:
        result += f"\nCouldn't interpret these tiers, so they were skipped: {unresolved}"
    return result


def get_budget_tools() -> List[StructuredTool]:
    """Return the LangChain tools this module provides, ready to hand to an agent."""
    return [
        StructuredTool.from_function(
            func=plan_daily_budget,
            name="plan_daily_budget",
            description=(
                "Use this to split a traveler's total trip budget into a per-day, "
                "per-person spending plan with a suggested food/activities/transport breakdown."
            ),
            args_schema=DailyBudgetInput,
        ),
        StructuredTool.from_function(
            func=estimate_itinerary_cost,
            name="estimate_itinerary_cost",
            description=(
                "Use this to estimate a low/high cost range for a set of planned "
                "attractions or restaurants, based on their Google price tier "
                "(free, budget/$, moderate/$$, expensive/$$$, very_expensive/$$$$)."
            ),
            args_schema=EstimateCostInput,
        ),
    ]
