"""
Real-Time Data API Integration for HospitAI
Fetches live weather and air quality from OpenWeatherMap.
"""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

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
        raise ValueError("OPENWEATHER_API_KEY not configured in .env file")
    
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": OPENWEATHER_API_KEY, "units": "metric"}
    
    print(f"[Weather API] Fetching weather for {city}...")
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    print(f"[Weather API] Raw response for {city}: {data}")
    
    result = {
        "temperature": round(data["main"]["temp"], 1),
        "humidity": data["main"]["humidity"],
        "pressure": data["main"]["pressure"],
        "description": data["weather"][0]["description"],
        "city": data["name"],
        "timestamp": datetime.now().isoformat(),
        "source": "OpenWeatherMap Live"
    }
    
    print(f"[Weather API] Parsed result: {result}")
    return result


def get_air_quality(city=None):
    """Fetch air quality from OpenWeatherMap Air Pollution API."""
    city = city or DEFAULT_CITY
    
    if not OPENWEATHER_API_KEY:
        raise ValueError("OPENWEATHER_API_KEY not configured in .env file")
    
    # Get coordinates
    lat, lon = CITY_COORDS.get(city, CITY_COORDS["Delhi"])
    
    url = "http://api.openweathermap.org/data/2.5/air_pollution"
    params = {"lat": lat, "lon": lon, "appid": OPENWEATHER_API_KEY}
    
    print(f"[AQI API] Fetching air quality for {city} (lat={lat}, lon={lon})...")
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    print(f"[AQI API] Raw response for {city}: {data}")
    
    components = data["list"][0]["components"]
    aqi_index = data["list"][0]["main"]["aqi"]  # 1-5 scale from OpenWeatherMap
    
    # Get PM2.5 value and calculate proper AQI
    pm25 = components.get("pm2_5", 0)
    aqi = calculate_aqi_from_pm25(pm25)
    
    print(f"[AQI API] {city}: OpenWeather AQI Index={aqi_index}, PM2.5={pm25}, Calculated AQI={aqi}")
    
    result = {
        "aqi": aqi,
        "aqi_index": aqi_index,  # Original 1-5 scale for reference
        "pm25": round(pm25, 1),
        "pm10": round(components.get("pm10", 0), 1),
        "no2": round(components.get("no2", 0), 1),
        "o3": round(components.get("o3", 0), 1),
        "co": round(components.get("co", 0), 1),
        "so2": round(components.get("so2", 0), 1),
        "nh3": round(components.get("nh3", 0), 1),
        "city": city,
        "timestamp": datetime.now().isoformat(),
        "source": "OpenWeatherMap Live"
    }
    
    print(f"[AQI API] Parsed result: {result}")
    return result


def calculate_aqi_from_pm25(pm25):
    """
    Calculate US EPA AQI from PM2.5 concentration (µg/m³).
    This provides accurate AQI values based on PM2.5 levels.
    """
    # US EPA AQI breakpoints for PM2.5
    breakpoints = [
        (0.0, 12.0, 0, 50),       # Good
        (12.1, 35.4, 51, 100),    # Moderate
        (35.5, 55.4, 101, 150),   # Unhealthy for Sensitive Groups
        (55.5, 150.4, 151, 200),  # Unhealthy
        (150.5, 250.4, 201, 300), # Very Unhealthy
        (250.5, 500.4, 301, 500)  # Hazardous
    ]
    
    for bp_lo, bp_hi, aqi_lo, aqi_hi in breakpoints:
        if bp_lo <= pm25 <= bp_hi:
            # Linear interpolation
            aqi = ((aqi_hi - aqi_lo) / (bp_hi - bp_lo)) * (pm25 - bp_lo) + aqi_lo
            return round(aqi)
    
    # If PM2.5 is above 500.4, cap at 500
    if pm25 > 500.4:
        return 500
    
    return round(pm25)  # Fallback


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
            "pm10": aqi["pm10"],
            "city": city,
            "timestamp": datetime.now().isoformat(),
            "is_live": True
        }
    }


def check_api_status():
    """Check API configuration status."""
    configured = bool(OPENWEATHER_API_KEY)
    
    result = {
        "openweather_configured": configured,
        "api_key_preview": OPENWEATHER_API_KEY[:8] + "..." if OPENWEATHER_API_KEY else "Not set",
        "default_city": DEFAULT_CITY
    }
    
    # Test the API if configured
    if configured:
        try:
            # Quick test call
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {"q": "Delhi", "appid": OPENWEATHER_API_KEY, "units": "metric"}
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            result["api_status"] = "connected"
            result["api_message"] = "API key is valid and working"
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                result["api_status"] = "invalid_key"
                result["api_message"] = "API key is invalid"
            else:
                result["api_status"] = "error"
                result["api_message"] = str(e)
        except Exception as e:
            result["api_status"] = "error"
            result["api_message"] = str(e)
    else:
        result["api_status"] = "not_configured"
        result["api_message"] = "Add OPENWEATHER_API_KEY to .env file"
    
    return result


if __name__ == "__main__":
    print("Testing Real Data APIs:\n")
    
    status = check_api_status()
    print(f"API Status: {status}\n")
    
    if status["openweather_configured"]:
        print("Fetching live data for multiple cities...\n")
        
        for city in ["Delhi", "Mumbai", "Bangalore"]:
            try:
                print(f"--- {city} ---")
                data = get_realtime_data(city)
                
                print(f"🌡️  Temperature: {data['weather']['temperature']}°C")
                print(f"💧 Humidity: {data['weather']['humidity']}%")
                print(f"🌫️  AQI: {data['air_quality']['aqi']} (PM2.5: {data['air_quality']['pm25']} µg/m³)")
                print(f"📍 Source: {data['weather']['source']}")
                print()
            except Exception as e:
                print(f"Error fetching data for {city}: {e}\n")
    else:
        print("❌ OPENWEATHER_API_KEY not configured. Add it to backend/.env file.")
