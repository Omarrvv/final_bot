"""
Cross-table query capabilities for the Egypt Tourism Chatbot.
This module provides functions to query multiple tables and join the results.
"""

import logging
import json
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class CrossTableQueryManager:
    """
    Manages cross-table queries for the Egypt Tourism Chatbot.
    """

    def __init__(self, db_manager):
        """
        Initialize the CrossTableQueryManager.

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager

    def find_restaurants_near_attraction(self, attraction_id: int = None, attraction_name: str = None,
                                        city: str = None, limit: int = 5) -> List[Dict]:
        """
        Find restaurants near a specific attraction.

        Args:
            attraction_id: ID of the attraction
            attraction_name: Name of the attraction (used if ID is not provided)
            city: City name (used if attraction details are not provided)
            limit: Maximum number of results to return

        Returns:
            List of restaurant dictionaries
        """
        logger.info(f"Finding restaurants near attraction: ID={attraction_id}, name={attraction_name}, city={city}")

        try:
            # Get attraction details if ID or name is provided
            attraction = None
            if attraction_id:
                # Get attraction by ID
                attraction = self._get_attraction_by_id(attraction_id)
            elif attraction_name:
                # Search for attraction by name
                # Try multiple search approaches for finding the attraction
                attractions = None

                # First try: Direct name match
                try:
                    attractions = self.db_manager.search_attractions(
                        query={"text": attraction_name},
                        limit=1
                    )
                except Exception as e:
                    logger.warning(f"Error searching attraction by text: {str(e)}")

                # Second try: Use enhanced search if available
                if not attractions or len(attractions) == 0:
                    try:
                        if hasattr(self.db_manager, 'enhanced_search'):
                            logger.info(f"Using enhanced search for attraction: {attraction_name}")
                            attractions = self.db_manager.enhanced_search(
                                table="attractions",
                                search_text=attraction_name,
                                limit=1
                            )
                    except Exception as e:
                        logger.warning(f"Error using enhanced search for attraction: {str(e)}")

                # Third try: Direct SQL query as fallback
                if not attractions or len(attractions) == 0:
                    try:
                        logger.info(f"Using direct SQL query for attraction: {attraction_name}")
                        attractions = self.db_manager.execute_postgres_query(
                            "SELECT * FROM attractions WHERE name->>'en' ILIKE %s OR name->>'ar' ILIKE %s LIMIT 1",
                            (f"%{attraction_name}%", f"%{attraction_name}%")
                        )
                    except Exception as e:
                        logger.warning(f"Error using direct SQL query for attraction: {str(e)}")
                if attractions and len(attractions) > 0:
                    attraction = attractions[0]

            # Extract location information
            location = None
            city_name = None
            coordinates = None

            if attraction:
                # Get location from attraction
                if 'city' in attraction:
                    city_name = attraction['city']
                    location = city_name
                elif 'location' in attraction and isinstance(attraction['location'], dict):
                    if 'city' in attraction['location']:
                        city_name = attraction['location'].get('city')
                        location = city_name
                    # Get coordinates if available
                    if 'latitude' in attraction['location'] and 'longitude' in attraction['location']:
                        coordinates = {
                            'latitude': attraction['location'].get('latitude'),
                            'longitude': attraction['location'].get('longitude')
                        }
                    elif 'lat' in attraction['location'] and 'lng' in attraction['location']:
                        coordinates = {
                            'latitude': attraction['location'].get('lat'),
                            'longitude': attraction['location'].get('lng')
                        }
                elif 'location_description' in attraction and isinstance(attraction['location_description'], dict):
                    location = attraction['location_description'].get('en')
                    # Try to extract city name from location description
                    if location and isinstance(location, str) and ',' in location:
                        city_name = location.split(',')[0].strip()

                # Try to get coordinates directly
                if not coordinates and 'latitude' in attraction and 'longitude' in attraction:
                    coordinates = {
                        'latitude': attraction.get('latitude'),
                        'longitude': attraction.get('longitude')
                    }
                elif not coordinates and 'coordinates' in attraction and isinstance(attraction['coordinates'], dict):
                    coordinates = attraction['coordinates']

            # Use provided city if no location found
            if not location and city:
                location = city
                city_name = city

            if not location:
                logger.warning("Could not determine location for restaurant search")
                return []

            # Try multiple search approaches
            logger.info(f"Searching for restaurants in location: {location}")
            restaurants = []

            # First try: Search by city name if available
            if city_name:
                logger.info(f"Searching restaurants by city name: {city_name}")
                try:
                    # Try multiple approaches for city search
                    city_results = None

                    # First approach: Direct city match
                    try:
                        city_results = self.db_manager.search_restaurants(
                            query={"city": city_name},
                            limit=limit
                        )
                    except Exception as e:
                        logger.warning(f"Error searching restaurants by city (direct): {str(e)}")

                    # Second approach: Try with city_id if no results
                    if not city_results or len(city_results) == 0:
                        try:
                            # Find city ID first
                            cities = self.db_manager.execute_postgres_query(
                                "SELECT id FROM cities WHERE name->>'en' ILIKE %s OR name->>'ar' ILIKE %s LIMIT 1",
                                (f"%{city_name}%", f"%{city_name}%")
                            )
                            if cities and len(cities) > 0:
                                city_id = cities[0].get('id')
                                logger.info(f"Found city ID {city_id} for {city_name}")
                                city_results = self.db_manager.search_restaurants(
                                    query={"city_id": city_id},
                                    limit=limit
                                )
                        except Exception as e:
                            logger.warning(f"Error searching restaurants by city_id: {str(e)}")

                    # Third approach: Direct SQL query as fallback
                    if not city_results or len(city_results) == 0:
                        try:
                            logger.info(f"Using direct SQL query for restaurants in {city_name}")
                            city_results = self.db_manager.execute_postgres_query(
                                "SELECT * FROM restaurants WHERE city_id IN (SELECT id FROM cities WHERE name->>'en' ILIKE %s OR name->>'ar' ILIKE %s) LIMIT %s",
                                (f"%{city_name}%", f"%{city_name}%", limit)
                            )
                        except Exception as e:
                            logger.warning(f"Error using direct SQL query for restaurants: {str(e)}")

                    if city_results:
                        logger.info(f"Found {len(city_results)} restaurants by city match")
                        restaurants.extend(city_results)
                except Exception as e:
                    logger.warning(f"Error searching restaurants by city: {str(e)}")

            # Second try: Search by location text
            if len(restaurants) < limit:
                remaining = limit - len(restaurants)
                logger.info(f"Searching restaurants by location text: {location}")
                try:
                    text_results = self.db_manager.search_restaurants(
                        query={"text": location},
                        limit=remaining
                    )
                    if text_results:
                        logger.info(f"Found {len(text_results)} restaurants by text match")
                        # Add only restaurants that aren't already in the results
                        existing_ids = {r.get('id') for r in restaurants}
                        for r in text_results:
                            if r.get('id') not in existing_ids:
                                restaurants.append(r)
                                existing_ids.add(r.get('id'))
                except Exception as e:
                    logger.warning(f"Error searching restaurants by text: {str(e)}")

            # Third try: Search by coordinates if available
            if coordinates and len(restaurants) < limit:
                remaining = limit - len(restaurants)
                logger.info(f"Searching restaurants by coordinates: {coordinates}")
                try:
                    # Try to use spatial search if available
                    if hasattr(self.db_manager, 'find_restaurants_near_coordinates'):
                        coord_results = self.db_manager.find_restaurants_near_coordinates(
                            latitude=coordinates.get('latitude', coordinates.get('lat')),
                            longitude=coordinates.get('longitude', coordinates.get('lng')),
                            radius_km=5,
                            limit=remaining
                        )
                        if coord_results:
                            logger.info(f"Found {len(coord_results)} restaurants by coordinate match")
                            # Add only restaurants that aren't already in the results
                            existing_ids = {r.get('id') for r in restaurants}
                            for r in coord_results:
                                if r.get('id') not in existing_ids:
                                    restaurants.append(r)
                                    existing_ids.add(r.get('id'))
                except Exception as e:
                    logger.warning(f"Error searching restaurants by coordinates: {str(e)}")

            # Add distance information if attraction has coordinates
            if attraction and 'coordinates' in attraction:
                attraction_coords = attraction['coordinates']
                for restaurant in restaurants:
                    if 'coordinates' in restaurant:
                        restaurant['distance_km'] = self._calculate_distance(
                            attraction_coords, restaurant['coordinates']
                        )

                # Sort by distance
                restaurants.sort(key=lambda x: x.get('distance_km', float('inf')))

            return restaurants[:limit]

        except Exception as e:
            logger.error(f"Error finding restaurants near attraction: {str(e)}")
            return []

    def find_hotels_near_attraction(self, attraction_id: int = None, attraction_name: str = None,
                                   city: str = None, limit: int = 5) -> List[Dict]:
        """
        Find hotels near a specific attraction.

        Args:
            attraction_id: ID of the attraction
            attraction_name: Name of the attraction (used if ID is not provided)
            city: City name (used if attraction details are not provided)
            limit: Maximum number of results to return

        Returns:
            List of hotel dictionaries
        """
        logger.info(f"Finding hotels near attraction: ID={attraction_id}, name={attraction_name}, city={city}")

        try:
            # Get attraction details if ID or name is provided
            attraction = None
            if attraction_id:
                # Get attraction by ID
                attraction = self._get_attraction_by_id(attraction_id)
            elif attraction_name:
                # Search for attraction by name
                # Try multiple search approaches for finding the attraction
                attractions = None

                # First try: Direct name match
                try:
                    attractions = self.db_manager.search_attractions(
                        query={"text": attraction_name},
                        limit=1
                    )
                except Exception as e:
                    logger.warning(f"Error searching attraction by text: {str(e)}")

                # Second try: Use enhanced search if available
                if not attractions or len(attractions) == 0:
                    try:
                        if hasattr(self.db_manager, 'enhanced_search'):
                            logger.info(f"Using enhanced search for attraction: {attraction_name}")
                            attractions = self.db_manager.enhanced_search(
                                table="attractions",
                                search_text=attraction_name,
                                limit=1
                            )
                    except Exception as e:
                        logger.warning(f"Error using enhanced search for attraction: {str(e)}")

                # Third try: Direct SQL query as fallback
                if not attractions or len(attractions) == 0:
                    try:
                        logger.info(f"Using direct SQL query for attraction: {attraction_name}")
                        attractions = self.db_manager.execute_postgres_query(
                            "SELECT * FROM attractions WHERE name->>'en' ILIKE %s OR name->>'ar' ILIKE %s LIMIT 1",
                            (f"%{attraction_name}%", f"%{attraction_name}%")
                        )
                    except Exception as e:
                        logger.warning(f"Error using direct SQL query for attraction: {str(e)}")
                if attractions and len(attractions) > 0:
                    attraction = attractions[0]

            # Extract location information
            location = None
            city_name = None
            coordinates = None

            if attraction:
                # Get location from attraction
                if 'city' in attraction:
                    city_name = attraction['city']
                    location = city_name
                elif 'location' in attraction and isinstance(attraction['location'], dict):
                    if 'city' in attraction['location']:
                        city_name = attraction['location'].get('city')
                        location = city_name
                    # Get coordinates if available
                    if 'latitude' in attraction['location'] and 'longitude' in attraction['location']:
                        coordinates = {
                            'latitude': attraction['location'].get('latitude'),
                            'longitude': attraction['location'].get('longitude')
                        }
                    elif 'lat' in attraction['location'] and 'lng' in attraction['location']:
                        coordinates = {
                            'latitude': attraction['location'].get('lat'),
                            'longitude': attraction['location'].get('lng')
                        }
                elif 'location_description' in attraction and isinstance(attraction['location_description'], dict):
                    location = attraction['location_description'].get('en')
                    # Try to extract city name from location description
                    if location and isinstance(location, str) and ',' in location:
                        city_name = location.split(',')[0].strip()

                # Try to get coordinates directly
                if not coordinates and 'latitude' in attraction and 'longitude' in attraction:
                    coordinates = {
                        'latitude': attraction.get('latitude'),
                        'longitude': attraction.get('longitude')
                    }
                elif not coordinates and 'coordinates' in attraction and isinstance(attraction['coordinates'], dict):
                    coordinates = attraction['coordinates']

            # Use provided city if no location found
            if not location and city:
                location = city
                city_name = city

            if not location:
                logger.warning("Could not determine location for hotel search")
                return []

            # Try multiple search approaches
            logger.info(f"Searching for hotels in location: {location}")
            hotels = []

            # First try: Search by city name if available
            if city_name:
                logger.info(f"Searching hotels by city name: {city_name}")
                try:
                    city_results = self.db_manager.search_hotels(
                        query={"city": city_name},
                        limit=limit
                    )
                    if city_results:
                        logger.info(f"Found {len(city_results)} hotels by city match")
                        hotels.extend(city_results)
                except Exception as e:
                    logger.warning(f"Error searching hotels by city: {str(e)}")

            # Second try: Search by location text
            if len(hotels) < limit:
                remaining = limit - len(hotels)
                logger.info(f"Searching hotels by location text: {location}")
                try:
                    text_results = self.db_manager.search_hotels(
                        query={"text": location},
                        limit=remaining
                    )
                    if text_results:
                        logger.info(f"Found {len(text_results)} hotels by text match")
                        # Add only hotels that aren't already in the results
                        existing_ids = {h.get('id') for h in hotels}
                        for h in text_results:
                            if h.get('id') not in existing_ids:
                                hotels.append(h)
                                existing_ids.add(h.get('id'))
                except Exception as e:
                    logger.warning(f"Error searching hotels by text: {str(e)}")

            # Third try: Search by coordinates if available
            if coordinates and len(hotels) < limit:
                remaining = limit - len(hotels)
                logger.info(f"Searching hotels by coordinates: {coordinates}")
                try:
                    # Try to use spatial search if available
                    if hasattr(self.db_manager, 'find_hotels_near_coordinates'):
                        coord_results = self.db_manager.find_hotels_near_coordinates(
                            latitude=coordinates.get('latitude', coordinates.get('lat')),
                            longitude=coordinates.get('longitude', coordinates.get('lng')),
                            radius_km=5,
                            limit=remaining
                        )
                        if coord_results:
                            logger.info(f"Found {len(coord_results)} hotels by coordinate match")
                            # Add only hotels that aren't already in the results
                            existing_ids = {h.get('id') for h in hotels}
                            for h in coord_results:
                                if h.get('id') not in existing_ids:
                                    hotels.append(h)
                                    existing_ids.add(h.get('id'))
                except Exception as e:
                    logger.warning(f"Error searching hotels by coordinates: {str(e)}")

            # Add distance information if attraction has coordinates
            if attraction and 'coordinates' in attraction:
                attraction_coords = attraction['coordinates']
                for hotel in hotels:
                    if 'coordinates' in hotel:
                        hotel['distance_km'] = self._calculate_distance(
                            attraction_coords, hotel['coordinates']
                        )

                # Sort by distance
                hotels.sort(key=lambda x: x.get('distance_km', float('inf')))

            return hotels[:limit]

        except Exception as e:
            logger.error(f"Error finding hotels near attraction: {str(e)}")
            return []

    def find_attractions_in_itinerary_cities(self, itinerary_id: int = None,
                                           itinerary_name: str = None, limit: int = 10) -> Dict[str, List[Dict]]:
        """
        Find attractions in cities mentioned in an itinerary.

        Args:
            itinerary_id: ID of the itinerary
            itinerary_name: Name of the itinerary (used if ID is not provided)
            limit: Maximum number of attractions per city

        Returns:
            Dictionary mapping city names to lists of attractions
        """
        logger.info(f"Finding attractions in itinerary cities: ID={itinerary_id}, name={itinerary_name}")

        try:
            # Get itinerary details
            itinerary = None
            if itinerary_id:
                # Get itinerary by ID
                itinerary = self._get_itinerary_by_id(itinerary_id)
            elif itinerary_name:
                # Search for itinerary by name
                itineraries = self.db_manager.execute_query(
                    "SELECT * FROM itineraries WHERE name->>'en' ILIKE %s LIMIT 1",
                    (f"%{itinerary_name}%",)
                )
                if itineraries and len(itineraries) > 0:
                    itinerary = itineraries[0]

            if not itinerary:
                logger.warning(f"Itinerary not found: ID={itinerary_id}, name={itinerary_name}")
                return {}

            # Extract cities from itinerary using junction table
            cities = []
            try:
                # Query the itinerary_cities junction table
                city_results = self.db_manager.execute_query(
                    """
                    SELECT c.id, c.name
                    FROM itinerary_cities ic
                    JOIN cities c ON ic.city_id = c.id
                    WHERE ic.itinerary_id = %s
                    ORDER BY ic.order_index
                    """,
                    (itinerary['id'],)
                )

                if city_results and len(city_results) > 0:
                    for city_result in city_results:
                        if 'name' in city_result and isinstance(city_result['name'], dict):
                            city_name = city_result['name'].get('en', '')
                            if city_name:
                                cities.append(city_name)
                        elif 'id' in city_result:
                            cities.append(city_result['id'])
            except Exception as e:
                logger.warning(f"Error querying itinerary_cities junction table: {str(e)}")

                # No fallback to legacy array column as it's been removed
                # Try to get cities from the itinerary name or description
                if not cities and 'name' in itinerary and isinstance(itinerary['name'], dict):
                    itinerary_name = itinerary['name'].get('en', '')
                    # Try to extract city names from the itinerary name
                    if itinerary_name:
                        logger.info(f"Trying to extract city names from itinerary name: {itinerary_name}")
                        # This is a simple approach - in a real system, you'd use NLP to extract city names
                        for city_candidate in itinerary_name.split():
                            if len(city_candidate) > 3:  # Avoid short words
                                cities.append(city_candidate)

            if not cities:
                logger.warning("No cities found in itinerary")
                return {}

            # Find attractions in each city
            result = {}
            for city in cities:
                logger.info(f"Searching for attractions in city: {city}")
                city_attractions = []

                # First try: Use the city_id to query attractions
                try:
                    # Find city ID first
                    cities = self.db_manager.execute_postgres_query(
                        "SELECT id FROM cities WHERE name->>'en' ILIKE %s OR name->>'ar' ILIKE %s LIMIT 1",
                        (f"%{city}%", f"%{city}%")
                    )
                    if cities and len(cities) > 0:
                        city_id = cities[0].get('id')
                        logger.info(f"Found city ID {city_id} for {city}")

                        # Query attractions by city_id
                        city_id_results = self.db_manager.search_attractions(
                            query={"city_id": city_id},
                            limit=limit
                        )
                        if city_id_results:
                            logger.info(f"Found {len(city_id_results)} attractions by city_id")
                            city_attractions.extend(city_id_results)
                except Exception as e:
                    logger.warning(f"Error searching attractions by city_id: {str(e)}")

                # Second try: Fallback to legacy city field
                if len(city_attractions) < limit:
                    remaining = limit - len(city_attractions)
                    try:
                        logger.info(f"Searching attractions by city field: {city}")
                        city_results = self.db_manager.search_attractions(
                            query={"city": city},
                            limit=remaining
                        )
                        if city_results:
                            logger.info(f"Found {len(city_results)} attractions by city field")
                            # Add only attractions that aren't already in the results
                            existing_ids = {a.get('id') for a in city_attractions}
                            for a in city_results:
                                if a.get('id') not in existing_ids:
                                    city_attractions.append(a)
                                    existing_ids.add(a.get('id'))
                    except Exception as e:
                        logger.warning(f"Error searching attractions by city field: {str(e)}")

                # Third try: Search by text
                if len(city_attractions) < limit:
                    remaining = limit - len(city_attractions)
                    try:
                        logger.info(f"Searching attractions by text: {city}")
                        text_results = self.db_manager.search_attractions(
                            query={"text": city},
                            limit=remaining
                        )
                        if text_results:
                            logger.info(f"Found {len(text_results)} attractions by text")
                            # Add only attractions that aren't already in the results
                            existing_ids = {a.get('id') for a in city_attractions}
                            for a in text_results:
                                if a.get('id') not in existing_ids:
                                    city_attractions.append(a)
                                    existing_ids.add(a.get('id'))
                    except Exception as e:
                        logger.warning(f"Error searching attractions by text: {str(e)}")

                # Add attractions to result if we found any
                if city_attractions:
                    result[city] = city_attractions

            return result

        except Exception as e:
            logger.error(f"Error finding attractions in itinerary cities: {str(e)}")
            return {}

    def find_events_near_attraction(self, attraction_id: int = None, attraction_name: str = None,
                                  city: str = None, limit: int = 5) -> List[Dict]:
        """
        Find events near a specific attraction.

        Args:
            attraction_id: ID of the attraction
            attraction_name: Name of the attraction (used if ID is not provided)
            city: City name (used if attraction details are not provided)
            limit: Maximum number of results to return

        Returns:
            List of event dictionaries
        """
        logger.info(f"Finding events near attraction: ID={attraction_id}, name={attraction_name}, city={city}")

        try:
            # Get attraction details if ID or name is provided
            attraction = None
            if attraction_id:
                # Get attraction by ID
                attraction = self._get_attraction_by_id(attraction_id)
            elif attraction_name:
                # Search for attraction by name
                # Try multiple search approaches for finding the attraction
                attractions = None

                # First try: Direct name match
                try:
                    attractions = self.db_manager.search_attractions(
                        query={"text": attraction_name},
                        limit=1
                    )
                except Exception as e:
                    logger.warning(f"Error searching attraction by text: {str(e)}")

                # Second try: Use enhanced search if available
                if not attractions or len(attractions) == 0:
                    try:
                        if hasattr(self.db_manager, 'enhanced_search'):
                            logger.info(f"Using enhanced search for attraction: {attraction_name}")
                            attractions = self.db_manager.enhanced_search(
                                table="attractions",
                                search_text=attraction_name,
                                limit=1
                            )
                    except Exception as e:
                        logger.warning(f"Error using enhanced search for attraction: {str(e)}")

                # Third try: Direct SQL query as fallback
                if not attractions or len(attractions) == 0:
                    try:
                        logger.info(f"Using direct SQL query for attraction: {attraction_name}")
                        attractions = self.db_manager.execute_postgres_query(
                            "SELECT * FROM attractions WHERE name->>'en' ILIKE %s OR name->>'ar' ILIKE %s LIMIT 1",
                            (f"%{attraction_name}%", f"%{attraction_name}%")
                        )
                    except Exception as e:
                        logger.warning(f"Error using direct SQL query for attraction: {str(e)}")
                if attractions and len(attractions) > 0:
                    attraction = attractions[0]

            # Extract location information
            location = None
            city_name = None
            region_name = None

            if attraction:
                # Get location from attraction
                if 'city' in attraction:
                    city_name = attraction['city']
                    location = city_name
                elif 'location' in attraction and isinstance(attraction['location'], dict):
                    if 'city' in attraction['location']:
                        city_name = attraction['location'].get('city')
                        location = city_name
                elif 'location_description' in attraction and isinstance(attraction['location_description'], dict):
                    location = attraction['location_description'].get('en')
                    # Try to extract city name from location description
                    if location and isinstance(location, str) and ',' in location:
                        city_name = location.split(',')[0].strip()

                # Try to get region information
                if 'region' in attraction:
                    region_name = attraction['region']

            # Use provided city if no location found
            if not location and city:
                location = city
                city_name = city

            if not location:
                logger.warning("Could not determine location for event search")
                return []

            # Try multiple search approaches
            logger.info(f"Searching for events in location: {location}")
            events = []

            # First try: Search by city name if available
            if city_name:
                logger.info(f"Searching events by city name: {city_name}")
                try:
                    # Try to use the search_events_festivals method if available
                    if hasattr(self.db_manager, 'search_events_festivals'):
                        city_results = self.db_manager.search_events_festivals(
                            query={"city": city_name},
                            limit=limit
                        )
                        if city_results:
                            logger.info(f"Found {len(city_results)} events by city match")
                            events.extend(city_results)
                    else:
                        # Fallback to direct query
                        city_results = self.db_manager.execute_query(
                            """
                            SELECT * FROM events_festivals
                            WHERE location_description->>'en' ILIKE %s
                            OR venue->>'city' = %s
                            LIMIT %s
                            """,
                            (f"%{city_name}%", city_name, limit)
                        )
                        if city_results:
                            logger.info(f"Found {len(city_results)} events by city match (direct query)")
                            events.extend(city_results)
                except Exception as e:
                    logger.warning(f"Error searching events by city: {str(e)}")

            # Second try: Search by region if available and we need more results
            if region_name and len(events) < limit:
                remaining = limit - len(events)
                logger.info(f"Searching events by region: {region_name}")
                try:
                    # Try to use the search_events_festivals method if available
                    if hasattr(self.db_manager, 'search_events_festivals'):
                        region_results = self.db_manager.search_events_festivals(
                            query={"region": region_name},
                            limit=remaining
                        )
                        if region_results:
                            logger.info(f"Found {len(region_results)} events by region match")
                            # Add only events that aren't already in the results
                            existing_ids = {e.get('id') for e in events}
                            for e in region_results:
                                if e.get('id') not in existing_ids:
                                    events.append(e)
                                    existing_ids.add(e.get('id'))
                    else:
                        # Fallback to direct query
                        region_results = self.db_manager.execute_query(
                            """
                            SELECT * FROM events_festivals
                            WHERE location_description->>'en' ILIKE %s
                            LIMIT %s
                            """,
                            (f"%{region_name}%", remaining)
                        )
                        if region_results:
                            logger.info(f"Found {len(region_results)} events by region match (direct query)")
                            # Add only events that aren't already in the results
                            existing_ids = {e.get('id') for e in events}
                            for e in region_results:
                                if e.get('id') not in existing_ids:
                                    events.append(e)
                                    existing_ids.add(e.get('id'))
                except Exception as e:
                    logger.warning(f"Error searching events by region: {str(e)}")

            # Third try: General location search if we still need more results
            if len(events) < limit:
                remaining = limit - len(events)
                logger.info(f"Searching events by general location: {location}")
                try:
                    # Try to use the search_events_festivals method if available
                    if hasattr(self.db_manager, 'search_events_festivals'):
                        text_results = self.db_manager.search_events_festivals(
                            query={"text": location},
                            limit=remaining
                        )
                        if text_results:
                            logger.info(f"Found {len(text_results)} events by text match")
                            # Add only events that aren't already in the results
                            existing_ids = {e.get('id') for e in events}
                            for e in text_results:
                                if e.get('id') not in existing_ids:
                                    events.append(e)
                                    existing_ids.add(e.get('id'))
                    else:
                        # Fallback to direct query
                        text_results = self.db_manager.execute_query(
                            """
                            SELECT * FROM events_festivals
                            WHERE location_description->>'en' ILIKE %s
                            OR venue->>'address'->>'en' ILIKE %s
                            OR name->>'en' ILIKE %s
                            LIMIT %s
                            """,
                            (f"%{location}%", f"%{location}%", f"%{location}%", remaining)
                        )
                        if text_results:
                            logger.info(f"Found {len(text_results)} events by text match (direct query)")
                            # Add only events that aren't already in the results
                            existing_ids = {e.get('id') for e in events}
                            for e in text_results:
                                if e.get('id') not in existing_ids:
                                    events.append(e)
                                    existing_ids.add(e.get('id'))
                except Exception as e:
                    logger.warning(f"Error searching events by text: {str(e)}")

            return events if events else []

        except Exception as e:
            logger.error(f"Error finding events near attraction: {str(e)}")
            return []

    def _get_attraction_by_id(self, attraction_id: int) -> Optional[Dict]:
        """Get attraction by ID."""
        try:
            result = self.db_manager.execute_query(
                "SELECT * FROM attractions WHERE id = %s",
                (attraction_id,),
                fetchall=False
            )
            return result
        except Exception as e:
            logger.error(f"Error getting attraction by ID: {str(e)}")
            return None

    def _get_itinerary_by_id(self, itinerary_id: int) -> Optional[Dict]:
        """Get itinerary by ID."""
        try:
            result = self.db_manager.execute_query(
                "SELECT * FROM itineraries WHERE id = %s",
                (itinerary_id,),
                fetchall=False
            )
            return result
        except Exception as e:
            logger.error(f"Error getting itinerary by ID: {str(e)}")
            return None

    def _calculate_distance(self, coords1: Dict, coords2: Dict) -> float:
        """
        Calculate distance between two coordinates in kilometers.
        Simple implementation using Euclidean distance as an approximation.

        Args:
            coords1: First coordinates (lat, lng)
            coords2: Second coordinates (lat, lng)

        Returns:
            Distance in kilometers
        """
        # Extract coordinates
        lat1 = coords1.get('lat', 0)
        lng1 = coords1.get('lng', 0)
        lat2 = coords2.get('lat', 0)
        lng2 = coords2.get('lng', 0)

        # Simple distance calculation (not accurate for long distances)
        # For a demo, this approximation is sufficient
        lat_diff = abs(lat1 - lat2) * 111  # 1 degree latitude is approximately 111 km
        lng_diff = abs(lng1 - lng2) * 111 * abs(0.5)  # Rough approximation

        return round((lat_diff**2 + lng_diff**2)**0.5, 2)
