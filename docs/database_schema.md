# Egypt Tourism Chatbot Database Schema Documentation

## Overview

The Egypt Tourism Chatbot database is designed to store comprehensive information about Egyptian tourism, including attractions, accommodations, restaurants, destinations, transportation options, events, and practical travel information. The database uses PostgreSQL with PostGIS for spatial data and pgvector for vector embeddings to support semantic search.

## Core Design Principles

1. **Multilingual Support**: All content-related fields use JSONB columns to store multilingual text (primarily English and Arabic).
2. **Vector Search**: All major entities have embedding columns for semantic search capabilities.
3. **Hierarchical Structure**: Destinations and attractions follow a hierarchical structure to represent geographic relationships.
4. **Cross-References**: Entities are interconnected through foreign key relationships to enable complex queries.
5. **Extensibility**: JSONB data columns allow for flexible schema evolution without requiring structural changes.

## Database Tables

### Core Tourism Entities

#### attractions

Stores information about tourist attractions in Egypt.

| Column         | Type      | Description                                |
| -------------- | --------- | ------------------------------------------ |
| id             | integer   | Primary key                                |
| name           | jsonb     | Multilingual name of the attraction        |
| description    | jsonb     | Multilingual description of the attraction |
| type_id        | text      | Foreign key to attraction_types            |
| city_id        | text      | Foreign key to cities (legacy)             |
| region_id      | text      | Foreign key to destinations                |
| location       | geometry  | Geographic coordinates (PostGIS Point)     |
| address        | jsonb     | Multilingual address information           |
| opening_hours  | jsonb     | Opening hours information                  |
| admission_fees | jsonb     | Admission fees information                 |
| accessibility  | jsonb     | Accessibility information                  |
| contact_info   | jsonb     | Contact information                        |
| images         | jsonb     | Image URLs and metadata                    |
| rating         | float     | Average rating (0-5)                       |
| reviews        | jsonb     | User reviews                               |
| tags           | text[]    | Array of tags for categorization           |
| is_featured    | boolean   | Whether the attraction is featured         |
| view_count     | integer   | Number of views/queries                    |
| data           | jsonb     | Additional flexible data                   |
| embedding      | vector    | Vector embedding for semantic search       |
| created_at     | timestamp | Creation timestamp                         |
| updated_at     | timestamp | Last update timestamp                      |
| user_id        | text      | Creator/owner reference                    |

#### accommodations

Stores information about hotels, resorts, and other lodging options.

| Column       | Type      | Description                            |
| ------------ | --------- | -------------------------------------- |
| id           | integer   | Primary key                            |
| name         | jsonb     | Multilingual name of the accommodation |
| description  | jsonb     | Multilingual description               |
| type_id      | text      | Foreign key to accommodation_types     |
| city_id      | text      | Foreign key to cities (legacy)         |
| region_id    | text      | Foreign key to destinations            |
| location     | geometry  | Geographic coordinates (PostGIS Point) |
| address      | jsonb     | Multilingual address information       |
| amenities    | jsonb     | Available amenities                    |
| price_range  | jsonb     | Price range information                |
| contact_info | jsonb     | Contact information                    |
| booking_info | jsonb     | Booking information and links          |
| images       | jsonb     | Image URLs and metadata                |
| rating       | float     | Average rating (0-5)                   |
| reviews      | jsonb     | User reviews                           |
| tags         | text[]    | Array of tags for categorization       |
| is_featured  | boolean   | Whether the accommodation is featured  |
| view_count   | integer   | Number of views/queries                |
| data         | jsonb     | Additional flexible data               |
| embedding    | vector    | Vector embedding for semantic search   |
| created_at   | timestamp | Creation timestamp                     |
| updated_at   | timestamp | Last update timestamp                  |
| user_id      | text      | Creator/owner reference                |

#### restaurants

Stores information about restaurants, cafes, and dining options.

| Column           | Type      | Description                                      |
| ---------------- | --------- | ------------------------------------------------ |
| id               | integer   | Primary key                                      |
| name             | jsonb     | Multilingual name of the restaurant              |
| description      | jsonb     | Multilingual description                         |
| cuisine_type     | jsonb     | Type of cuisine                                  |
| city_id          | text      | Foreign key to cities (legacy)                   |
| region_id        | text      | Foreign key to destinations                      |
| location         | geometry  | Geographic coordinates (PostGIS Point)           |
| address          | jsonb     | Multilingual address information                 |
| opening_hours    | jsonb     | Opening hours information                        |
| price_range      | jsonb     | Price range information                          |
| menu             | jsonb     | Menu information                                 |
| dietary_options  | jsonb     | Dietary accommodations (vegetarian, halal, etc.) |
| contact_info     | jsonb     | Contact information                              |
| reservation_info | jsonb     | Reservation information                          |
| images           | jsonb     | Image URLs and metadata                          |
| rating           | float     | Average rating (0-5)                             |
| reviews          | jsonb     | User reviews                                     |
| tags             | text[]    | Array of tags for categorization                 |
| is_featured      | boolean   | Whether the restaurant is featured               |
| view_count       | integer   | Number of views/queries                          |
| data             | jsonb     | Additional flexible data                         |
| embedding        | vector    | Vector embedding for semantic search             |
| created_at       | timestamp | Creation timestamp                               |
| updated_at       | timestamp | Last update timestamp                            |
| user_id          | text      | Creator/owner reference                          |

#### destinations

Hierarchical structure for geographic locations (regions, cities, districts).

| Column              | Type      | Description                                           |
| ------------------- | --------- | ----------------------------------------------------- |
| id                  | text      | Primary key (slug format)                             |
| name                | jsonb     | Multilingual name of the destination                  |
| description         | jsonb     | Multilingual description                              |
| type                | text      | Type of destination (country, region, city, district) |
| parent_id           | text      | Foreign key to parent destination                     |
| location            | geometry  | Geographic coordinates (PostGIS Point)                |
| boundaries          | geometry  | Geographic boundaries (PostGIS Polygon)               |
| population          | integer   | Population count                                      |
| climate             | jsonb     | Climate information                                   |
| best_time_to_visit  | jsonb     | Recommended visiting times                            |
| local_customs       | jsonb     | Information about local customs                       |
| transportation_info | jsonb     | Local transportation information                      |
| images              | jsonb     | Image URLs and metadata                               |
| tags                | text[]    | Array of tags for categorization                      |
| is_featured         | boolean   | Whether the destination is featured                   |
| view_count          | integer   | Number of views/queries                               |
| data                | jsonb     | Additional flexible data                              |
| embedding           | vector    | Vector embedding for semantic search                  |
| created_at          | timestamp | Creation timestamp                                    |
| updated_at          | timestamp | Last update timestamp                                 |
| user_id             | text      | Creator/owner reference                               |

### Tourism Information Tables

#### tourism_faqs

Stores frequently asked questions about Egyptian tourism.

| Column      | Type      | Description                          |
| ----------- | --------- | ------------------------------------ |
| id          | integer   | Primary key                          |
| category_id | text      | Foreign key to faq_categories        |
| question    | jsonb     | Multilingual question text           |
| answer      | jsonb     | Multilingual answer text             |
| tags        | text[]    | Array of tags for categorization     |
| is_featured | boolean   | Whether the FAQ is featured          |
| view_count  | integer   | Number of views/queries              |
| data        | jsonb     | Additional flexible data             |
| embedding   | vector    | Vector embedding for semantic search |
| created_at  | timestamp | Creation timestamp                   |
| updated_at  | timestamp | Last update timestamp                |
| user_id     | text      | Creator/owner reference              |

#### practical_info

Stores practical travel information for tourists.

| Column      | Type      | Description                                      |
| ----------- | --------- | ------------------------------------------------ |
| id          | integer   | Primary key                                      |
| category_id | text      | Foreign key to practical_info_categories         |
| title       | jsonb     | Multilingual title                               |
| content     | jsonb     | Multilingual content                             |
| region_id   | text      | Foreign key to destinations (if region-specific) |
| valid_from  | date      | Start date of validity                           |
| valid_until | date      | End date of validity                             |
| importance  | integer   | Importance level (1-5)                           |
| tags        | text[]    | Array of tags for categorization                 |
| is_featured | boolean   | Whether the information is featured              |
| view_count  | integer   | Number of views/queries                          |
| data        | jsonb     | Additional flexible data                         |
| embedding   | vector    | Vector embedding for semantic search             |
| created_at  | timestamp | Creation timestamp                               |
| updated_at  | timestamp | Last update timestamp                            |
| user_id     | text      | Creator/owner reference                          |

#### transportation_routes

Stores information about transportation options between destinations.

| Column         | Type      | Description                                    |
| -------------- | --------- | ---------------------------------------------- |
| id             | integer   | Primary key                                    |
| type           | text      | Type of transportation (air, train, bus, boat) |
| origin_id      | text      | Foreign key to destinations (origin)           |
| destination_id | text      | Foreign key to destinations (destination)      |
| name           | jsonb     | Multilingual name/number of the route          |
| description    | jsonb     | Multilingual description                       |
| schedule       | jsonb     | Schedule information                           |
| duration       | jsonb     | Duration information                           |
| price_range    | jsonb     | Price range information                        |
| booking_info   | jsonb     | Booking information                            |
| operator       | jsonb     | Operator information                           |
| amenities      | jsonb     | Available amenities                            |
| route_map      | jsonb     | Route map information                          |
| tags           | text[]    | Array of tags for categorization               |
| is_featured    | boolean   | Whether the route is featured                  |
| view_count     | integer   | Number of views/queries                        |
| data           | jsonb     | Additional flexible data                       |
| embedding      | vector    | Vector embedding for semantic search           |
| created_at     | timestamp | Creation timestamp                             |
| updated_at     | timestamp | Last update timestamp                          |
| user_id        | text      | Creator/owner reference                        |

#### tour_packages

Stores information about available tour packages.

| Column               | Type      | Description                            |
| -------------------- | --------- | -------------------------------------- |
| id                   | integer   | Primary key                            |
| category_id          | text      | Foreign key to tour_package_categories |
| name                 | jsonb     | Multilingual name of the tour package  |
| description          | jsonb     | Multilingual description               |
| duration_days        | integer   | Duration in days                       |
| price_range          | jsonb     | Price range information                |
| included_services    | jsonb     | Services included in the package       |
| excluded_services    | jsonb     | Services excluded from the package     |
| itinerary            | jsonb     | Detailed itinerary                     |
| destinations         | text[]    | Array of destination IDs               |
| attractions          | text[]    | Array of attraction IDs                |
| accommodations       | text[]    | Array of accommodation IDs             |
| transportation_types | text[]    | Array of transportation types          |
| min_group_size       | integer   | Minimum group size                     |
| max_group_size       | integer   | Maximum group size                     |
| difficulty_level     | text      | Difficulty level                       |
| accessibility_info   | jsonb     | Accessibility information              |
| seasonal_info        | jsonb     | Seasonal availability information      |
| booking_info         | jsonb     | Booking information                    |
| cancellation_policy  | jsonb     | Cancellation policy                    |
| reviews              | jsonb     | User reviews                           |
| rating               | float     | Average rating (0-5)                   |
| images               | jsonb     | Image URLs and metadata                |
| tags                 | text[]    | Array of tags for categorization       |
| is_featured          | boolean   | Whether the package is featured        |
| is_private           | boolean   | Whether it's a private tour            |
| view_count           | integer   | Number of views/queries                |
| data                 | jsonb     | Additional flexible data               |
| embedding            | vector    | Vector embedding for semantic search   |
| created_at           | timestamp | Creation timestamp                     |
| updated_at           | timestamp | Last update timestamp                  |
| user_id              | text      | Creator/owner reference                |

#### events_festivals

Stores information about events and festivals in Egypt.

| Column                  | Type      | Description                          |
| ----------------------- | --------- | ------------------------------------ |
| id                      | integer   | Primary key                          |
| category_id             | text      | Foreign key to event_categories      |
| name                    | jsonb     | Multilingual name of the event       |
| description             | jsonb     | Multilingual description             |
| start_date              | date      | Start date                           |
| end_date                | date      | End date                             |
| is_annual               | boolean   | Whether the event occurs annually    |
| annual_month            | integer   | Month of annual occurrence (1-12)    |
| annual_day              | integer   | Day of annual occurrence (1-31)      |
| lunar_calendar          | boolean   | Whether dates follow lunar calendar  |
| location_description    | jsonb     | Multilingual location description    |
| destination_id          | text      | Foreign key to destinations          |
| venue                   | jsonb     | Venue information                    |
| organizer               | jsonb     | Organizer information                |
| admission               | jsonb     | Admission information                |
| schedule                | jsonb     | Event schedule                       |
| highlights              | jsonb     | Event highlights                     |
| historical_significance | jsonb     | Historical significance              |
| tips                    | jsonb     | Tips for attendees                   |
| images                  | jsonb     | Image URLs and metadata              |
| website                 | text      | Event website                        |
| contact_info            | jsonb     | Contact information                  |
| tags                    | text[]    | Array of tags for categorization     |
| is_featured             | boolean   | Whether the event is featured        |
| view_count              | integer   | Number of views/queries              |
| data                    | jsonb     | Additional flexible data             |
| embedding               | vector    | Vector embedding for semantic search |
| created_at              | timestamp | Creation timestamp                   |
| updated_at              | timestamp | Last update timestamp                |
| user_id                 | text      | Creator/owner reference              |

### Lookup Tables

- **attraction_types**: Types of attractions (monument, museum, park, etc.)
- **accommodation_types**: Types of accommodations (hotel, resort, hostel, etc.)
- **faq_categories**: Categories for tourism FAQs
- **practical_info_categories**: Categories for practical information
- **tour_package_categories**: Categories for tour packages
- **event_categories**: Categories for events and festivals

### Legacy Tables

- **cities**: Legacy table for cities (replaced by destinations)
- **regions**: Legacy table for regions (replaced by destinations)

## Database Relationships

The database uses foreign key constraints to maintain referential integrity between tables:

1. **Hierarchical Relationships**:

   - destinations.parent_id → destinations.id (self-referential)

2. **Entity Relationships**:
   - attractions.type_id → attraction_types.id
   - attractions.region_id → destinations.id
   - accommodations.type_id → accommodation_types.id
   - accommodations.region_id → destinations.id
   - restaurants.region_id → destinations.id
   - tourism_faqs.category_id → faq_categories.id
   - practical_info.category_id → practical_info_categories.id
   - transportation_routes.origin_id → destinations.id
   - transportation_routes.destination_id → destinations.id
   - tour_packages.category_id → tour_package_categories.id
   - events_festivals.category_id → event_categories.id
   - events_festivals.destination_id → destinations.id

### Foreign Key Constraint Strategy

The database follows a consistent strategy for foreign key constraints:

1. **Category References** (e.g., category_id columns):

   - **ON DELETE CASCADE**: If a category is deleted, all associated records are deleted.
   - **ON UPDATE CASCADE**: If a category ID is updated, all references are updated accordingly.
   - **Rationale**: Categories are tightly coupled with their records; orphaned records without categories are not useful.

2. **Hierarchical References** (e.g., parent_id columns):

   - **ON DELETE RESTRICT**: Prevents deletion of parent records that have children.
   - **ON UPDATE CASCADE**: If a parent ID is updated, all references are updated accordingly.
   - **Rationale**: Maintains hierarchical integrity while allowing reorganization.

3. **Entity References** (e.g., destination_id, region_id columns):
   - **ON DELETE RESTRICT**: Prevents deletion of referenced entities that are being used.
   - **ON UPDATE CASCADE**: If an entity ID is updated, all references are updated accordingly.
   - **Rationale**: Prevents accidental data loss while allowing entity ID changes to propagate.

## Indexes

The database uses several types of indexes to optimize query performance:

1. **B-tree Indexes**: Standard indexes on primary keys and foreign keys
2. **GIN Indexes**: For JSONB columns to enable efficient text search
3. **GiST Indexes**: For spatial data (PostGIS geometry columns)
4. **HNSW Indexes**: For vector columns to enable efficient similarity search

## Vector Search

The database uses pgvector with HNSW indexes for semantic search:

- All major entities have an `embedding` column of type `vector(1536)` to store embeddings
- HNSW indexes are configured with optimal parameters (m=16, ef_construction=64)
- The application uses hybrid search combining vector similarity and text matching

## Multilingual Support

All content-related fields use JSONB columns with language codes as keys:

```json
{
  "en": "English text",
  "ar": "النص العربي"
}
```

This approach allows for:

- Adding new languages without schema changes
- Efficient querying of specific languages
- Fallback mechanisms when content is not available in a requested language

## Data Validation

The database relies on application-level validation to ensure:

- JSONB structures follow expected patterns
- Required language keys are present
- Foreign key references exist before insertion
- Embeddings have the correct dimension (1536)

## Migration History

Database migrations are tracked in the `schema_migrations` table, which records:

- Migration version
- Migration name
- Application timestamp
- Status (success/failure)

## Conclusion

This schema documentation provides a comprehensive overview of the Egypt Tourism Chatbot database structure. The design prioritizes flexibility, multilingual support, and efficient semantic search capabilities to deliver a high-quality tourism information system.
