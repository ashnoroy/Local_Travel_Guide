"""
places_tool.py
---------------
Wraps the Google Places API and exposes it as LangChain Tools so the
agent can search for nearby attractions and restaurants, and pull
enough detail (rating, price level, address) to feed budget planning.

The Google Places API key is passed in at build time (get_places_tools),
NOT read from a global settings object — this lets each user supply
their own key from the Streamlit sidebar instead of sharing the app
owner's key/quota.
"""

from typing import List, Optional

import googlemaps
from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

from src.config import settings

# Google's price_level is 0-4; map it to something a person understands.
PRICE_LEVEL_MAP = {
    0: "Free",
    1: "Budget ($)",
    2: "Moderate ($$)",
    3: "Expensive ($$$)",
    4: "Very Expensive ($$$$)",
}


def _get_client(api_key: str) -> googlemaps.Client:
    if not api_key:
        raise EnvironmentError("No Google Places API key was provided.")
    return googlemaps.Client(key=api_key)


def _geocode(location: str, api_key: str):
    """Turn a free-text location ('Jaipur, India') into lat/lng."""
    client = _get_client(api_key)
    results = client.geocode(location)
    if not results:
        raise ValueError(f"Could not find a location matching '{location}'.")
    loc = results[0]["geometry"]["location"]
    return loc["lat"], loc["lng"], results[0].get("formatted_address", location)


def _format_place(place: dict) -> str:
    name = place.get("name", "Unknown")
    rating = place.get("rating", "N/A")
    total_ratings = place.get("user_ratings_total", 0)
    address = place.get("vicinity") or place.get("formatted_address", "Address unavailable")
    price_level = PRICE_LEVEL_MAP.get(place.get("price_level"), "Not listed")
    open_now = place.get("opening_hours", {}).get("open_now")
    open_str = (
        "Open now" if open_now is True else "Closed now" if open_now is False else "Hours unknown"
    )
    return (
        f"- **{name}** | ⭐ {rating} ({total_ratings} reviews) | "
        f"{price_level} | {open_str}\n  📍 {address}"
    )


def _search_nearby(
    location: str, place_type: str, keyword: Optional[str], radius: int, limit: int, api_key: str
) -> str:
    try:
        lat, lng, resolved_address = _geocode(location, api_key)
        client = _get_client(api_key)
        response = client.places_nearby(
            location=(lat, lng),
            radius=radius,
            type=place_type,
            keyword=keyword,
        )
        results = response.get("results", [])[:limit]
        if not results:
            return f"No {place_type.replace('_', ' ')}s found near {resolved_address}."

        header = f"Results near **{resolved_address}** (within {radius}m):\n"
        body = "\n".join(_format_place(p) for p in results)
        return header + body
    except Exception as exc:  # surfaced back to the agent as a tool observation
        return f"Places API error: {exc}"


# ---------- Tool: Nearby Attractions ----------

class AttractionsInput(BaseModel):
    location: str = Field(..., description="City, neighborhood, or address, e.g. 'Jaipur, India'")
    radius_meters: int = Field(
        default=settings.DEFAULT_SEARCH_RADIUS_METERS,
        description="Search radius in meters (default ~3km)",
    )
    limit: int = Field(default=5, description="Max number of results to return")


# ---------- Tool: Nearby Restaurants ----------

class RestaurantsInput(BaseModel):
    location: str = Field(..., description="City, neighborhood, or address, e.g. 'Jaipur, India'")
    cuisine: Optional[str] = Field(default=None, description="Optional cuisine keyword, e.g. 'vegetarian', 'street food'")
    radius_meters: int = Field(
        default=settings.DEFAULT_SEARCH_RADIUS_METERS,
        description="Search radius in meters (default ~3km)",
    )
    limit: int = Field(default=5, description="Max number of results to return")


def get_places_tools(google_places_api_key: str) -> List[StructuredTool]:
    """
    Return the LangChain tools this module provides, bound to the given
    Google Places API key (e.g. the one a specific user typed into the
    sidebar), ready to hand to an agent.
    """

    def find_nearby_attractions(location: str, radius_meters: int = None, limit: int = 5) -> str:
        """Find tourist attractions, landmarks, and points of interest near a location."""
        radius = radius_meters or settings.DEFAULT_SEARCH_RADIUS_METERS
        return _search_nearby(
            location, place_type="tourist_attraction", keyword=None,
            radius=radius, limit=limit, api_key=google_places_api_key,
        )

    def find_nearby_restaurants(location: str, cuisine: str = None, radius_meters: int = None, limit: int = 5) -> str:
        """Find restaurants near a location, optionally filtered by cuisine/keyword."""
        radius = radius_meters or settings.DEFAULT_SEARCH_RADIUS_METERS
        return _search_nearby(
            location, place_type="restaurant", keyword=cuisine,
            radius=radius, limit=limit, api_key=google_places_api_key,
        )

    return [
        StructuredTool.from_function(
            func=find_nearby_attractions,
            name="find_nearby_attractions",
            description=(
                "Use this to find tourist attractions, landmarks, museums, parks, "
                "and points of interest near a given place. Input a location string."
            ),
            args_schema=AttractionsInput,
        ),
        StructuredTool.from_function(
            func=find_nearby_restaurants,
            name="find_nearby_restaurants",
            description=(
                "Use this to find restaurants, cafes, and street food spots near a "
                "given place. Optionally filter by cuisine keyword."
            ),
            args_schema=RestaurantsInput,
        ),
    ]
