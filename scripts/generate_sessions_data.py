#!/usr/bin/env python
"""
Generate Sessions and Feedback Data

This script generates realistic user sessions and feedback data for the Egypt chatbot:
1. Creates user sessions with realistic timestamps and durations
2. Adds messages to sessions with tourism-related queries
3. Creates feedback for some sessions
"""

import os
import sys
import logging
import random
import uuid
import json
import time
import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from datetime import datetime, timedelta, timezone
from faker import Faker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('generate_sessions_data.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize Faker
fake = Faker()

# Set random seed for reproducibility
random.seed(42)

# Target counts for data generation
TARGET_SESSIONS = 1000
TARGET_FEEDBACK_RATIO = 0.3  # 30% of sessions should have feedback

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
        # Get users
        cursor.execute("SELECT id, username FROM users")
        existing_data['users'] = cursor.fetchall()

        # If no users exist, create a default user
        if not existing_data['users']:
            cursor.execute("""
                INSERT INTO users (id, username, email, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, username
            """, ('default_user', 'default_user', 'default@example.com', datetime.now(timezone.utc), datetime.now(timezone.utc)))
            existing_data['users'] = [cursor.fetchone()]
            conn.commit()

        # Get attractions
        cursor.execute("SELECT id, name FROM attractions")
        existing_data['attractions'] = cursor.fetchall()

        # Get accommodations
        cursor.execute("SELECT id, name FROM accommodations")
        existing_data['accommodations'] = cursor.fetchall()

        # Get cities
        cursor.execute("SELECT id, name FROM cities")
        existing_data['cities'] = cursor.fetchall()

        # Get regions
        cursor.execute("SELECT id, name FROM regions")
        existing_data['regions'] = cursor.fetchall()

        # Get existing sessions
        cursor.execute("SELECT id FROM sessions")
        existing_data['sessions'] = cursor.fetchall()

    return existing_data

def generate_tourism_query(entity_type, entity_name):
    """Generate a realistic tourism query about an entity"""
    query_templates = {
        'attraction': [
            "Tell me about {}",
            "What are the opening hours for {}?",
            "How much does it cost to visit {}?",
            "Where is {} located?",
            "What's the best time to visit {}?",
            "How do I get to {}?",
            "Is {} worth visiting?",
            "What's special about {}?",
            "Can I book tickets online for {}?",
            "Are there guided tours for {}?",
            "What's the history of {}?",
            "What's nearby {}?",
            "How long should I spend at {}?",
            "Is {} suitable for children?",
            "What's the dress code for {}?"
        ],
        'accommodation': [
            "Tell me about {}",
            "How much does it cost to stay at {}?",
            "Where is {} located?",
            "What amenities does {} offer?",
            "Is breakfast included at {}?",
            "How do I book a room at {}?",
            "Is {} family-friendly?",
            "Does {} have a pool?",
            "What's the check-in time at {}?",
            "Is there parking at {}?",
            "Does {} have a restaurant?",
            "What's the cancellation policy at {}?",
            "Is {} close to attractions?",
            "Does {} offer airport shuttle?",
            "What's the WiFi like at {}?"
        ],
        'city': [
            "Tell me about {}",
            "What are the top attractions in {}?",
            "How do I get to {}?",
            "What's the best time to visit {}?",
            "What's the weather like in {}?",
            "What's the local cuisine in {}?",
            "What's the history of {}?",
            "Is {} safe for tourists?",
            "What's the public transportation like in {}?",
            "What are the best hotels in {}?",
            "What souvenirs can I buy in {}?",
            "What's the local currency in {}?",
            "Do I need a visa to visit {}?",
            "What languages are spoken in {}?",
            "What festivals are celebrated in {}?"
        ],
        'region': [
            "Tell me about {}",
            "What cities are in {}?",
            "What's the best time to visit {}?",
            "What's the weather like in {}?",
            "What's the geography of {}?",
            "What's the history of {}?",
            "What's the culture like in {}?",
            "What's the local cuisine in {}?",
            "What are the top attractions in {}?",
            "How do I get around in {}?",
            "What's the best way to travel to {}?",
            "What's the accommodation like in {}?",
            "Is {} good for families?",
            "What's the best itinerary for {}?",
            "What should I pack for a trip to {}?"
        ]
    }

    # Get the appropriate templates for the entity type
    templates = query_templates.get(entity_type, query_templates['attraction'])

    # Generate a query
    query = random.choice(templates).format(entity_name)

    return query

def generate_chatbot_response(query, entity_type, entity_id):
    """Generate a realistic chatbot response to a tourism query"""
    # Generic responses based on query type
    if "opening hours" in query.lower():
        return f"The opening hours are typically from 8:00 AM to 5:00 PM, but this may vary by season. I recommend checking the official website for the most up-to-date information."

    if "cost" in query.lower() or "price" in query.lower():
        if entity_type == 'attraction':
            return f"The entrance fee is approximately 100-200 EGP for foreign visitors and 20-50 EGP for Egyptian nationals. Some special exhibitions may have additional fees."
        elif entity_type == 'accommodation':
            return f"The price range is typically between $50-$150 per night depending on the season and room type. I recommend checking booking platforms for current rates and promotions."

    if "located" in query.lower() or "where is" in query.lower():
        return f"It's located in the heart of the city, about 2 km from the city center. You can easily reach it by taxi or public transportation."

    if "best time" in query.lower():
        return f"The best time to visit is during spring (March-May) or fall (September-November) when the weather is pleasant and there are fewer tourists. Summer can be extremely hot, especially in southern Egypt."

    if "history" in query.lower():
        return f"It has a rich history dating back to ancient times. It was built during the reign of Pharaoh Ramses II and has been an important cultural site ever since. Over the centuries, it has been renovated and expanded by various rulers."

    # Generic response for other queries
    return f"This is a popular {entity_type} in Egypt known for its unique architecture and historical significance. Many tourists visit it each year to experience its beauty and learn about Egyptian culture and history."

def generate_sessions(conn, existing_data, count=TARGET_SESSIONS):
    """Generate user sessions with messages and feedback"""
    logger.info(f"Generating {count} user sessions")

    # Get existing data
    users = existing_data['users']
    attractions = existing_data['attractions']
    accommodations = existing_data['accommodations']
    cities = existing_data['cities']
    regions = existing_data['regions']

    # Combine all entities
    all_entities = []
    for attraction in attractions:
        name = json.loads(attraction['name'])['en'] if isinstance(attraction['name'], str) else attraction['name']['en']
        all_entities.append(('attraction', attraction['id'], name))

    for accommodation in accommodations:
        name = json.loads(accommodation['name'])['en'] if isinstance(accommodation['name'], str) else accommodation['name']['en']
        all_entities.append(('accommodation', accommodation['id'], name))

    for city in cities:
        name = json.loads(city['name'])['en'] if isinstance(city['name'], str) else city['name']['en']
        all_entities.append(('city', city['id'], name))

    for region in regions:
        name = json.loads(region['name'])['en'] if isinstance(region['name'], str) else region['name']['en']
        all_entities.append(('region', region['id'], name))

    # Generate sessions
    sessions = []
    feedback_data = []

    for i in range(count):
        # Generate a unique session ID
        session_id = str(uuid.uuid4())

        # Select a random user (or None for anonymous session)
        user = random.choice(users) if random.random() < 0.7 else None
        user_id = user['id'] if user else None

        # Generate timestamps (within the last 30 days)
        created_at = datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30),
                                               hours=random.randint(0, 23),
                                               minutes=random.randint(0, 59))

        # Format as ISO string
        created_at_str = created_at.isoformat()

        # Updated at is slightly later
        updated_at = created_at + timedelta(minutes=random.randint(5, 60))
        updated_at_str = updated_at.isoformat()

        # Expires after 7 days
        expires_at = created_at + timedelta(days=7)
        expires_at_str = expires_at.isoformat()

        # Generate session data
        session_data = {
            "language": random.choice(["en", "ar"]),
            "client_info": {
                "browser": random.choice(["Chrome", "Firefox", "Safari", "Edge"]),
                "os": random.choice(["Windows", "MacOS", "iOS", "Android"]),
                "device": random.choice(["Desktop", "Mobile", "Tablet"])
            },
            "query_topics": []
        }

        # Generate query topics
        for _ in range(random.randint(1, 5)):
            # Select a random entity
            entity_type, entity_id, entity_name = random.choice(all_entities)

            # Generate a query
            query = generate_tourism_query(entity_type, entity_name)

            # Generate a response
            response = generate_chatbot_response(query, entity_type, entity_id)

            session_data["query_topics"].append({
                "type": entity_type,
                "id": entity_id,
                "name": entity_name,
                "query": query,
                "response": response
            })

        # Add messages to session data
        messages = []
        for i in range(random.randint(1, 10)):
            topic = random.choice(session_data["query_topics"])
            messages.append({
                "role": "user" if i % 2 == 0 else "assistant",
                "content": topic["query"] if i % 2 == 0 else topic["response"],
                "timestamp": (created_at + timedelta(minutes=i*2)).isoformat()
            })

        session_data["messages"] = messages

        sessions.append((
            session_id, user_id, created_at_str, updated_at_str, expires_at_str, json.dumps(session_data)
        ))

        # Generate feedback for some sessions
        if random.random() < TARGET_FEEDBACK_RATIO:
            rating = random.randint(1, 5)
            feedback_text = fake.paragraph(nb_sentences=1) if random.random() < 0.5 else None

            # Get a random message ID from the session
            message_id = str(uuid.uuid4())  # Fallback if no messages
            if session_data.get("messages") and len(session_data["messages"]) > 0:
                # Use the timestamp of a random message as a pseudo-ID
                random_message = random.choice(session_data["messages"])
                message_id = random_message.get("timestamp", message_id)

            feedback_data.append((
                random.randint(1000, 9999),  # ID is integer
                session_id,
                user_id,
                message_id,
                rating,
                feedback_text,
                datetime.now(timezone.utc)
            ))

    # Insert sessions into database
    try:
        with conn.cursor() as cursor:
            # Insert sessions
            execute_values(
                cursor,
                """
                INSERT INTO sessions
                (id, user_id, created_at, updated_at, expires_at, data)
                VALUES %s
                ON CONFLICT (id) DO NOTHING
                """,
                sessions
            )

            logger.info(f"Inserted {cursor.rowcount} sessions")

            # Insert feedback
            if feedback_data:
                execute_values(
                    cursor,
                    """
                    INSERT INTO feedback
                    (id, session_id, user_id, message_id, rating, feedback_text, created_at)
                    VALUES %s
                    ON CONFLICT (id) DO NOTHING
                    """,
                    feedback_data
                )

                logger.info(f"Inserted {cursor.rowcount} feedback entries")

        conn.commit()
        return len(sessions), len(feedback_data)

    except Exception as e:
        conn.rollback()
        logger.error(f"Error inserting sessions and feedback: {e}")
        return 0, 0

def verify_data_volume(conn):
    """Verify the data volume in the database"""
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        # Check data volume
        cursor.execute("""
            SELECT 'sessions' as table_name, COUNT(*) as count FROM sessions
            UNION ALL
            SELECT 'feedback' as table_name, COUNT(*) as count FROM feedback;
        """)
        counts = cursor.fetchall()

        logger.info("Data volume in database:")
        for count in counts:
            logger.info(f"  - {count['table_name']}: {count['count']} records")

        # Check if we have enough data
        sessions_count = next((int(c['count']) for c in counts if c['table_name'] == 'sessions'), 0)
        feedback_count = next((int(c['count']) for c in counts if c['table_name'] == 'feedback'), 0)

        if sessions_count >= TARGET_SESSIONS:
            logger.info("✅ Target session volume achieved")
            return True
        else:
            logger.warning(f"⚠️ Target session volume not achieved: {sessions_count}/{TARGET_SESSIONS}")
            return False

def main():
    """Main function to generate sessions data"""
    try:
        # Connect to database
        conn = connect_to_db()

        # Get existing data
        existing_data = get_existing_data(conn)

        # Calculate how many more sessions we need to generate
        existing_sessions_count = len(existing_data['sessions'])
        sessions_to_generate = max(0, TARGET_SESSIONS - existing_sessions_count)

        logger.info(f"Existing data: {existing_sessions_count} sessions")
        logger.info(f"Will generate: {sessions_to_generate} sessions")

        # Generate sessions
        if sessions_to_generate > 0:
            sessions_count, feedback_count = generate_sessions(conn, existing_data, sessions_to_generate)
            logger.info(f"Generated {sessions_count} sessions and {feedback_count} feedback entries")

        # Verify data volume
        verify_data_volume(conn)

        logger.info("Sessions data generation completed successfully")
        return True

    except Exception as e:
        logger.error(f"Error generating sessions data: {str(e)}", exc_info=True)
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
