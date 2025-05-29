-- Migration to refactor array relationships to junction tables
-- This script creates junction tables for complex relationships

-- Create junction table for attractions.related_attractions
CREATE TABLE attraction_relationships (
    id SERIAL PRIMARY KEY,
    attraction_id INTEGER NOT NULL REFERENCES attractions(id) ON DELETE CASCADE,
    related_attraction_id INTEGER NOT NULL REFERENCES attractions(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) DEFAULT 'related',
    description JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(attraction_id, related_attraction_id)
);

CREATE INDEX idx_attraction_relationships_attraction_id ON attraction_relationships(attraction_id);
CREATE INDEX idx_attraction_relationships_related_attraction_id ON attraction_relationships(related_attraction_id);

-- Create junction table for itineraries.attractions
CREATE TABLE itinerary_attractions (
    id SERIAL PRIMARY KEY,
    itinerary_id INTEGER NOT NULL REFERENCES itineraries(id) ON DELETE CASCADE,
    attraction_id INTEGER NOT NULL REFERENCES attractions(id) ON DELETE CASCADE,
    order_index INTEGER NOT NULL,
    day_number INTEGER,
    visit_duration INTEGER, -- in minutes
    notes JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(itinerary_id, attraction_id, day_number)
);

CREATE INDEX idx_itinerary_attractions_itinerary_id ON itinerary_attractions(itinerary_id);
CREATE INDEX idx_itinerary_attractions_attraction_id ON itinerary_attractions(attraction_id);

-- Create junction table for itineraries.cities
CREATE TABLE itinerary_cities (
    id SERIAL PRIMARY KEY,
    itinerary_id INTEGER NOT NULL REFERENCES itineraries(id) ON DELETE CASCADE,
    city_id INTEGER NOT NULL REFERENCES cities(id) ON DELETE CASCADE,
    order_index INTEGER NOT NULL,
    stay_duration INTEGER, -- in days
    notes JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(itinerary_id, city_id)
);

CREATE INDEX idx_itinerary_cities_itinerary_id ON itinerary_cities(itinerary_id);
CREATE INDEX idx_itinerary_cities_city_id ON itinerary_cities(city_id);

-- Create junction table for tour_packages.attractions
CREATE TABLE tour_package_attractions (
    id SERIAL PRIMARY KEY,
    tour_package_id INTEGER NOT NULL REFERENCES tour_packages(id) ON DELETE CASCADE,
    attraction_id INTEGER NOT NULL REFERENCES attractions(id) ON DELETE CASCADE,
    order_index INTEGER NOT NULL,
    day_number INTEGER,
    visit_duration INTEGER, -- in minutes
    notes JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tour_package_id, attraction_id, day_number)
);

CREATE INDEX idx_tour_package_attractions_tour_package_id ON tour_package_attractions(tour_package_id);
CREATE INDEX idx_tour_package_attractions_attraction_id ON tour_package_attractions(attraction_id);

-- Create junction table for tour_packages.destinations
CREATE TABLE tour_package_destinations (
    id SERIAL PRIMARY KEY,
    tour_package_id INTEGER NOT NULL REFERENCES tour_packages(id) ON DELETE CASCADE,
    destination_id INTEGER NOT NULL REFERENCES destinations(id) ON DELETE CASCADE,
    order_index INTEGER NOT NULL,
    stay_duration INTEGER, -- in days
    notes JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tour_package_id, destination_id)
);

CREATE INDEX idx_tour_package_destinations_tour_package_id ON tour_package_destinations(tour_package_id);
CREATE INDEX idx_tour_package_destinations_destination_id ON tour_package_destinations(destination_id);

-- Create junction table for practical_info.related_destination_ids
CREATE TABLE practical_info_destinations (
    id SERIAL PRIMARY KEY,
    practical_info_id INTEGER NOT NULL REFERENCES practical_info(id) ON DELETE CASCADE,
    destination_id INTEGER NOT NULL REFERENCES destinations(id) ON DELETE CASCADE,
    relevance_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(practical_info_id, destination_id)
);

CREATE INDEX idx_practical_info_destinations_practical_info_id ON practical_info_destinations(practical_info_id);
CREATE INDEX idx_practical_info_destinations_destination_id ON practical_info_destinations(destination_id);

-- Create junction table for tourism_faqs.related_destination_ids
CREATE TABLE tourism_faq_destinations (
    id SERIAL PRIMARY KEY,
    tourism_faq_id INTEGER NOT NULL REFERENCES tourism_faqs(id) ON DELETE CASCADE,
    destination_id INTEGER NOT NULL REFERENCES destinations(id) ON DELETE CASCADE,
    relevance_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tourism_faq_id, destination_id)
);

CREATE INDEX idx_tourism_faq_destinations_tourism_faq_id ON tourism_faq_destinations(tourism_faq_id);
CREATE INDEX idx_tourism_faq_destinations_destination_id ON tourism_faq_destinations(destination_id);

-- Note: Data migration from arrays to junction tables would be done in a separate script
-- as it requires application logic to handle the conversion
