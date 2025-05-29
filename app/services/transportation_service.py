"""
Transportation Service

This module provides functions for finding transportation routes in the Egypt Tourism Chatbot.
It replaces the database functions that were previously used for transportation queries.
"""

from typing import List, Dict, Any, Optional
from app.database import get_connection


def find_transportation_routes(
    origin_id: str,
    destination_id: str,
    transportation_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Find transportation routes between two destinations.
    
    Args:
        origin_id (str): The ID of the origin destination.
        destination_id (str): The ID of the destination.
        transportation_type (Optional[str], optional): The type of transportation to filter by. Defaults to None.
        
    Returns:
        List[Dict[str, Any]]: A list of transportation routes between the two destinations.
    """
    query = """
    SELECT 
        r.id,
        r.origin_id,
        r.destination_id,
        r.transportation_type,
        r.name,
        r.description,
        r.distance_km,
        r.duration_minutes,
        r.price_range
    FROM 
        transportation_routes r
    WHERE 
        r.origin_id = %s
        AND r.destination_id = %s
    """
    
    params = [origin_id, destination_id]
    
    if transportation_type:
        query += " AND r.transportation_type = %s"
        params.append(transportation_type)
        
    query += " ORDER BY r.duration_minutes ASC"
    
    # Execute the query
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            results = cursor.fetchall()
            
    # Process results
    routes = []
    for row in results:
        routes.append({
            'id': row[0],
            'origin_id': row[1],
            'destination_id': row[2],
            'transportation_type': row[3],
            'name': row[4],
            'description': row[5],
            'distance_km': row[6],
            'duration_minutes': row[7],
            'price_range': row[8]
        })
            
    return routes


def find_routes_from_destination(
    origin_id: str,
    transportation_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Find transportation routes from a destination.
    
    Args:
        origin_id (str): The ID of the origin destination.
        transportation_type (Optional[str], optional): The type of transportation to filter by. Defaults to None.
        
    Returns:
        List[Dict[str, Any]]: A list of transportation routes from the destination.
    """
    query = """
    SELECT 
        r.id,
        r.origin_id,
        r.destination_id,
        d.name AS destination_name,
        r.transportation_type,
        r.name,
        r.distance_km,
        r.duration_minutes,
        r.price_range
    FROM 
        transportation_routes r
    JOIN
        destinations d ON r.destination_id = d.id
    WHERE 
        r.origin_id = %s
    """
    
    params = [origin_id]
    
    if transportation_type:
        query += " AND r.transportation_type = %s"
        params.append(transportation_type)
        
    query += " ORDER BY r.transportation_type, r.duration_minutes ASC"
    
    # Execute the query
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            results = cursor.fetchall()
            
    # Process results
    routes = []
    for row in results:
        routes.append({
            'id': row[0],
            'origin_id': row[1],
            'destination_id': row[2],
            'destination_name': row[3],
            'transportation_type': row[4],
            'name': row[5],
            'distance_km': row[6],
            'duration_minutes': row[7],
            'price_range': row[8]
        })
            
    return routes


def find_routes_to_destination(
    destination_id: str,
    transportation_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Find transportation routes to a destination.
    
    Args:
        destination_id (str): The ID of the destination.
        transportation_type (Optional[str], optional): The type of transportation to filter by. Defaults to None.
        
    Returns:
        List[Dict[str, Any]]: A list of transportation routes to the destination.
    """
    query = """
    SELECT 
        r.id,
        r.origin_id,
        d.name AS origin_name,
        r.destination_id,
        r.transportation_type,
        r.name,
        r.distance_km,
        r.duration_minutes,
        r.price_range
    FROM 
        transportation_routes r
    JOIN
        destinations d ON r.origin_id = d.id
    WHERE 
        r.destination_id = %s
    """
    
    params = [destination_id]
    
    if transportation_type:
        query += " AND r.transportation_type = %s"
        params.append(transportation_type)
        
    query += " ORDER BY r.transportation_type, r.duration_minutes ASC"
    
    # Execute the query
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            results = cursor.fetchall()
            
    # Process results
    routes = []
    for row in results:
        routes.append({
            'id': row[0],
            'origin_id': row[1],
            'origin_name': row[2],
            'destination_id': row[3],
            'transportation_type': row[4],
            'name': row[5],
            'distance_km': row[6],
            'duration_minutes': row[7],
            'price_range': row[8]
        })
            
    return routes


def find_related_attractions(
    attraction_id: str,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Find attractions related to a given attraction.
    
    Args:
        attraction_id (str): The ID of the attraction.
        limit (int, optional): The maximum number of results to return. Defaults to 5.
        
    Returns:
        List[Dict[str, Any]]: A list of attractions related to the given attraction.
    """
    query = """
    SELECT 
        a.id,
        a.name,
        a.type,
        a.subcategory_id,
        a.city_id,
        a.region_id
    FROM 
        attractions a
    WHERE 
        a.id = ANY(
            SELECT related_attractions 
            FROM attractions 
            WHERE id = %s
        )
    LIMIT %s
    """
    
    # Execute the query
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (attraction_id, limit))
            results = cursor.fetchall()
            
    # Process results
    attractions = []
    for row in results:
        attractions.append({
            'id': row[0],
            'name': row[1],
            'type': row[2],
            'subcategory_id': row[3],
            'city_id': row[4],
            'region_id': row[5]
        })
            
    return attractions
