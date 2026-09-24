import json
import urllib.parse
import urllib.request
from typing import Any


def get_destination_weather(city: str, event_dates: str = "") -> str:
    """Fetch live weather forecast and indoor vs outdoor scheduling recommendations using Open-Meteo.

    Args:
        city: Name of the destination city (e.g. 'Scottsdale', 'Miami', 'Cabo').
        event_dates: Optional target event dates or date range string (e.g. '2026-09-25 to 2026-09-27').

    Returns:
        JSON string with temperature forecast, precipitation probability, and indoor/outdoor scheduling advice.
    """
    try:
        # 1. Geocoding lookup
        encoded_city = urllib.parse.quote(city)
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_city}&count=1"
        req = urllib.request.Request(
            geo_url, headers={"User-Agent": "RevelisAgent/1.0"}
        )
        with urllib.request.urlopen(req) as resp:
            geo_data = json.loads(resp.read().decode())

        results = geo_data.get("results")
        if not results:
            return json.dumps({
                "error": f"Could not resolve location coordinates for '{city}'."
            })

        lat = results[0]["latitude"]
        lon = results[0]["longitude"]
        location_name = f"{results[0].get('name')}, {results[0].get('admin1', '')} {results[0].get('country', '')}".strip()
        timezone = results[0].get("timezone", "auto")

        # 2. Forecast lookup
        forecast_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&"
            f"daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode&"
            f"current_weather=true&temperature_unit=fahrenheit&timezone={urllib.parse.quote(timezone)}"
        )
        req_forecast = urllib.request.Request(
            forecast_url, headers={"User-Agent": "RevelisAgent/1.0"}
        )
        with urllib.request.urlopen(req_forecast) as resp:
            forecast_data = json.loads(resp.read().decode())

        current_weather = forecast_data.get("current_weather", {})
        daily = forecast_data.get("daily", {})

        times = daily.get("time", [])
        temp_maxs = daily.get("temperature_2m_max", [])
        temp_mins = daily.get("temperature_2m_min", [])
        precip_probs = daily.get("precipitation_probability_max", [])

        forecast_days = []
        high_precip_days = []
        for idx in range(min(len(times), 7)):
            date_str = times[idx]
            max_t = temp_maxs[idx] if idx < len(temp_maxs) else None
            min_t = temp_mins[idx] if idx < len(temp_mins) else None
            p_prob = precip_probs[idx] if idx < len(precip_probs) else 0

            forecast_days.append({
                "date": date_str,
                "high_f": max_t,
                "low_f": min_t,
                "precipitation_probability": f"{p_prob}%",
            })
            if p_prob >= 40:
                high_precip_days.append(date_str)

        # Recommendation logic
        if high_precip_days:
            scheduling_rec = f"Rain likely on {', '.join(high_precip_days)} (>40% chance). Recommend scheduling indoor dining, spa, or lounge events on those dates."
        else:
            scheduling_rec = "Favorable weather predicted with low rain probability. Excellent conditions for outdoor pool parties, yacht charters, and patio dining."

        summary = {
            "city": city,
            "resolved_location": location_name,
            "event_dates": event_dates if event_dates else "Upcoming 7-day forecast",
            "current_temperature_f": current_weather.get("temperature"),
            "daily_forecast": forecast_days,
            "scheduling_recommendation": scheduling_rec,
        }

        return json.dumps(summary, indent=2)

    except Exception as e:
        return json.dumps({
            "error": f"Failed to fetch weather data for '{city}': {str(e)}"
        })
