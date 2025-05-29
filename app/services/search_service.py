"""
Search Service

This module provides functions for searching various entities in the Egypt Tourism Chatbot.
It replaces the database functions that were previously used for searching.
"""

import re
from typing import List, Dict, Any, Optional, Union
from datetime import date

from app.database import get_connection
from app.utils.text import get_text_by_language


def search_attractions_by_keywords(keywords: str, lang: str = 'en') -> List[Dict[str, Any]]:
    """
    Search attractions by keywords.
    
    Args:
        keywords (str): The keywords to search for.
        lang (str, optional): The language to search in. Defaults to 'en'.
        
    Returns:
        List[Dict[str, Any]]: A list of attractions matching the keywords.
    """
    # Convert keywords to tsquery format
    tsquery = re.sub(r'\s+', ' & ', keywords.strip())
    
    query = """
    SELECT
        a.id,
        a.name,
        a.description,
        a.city_id,
        a.region_id,
        a.type,
        ts_rank_cd(
            to_tsvector(get_text_by_language(a.description, %s)),
            to_tsquery(%s)
        ) AS relevance
    FROM
        attractions a
    WHERE
        to_tsvector(get_text_by_language(a.description, %s)) @@
        to_tsquery(%s)
    ORDER BY
        relevance DESC
    """
    
    # Execute the query
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (lang, tsquery, lang, tsquery))
            results = cursor.fetchall()
            
    # Process results
    attractions = []
    for row in results:
        attractions.append({
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'city_id': row[3],
            'region_id': row[4],
            'type': row[5],
            'relevance': row[6]
        })
            
    return attractions


def get_attraction_by_name(search_name: str, lang: str = 'en') -> List[Dict[str, Any]]:
    """
    Get attractions by name.
    
    Args:
        search_name (str): The name to search for.
        lang (str, optional): The language to search in. Defaults to 'en'.
        
    Returns:
        List[Dict[str, Any]]: A list of attractions matching the name.
    """
    query = """
    SELECT
        a.id,
        a.name,
        a.description,
        a.city_id,
        a.region_id,
        a.type,
        similarity(get_text_by_language(a.name, %s), %s) AS similarity_score
    FROM
        attractions a
    WHERE
        search_jsonb_text(a.name, %s, %s) = TRUE
    ORDER BY
        similarity_score DESC
    LIMIT 5
    """
    
    # Execute the query
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (lang, search_name, search_name, lang))
            results = cursor.fetchall()
            
    # Process results
    attractions = []
    for row in results:
        attractions.append({
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'city_id': row[3],
            'region_id': row[4],
            'type': row[5],
            'similarity_score': row[6]
        })
            
    return attractions


def get_accommodations_by_city(city_name: str, lang: str = 'en') -> List[Dict[str, Any]]:
    """
    Get accommodations by city.
    
    Args:
        city_name (str): The city name to search for.
        lang (str, optional): The language to search in. Defaults to 'en'.
        
    Returns:
        List[Dict[str, Any]]: A list of accommodations in the specified city.
    """
    query = """
    SELECT
        a.id,
        a.name,
        a.description,
        a.city_id,
        a.type,
        a.stars
    FROM
        accommodations a
    JOIN
        cities c ON a.city_id = c.id
    WHERE
        search_jsonb_text(c.name, %s, %s) = TRUE
    ORDER BY
        a.stars DESC
    """
    
    # Execute the query
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (city_name, lang))
            results = cursor.fetchall()
            
    # Process results
    accommodations = []
    for row in results:
        accommodations.append({
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'city_id': row[3],
            'type': row[4],
            'stars': row[5]
        })
            
    return accommodations


def search_events_festivals(
    query: Optional[str] = None,
    category_id: Optional[str] = None,
    destination_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    is_annual: Optional[bool] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Search events and festivals.
    
    Args:
        query (Optional[str], optional): The search query. Defaults to None.
        category_id (Optional[str], optional): The category ID to filter by. Defaults to None.
        destination_id (Optional[str], optional): The destination ID to filter by. Defaults to None.
        start_date (Optional[date], optional): The start date to filter by. Defaults to None.
        end_date (Optional[date], optional): The end date to filter by. Defaults to None.
        is_annual (Optional[bool], optional): Whether to filter by annual events. Defaults to None.
        limit (int, optional): The maximum number of results to return. Defaults to 10.
        
    Returns:
        List[Dict[str, Any]]: A list of events and festivals matching the criteria.
    """
    sql_query = """
    SELECT 
        e.id,
        e.category_id,
        c.name AS category_name,
        e.name,
        e.description,
        e.start_date,
        e.end_date,
        e.is_annual,
        e.destination_id,
        e.venue,
        e.tags,
        e.is_featured
    FROM 
        events_festivals e
    JOIN
        event_categories c ON e.category_id = c.id
    WHERE 1=1
    """
    
    params = []
    
    if category_id:
        sql_query += " AND e.category_id = %s"
        params.append(category_id)
        
    if destination_id:
        sql_query += " AND e.destination_id = %s"
        params.append(destination_id)
        
    if start_date:
        sql_query += " AND (e.start_date >= %s OR e.is_annual = TRUE)"
        params.append(start_date)
        
    if end_date:
        sql_query += " AND (e.end_date <= %s OR e.is_annual = TRUE)"
        params.append(end_date)
        
    if is_annual is not None:
        sql_query += " AND e.is_annual = %s"
        params.append(is_annual)
        
    if query:
        sql_query += """
        AND (
            to_tsvector('english', e.name->>'en') @@ plainto_tsquery('english', %s)
            OR to_tsvector('english', e.description->>'en') @@ plainto_tsquery('english', %s)
            OR %s = ANY(e.tags)
        )
        """
        params.extend([query, query, query])
        
    sql_query += """
    ORDER BY 
        e.is_featured DESC,
        CASE WHEN e.start_date IS NOT NULL AND e.start_date >= CURRENT_DATE THEN 0 ELSE 1 END,
        e.start_date,
        e.view_count DESC
    LIMIT %s
    """
    params.append(limit)
    
    # Execute the query
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql_query, params)
            results = cursor.fetchall()
            
    # Process results
    events = []
    for row in results:
        events.append({
            'id': row[0],
            'category_id': row[1],
            'category_name': row[2],
            'name': row[3],
            'description': row[4],
            'start_date': row[5],
            'end_date': row[6],
            'is_annual': row[7],
            'destination_id': row[8],
            'venue': row[9],
            'tags': row[10],
            'is_featured': row[11]
        })
            
    return events
