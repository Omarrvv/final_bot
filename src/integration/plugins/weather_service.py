"""
Weather service plugin for the Egypt Tourism Chatbot.
Provides real-time weather information using OpenWeatherMap API.
"""
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from integration.service_hub import Service

logger = logging.getLogger(__name__)

class WeatherService(Service):
    """
    Weather service implementation using OpenWeatherMap API.
    Provides current weather and forecasts for Egyptian locations.
    """

    def __init__(self, name: str, config: Dict):
        """
        Initialize the weather service.

        Args:
            name (str): Service name
            config (dict): Service configuration
        """
        super().__init__(name, config)
        self.api_key = config.get("api_key", "")
        self.base_url = config.get("base_url", "https://api.openweathermap.org/data/2.5")

        # Egyptian cities with coordinates for quick lookup
        self.egyptian_cities = {
            "cairo": {"lat": 30.0444, "lon": 31.2357, "arabic": "القاهرة"},
            "alexandria": {"lat": 31.2001, "lon": 29.9187, "arabic": "الإسكندرية"},
            "giza": {"lat": 30.0131, "lon": 31.2089, "arabic": "الجيزة"},
            "luxor": {"lat": 25.6872, "lon": 32.6396, "arabic": "الأقصر"},
            "aswan": {"lat": 24.0889, "lon": 32.8998, "arabic": "أسوان"},
            "hurghada": {"lat": 27.2579, "lon": 33.8116, "arabic": "الغردقة"},
            "sharm el sheikh": {"lat": 27.9158, "lon": 34.3300, "arabic": "شرم الشيخ"},
            "dahab": {"lat": 28.4913, "lon": 34.5155, "arabic": "دهب"},
            "marsa alam": {"lat": 25.0693, "lon": 34.8939, "arabic": "مرسى علم"},
            "siwa": {"lat": 29.2032, "lon": 25.5168, "arabic": "سيوة"}
        }

        logger.info("Weather service initialized")

    def get_type(self) -> str:
        """Get the service type."""
        return "weather"

    def get_current_weather(self, location: str, language: str = "en") -> Dict:
        """
        Get current weather for a location.

        Args:
            location (str): Location name
            language (str): Language code

        Returns:
            dict: Weather data
        """
        if not self.api_key:
            return {
                "error": "Weather API key not configured",
                "weather": self._get_mock_weather(location, "current")
            }

        # Get coordinates for the location
        coords = self._get_coordinates(location)

        if not coords:
            return {
                "error": f"Location not found: {location}",
                "weather": self._get_mock_weather(location, "current")
            }

        # Set API parameters
        params = {
            "lat": coords["lat"],
            "lon": coords["lon"],
            "appid": self.api_key,
            "units": "metric",
            "lang": "ar" if language == "ar" else "en"
        }

        try:
            # Call OpenWeatherMap API
            response = requests.get(f"{self.base_url}/weather", params=params)
            response.raise_for_status()
            data = response.json()

            # Format the response
            result = self._format_current_weather(data, language)

            # Add location info
            result["location"] = {
                "name": {
                    "en": location,
                    "ar": self._get_arabic_name(location)
                },
                "coordinates": coords
            }

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Weather API error: {str(e)}")
            return {
                "error": f"API error: {str(e)}",
                "weather": self._get_mock_weather(location, "current")
            }

    def get_forecast(self, location: str, days: int = 5, language: str = "en") -> Dict:
        """
        Get weather forecast for a location.

        Args:
            location (str): Location name
            days (int): Number of days (1-7)
            language (str): Language code

        Returns:
            dict: Forecast data
        """
        if not self.api_key:
            return {
                "error": "Weather API key not configured",
                "forecast": self._get_mock_weather(location, "forecast", days)
            }

        # Limit days to 1-7
        days = max(1, min(7, days))

        # Get coordinates for the location
        coords = self._get_coordinates(location)

        if not coords:
            return {
                "error": f"Location not found: {location}",
                "forecast": self._get_mock_weather(location, "forecast", days)
            }

        # Set API parameters
        params = {
            "lat": coords["lat"],
            "lon": coords["lon"],
            "appid": self.api_key,
            "units": "metric",
            "cnt": days * 8,  # 8 data points per day (3-hour intervals)
            "lang": "ar" if language == "ar" else "en"
        }

        try:
            # Call OpenWeatherMap API
            response = requests.get(f"{self.base_url}/forecast", params=params)
            response.raise_for_status()
            data = response.json()

            # Format the response
            result = self._format_forecast(data, days, language)

            # Add location info
            result["location"] = {
                "name": {
                    "en": location,
                    "ar": self._get_arabic_name(location)
                },
                "coordinates": coords
            }

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Weather API error: {str(e)}")
            return {
                "error": f"API error: {str(e)}",
                "forecast": self._get_mock_weather(location, "forecast", days)
            }

    def get_best_time_to_visit(self, location: str, language: str = "en") -> Dict:
        """
        Get recommendations for the best time to visit a location.

        Args:
            location (str): Location name
            language (str): Language code

        Returns:
            dict: Recommendation data
        """
        # This would typically use historical weather data
        # For now, we'll use hardcoded recommendations for Egyptian destinations

        recommendations = {
            "cairo": {
                "best_time": {
                    "en": "October to April",
                    "ar": "من أكتوبر إلى أبريل"
                },
                "reason": {
                    "en": "Pleasant temperatures avoiding summer heat",
                    "ar": "درجات حرارة لطيفة تجنبًا لحرارة الصيف"
                },
                "avoid": {
                    "en": "June to August (extreme heat)",
                    "ar": "من يونيو إلى أغسطس (حرارة شديدة)"
                }
            },
            "alexandria": {
                "best_time": {
                    "en": "May to October",
                    "ar": "من مايو إلى أكتوبر"
                },
                "reason": {
                    "en": "Perfect Mediterranean weather and sea temperatures",
                    "ar": "طقس البحر المتوسط المثالي ودرجات حرارة البحر"
                },
                "avoid": {
                    "en": "December to February (rain season)",
                    "ar": "من ديسمبر إلى فبراير (موسم الأمطار)"
                }
            },
            "luxor": {
                "best_time": {
                    "en": "October to April",
                    "ar": "من أكتوبر إلى أبريل"
                },
                "reason": {
                    "en": "Comfortable temperatures for exploring ancient temples",
                    "ar": "درجات حرارة مريحة لاستكشاف المعابد القديمة"
                },
                "avoid": {
                    "en": "June to August (extremely hot, can reach 45°C)",
                    "ar": "من يونيو إلى أغسطس (حار للغاية، يمكن أن تصل إلى 45 درجة مئوية)"
                }
            },
            "aswan": {
                "best_time": {
                    "en": "October to April",
                    "ar": "من أكتوبر إلى أبريل"
                },
                "reason": {
                    "en": "Pleasant temperatures for Nile cruises and monument visits",
                    "ar": "درجات حرارة لطيفة للرحلات النيلية وزيارة المعالم"
                },
                "avoid": {
                    "en": "June to September (extremely hot)",
                    "ar": "من يونيو إلى سبتمبر (حار للغاية)"
                }
            },
            "hurghada": {
                "best_time": {
                    "en": "April to June, September to November",
                    "ar": "من أبريل إلى يونيو، من سبتمبر إلى نوفمبر"
                },
                "reason": {
                    "en": "Perfect weather for beach activities and diving",
                    "ar": "طقس مثالي للأنشطة الشاطئية والغوص"
                },
                "avoid": {
                    "en": "July and August can be very hot",
                    "ar": "يوليو وأغسطس يمكن أن يكونا شديدي الحرارة"
                }
            },
            "sharm el sheikh": {
                "best_time": {
                    "en": "Year-round destination, best from March to May and September to November",
                    "ar": "وجهة على مدار السنة، الأفضل من مارس إلى مايو ومن سبتمبر إلى نوفمبر"
                },
                "reason": {
                    "en": "Perfect weather for diving and beach activities",
                    "ar": "طقس مثالي للغوص والأنشطة الشاطئية"
                },
                "avoid": {
                    "en": "July and August can be crowded and hot",
                    "ar": "يوليو وأغسطس يمكن أن يكونا مزدحمين وحارين"
                }
            }
        }

        # Normalize location name
        location_lower = location.lower()

        # Get recommendation for location or default to Cairo
        recommendation = recommendations.get(location_lower, recommendations.get("cairo"))

        result = {
            "location": {
                "en": location,
                "ar": self._get_arabic_name(location)
            },
            "best_time": recommendation["best_time"][language if language in ["en", "ar"] else "en"],
            "reason": recommendation["reason"][language if language in ["en", "ar"] else "en"],
            "avoid": recommendation["avoid"][language if language in ["en", "ar"] else "en"]
        }

        return result

    def _get_coordinates(self, location: str) -> Optional[Dict]:
        """Get coordinates for a location."""
        # Normalize location name
        location_lower = location.lower()

        # Check if it's in our predefined Egyptian cities
        if location_lower in self.egyptian_cities:
            return {
                "lat": self.egyptian_cities[location_lower]["lat"],
                "lon": self.egyptian_cities[location_lower]["lon"]
            }

        # Try partial matching
        for city, data in self.egyptian_cities.items():
            if city in location_lower or location_lower in city:
                return {
                    "lat": data["lat"],
                    "lon": data["lon"]
                }

        # If not found, default to Cairo
        if self.api_key:
            # Try to geocode the location using OpenWeatherMap's geocoding API
            try:
                params = {
                    "q": f"{location},EG",  # Add Egypt as country to narrow results
                    "limit": 1,
                    "appid": self.api_key
                }

                response = requests.get("http://api.openweathermap.org/geo/1.0/direct", params=params)
                response.raise_for_status()
                data = response.json()

                if data and len(data) > 0:
                    return {
                        "lat": data[0]["lat"],
                        "lon": data[0]["lon"]
                    }
            except Exception as e:
                logger.error(f"Geocoding error: {str(e)}")

        # Default to Cairo if not found
        return {
            "lat": 30.0444,
            "lon": 31.2357
        }

    def _get_arabic_name(self, location: str) -> str:
        """Get Arabic name for a location."""
        location_lower = location.lower()

        if location_lower in self.egyptian_cities:
            return self.egyptian_cities[location_lower]["arabic"]

        # Try partial matching
        for city, data in self.egyptian_cities.items():
            if city in location_lower or location_lower in city:
                return data["arabic"]

        # Default to transliteration if no match
        # (This is a simplistic approach, proper transliteration would use a specialized library)
        return location

    def _format_current_weather(self, data: Dict, language: str) -> Dict:
        """Format current weather data."""
        try:
            weather = data["weather"][0]
            main = data["main"]
            wind = data["wind"]

            result = {
                "timestamp": datetime.utcnow().isoformat(),
                "weather": {
                    "description": weather["description"],
                    "icon": weather["icon"],
                    "main": weather["main"]
                },
                "temperature": {
                    "current": main["temp"],
                    "feels_like": main["feels_like"],
                    "min": main["temp_min"],
                    "max": main["temp_max"]
                },
                "humidity": main["humidity"],
                "wind": {
                    "speed": wind["speed"],
                    "direction": wind.get("deg", 0)
                },
                "pressure": main["pressure"]
            }

            # Add sunrise/sunset if available
            if "sys" in data and "sunrise" in data["sys"] and "sunset" in data["sys"]:
                result["sun"] = {
                    "sunrise": datetime.fromtimestamp(data["sys"]["sunrise"]).isoformat(),
                    "sunset": datetime.fromtimestamp(data["sys"]["sunset"]).isoformat()
                }

            return result
        except Exception as e:
            logger.error(f"Error formatting weather data: {str(e)}")
            return self._get_mock_weather(data.get("name", "Unknown"), "current")

    def _format_forecast(self, data: Dict, days: int, language: str) -> Dict:
        """Format forecast data."""
        try:
            # Group forecast by day
            daily_forecasts = {}

            for item in data["list"]:
                # Convert timestamp to datetime
                dt = datetime.fromtimestamp(item["dt"])
                date_key = dt.strftime("%Y-%m-%d")

                # Initialize day if not exists
                if date_key not in daily_forecasts:
                    daily_forecasts[date_key] = {
                        "date": date_key,
                        "day_name": self._get_day_name(dt, language),
                        "temperature": {
                            "min": float('inf'),
                            "max": float('-inf'),
                            "avg": []
                        },
                        "humidity": [],
                        "weather": [],
                        "wind": [],
                        "hours": []
                    }

                # Update min/max temperature
                temp = item["main"]["temp"]
                daily_forecasts[date_key]["temperature"]["min"] = min(daily_forecasts[date_key]["temperature"]["min"], temp)
                daily_forecasts[date_key]["temperature"]["max"] = max(daily_forecasts[date_key]["temperature"]["max"], temp)
                daily_forecasts[date_key]["temperature"]["avg"].append(temp)

                # Add humidity
                daily_forecasts[date_key]["humidity"].append(item["main"]["humidity"])

                # Add weather condition (most frequent will be selected later)
                daily_forecasts[date_key]["weather"].append({
                    "id": item["weather"][0]["id"],
                    "main": item["weather"][0]["main"],
                    "description": item["weather"][0]["description"],
                    "icon": item["weather"][0]["icon"]
                })

                # Add wind
                daily_forecasts[date_key]["wind"].append({
                    "speed": item["wind"]["speed"],
                    "direction": item["wind"].get("deg", 0)
                })

                # Add hour data
                daily_forecasts[date_key]["hours"].append({
                    "time": dt.strftime("%H:%M"),
                    "temperature": temp,
                    "weather": {
                        "main": item["weather"][0]["main"],
                        "description": item["weather"][0]["description"],
                        "icon": item["weather"][0]["icon"]
                    },
                    "humidity": item["main"]["humidity"],
                    "wind_speed": item["wind"]["speed"]
                })

            # Process daily forecasts
            forecast_list = []

            for date_key, day_data in sorted(daily_forecasts.items())[:days]:
                # Calculate averages
                day_data["temperature"]["avg"] = sum(day_data["temperature"]["avg"]) / len(day_data["temperature"]["avg"])
                day_data["humidity_avg"] = sum(day_data["humidity"]) / len(day_data["humidity"])

                # Get most frequent weather condition
                weather_count = {}
                for w in day_data["weather"]:
                    main = w["main"]
                    if main not in weather_count:
                        weather_count[main] = {"count": 0, "data": w}
                    weather_count[main]["count"] += 1

                most_frequent = max(weather_count.values(), key=lambda x: x["count"])
                day_data["weather_main"] = most_frequent["data"]

                # Calculate average wind
                wind_speed = sum(w["speed"] for w in day_data["wind"]) / len(day_data["wind"])
                day_data["wind_avg"] = {"speed": wind_speed}

                # Clean up unneeded data
                del day_data["weather"]
                del day_data["wind"]

                forecast_list.append(day_data)

            return {
                "forecast": forecast_list,
                "days": len(forecast_list),
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error formatting forecast data: {str(e)}")
            return {"forecast": self._get_mock_weather(data.get("city", {}).get("name", "Unknown"), "forecast", days)}

    def _get_day_name(self, dt: datetime, language: str) -> str:
        """Get day name in the specified language."""
        if language == "ar":
            # Arabic day names
            ar_days = ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"]
            return ar_days[dt.weekday()]
        else:
            # English day names
            return dt.strftime("%A")

    def _get_mock_weather(self, location: str, weather_type: str, days: int = 5) -> Dict:
        """Generate mock weather data when API is unavailable."""
        if weather_type == "current":
            return {
                "note": "This is simulated weather data",
                "location": {
                    "name": {
                        "en": location,
                        "ar": self._get_arabic_name(location)
                    }
                },
                "timestamp": datetime.utcnow().isoformat(),
                "weather": {
                    "description": "Clear sky",
                    "icon": "01d",
                    "main": "Clear"
                },
                "temperature": {
                    "current": 28.5,
                    "feels_like": 29.8,
                    "min": 25.2,
                    "max": 31.4
                },
                "humidity": 45,
                "wind": {
                    "speed": 3.6,
                    "direction": 120
                },
                "pressure": 1012
            }
        elif weather_type == "forecast":
            forecast_list = []

            for i in range(days):
                day = datetime.now() + timedelta(days=i)
                forecast_list.append({
                    "date": day.strftime("%Y-%m-%d"),
                    "day_name": day.strftime("%A"),
                    "temperature": {
                        "min": 25 + (i % 3) - 2,
                        "max": 32 + (i % 3),
                        "avg": 28 + (i % 3)
                    },
                    "humidity_avg": 45 + (i * 2) % 10,
                    "weather_main": {
                        "main": "Clear" if i % 3 == 0 else "Sunny",
                        "description": "Clear sky" if i % 3 == 0 else "Sunny",
                        "icon": "01d" if i % 3 == 0 else "02d"
                    },
                    "wind_avg": {
                        "speed": 3.5 + (i % 2)
                    },
                    "hours": [
                        {
                            "time": "09:00",
                            "temperature": 26 + (i % 3),
                            "weather": {
                                "main": "Clear",
                                "description": "Clear sky",
                                "icon": "01d"
                            },
                            "humidity": 40 + (i * 2) % 15,
                            "wind_speed": 3.2
                        },
                        {
                            "time": "15:00",
                            "temperature": 30 + (i % 3),
                            "weather": {
                                "main": "Sunny",
                                "description": "Sunny",
                                "icon": "02d"
                            },
                            "humidity": 45 + (i * 2) % 15,
                            "wind_speed": 4.1
                        },
                        {
                            "time": "21:00",
                            "temperature": 27 + (i % 3),
                            "weather": {
                                "main": "Clear",
                                "description": "Clear sky",
                                "icon": "01n"
                            },
                            "humidity": 50 + (i * 2) % 15,
                            "wind_speed": 2.8
                        }
                    ]
                })

            return {
                "note": "This is simulated forecast data",
                "forecast": forecast_list,
                "days": len(forecast_list),
                "generated_at": datetime.utcnow().isoformat()
            }