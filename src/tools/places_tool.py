"""
places_tool.py
---------------
Wraps OpenStreetMap's free, keyless APIs and exposes them as LangChain
Tools so the agent can search for nearby attractions and restaurants.

- Nominatim   -> turns a place name ("Jaipur, India") into lat/lon.
- Overpass API -> finds tagged points of interest (tourism / amenity)
                  within a radius of that lat/lon.

Both are completely free and require NO API key — only a descriptive
User-Agent header, per OpenStreetMap's usage policy. This means every
visitor to the app can search places with zero setup on their end.
"""

from typing import List, Optional

import requests
from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

from src.config import settings

REQUEST_TIMEOUT = 15


def _headers() -> dict:
    return {"User-Agent": settings.OSM_USER_AGENT}


def _geocode(location: str):
    """Turn a free-text location ('Jaipur, India') into lat/lon via Nominatim."""
    params = {"q": location, "format": "json", "limit": 1}
    resp = requests.get(settings.NOMINATIM_URL, params=params, headers=_headers(), timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    results = resp.json()
    if not results:
        raise ValueError(f"Could not find a location matching '{location}'.")
    top = results[0]
    return float(top["lat"]), float(top["lon"]), top.get("display_name", location)


def _overpass_query(lat: float, lon: float, radius: int, tag_filter: str, limit: int) -> list:
    """Run an Overpass QL query for nodes matching tag_filter within radius meters of (lat, lon)."""
    query = f"""
    [out:json][timeout:25];
    (
      node{tag_filter}(around:{radius},{lat},{lon});
      way{tag_filter}(around:{radius},{lat},{lon});
    );
    out center {limit};
    """
    resp = requests.post(settings.OVERPASS_URL, data={"data": query}, headers=_headers(), timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json().get("elements", [])


def _format_element(el: dict) -> str:
    tags = el.get("tags", {})
    name = tags.get("name", "Unnamed place")
    kind = tags.get("tourism") or tags.get("amenity") or tags.get("cuisine") or "Point of interest"
    address_parts = [
        tags.get("addr:housenumber"), tags.get("addr:street"),
        tags.get("addr:suburb"), tags.get("addr:city"),
    ]
    address = ", ".join(p for p in address_parts if p) or "Address not listed on OpenStreetMap"
    opening_hours = tags.get("opening_hours", "Hours not listed")
    website = tags.get("website") or tags.get("contact:website")
    line = f"- **{name}** | {kind.replace('_', ' ').title()} | 🕐 {opening_hours}\n  📍 {address}"
    if website:
        line += f"\n  🔗 {website}"
    return line


def _search_nearby(location: str, tag_filter: str, radius: int, limit: int) -> str:
    try:
        lat, lon, resolved_address = _geocode(location)
        elements = _overpass_query(lat, lon, radius, tag_filter, limit)
        elements = [e for e in elements if e.get("tags", {}).get("name")][:limit]
        if not elements:
            return f"No matching places found near {resolved_address} within {radius}m."

        header = f"Results near **{resolved_address}** (within {radius}m), via OpenStreetMap:\n"
        body = "\n".join(_format_element(e) for e in elements)
        return header + body
    except Exception as exc:  # surfaced back to the agent as a tool observation
        return f"Places search error: {exc}"


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
    cuisine: Optional[str] = Field(default=None, description="Optional cuisine keyword, e.g. 'vegetarian', 'italian' (matched loosely against OSM cuisine tags)")
    radius_meters: int = Field(
        default=settings.DEFAULT_SEARCH_RADIUS_METERS,
        description="Search radius in meters (default ~3km)",
    )
    limit: int = Field(default=5, description="Max number of results to return")


def get_places_tools() -> List[StructuredTool]:
    """
    Return the LangChain tools this module provides. No API key needed —
    OpenStreetMap's Nominatim + Overpass APIs are free and keyless.
    """

    def find_nearby_attractions(location: str, radius_meters: int = None, limit: int = 5) -> str:
        """Find tourist attractions, landmarks, museums, and points of interest near a location."""
        radius = radius_meters or settings.DEFAULT_SEARCH_RADIUS_METERS
        return _search_nearby(location, tag_filter='["tourism"]', radius=radius, limit=limit)

    def find_nearby_restaurants(location: str, cuisine: str = None, radius_meters: int = None, limit: int = 5) -> str:
        """Find restaurants, cafes, and fast food places near a location, optionally filtered by cuisine."""
        radius = radius_meters or settings.DEFAULT_SEARCH_RADIUS_METERS
        if cuisine:
            tag_filter = f'["amenity"~"restaurant|cafe|fast_food"]["cuisine"~"{cuisine}",i]'
            result = _search_nearby(location, tag_filter=tag_filter, radius=radius, limit=limit)
            # OSM cuisine tagging is inconsistent — fall back to an unfiltered search if nothing matched.
            if result.startswith("No matching places"):
                fallback = _search_nearby(location, tag_filter='["amenity"~"restaurant|cafe|fast_food"]', radius=radius, limit=limit)
                return f"No exact '{cuisine}' matches tagged on OpenStreetMap — showing nearby restaurants instead:\n\n{fallback}"
            return result
        return _search_nearby(location, tag_filter='["amenity"~"restaurant|cafe|fast_food"]', radius=radius, limit=limit)

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
                "Use this to find restaurants, cafes, and fast food spots near a "
                "given place. Optionally filter by cuisine keyword."
            ),
            args_schema=RestaurantsInput,
        ),
    ]
