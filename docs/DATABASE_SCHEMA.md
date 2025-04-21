# Database Schema (SQLite)

This document outlines the schema for the SQLite database (`data/egypt_chatbot.db`) as defined in `init_db.py`.

## Tables

### 1. `attractions`

Stores information about tourist attractions.

| Column           | Type | Constraints | Description                                    |
| ---------------- | ---- | ----------- | ---------------------------------------------- |
| `id`             | TEXT | PRIMARY KEY | Unique identifier (e.g., slug or UUID)         |
| `name_en`        | TEXT | NOT NULL    | English name of the attraction                 |
| `name_ar`        | TEXT |             | Arabic name of the attraction                  |
| `type`           | TEXT |             | Type/category (e.g., historical, museum, park) |
| `city`           | TEXT |             | City where the attraction is located           |
| `region`         | TEXT |             | Broader region or governorate                  |
| `latitude`       | REAL |             | Latitude coordinate                            |
| `longitude`      | REAL |             | Longitude coordinate                           |
| `description_en` | TEXT |             | English description                            |
| `description_ar` | TEXT |             | Arabic description                             |
| `data`           | JSON |             | Flexible JSON field for additional attributes  |
| `created_at`     | TEXT |             | Record creation timestamp (ISO 8601 format)    |
| `updated_at`     | TEXT |             | Record last update timestamp (ISO 8601 format) |

**Indexes**: `type`, `city`

### 2. `accommodations`

Stores information about hotels, resorts, etc.

| Column           | Type | Constraints | Description                                    |
| ---------------- | ---- | ----------- | ---------------------------------------------- |
| `id`             | TEXT | PRIMARY KEY | Unique identifier                              |
| `name_en`        | TEXT | NOT NULL    | English name                                   |
| `name_ar`        | TEXT |             | Arabic name                                    |
| `type`           | TEXT |             | Type (e.g., hotel, resort, guesthouse)         |
| `category`       | TEXT |             | Star rating or category (e.g., 5-star, budget) |
| `city`           | TEXT |             | City location                                  |
| `region`         | TEXT |             | Broader region                                 |
| `latitude`       | REAL |             | Latitude coordinate                            |
| `longitude`      | REAL |             | Longitude coordinate                           |
| `description_en` | TEXT |             | English description                            |
| `description_ar` | TEXT |             | Arabic description                             |
| `price_min`      | REAL |             | Minimum price (approximate)                    |
| `price_max`      | REAL |             | Maximum price (approximate)                    |
| `data`           | JSON |             | Flexible JSON field (amenities, contact, etc.) |
| `created_at`     | TEXT |             | Record creation timestamp                      |
| `updated_at`     | TEXT |             | Record last update timestamp                   |

**Indexes**: `type`, `city`

### 3. `restaurants`

Stores information about dining options.

| Column           | Type | Constraints | Description                                  |
| ---------------- | ---- | ----------- | -------------------------------------------- |
| `id`             | TEXT | PRIMARY KEY | Unique identifier                            |
| `name_en`        | TEXT | NOT NULL    | English name                                 |
| `name_ar`        | TEXT |             | Arabic name                                  |
| `cuisine`        | TEXT |             | Type of cuisine (e.g., Egyptian, Italian)    |
| `city`           | TEXT |             | City location                                |
| `region`         | TEXT |             | Broader region                               |
| `latitude`       | REAL |             | Latitude coordinate                          |
| `longitude`      | REAL |             | Longitude coordinate                         |
| `description_en` | TEXT |             | English description                          |
| `description_ar` | TEXT |             | Arabic description                           |
| `price_range`    | TEXT |             | Price category (e.g., $, $$, $$$)            |
| `data`           | JSON |             | Flexible JSON field (menu highlights, hours) |
| `created_at`     | TEXT |             | Record creation timestamp                    |
| `updated_at`     | TEXT |             | Record last update timestamp                 |

**Indexes**: `city`, `cuisine`

### 4. `sessions`

Stores user session data.

| Column       | Type | Constraints | Description                                     |
| ------------ | ---- | ----------- | ----------------------------------------------- |
| `id`         | TEXT | PRIMARY KEY | Unique session identifier                       |
| `data`       | JSON |             | Session state data (conversation history, etc.) |
| `created_at` | TEXT |             | Session creation timestamp                      |
| `updated_at` | TEXT |             | Session last update timestamp                   |
| `expires_at` | TEXT |             | Session expiration timestamp                    |

**Indexes**: `expires_at`

### 5. `users`

Stores user account information.

| Column          | Type | Constraints      | Description                          |
| --------------- | ---- | ---------------- | ------------------------------------ |
| `id`            | TEXT | PRIMARY KEY      | Unique user identifier               |
| `username`      | TEXT | UNIQUE, NOT NULL | User login name                      |
| `email`         | TEXT | UNIQUE           | User email address                   |
| `password_hash` | TEXT | NOT NULL         | Hashed user password                 |
| `salt`          | TEXT | NOT NULL         | Salt used for password hashing       |
| `role`          | TEXT |                  | User role (e.g., user, admin)        |
| `data`          | JSON |                  | Flexible JSON field for profile info |
| `created_at`    | TEXT |                  | Account creation timestamp           |
| `last_login`    | TEXT |                  | Last login timestamp                 |

**Indexes**: `username`

### 6. `analytics`

Stores event data for analytics.

| Column       | Type | Constraints | Description                                  |
| ------------ | ---- | ----------- | -------------------------------------------- |
| `id`         | TEXT | PRIMARY KEY | Unique event identifier                      |
| `session_id` | TEXT |             | Associated session ID                        |
| `user_id`    | TEXT |             | Associated user ID (if logged in)            |
| `event_type` | TEXT |             | Type of event (e.g., message, intent, error) |
| `event_data` | JSON |             | Details of the event                         |
| `timestamp`  | TEXT |             | Event timestamp                              |

**Indexes**: `timestamp`, `event_type`, `session_id`, `user_id`
