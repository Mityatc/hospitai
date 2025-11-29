"""
Real-Time Data API Integration for HospitAI
Fetches live weather and air quality from OpenWeatherMap.
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

# City coordinates for Air Pollution API
CITY_COORDS = {
    "Delhi": (28.6139, 77.2090),
    "Mumbai": (19.0760, 72.8777),
    "Bangalore": (12.9716, 77.5946),
    "Chennai": (13.0827, 80.2707),
    "Kolkata": (22.5726, 88.3639),
    "Hyderabad": (17.3850, 78.4867),
}


def get_weather_data(city=None):
    """Fetch current weather from OpenWeatherMap."""
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
            "source": "🌐 OpenWeatherMap Live"
        }
    except Exception as e:
        logger.warning(f"Weather API error: {e}")
        return _mock_weather_data(city)


def get_air_quality(city=None):
    """Fetch air quality from OpenWeatherMap Air Pollution API."""
    city = city or DEFAULT_CITY
    
    if not OPENWEATHER_API_KEY:
        return _mock_aqi_data(city)
    
    try:
        # Get coordinates
        lat, lon = CITY_COORDS.get(city, CITY_COORDS["Delhi"])
        
        url = "http://api.openweathermap.org/data/2.5/air_pollution"
        params = {"lat": lat, "lon": lon, "appid": OPENWEATHER_API_KEY}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        components = data["list"][0]["components"]
        aqi_index = data["list"][0]["main"]["aqi"]  # 1-5 scale
        
        # Convert to standard AQI (approximate)
        aqi_map = {1: 25, 2: 50, 3: 100, 4: 150, 5: 200}
        aqi = aqi_map.get(aqi_index, 100)
        
        return {
            "aqi": aqi,
            "pm25": round(components.get("pm2_5", 0), 1),
            "pm10": round(components.get("pm10", 0), 1),
            "no2": round(components.get("no2", 0), 1),
            "o3": round(components.get("o3", 0), 1),
            "co": round(components.get("co", 0), 1),
            "city": city,
            "timestamp": datetime.now().isoformat(),
            "source": "🌐 OpenWeatherMap Live"
        }
    except Exception as e:
        logger.warning(f"AQI API error: {e}")
        return _mock_aqi_data(city)


def _mock_weather_data(city):
    """Mock weather when API unavailable."""
    import random
    return {
        "temperature": round(random.uniform(20, 35), 1),
        "humidity": round(random.uniform(40, 80), 1),
        "pressure": round(random.uniform(1005, 1020), 1),
        "description": "partly cloudy",
        "city": city,
        "timestamp": datetime.now().isoformat(),
        "source": "🎭 Simulated"
    }


def _mock_aqi_data(city):
    """Mock AQI when API unavailable."""
    import random
    return {
        "aqi": random.randint(50, 180),
        "pm25": round(random.uniform(20, 100), 1),
        "pm10": round(random.uniform(30, 150), 1),
        "no2": round(random.uniform(10, 50), 1),
        "o3": round(random.uniform(20, 80), 1),
        "co": round(random.uniform(200, 500), 1),
        "city": city,
        "timestamp": datetime.now().isoformat(),
        "source": "🎭 Simulated"
    }


def get_realtime_data(city=None):
    """Get combined real-time environmental data."""
    city = city or DEFAULT_CITY
    weather = get_weather_data(city)
    aqi = get_air_quality(city)
    
    return {
        "weather": weather,
        "air_quality": aqi,
        "combined": {
            "temperature": weather["temperature"],
            "humidity": weather["humidity"],
            "pollution": aqi["aqi"],
            "pm25": aqi["pm25"],
            "city": city,
            "timestamp": datetime.now().isoformat(),
            "is_live": "Live" in weather["source"]
        }
    }


def check_api_status():
    """Check API configuration status."""
    return {
        "openweather_configured": bool(OPENWEATHER_API_KEY),
        "api_key_preview": OPENWEATHER_API_KEY[:8] + "..." if OPENWEATHER_API_KEY else "Not set",
        "default_city": DEFAULT_CITY
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    status = check_api_status()
    logger.info(f"API Status: {status}")
    data = get_realtime_data("Delhi")
    logger.info(f"Weather: {data['weather']}")
    logger.info(f"Air Quality: {data['air_quality']}")
