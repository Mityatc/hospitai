"""
Real-Time Data API Integration for HospitAI
"""

import logging
import os
from datetime import datetime
import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
DEFAULT_CITY = os.getenv("DEFAULT_CITY", "Delhi")

CITY_COORDS = {
    "Delhi": (28.6139, 77.2090), "Mumbai": (19.0760, 72.8777),
    "Bangalore": (12.9716, 77.5946), "Chennai": (13.0827, 80.2707),
}


def get_weather_data(city=None):
    city = city or DEFAULT_CITY
    if not OPENWEATHER_API_KEY:
        return _mock_weather_data(city)
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"q": city, "appid": OPENWEATHER_API_KEY, "units": "metric"}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {
            "temperature": round(data["main"]["temp"], 1),
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "description": data["weather"][0]["description"],
            "city": data["name"],
            "timestamp": datetime.now().isoformat(),
            "source": "Live"
        }
    except Exception as e:
        logger.warning(f"Weather API error: {e}")
        return _mock_weather_data(city)


def get_air_quality(city=None):
    city = city or DEFAULT_CITY
    if not OPENWEATHER_API_KEY:
        return _mock_aqi_data(city)
    try:
        lat, lon = CITY_COORDS.get(city, CITY_COORDS["Delhi"])
        url = "http://api.openweathermap.org/data/2.5/air_pollution"
        params = {"lat": lat, "lon": lon, "appid": OPENWEATHER_API_KEY}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        components = data["list"][0]["components"]
        aqi_map = {1: 25, 2: 50, 3: 100, 4: 150, 5: 200}
        return {
            "aqi": aqi_map.get(data["list"][0]["main"]["aqi"], 100),
            "pm25": round(components.get("pm2_5", 0), 1),
            "pm10": round(components.get("pm10", 0), 1),
            "city": city,
            "timestamp": datetime.now().isoformat(),
            "source": "Live"
        }
    except Exception as e:
        logger.warning(f"AQI API error: {e}")
        return _mock_aqi_data(city)


def _mock_weather_data(city):
    import random
    return {"temperature": round(random.uniform(20, 35), 1), "humidity": round(random.uniform(40, 80), 1),
            "pressure": 1013, "description": "partly cloudy", "city": city,
            "timestamp": datetime.now().isoformat(), "source": "Simulated"}


def _mock_aqi_data(city):
    import random
    return {"aqi": random.randint(50, 180), "pm25": round(random.uniform(20, 100), 1),
            "pm10": round(random.uniform(30, 150), 1), "city": city,
            "timestamp": datetime.now().isoformat(), "source": "Simulated"}


def get_realtime_data(city=None):
    city = city or DEFAULT_CITY
    weather = get_weather_data(city)
    aqi = get_air_quality(city)
    return {
        "weather": weather, "air_quality": aqi,
        "combined": {"temperature": weather["temperature"], "humidity": weather["humidity"],
                     "pollution": aqi["aqi"], "pm25": aqi["pm25"], "city": city,
                     "timestamp": datetime.now().isoformat(), "is_live": weather["source"] == "Live"}
    }


def check_api_status():
    return {"openweather_configured": bool(OPENWEATHER_API_KEY), "default_city": DEFAULT_CITY}
