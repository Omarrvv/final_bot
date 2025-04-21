# Data Validation Rules

This document outlines basic validation principles for the JSON data intended to be loaded into the database (`data/` directory) and for data handled by the API.

## General Principles

- **Required Fields**: Ensure all fields marked `NOT NULL` in the `DATABASE_SCHEMA.md` are present and non-empty in the source JSON files before population.
- **Language Consistency**: If `name_en` is present, strive to provide `name_ar` and corresponding descriptions.
- **Data Types**: Values should generally match the target database column types (e.g., numbers for REAL, strings for TEXT, valid JSON for JSON fields).
- **Uniqueness**: Ensure `id` fields are unique within their respective types (attractions, accommodations, etc.). `username` and `email` in the `users` table must be unique across all users.

## Specific Field Rules

- **Coordinates (`latitude`, `longitude`)**:
  - Must be valid floating-point numbers.
  - Latitude should be within -90 to 90.
  - Longitude should be within -180 to 180.
  - Should correspond plausibly to the specified `city`/`region`.
- **Timestamps (`created_at`, `updated_at`, `expires_at`, `last_login`, `timestamp`)**:
  - Should ideally be stored in ISO 8601 format (e.g., `YYYY-MM-DDTHH:MM:SSZ` or `YYYY-MM-DD HH:MM:SS`).
- **JSON Fields (`data`)**:
  - Must contain valid JSON structures.
  - Schema within the JSON can be flexible but should aim for consistency within entity types.
- **Category/Type Fields (`attractions.type`, `accommodations.type`, `restaurants.cuisine`, `users.role`)**:
  - Should use a reasonably consistent set of values (consider defining enums or controlled vocabularies if strictness is needed).
- **Price Fields (`accommodations.price_min`, `accommodations.price_max`, `restaurants.price_range`)**:
  - Prices should be non-negative numbers.
  - `price_min` should generally be less than or equal to `price_max`.
  - `price_range` should use consistent symbols (e.g., $, $$, $$$).

## API Validation

- API endpoints should use Pydantic models (or similar) to validate request bodies, query parameters, and path parameters against expected types and constraints.
- Input sanitization should be performed where appropriate, especially for free-text fields, to prevent injection attacks.

## Future Enhancements

- Implement programmatic validation scripts to check JSON files before database population.
- Define formal JSON schemas for the `data` fields within each table type.
- Add database constraints (CHECK constraints) where appropriate.
