#!/usr/bin/env python3
import psycopg2
import sys

def test_database_query():
    """Test if the database contains tourism data and can be queried."""
    
    try:
        # Connect to PostgreSQL database
        conn = psycopg2.connect("dbname=egypt_chatbot")
        cursor = conn.cursor()
        
        # First, let's check the schema of the attractions table
        print("Checking attractions table schema...")
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'attractions'
        """)
        columns = cursor.fetchall()
        
        print("Attractions table columns:")
        for col in columns:
            print(f"  - {col[0]} ({col[1]})")
        
        # Test attraction query using just the city column
        print("\nTesting query for attractions in Cairo...")
        cursor.execute("""
            SELECT id, name_en, description_en 
            FROM attractions 
            WHERE city ILIKE %s
            LIMIT 5
        """, ('%cairo%',))
        
        attractions = cursor.fetchall()
        if attractions:
            print(f"✅ Found {len(attractions)} attractions in Cairo:")
            for attraction in attractions:
                print(f"  - {attraction[1]}")
            return True
        else:
            print("❌ No attractions found in Cairo.")
            
            # Try a broader query to see if any attractions exist
            cursor.execute("SELECT COUNT(*) FROM attractions")
            count = cursor.fetchone()[0]
            print(f"Total attractions in database: {count}")
            
            if count > 0:
                # Show some sample cities
                cursor.execute("SELECT DISTINCT city FROM attractions WHERE city IS NOT NULL LIMIT 10")
                cities = cursor.fetchall()
                if cities:
                    print(f"Available cities: {', '.join([city[0] for city in cities if city[0]])}")
                
                # Show some sample attractions
                cursor.execute("SELECT id, name_en FROM attractions LIMIT 5")
                sample_attractions = cursor.fetchall()
                if sample_attractions:
                    print("\nSample attractions:")
                    for attraction in sample_attractions:
                        print(f"  - {attraction[1]} (ID: {attraction[0]})")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
    
    return False

if __name__ == "__main__":
    print("Testing direct database query for Egypt tourism data...")
    if test_database_query():
        print("\n✅ Database test passed! Your database contains tourism data.")
        sys.exit(0)
    else:
        print("\n❌ Database test failed! Your database might be empty or misconfigured.")
        sys.exit(1)