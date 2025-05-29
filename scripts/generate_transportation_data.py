#!/usr/bin/env python3
"""
Generate transportation data for the Egypt Tourism Chatbot database.

This script:
1. Creates transportation stations for major cities
2. Generates transportation routes between destinations
3. Adds schedules, prices, and other details for transportation options
"""

import os
import sys
import json
import random
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone, time, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set random seed for reproducibility
random.seed(42)

def get_postgres_uri():
    """Get PostgreSQL connection URI from environment or use default"""
    return os.getenv("POSTGRES_URI", "postgresql://postgres:postgres@localhost:5432/egypt_chatbot")

def connect_to_db():
    """Connect to PostgreSQL database"""
    postgres_uri = get_postgres_uri()
    logger.info(f"Connecting to PostgreSQL database")
    conn = psycopg2.connect(postgres_uri)
    conn.autocommit = False
    return conn

def get_existing_data(conn):
    """Get existing data from the database"""
    existing_data = {}

    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        # Get destinations
        cursor.execute("""
            SELECT id, name, type, parent_id, latitude, longitude
            FROM destinations
            WHERE type IN ('country', 'region', 'city')
        """)
        existing_data['destinations'] = cursor.fetchall()

        # Get transportation types
        cursor.execute("SELECT type, name FROM transportation_types")
        existing_data['transportation_types'] = cursor.fetchall()

        # Get existing transportation stations
        cursor.execute("SELECT id FROM transportation_stations")
        existing_data['stations'] = cursor.fetchall()

        # Get existing transportation routes
        cursor.execute("SELECT id, origin_id, destination_id, transportation_type FROM transportation_routes")
        existing_data['routes'] = cursor.fetchall()

    return existing_data

def generate_transportation_stations(conn, existing_data):
    """Generate transportation stations for major cities"""
    logger.info("Generating transportation stations")

    # Extract existing station IDs
    existing_station_ids = [station['id'] for station in existing_data['stations']]

    # Get cities
    cities = [dest for dest in existing_data['destinations'] if dest['type'] == 'city']

    # Station types by transportation type
    station_types = {
        'train': 'train_station',
        'bus': 'bus_station',
        'domestic_flight': 'airport',
        'ferry': 'ferry_terminal',
        'nile_cruise': 'cruise_terminal',
        'taxi': 'taxi_stand',
        'microbus': 'microbus_station',
        'car_rental': 'car_rental_office',
        'private_transfer': 'transfer_office',
        'camel_ride': 'camel_station'
    }

    # Major cities that should have all transportation types
    major_cities = ['cairo', 'alexandria', 'luxor', 'aswan', 'hurghada', 'sharm_el_sheikh']

    # Prepare stations data
    stations_data = []
    for city in cities:
        city_id = city['id']

        # Extract name from JSONB
        city_name_en = ""
        city_name_ar = ""

        if city['name']:
            if isinstance(city['name'], str):
                try:
                    name_json = json.loads(city['name'])
                    if 'en' in name_json:
                        city_name_en = name_json['en']
                    if 'ar' in name_json:
                        city_name_ar = name_json['ar']
                except:
                    pass
            elif isinstance(city['name'], dict):
                if 'en' in city['name']:
                    city_name_en = city['name']['en']
                if 'ar' in city['name']:
                    city_name_ar = city['name']['ar']

        # Determine which transportation types this city should have
        if city_id in major_cities:
            # Major cities have all transportation types
            city_transportation_types = list(station_types.keys())
        else:
            # Other cities have a subset of transportation types
            # All cities have taxis and microbuses
            city_transportation_types = ['taxi', 'microbus']

            # 80% of cities have bus stations
            if random.random() < 0.8:
                city_transportation_types.append('bus')

            # 50% of cities have train stations
            if random.random() < 0.5:
                city_transportation_types.append('train')

            # 20% of cities have airports
            if random.random() < 0.2:
                city_transportation_types.append('domestic_flight')

            # Cities near the Nile have ferry and cruise terminals
            if random.random() < 0.3:
                city_transportation_types.append('ferry')

            if random.random() < 0.2:
                city_transportation_types.append('nile_cruise')

            # 30% of cities have car rental offices
            if random.random() < 0.3:
                city_transportation_types.append('car_rental')

            # 20% of cities have private transfer offices
            if random.random() < 0.2:
                city_transportation_types.append('private_transfer')

            # 10% of cities have camel stations (mostly in desert areas)
            if random.random() < 0.1:
                city_transportation_types.append('camel_ride')

        # Create stations for each transportation type
        for trans_type in city_transportation_types:
            station_type = station_types[trans_type]
            station_id = f"{city_id}_{station_type}"

            # Skip if already exists
            if station_id in existing_station_ids:
                continue

            # Generate station name
            if station_type == 'train_station':
                name_en = f"{city_name_en} Train Station"
                name_ar = f"محطة قطار {city_name_ar if city_name_ar else city_name_en}"
            elif station_type == 'bus_station':
                name_en = f"{city_name_en} Bus Terminal"
                name_ar = f"محطة حافلات {city_name_ar if city_name_ar else city_name_en}"
            elif station_type == 'airport':
                name_en = f"{city_name_en} International Airport"
                name_ar = f"مطار {city_name_ar if city_name_ar else city_name_en} الدولي"
            elif station_type == 'ferry_terminal':
                name_en = f"{city_name_en} Ferry Terminal"
                name_ar = f"محطة عبارات {city_name_ar if city_name_ar else city_name_en}"
            elif station_type == 'cruise_terminal':
                name_en = f"{city_name_en} Cruise Terminal"
                name_ar = f"محطة رحلات نيلية {city_name_ar if city_name_ar else city_name_en}"
            elif station_type == 'taxi_stand':
                name_en = f"{city_name_en} Taxi Stand"
                name_ar = f"موقف سيارات أجرة {city_name_ar if city_name_ar else city_name_en}"
            elif station_type == 'microbus_station':
                name_en = f"{city_name_en} Microbus Station"
                name_ar = f"محطة ميكروباص {city_name_ar if city_name_ar else city_name_en}"
            elif station_type == 'car_rental_office':
                name_en = f"{city_name_en} Car Rental Office"
                name_ar = f"مكتب تأجير سيارات {city_name_ar if city_name_ar else city_name_en}"
            elif station_type == 'transfer_office':
                name_en = f"{city_name_en} Private Transfer Office"
                name_ar = f"مكتب نقل خاص {city_name_ar if city_name_ar else city_name_en}"
            else:  # camel_station
                name_en = f"{city_name_en} Camel Station"
                name_ar = f"محطة جمال {city_name_ar if city_name_ar else city_name_en}"

            # Generate description
            description_en = f"The main {station_type.replace('_', ' ')} in {city_name_en}."
            description_ar = f"محطة {station_type.replace('_', ' ')} الرئيسية في {city_name_ar if city_name_ar else city_name_en}."

            # Generate coordinates (slightly offset from city center)
            latitude = city['latitude'] + random.uniform(-0.01, 0.01) if city['latitude'] else None
            longitude = city['longitude'] + random.uniform(-0.01, 0.01) if city['longitude'] else None

            # Generate facilities based on station type
            facilities = {}
            if station_type == 'train_station':
                facilities = {
                    "waiting_area": True,
                    "restrooms": True,
                    "food_vendors": random.choice([True, False]),
                    "ticket_office": True,
                    "luggage_storage": random.choice([True, False]),
                    "wifi": random.choice([True, False]),
                    "atm": random.choice([True, False])
                }
            elif station_type == 'bus_station':
                facilities = {
                    "waiting_area": True,
                    "restrooms": random.choice([True, False]),
                    "food_vendors": random.choice([True, False]),
                    "ticket_office": True,
                    "luggage_storage": random.choice([True, False]),
                    "wifi": random.choice([True, False])
                }
            elif station_type == 'airport':
                facilities = {
                    "waiting_area": True,
                    "restrooms": True,
                    "food_vendors": True,
                    "ticket_office": True,
                    "luggage_storage": True,
                    "wifi": True,
                    "atm": True,
                    "currency_exchange": True,
                    "duty_free_shops": random.choice([True, False]),
                    "car_rental": random.choice([True, False])
                }
            else:
                facilities = {
                    "waiting_area": random.choice([True, False]),
                    "restrooms": random.choice([True, False]),
                    "food_vendors": random.choice([True, False]),
                    "ticket_office": random.choice([True, False]),
                    "wifi": random.choice([True, False])
                }

            # Create station data
            station_data = {
                'id': station_id,
                'name': json.dumps({'en': name_en, 'ar': name_ar}),
                'description': json.dumps({'en': description_en, 'ar': description_ar}),
                'destination_id': city_id,
                'station_type': station_type,
                'latitude': latitude,
                'longitude': longitude,
                'address': json.dumps({
                    'en': f"Main {station_type.replace('_', ' ')} area, {city_name_en}",
                    'ar': f"منطقة {station_type.replace('_', ' ')} الرئيسية، {city_name_ar if city_name_ar else city_name_en}"
                }),
                'contact_info': json.dumps({
                    'phone': f"+20 {random.randint(10, 99)} {random.randint(1000, 9999)} {random.randint(1000, 9999)}",
                    'email': f"info@{station_id}.com",
                    'website': f"https://www.{station_id}.com"
                }),
                'facilities': json.dumps(facilities),
                'accessibility': json.dumps({
                    'wheelchair_accessible': random.choice([True, False]),
                    'accessible_restrooms': random.choice([True, False]),
                    'accessible_parking': random.choice([True, False])
                }),
                'data': json.dumps({
                    'transportation_type': trans_type,
                    'opening_hours': {
                        'monday': {'open': '06:00', 'close': '22:00'},
                        'tuesday': {'open': '06:00', 'close': '22:00'},
                        'wednesday': {'open': '06:00', 'close': '22:00'},
                        'thursday': {'open': '06:00', 'close': '22:00'},
                        'friday': {'open': '06:00', 'close': '22:00'},
                        'saturday': {'open': '06:00', 'close': '22:00'},
                        'sunday': {'open': '06:00', 'close': '22:00'}
                    }
                })
            }

            stations_data.append(station_data)

    # Insert stations into database
    with conn.cursor() as cursor:
        for station_data in stations_data:
            cursor.execute("""
                INSERT INTO transportation_stations (
                    id, name, description, destination_id, station_type,
                    latitude, longitude, address, contact_info, facilities,
                    accessibility, data, created_at, updated_at, user_id
                ) VALUES (
                    %s, %s::jsonb, %s::jsonb, %s, %s,
                    %s, %s, %s::jsonb, %s::jsonb, %s::jsonb,
                    %s::jsonb, %s::jsonb, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'system'
                )
            """, (
                station_data['id'],
                station_data['name'],
                station_data['description'],
                station_data['destination_id'],
                station_data['station_type'],
                station_data['latitude'],
                station_data['longitude'],
                station_data['address'],
                station_data['contact_info'],
                station_data['facilities'],
                station_data['accessibility'],
                station_data['data']
            ))

    conn.commit()
    logger.info(f"Generated {len(stations_data)} transportation stations")
    return stations_data

def generate_transportation_routes(conn, existing_data):
    """Generate transportation routes between destinations"""
    logger.info("Generating transportation routes")

    # Extract existing route IDs
    existing_routes = existing_data['routes']
    existing_route_keys = [(route['origin_id'], route['destination_id'], route['transportation_type'])
                          for route in existing_routes]

    # Get cities
    cities = [dest for dest in existing_data['destinations'] if dest['type'] == 'city']

    # Get transportation types
    transportation_types = existing_data['transportation_types']

    # Define route generation parameters
    route_params = {
        'train': {
            'probability': 0.4,  # Probability of creating a train route between two cities
            'min_distance': 20,  # Minimum distance in km
            'max_distance': 1000,  # Maximum distance in km
            'speed_km_h': 60,  # Average speed in km/h
            'min_price': 50,  # Minimum price in EGP
            'max_price': 500,  # Maximum price in EGP
            'price_per_km': 0.5,  # Price per km in EGP
            'frequency': {
                'min_daily': 1,  # Minimum daily frequency
                'max_daily': 12  # Maximum daily frequency
            }
        },
        'bus': {
            'probability': 0.6,
            'min_distance': 10,
            'max_distance': 800,
            'speed_km_h': 50,
            'min_price': 30,
            'max_price': 300,
            'price_per_km': 0.3,
            'frequency': {
                'min_daily': 2,
                'max_daily': 24
            }
        },
        'domestic_flight': {
            'probability': 0.2,
            'min_distance': 200,
            'max_distance': 1500,
            'speed_km_h': 500,
            'min_price': 500,
            'max_price': 2000,
            'price_per_km': 1.5,
            'frequency': {
                'min_daily': 1,
                'max_daily': 8
            }
        },
        'ferry': {
            'probability': 0.1,
            'min_distance': 5,
            'max_distance': 100,
            'speed_km_h': 20,
            'min_price': 20,
            'max_price': 150,
            'price_per_km': 0.2,
            'frequency': {
                'min_daily': 2,
                'max_daily': 12
            }
        },
        'nile_cruise': {
            'probability': 0.05,
            'min_distance': 50,
            'max_distance': 500,
            'speed_km_h': 15,
            'min_price': 1000,
            'max_price': 5000,
            'price_per_km': 10,
            'frequency': {
                'min_daily': 1,
                'max_daily': 2
            }
        },
        'taxi': {
            'probability': 0.8,
            'min_distance': 1,
            'max_distance': 200,
            'speed_km_h': 60,
            'min_price': 50,
            'max_price': 1000,
            'price_per_km': 5,
            'frequency': {
                'min_daily': 24,
                'max_daily': 24  # Taxis run 24/7
            }
        },
        'microbus': {
            'probability': 0.7,
            'min_distance': 1,
            'max_distance': 150,
            'speed_km_h': 40,
            'min_price': 10,
            'max_price': 100,
            'price_per_km': 0.2,
            'frequency': {
                'min_daily': 12,
                'max_daily': 24
            }
        },
        'car_rental': {
            'probability': 0.3,
            'min_distance': 1,
            'max_distance': 1000,
            'speed_km_h': 70,
            'min_price': 300,
            'max_price': 1500,
            'price_per_km': 0,  # Fixed price per day
            'frequency': {
                'min_daily': 24,
                'max_daily': 24  # Available 24/7
            }
        },
        'private_transfer': {
            'probability': 0.4,
            'min_distance': 5,
            'max_distance': 500,
            'speed_km_h': 70,
            'min_price': 200,
            'max_price': 2000,
            'price_per_km': 3,
            'frequency': {
                'min_daily': 24,
                'max_daily': 24  # Available 24/7
            }
        },
        'camel_ride': {
            'probability': 0.05,
            'min_distance': 1,
            'max_distance': 20,
            'speed_km_h': 5,
            'min_price': 100,
            'max_price': 500,
            'price_per_km': 50,
            'frequency': {
                'min_daily': 8,
                'max_daily': 12  # Typically daytime only
            }
        }
    }

    # Prepare routes data
    routes_data = []

    # Generate routes between cities
    for origin in cities:
        for destination in cities:
            # Skip self-routes
            if origin['id'] == destination['id']:
                continue

            # Calculate distance between cities (if coordinates available)
            distance_km = None
            if (origin['latitude'] and origin['longitude'] and
                destination['latitude'] and destination['longitude']):
                # Simple Euclidean distance (not accurate for long distances but good enough for simulation)
                lat_diff = destination['latitude'] - origin['latitude']
                lon_diff = destination['longitude'] - origin['longitude']
                # Rough conversion to km (1 degree ≈ 111 km)
                distance_km = ((lat_diff ** 2 + lon_diff ** 2) ** 0.5) * 111
            else:
                # If coordinates not available, generate a random distance
                distance_km = random.uniform(50, 500)

            # Generate routes for each transportation type
            for trans_type in [t['type'] for t in transportation_types]:
                # Skip if this route already exists
                if (origin['id'], destination['id'], trans_type) in existing_route_keys:
                    continue

                # Get parameters for this transportation type
                params = route_params.get(trans_type, {})

                # Skip if distance is outside the range for this transportation type
                if (distance_km < params.get('min_distance', 0) or
                    distance_km > params.get('max_distance', float('inf'))):
                    continue

                # Determine if we should create this route based on probability
                if random.random() > params.get('probability', 0):
                    continue

                # Calculate duration in minutes
                speed_km_h = params.get('speed_km_h', 60)
                duration_minutes = int((distance_km / speed_km_h) * 60)

                # Calculate price range
                base_price = params.get('min_price', 50)
                price_per_km = params.get('price_per_km', 0.5)

                if trans_type == 'car_rental':
                    # Car rental is priced per day, not per km
                    economy_price = random.uniform(300, 600)
                    midrange_price = random.uniform(600, 1200)
                    luxury_price = random.uniform(1200, 2500)
                else:
                    # Other transportation is priced by distance
                    economy_price = base_price + (distance_km * price_per_km)
                    midrange_price = economy_price * 1.5
                    luxury_price = economy_price * 3

                # Generate frequency
                min_daily = params.get('frequency', {}).get('min_daily', 1)
                max_daily = params.get('frequency', {}).get('max_daily', 12)
                daily_frequency = random.randint(min_daily, max_daily)

                # Generate schedule
                schedule = {}
                if trans_type in ['taxi', 'car_rental', 'private_transfer']:
                    # These are available on demand
                    schedule = {
                        "type": "on_demand",
                        "availability": "24/7",
                        "booking_required": trans_type != 'taxi'
                    }
                else:
                    # Generate departure times
                    departures = []
                    for _ in range(daily_frequency):
                        hour = random.randint(6, 22)
                        minute = random.choice([0, 15, 30, 45])
                        departures.append(f"{hour:02d}:{minute:02d}")

                    departures.sort()
                    schedule = {
                        "type": "scheduled",
                        "departures": departures,
                        "days": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
                    }

                # Extract names
                origin_name_en = origin['id']
                destination_name_en = destination['id']

                if origin['name']:
                    if isinstance(origin['name'], str):
                        try:
                            name_json = json.loads(origin['name'])
                            if 'en' in name_json:
                                origin_name_en = name_json['en']
                        except:
                            pass
                    elif isinstance(origin['name'], dict) and 'en' in origin['name']:
                        origin_name_en = origin['name']['en']

                if destination['name']:
                    if isinstance(destination['name'], str):
                        try:
                            name_json = json.loads(destination['name'])
                            if 'en' in name_json:
                                destination_name_en = name_json['en']
                        except:
                            pass
                    elif isinstance(destination['name'], dict) and 'en' in destination['name']:
                        destination_name_en = destination['name']['en']

                # Generate route name
                if trans_type == 'train':
                    name_en = f"Train: {origin_name_en} to {destination_name_en}"
                    name_ar = f"قطار: {origin_name_en} إلى {destination_name_en}"
                elif trans_type == 'bus':
                    name_en = f"Bus: {origin_name_en} to {destination_name_en}"
                    name_ar = f"حافلة: {origin_name_en} إلى {destination_name_en}"
                elif trans_type == 'domestic_flight':
                    name_en = f"Flight: {origin_name_en} to {destination_name_en}"
                    name_ar = f"رحلة طيران: {origin_name_en} إلى {destination_name_en}"
                elif trans_type == 'ferry':
                    name_en = f"Ferry: {origin_name_en} to {destination_name_en}"
                    name_ar = f"عبّارة: {origin_name_en} إلى {destination_name_en}"
                elif trans_type == 'nile_cruise':
                    name_en = f"Nile Cruise: {origin_name_en} to {destination_name_en}"
                    name_ar = f"رحلة نيلية: {origin_name_en} إلى {destination_name_en}"
                elif trans_type == 'taxi':
                    name_en = f"Taxi: {origin_name_en} to {destination_name_en}"
                    name_ar = f"سيارة أجرة: {origin_name_en} إلى {destination_name_en}"
                elif trans_type == 'microbus':
                    name_en = f"Microbus: {origin_name_en} to {destination_name_en}"
                    name_ar = f"ميكروباص: {origin_name_en} إلى {destination_name_en}"
                elif trans_type == 'car_rental':
                    name_en = f"Car Rental: {origin_name_en} to {destination_name_en}"
                    name_ar = f"تأجير سيارات: {origin_name_en} إلى {destination_name_en}"
                elif trans_type == 'private_transfer':
                    name_en = f"Private Transfer: {origin_name_en} to {destination_name_en}"
                    name_ar = f"نقل خاص: {origin_name_en} إلى {destination_name_en}"
                else:  # camel_ride
                    name_en = f"Camel Ride: {origin_name_en} to {destination_name_en}"
                    name_ar = f"ركوب الجمل: {origin_name_en} إلى {destination_name_en}"

                # Generate description
                description_en = f"Travel from {origin_name_en} to {destination_name_en} by {trans_type.replace('_', ' ')}. "
                description_en += f"The journey takes approximately {duration_minutes // 60} hours and {duration_minutes % 60} minutes."

                description_ar = f"السفر من {origin_name_en} إلى {destination_name_en} بواسطة {trans_type.replace('_', ' ')}. "
                description_ar += f"تستغرق الرحلة حوالي {duration_minutes // 60} ساعة و {duration_minutes % 60} دقيقة."

                # Create route data
                route_data = {
                    'origin_id': origin['id'],
                    'destination_id': destination['id'],
                    'transportation_type': trans_type,
                    'name': json.dumps({'en': name_en, 'ar': name_ar}),
                    'description': json.dumps({'en': description_en, 'ar': description_ar}),
                    'distance_km': distance_km,
                    'duration_minutes': duration_minutes,
                    'frequency': json.dumps({
                        'daily_frequency': daily_frequency,
                        'peak_hours': ['07:00-09:00', '16:00-19:00'],
                        'off_peak_hours': ['10:00-15:00', '20:00-22:00']
                    }),
                    'schedule': json.dumps(schedule),
                    'price_range': json.dumps({
                        'currency': 'EGP',
                        'economy': round(economy_price, 0),
                        'business': round(midrange_price, 0),
                        'first_class': round(luxury_price, 0)
                    }),
                    'booking_info': json.dumps({
                        'booking_required': trans_type not in ['taxi', 'microbus'],
                        'advance_booking_recommended': trans_type in ['train', 'domestic_flight', 'nile_cruise'],
                        'booking_channels': ['online', 'phone', 'in-person'],
                        'cancellation_policy': 'Varies by provider'
                    }),
                    'amenities': json.dumps({
                        'wifi': trans_type in ['train', 'domestic_flight', 'nile_cruise'],
                        'food_service': trans_type in ['train', 'domestic_flight', 'nile_cruise'],
                        'air_conditioning': trans_type in ['train', 'domestic_flight', 'nile_cruise', 'bus', 'taxi', 'private_transfer', 'car_rental'],
                        'restroom': trans_type in ['train', 'domestic_flight', 'nile_cruise', 'bus'],
                        'entertainment': trans_type in ['domestic_flight', 'nile_cruise']
                    }),
                    'tips': json.dumps({
                        'en': [
                            "Book in advance during peak tourist season.",
                            f"Allow extra time for {trans_type.replace('_', ' ')} travel in Egypt.",
                            "Confirm your booking 24 hours before departure.",
                            "Keep your ticket or booking confirmation handy."
                        ],
                        'ar': [
                            "احجز مسبقًا خلال موسم الذروة السياحية.",
                            f"اسمح بوقت إضافي للسفر بـ {trans_type.replace('_', ' ')} في مصر.",
                            "قم بتأكيد حجزك قبل 24 ساعة من المغادرة.",
                            "احتفظ بتذكرتك أو تأكيد الحجز في متناول اليد."
                        ]
                    }),
                    'data': json.dumps({
                        'route_type': 'direct',
                        'route_number': f"{origin['id'][0:3]}-{destination['id'][0:3]}-{trans_type[0:3]}",
                        'operator': f"Egypt {trans_type.replace('_', ' ').title()} Services",
                        'reliability_score': round(random.uniform(3.0, 5.0), 1),
                        'popular_times': {
                            'morning': random.randint(1, 5),
                            'afternoon': random.randint(1, 5),
                            'evening': random.randint(1, 5),
                            'night': random.randint(1, 5)
                        }
                    })
                }

                routes_data.append(route_data)

    # Insert routes into database
    with conn.cursor() as cursor:
        for route_data in routes_data:
            cursor.execute("""
                INSERT INTO transportation_routes (
                    origin_id, destination_id, transportation_type,
                    name, description, distance_km, duration_minutes,
                    frequency, schedule, price_range, booking_info,
                    amenities, tips, data, created_at, updated_at, user_id
                ) VALUES (
                    %s, %s, %s,
                    %s::jsonb, %s::jsonb, %s, %s,
                    %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb,
                    %s::jsonb, %s::jsonb, %s::jsonb, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'system'
                )
            """, (
                route_data['origin_id'],
                route_data['destination_id'],
                route_data['transportation_type'],
                route_data['name'],
                route_data['description'],
                route_data['distance_km'],
                route_data['duration_minutes'],
                route_data['frequency'],
                route_data['schedule'],
                route_data['price_range'],
                route_data['booking_info'],
                route_data['amenities'],
                route_data['tips'],
                route_data['data']
            ))

    conn.commit()
    logger.info(f"Generated {len(routes_data)} transportation routes")
    return routes_data

def verify_transportation_data(conn):
    """Verify the transportation data in the database"""
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        # Check transportation stations count
        cursor.execute("SELECT COUNT(*) as count FROM transportation_stations")
        station_count = cursor.fetchone()['count']
        logger.info(f"Total transportation stations in database: {station_count}")

        # Check transportation routes count
        cursor.execute("SELECT COUNT(*) as count FROM transportation_routes")
        route_count = cursor.fetchone()['count']
        logger.info(f"Total transportation routes in database: {route_count}")

        # Check transportation types
        cursor.execute("""
            SELECT transportation_type, COUNT(*) as count
            FROM transportation_routes
            GROUP BY transportation_type
            ORDER BY count DESC
        """)
        type_counts = cursor.fetchall()
        logger.info("Transportation routes by type:")
        for type_count in type_counts:
            logger.info(f"  - {type_count['transportation_type']}: {type_count['count']} routes")

        # Check if we have enough data
        if station_count > 0 and route_count > 0:
            logger.info("✅ Transportation data generation successful")
            return True
        else:
            logger.warning("⚠️ Transportation data generation failed")
            return False

def main():
    """Main function to generate transportation data"""
    try:
        # Connect to database
        conn = connect_to_db()

        # Get existing data
        existing_data = get_existing_data(conn)

        # Generate transportation stations
        generate_transportation_stations(conn, existing_data)

        # Update existing data to include new stations
        existing_data = get_existing_data(conn)

        # Generate transportation routes
        generate_transportation_routes(conn, existing_data)

        # Verify transportation data
        verify_transportation_data(conn)

        logger.info("Transportation data generation completed successfully")
        return True

    except Exception as e:
        logger.error(f"Error generating transportation data: {str(e)}", exc_info=True)
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = main()
    if success:
        sys.exit(0)
    else:
        sys.exit(1)
