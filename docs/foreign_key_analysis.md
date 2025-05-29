# Foreign Key Relationship Analysis

This document analyzes the foreign key relationships in the Egypt Tourism Chatbot database and recommends appropriate ON DELETE and ON UPDATE actions for each constraint.

## Current Configuration

All foreign key constraints currently use:
- ON DELETE SET NULL
- ON UPDATE CASCADE (except cities.user_id which uses ON UPDATE NO ACTION)

## Relationship Analysis

### attractions.city_id → cities.id

**Relationship Type**: Many-to-One (Many attractions can belong to one city)

**Current Actions**:
- ON DELETE SET NULL
- ON UPDATE CASCADE

**Analysis**:
- If a city is deleted, should the attractions be deleted too? No, they should be preserved but disassociated from the city.
- If a city's ID is updated, should the attractions' city_id be updated too? Yes, to maintain referential integrity.

**Recommendation**:
- ON DELETE SET NULL (Keep current)
- ON UPDATE CASCADE (Keep current)

### attractions.region_id → regions.id

**Relationship Type**: Many-to-One (Many attractions can belong to one region)

**Current Actions**:
- ON DELETE SET NULL
- ON UPDATE CASCADE

**Analysis**:
- If a region is deleted, should the attractions be deleted too? No, they should be preserved but disassociated from the region.
- If a region's ID is updated, should the attractions' region_id be updated too? Yes, to maintain referential integrity.

**Recommendation**:
- ON DELETE SET NULL (Keep current)
- ON UPDATE CASCADE (Keep current)

### attractions.type_id → attraction_types.type

**Relationship Type**: Many-to-One (Many attractions can have one type)

**Current Actions**:
- ON DELETE SET NULL
- ON UPDATE CASCADE

**Analysis**:
- If an attraction type is deleted, should the attractions be deleted too? No, but attraction types are fundamental categories that should rarely be deleted.
- Setting to NULL would leave attractions without a type, which is not ideal.

**Recommendation**:
- ON DELETE RESTRICT (Change from SET NULL)
- ON UPDATE CASCADE (Keep current)

### accommodations.city_id → cities.id

**Relationship Type**: Many-to-One (Many accommodations can belong to one city)

**Current Actions**:
- ON DELETE SET NULL
- ON UPDATE CASCADE

**Analysis**:
- If a city is deleted, should the accommodations be deleted too? No, they should be preserved but disassociated from the city.
- If a city's ID is updated, should the accommodations' city_id be updated too? Yes, to maintain referential integrity.

**Recommendation**:
- ON DELETE SET NULL (Keep current)
- ON UPDATE CASCADE (Keep current)

### accommodations.region_id → regions.id

**Relationship Type**: Many-to-One (Many accommodations can belong to one region)

**Current Actions**:
- ON DELETE SET NULL
- ON UPDATE CASCADE

**Analysis**:
- If a region is deleted, should the accommodations be deleted too? No, they should be preserved but disassociated from the region.
- If a region's ID is updated, should the accommodations' region_id be updated too? Yes, to maintain referential integrity.

**Recommendation**:
- ON DELETE SET NULL (Keep current)
- ON UPDATE CASCADE (Keep current)

### accommodations.type_id → accommodation_types.type

**Relationship Type**: Many-to-One (Many accommodations can have one type)

**Current Actions**:
- ON DELETE SET NULL
- ON UPDATE CASCADE

**Analysis**:
- If an accommodation type is deleted, should the accommodations be deleted too? No, but accommodation types are fundamental categories that should rarely be deleted.
- Setting to NULL would leave accommodations without a type, which is not ideal.

**Recommendation**:
- ON DELETE RESTRICT (Change from SET NULL)
- ON UPDATE CASCADE (Keep current)

### cities.region_id → regions.id

**Relationship Type**: Many-to-One (Many cities can belong to one region)

**Current Actions**:
- ON DELETE SET NULL
- ON UPDATE CASCADE

**Analysis**:
- If a region is deleted, should the cities be deleted too? No, they should be preserved but disassociated from the region.
- If a region's ID is updated, should the cities' region_id be updated too? Yes, to maintain referential integrity.

**Recommendation**:
- ON DELETE SET NULL (Keep current)
- ON UPDATE CASCADE (Keep current)

### cities.user_id → users.id

**Relationship Type**: Many-to-One (Many cities can be created by one user)

**Current Actions**:
- ON DELETE SET NULL
- ON UPDATE NO ACTION

**Analysis**:
- If a user is deleted, should the cities they created be deleted too? No, they should be preserved.
- If a user's ID is updated, should the cities' user_id be updated too? Yes, to maintain referential integrity.

**Recommendation**:
- ON DELETE SET NULL (Keep current)
- ON UPDATE CASCADE (Change from NO ACTION)

## Summary of Recommended Changes

1. **attractions.type_id → attraction_types.type**:
   - Change ON DELETE from SET NULL to RESTRICT

2. **accommodations.type_id → accommodation_types.type**:
   - Change ON DELETE from SET NULL to RESTRICT

3. **cities.user_id → users.id**:
   - Change ON UPDATE from NO ACTION to CASCADE
