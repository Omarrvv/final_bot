# Egypt Tourism Chatbot - Practical Information Module

This module provides functionality to search for practical information in the Egypt Tourism Chatbot database, including currency information, emergency contacts, business hours, and more.

## Files

- `currency_info.sql`: SQL script to add currency information to the database
- `get_currency_info.py`: Script to retrieve currency information
- `search_practical_info.py`: Script to search for any practical information
- `test_practical_info.py`: Unit test for the search_practical_info method

## Setup

1. First, add the currency information to the database:

```bash
psql -U postgres -d egypt_chatbot -f currency_info.sql
```

2. Make sure the environment variable for the database connection is set:

```bash
export POSTGRES_URI="postgresql://postgres:postgres@localhost:5432/egypt_chatbot"
```

## Usage

### Get Currency Information

To retrieve currency information:

```bash
python get_currency_info.py
```

### Search for Practical Information

To search for practical information:

```bash
# List all available categories
python search_practical_info.py --list-categories

# Search by category
python search_practical_info.py --category currency

# Search by text
python search_practical_info.py --text "exchange rates"

# Search by both category and text
python search_practical_info.py --category currency --text "ATM"
```

## Implementation Details

The practical information search functionality is implemented in the `KnowledgeBase` class in `src/knowledge/knowledge_base.py`. The key methods are:

- `search_practical_info`: Searches for practical information based on query filters
- `_format_practical_info_data`: Formats practical information data from the database

The database tables used are:

- `practical_info`: Stores practical information content
- `practical_info_categories`: Stores categories for practical information

## Data Structure

Practical information is stored with the following structure:

- `id`: Unique identifier
- `category_id`: Category identifier (e.g., "currency", "emergency_contacts")
- `title`: JSON object with localized titles (e.g., `{"en": "Title in English", "ar": "Title in Arabic"}`)
- `content`: JSON object with localized content (e.g., `{"en": "Content in English", "ar": "Content in Arabic"}`)
- `related_destination_ids`: Array of destination IDs this information relates to
- `tags`: Array of tags for improved searchability
- `is_featured`: Boolean indicating if this is featured information
- `data`: Additional JSON data (optional)

## Adding New Practical Information

To add new practical information, create an SQL script similar to `currency_info.sql` with the following structure:

1. Add a new category to `practical_info_categories` if needed
2. Insert the practical information into the `practical_info` table

Example:

```sql
-- Add new category
INSERT INTO practical_info_categories (
    id,
    name,
    description,
    icon,
    created_at,
    updated_at
) VALUES (
    'new_category',
    '{"en": "New Category", "ar": "فئة جديدة"}',
    '{"en": "Description of new category", "ar": "وصف الفئة الجديدة"}',
    'icon-name',
    NOW(),
    NOW()
);

-- Insert practical info
INSERT INTO practical_info (
    category_id,
    title,
    content,
    related_destination_ids,
    tags,
    is_featured
) VALUES (
    'new_category',
    '{"en": "Title in English", "ar": "العنوان بالعربية"}',
    '{"en": "Content in English", "ar": "المحتوى بالعربية"}',
    ARRAY['egypt'],
    ARRAY['tag1', 'tag2'],
    false
);
```
