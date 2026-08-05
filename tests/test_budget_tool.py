"""
test_budget_tool.py
--------------------
Unit tests for budget planning logic. These don't call any external
APIs, so they run offline once project dependencies are installed
(`pip install -r requirements.txt`).

Run with:
    pytest tests/
or:
    python tests/test_budget_tool.py
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.tools.budget_tool import plan_daily_budget, estimate_itinerary_cost


def test_plan_daily_budget_basic():
    result = plan_daily_budget(total_budget=300, num_days=3, num_travelers=2, currency="USD")
    assert "300.00 USD" in result
    assert "3 day(s)" in result
    assert "2 traveler(s)" in result


def test_plan_daily_budget_invalid_days():
    result = plan_daily_budget(total_budget=100, num_days=0, num_travelers=1)
    assert "greater than zero" in result


def test_estimate_itinerary_cost_known_tiers():
    result = estimate_itinerary_cost(["free", "moderate", "$$$"], num_travelers=2, currency="USD")
    assert "3 stop(s)" in result
    assert "2 traveler(s)" in result


def test_estimate_itinerary_cost_unknown_tier():
    result = estimate_itinerary_cost(["free", "mystery_tier"], num_travelers=1)
    assert "Couldn't interpret" in result


if __name__ == "__main__":
    test_plan_daily_budget_basic()
    test_plan_daily_budget_invalid_days()
    test_estimate_itinerary_cost_known_tiers()
    test_estimate_itinerary_cost_unknown_tier()
    print("All tests passed.")
