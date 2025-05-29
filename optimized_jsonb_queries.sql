-- Get name from accommodations

                        CREATE OR REPLACE FUNCTION get_accommodations_name(p_id TEXT)
                        RETURNS TEXT AS $$
                        DECLARE
                            result TEXT;
                        BEGIN
                            SELECT data->>name
                            INTO result
                            FROM accommodations
                            WHERE id = p_id;
                            
                            RETURN result;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Get description from accommodations

                        CREATE OR REPLACE FUNCTION get_accommodations_description(p_id TEXT)
                        RETURNS TEXT AS $$
                        DECLARE
                            result TEXT;
                        BEGIN
                            SELECT data->>description
                            INTO result
                            FROM accommodations
                            WHERE id = p_id;
                            
                            RETURN result;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search accommodations by name

                        CREATE OR REPLACE FUNCTION search_accommodations_by_name(p_value TEXT)
                        RETURNS TABLE (
                            id TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.data
                            FROM accommodations t
                            WHERE t.data->>name ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search accommodations by description

                        CREATE OR REPLACE FUNCTION search_accommodations_by_description(p_value TEXT)
                        RETURNS TABLE (
                            id TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.data
                            FROM accommodations t
                            WHERE t.data->>description ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Get ar from accommodations

                        CREATE OR REPLACE FUNCTION get_accommodations_ar(p_id TEXT)
                        RETURNS TEXT AS $$
                        DECLARE
                            result TEXT;
                        BEGIN
                            SELECT description->>ar
                            INTO result
                            FROM accommodations
                            WHERE id = p_id;
                            
                            RETURN result;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Get en from accommodations

                        CREATE OR REPLACE FUNCTION get_accommodations_en(p_id TEXT)
                        RETURNS TEXT AS $$
                        DECLARE
                            result TEXT;
                        BEGIN
                            SELECT description->>en
                            INTO result
                            FROM accommodations
                            WHERE id = p_id;
                            
                            RETURN result;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search accommodations by ar

                        CREATE OR REPLACE FUNCTION search_accommodations_by_ar(p_value TEXT)
                        RETURNS TABLE (
                            id TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.description
                            FROM accommodations t
                            WHERE t.description->>ar ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search accommodations by en

                        CREATE OR REPLACE FUNCTION search_accommodations_by_en(p_value TEXT)
                        RETURNS TABLE (
                            id TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.description
                            FROM accommodations t
                            WHERE t.description->>en ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search accommodations in multiple languages

                        CREATE OR REPLACE FUNCTION search_accommodations_multilingual(p_value TEXT, p_language TEXT DEFAULT 'en')
                        RETURNS TABLE (
                            id TEXT,
                            name TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.description->p_language AS name, t.description
                            FROM accommodations t
                            WHERE t.description->p_language ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Get ar from accommodations

                        CREATE OR REPLACE FUNCTION get_accommodations_ar(p_id TEXT)
                        RETURNS TEXT AS $$
                        DECLARE
                            result TEXT;
                        BEGIN
                            SELECT name->>ar
                            INTO result
                            FROM accommodations
                            WHERE id = p_id;
                            
                            RETURN result;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Get en from accommodations

                        CREATE OR REPLACE FUNCTION get_accommodations_en(p_id TEXT)
                        RETURNS TEXT AS $$
                        DECLARE
                            result TEXT;
                        BEGIN
                            SELECT name->>en
                            INTO result
                            FROM accommodations
                            WHERE id = p_id;
                            
                            RETURN result;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search accommodations by ar

                        CREATE OR REPLACE FUNCTION search_accommodations_by_ar(p_value TEXT)
                        RETURNS TABLE (
                            id TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.name
                            FROM accommodations t
                            WHERE t.name->>ar ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search accommodations by en

                        CREATE OR REPLACE FUNCTION search_accommodations_by_en(p_value TEXT)
                        RETURNS TABLE (
                            id TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.name
                            FROM accommodations t
                            WHERE t.name->>en ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search accommodations in multiple languages

                        CREATE OR REPLACE FUNCTION search_accommodations_multilingual(p_value TEXT, p_language TEXT DEFAULT 'en')
                        RETURNS TABLE (
                            id TEXT,
                            name TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.name->p_language AS name, t.name
                            FROM accommodations t
                            WHERE t.name->p_language ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Get intent from analytics

                        CREATE OR REPLACE FUNCTION get_analytics_intent(p_id TEXT)
                        RETURNS TEXT AS $$
                        DECLARE
                            result TEXT;
                        BEGIN
                            SELECT event_data->>intent
                            INTO result
                            FROM analytics
                            WHERE id = p_id;
                            
                            RETURN result;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Get entities from analytics

                        CREATE OR REPLACE FUNCTION get_analytics_entities(p_id TEXT)
                        RETURNS TEXT AS $$
                        DECLARE
                            result TEXT;
                        BEGIN
                            SELECT event_data->>entities
                            INTO result
                            FROM analytics
                            WHERE id = p_id;
                            
                            RETURN result;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Get language from analytics

                        CREATE OR REPLACE FUNCTION get_analytics_language(p_id TEXT)
                        RETURNS TEXT AS $$
                        DECLARE
                            result TEXT;
                        BEGIN
                            SELECT event_data->>language
                            INTO result
                            FROM analytics
                            WHERE id = p_id;
                            
                            RETURN result;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Get bot_response from analytics

                        CREATE OR REPLACE FUNCTION get_analytics_bot_response(p_id TEXT)
                        RETURNS TEXT AS $$
                        DECLARE
                            result TEXT;
                        BEGIN
                            SELECT event_data->>bot_response
                            INTO result
                            FROM analytics
                            WHERE id = p_id;
                            
                            RETURN result;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Get user_message from analytics

                        CREATE OR REPLACE FUNCTION get_analytics_user_message(p_id TEXT)
                        RETURNS TEXT AS $$
                        DECLARE
                            result TEXT;
                        BEGIN
                            SELECT event_data->>user_message
                            INTO result
                            FROM analytics
                            WHERE id = p_id;
                            
                            RETURN result;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Get intent_confidence from analytics

                        CREATE OR REPLACE FUNCTION get_analytics_intent_confidence(p_id TEXT)
                        RETURNS TEXT AS $$
                        DECLARE
                            result TEXT;
                        BEGIN
                            SELECT event_data->>intent_confidence
                            INTO result
                            FROM analytics
                            WHERE id = p_id;
                            
                            RETURN result;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Get suggestions_provided from analytics

                        CREATE OR REPLACE FUNCTION get_analytics_suggestions_provided(p_id TEXT)
                        RETURNS TEXT AS $$
                        DECLARE
                            result TEXT;
                        BEGIN
                            SELECT event_data->>suggestions_provided
                            INTO result
                            FROM analytics
                            WHERE id = p_id;
                            
                            RETURN result;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search analytics by intent

                        CREATE OR REPLACE FUNCTION search_analytics_by_intent(p_value TEXT)
                        RETURNS TABLE (
                            id TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.event_data
                            FROM analytics t
                            WHERE t.event_data->>intent ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search analytics by entities

                        CREATE OR REPLACE FUNCTION search_analytics_by_entities(p_value TEXT)
                        RETURNS TABLE (
                            id TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.event_data
                            FROM analytics t
                            WHERE t.event_data->>entities ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search analytics by language

                        CREATE OR REPLACE FUNCTION search_analytics_by_language(p_value TEXT)
                        RETURNS TABLE (
                            id TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.event_data
                            FROM analytics t
                            WHERE t.event_data->>language ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search analytics by bot_response

                        CREATE OR REPLACE FUNCTION search_analytics_by_bot_response(p_value TEXT)
                        RETURNS TABLE (
                            id TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.event_data
                            FROM analytics t
                            WHERE t.event_data->>bot_response ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search analytics by user_message

                        CREATE OR REPLACE FUNCTION search_analytics_by_user_message(p_value TEXT)
                        RETURNS TABLE (
                            id TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.event_data
                            FROM analytics t
                            WHERE t.event_data->>user_message ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search analytics by intent_confidence

                        CREATE OR REPLACE FUNCTION search_analytics_by_intent_confidence(p_value TEXT)
                        RETURNS TABLE (
                            id TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.event_data
                            FROM analytics t
                            WHERE t.event_data->>intent_confidence ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search analytics by suggestions_provided

                        CREATE OR REPLACE FUNCTION search_analytics_by_suggestions_provided(p_value TEXT)
                        RETURNS TABLE (
                            id TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.event_data
                            FROM analytics t
                            WHERE t.event_data->>suggestions_provided ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Get name from attractions

                        CREATE OR REPLACE FUNCTION get_attractions_name(p_id TEXT)
                        RETURNS TEXT AS $$
                        DECLARE
                            result TEXT;
                        BEGIN
                            SELECT data->>name
                            INTO result
                            FROM attractions
                            WHERE id = p_id;
                            
                            RETURN result;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Get description from attractions

                        CREATE OR REPLACE FUNCTION get_attractions_description(p_id TEXT)
                        RETURNS TEXT AS $$
                        DECLARE
                            result TEXT;
                        BEGIN
                            SELECT data->>description
                            INTO result
                            FROM attractions
                            WHERE id = p_id;
                            
                            RETURN result;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search attractions by name

                        CREATE OR REPLACE FUNCTION search_attractions_by_name(p_value TEXT)
                        RETURNS TABLE (
                            id TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.data
                            FROM attractions t
                            WHERE t.data->>name ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search attractions by description

                        CREATE OR REPLACE FUNCTION search_attractions_by_description(p_value TEXT)
                        RETURNS TABLE (
                            id TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.data
                            FROM attractions t
                            WHERE t.data->>description ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Get ar from attractions

                        CREATE OR REPLACE FUNCTION get_attractions_ar(p_id TEXT)
                        RETURNS TEXT AS $$
                        DECLARE
                            result TEXT;
                        BEGIN
                            SELECT description->>ar
                            INTO result
                            FROM attractions
                            WHERE id = p_id;
                            
                            RETURN result;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Get en from attractions

                        CREATE OR REPLACE FUNCTION get_attractions_en(p_id TEXT)
                        RETURNS TEXT AS $$
                        DECLARE
                            result TEXT;
                        BEGIN
                            SELECT description->>en
                            INTO result
                            FROM attractions
                            WHERE id = p_id;
                            
                            RETURN result;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search attractions by ar

                        CREATE OR REPLACE FUNCTION search_attractions_by_ar(p_value TEXT)
                        RETURNS TABLE (
                            id TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.description
                            FROM attractions t
                            WHERE t.description->>ar ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search attractions by en

                        CREATE OR REPLACE FUNCTION search_attractions_by_en(p_value TEXT)
                        RETURNS TABLE (
                            id TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.description
                            FROM attractions t
                            WHERE t.description->>en ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search attractions in multiple languages

                        CREATE OR REPLACE FUNCTION search_attractions_multilingual(p_value TEXT, p_language TEXT DEFAULT 'en')
                        RETURNS TABLE (
                            id TEXT,
                            name TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.description->p_language AS name, t.description
                            FROM attractions t
                            WHERE t.description->p_language ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Get ar from attractions

                        CREATE OR REPLACE FUNCTION get_attractions_ar(p_id TEXT)
                        RETURNS TEXT AS $$
                        DECLARE
                            result TEXT;
                        BEGIN
                            SELECT name->>ar
                            INTO result
                            FROM attractions
                            WHERE id = p_id;
                            
                            RETURN result;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Get en from attractions

                        CREATE OR REPLACE FUNCTION get_attractions_en(p_id TEXT)
                        RETURNS TEXT AS $$
                        DECLARE
                            result TEXT;
                        BEGIN
                            SELECT name->>en
                            INTO result
                            FROM attractions
                            WHERE id = p_id;
                            
                            RETURN result;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search attractions by ar

                        CREATE OR REPLACE FUNCTION search_attractions_by_ar(p_value TEXT)
                        RETURNS TABLE (
                            id TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.name
                            FROM attractions t
                            WHERE t.name->>ar ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search attractions by en

                        CREATE OR REPLACE FUNCTION search_attractions_by_en(p_value TEXT)
                        RETURNS TABLE (
                            id TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.name
                            FROM attractions t
                            WHERE t.name->>en ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search attractions in multiple languages

                        CREATE OR REPLACE FUNCTION search_attractions_multilingual(p_value TEXT, p_language TEXT DEFAULT 'en')
                        RETURNS TABLE (
                            id TEXT,
                            name TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.name->p_language AS name, t.name
                            FROM attractions t
                            WHERE t.name->p_language ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Get name from cities

                        CREATE OR REPLACE FUNCTION get_cities_name(p_id TEXT)
                        RETURNS TEXT AS $$
                        DECLARE
                            result TEXT;
                        BEGIN
                            SELECT data->>name
                            INTO result
                            FROM cities
                            WHERE id = p_id;
                            
                            RETURN result;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Get description from cities

                        CREATE OR REPLACE FUNCTION get_cities_description(p_id TEXT)
                        RETURNS TEXT AS $$
                        DECLARE
                            result TEXT;
                        BEGIN
                            SELECT data->>description
                            INTO result
                            FROM cities
                            WHERE id = p_id;
                            
                            RETURN result;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search cities by name

                        CREATE OR REPLACE FUNCTION search_cities_by_name(p_value TEXT)
                        RETURNS TABLE (
                            id TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.data
                            FROM cities t
                            WHERE t.data->>name ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search cities by description

                        CREATE OR REPLACE FUNCTION search_cities_by_description(p_value TEXT)
                        RETURNS TABLE (
                            id TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.data
                            FROM cities t
                            WHERE t.data->>description ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Get ar from cities

                        CREATE OR REPLACE FUNCTION get_cities_ar(p_id TEXT)
                        RETURNS TEXT AS $$
                        DECLARE
                            result TEXT;
                        BEGIN
                            SELECT description->>ar
                            INTO result
                            FROM cities
                            WHERE id = p_id;
                            
                            RETURN result;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Get en from cities

                        CREATE OR REPLACE FUNCTION get_cities_en(p_id TEXT)
                        RETURNS TEXT AS $$
                        DECLARE
                            result TEXT;
                        BEGIN
                            SELECT description->>en
                            INTO result
                            FROM cities
                            WHERE id = p_id;
                            
                            RETURN result;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search cities by ar

                        CREATE OR REPLACE FUNCTION search_cities_by_ar(p_value TEXT)
                        RETURNS TABLE (
                            id TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.description
                            FROM cities t
                            WHERE t.description->>ar ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search cities by en

                        CREATE OR REPLACE FUNCTION search_cities_by_en(p_value TEXT)
                        RETURNS TABLE (
                            id TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.description
                            FROM cities t
                            WHERE t.description->>en ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search cities in multiple languages

                        CREATE OR REPLACE FUNCTION search_cities_multilingual(p_value TEXT, p_language TEXT DEFAULT 'en')
                        RETURNS TABLE (
                            id TEXT,
                            name TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.description->p_language AS name, t.description
                            FROM cities t
                            WHERE t.description->p_language ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Get ar from cities

                        CREATE OR REPLACE FUNCTION get_cities_ar(p_id TEXT)
                        RETURNS TEXT AS $$
                        DECLARE
                            result TEXT;
                        BEGIN
                            SELECT name->>ar
                            INTO result
                            FROM cities
                            WHERE id = p_id;
                            
                            RETURN result;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Get en from cities

                        CREATE OR REPLACE FUNCTION get_cities_en(p_id TEXT)
                        RETURNS TEXT AS $$
                        DECLARE
                            result TEXT;
                        BEGIN
                            SELECT name->>en
                            INTO result
                            FROM cities
                            WHERE id = p_id;
                            
                            RETURN result;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search cities by ar

                        CREATE OR REPLACE FUNCTION search_cities_by_ar(p_value TEXT)
                        RETURNS TABLE (
                            id TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.name
                            FROM cities t
                            WHERE t.name->>ar ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search cities by en

                        CREATE OR REPLACE FUNCTION search_cities_by_en(p_value TEXT)
                        RETURNS TABLE (
                            id TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.name
                            FROM cities t
                            WHERE t.name->>en ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search cities in multiple languages

                        CREATE OR REPLACE FUNCTION search_cities_multilingual(p_value TEXT, p_language TEXT DEFAULT 'en')
                        RETURNS TABLE (
                            id TEXT,
                            name TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.name->p_language AS name, t.name
                            FROM cities t
                            WHERE t.name->p_language ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Get ar from regions

                        CREATE OR REPLACE FUNCTION get_regions_ar(p_id TEXT)
                        RETURNS TEXT AS $$
                        DECLARE
                            result TEXT;
                        BEGIN
                            SELECT name->>ar
                            INTO result
                            FROM regions
                            WHERE id = p_id;
                            
                            RETURN result;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Get en from regions

                        CREATE OR REPLACE FUNCTION get_regions_en(p_id TEXT)
                        RETURNS TEXT AS $$
                        DECLARE
                            result TEXT;
                        BEGIN
                            SELECT name->>en
                            INTO result
                            FROM regions
                            WHERE id = p_id;
                            
                            RETURN result;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search regions by ar

                        CREATE OR REPLACE FUNCTION search_regions_by_ar(p_value TEXT)
                        RETURNS TABLE (
                            id TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.name
                            FROM regions t
                            WHERE t.name->>ar ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search regions by en

                        CREATE OR REPLACE FUNCTION search_regions_by_en(p_value TEXT)
                        RETURNS TABLE (
                            id TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.name
                            FROM regions t
                            WHERE t.name->>en ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search regions in multiple languages

                        CREATE OR REPLACE FUNCTION search_regions_multilingual(p_value TEXT, p_language TEXT DEFAULT 'en')
                        RETURNS TABLE (
                            id TEXT,
                            name TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.name->p_language AS name, t.name
                            FROM regions t
                            WHERE t.name->p_language ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Get name from restaurants

                        CREATE OR REPLACE FUNCTION get_restaurants_name(p_id TEXT)
                        RETURNS TEXT AS $$
                        DECLARE
                            result TEXT;
                        BEGIN
                            SELECT data->>name
                            INTO result
                            FROM restaurants
                            WHERE id = p_id;
                            
                            RETURN result;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Get description from restaurants

                        CREATE OR REPLACE FUNCTION get_restaurants_description(p_id TEXT)
                        RETURNS TEXT AS $$
                        DECLARE
                            result TEXT;
                        BEGIN
                            SELECT data->>description
                            INTO result
                            FROM restaurants
                            WHERE id = p_id;
                            
                            RETURN result;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search restaurants by name

                        CREATE OR REPLACE FUNCTION search_restaurants_by_name(p_value TEXT)
                        RETURNS TABLE (
                            id TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.data
                            FROM restaurants t
                            WHERE t.data->>name ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search restaurants by description

                        CREATE OR REPLACE FUNCTION search_restaurants_by_description(p_value TEXT)
                        RETURNS TABLE (
                            id TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.data
                            FROM restaurants t
                            WHERE t.data->>description ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Get language from sessions

                        CREATE OR REPLACE FUNCTION get_sessions_language(p_id TEXT)
                        RETURNS TEXT AS $$
                        DECLARE
                            result TEXT;
                        BEGIN
                            SELECT data->>language
                            INTO result
                            FROM sessions
                            WHERE id = p_id;
                            
                            RETURN result;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Get messages from sessions

                        CREATE OR REPLACE FUNCTION get_sessions_messages(p_id TEXT)
                        RETURNS TEXT AS $$
                        DECLARE
                            result TEXT;
                        BEGIN
                            SELECT data->>messages
                            INTO result
                            FROM sessions
                            WHERE id = p_id;
                            
                            RETURN result;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Get client_info from sessions

                        CREATE OR REPLACE FUNCTION get_sessions_client_info(p_id TEXT)
                        RETURNS TEXT AS $$
                        DECLARE
                            result TEXT;
                        BEGIN
                            SELECT data->>client_info
                            INTO result
                            FROM sessions
                            WHERE id = p_id;
                            
                            RETURN result;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Get query_topics from sessions

                        CREATE OR REPLACE FUNCTION get_sessions_query_topics(p_id TEXT)
                        RETURNS TEXT AS $$
                        DECLARE
                            result TEXT;
                        BEGIN
                            SELECT data->>query_topics
                            INTO result
                            FROM sessions
                            WHERE id = p_id;
                            
                            RETURN result;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search sessions by language

                        CREATE OR REPLACE FUNCTION search_sessions_by_language(p_value TEXT)
                        RETURNS TABLE (
                            id TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.data
                            FROM sessions t
                            WHERE t.data->>language ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search sessions by messages

                        CREATE OR REPLACE FUNCTION search_sessions_by_messages(p_value TEXT)
                        RETURNS TABLE (
                            id TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.data
                            FROM sessions t
                            WHERE t.data->>messages ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search sessions by client_info

                        CREATE OR REPLACE FUNCTION search_sessions_by_client_info(p_value TEXT)
                        RETURNS TABLE (
                            id TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.data
                            FROM sessions t
                            WHERE t.data->>client_info ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

-- Search sessions by query_topics

                        CREATE OR REPLACE FUNCTION search_sessions_by_query_topics(p_value TEXT)
                        RETURNS TABLE (
                            id TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.data
                            FROM sessions t
                            WHERE t.data->>query_topics ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    

