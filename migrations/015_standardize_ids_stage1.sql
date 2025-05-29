-- Migration: 015_standardize_ids_stage1.sql
-- Purpose: Standardize IDs for independent tables (Stage 1)
-- Tables: users, chat_logs, analytics_events, media, reviews, favorites, sessions

-- Begin transaction
BEGIN;

-- Create ID mapping tables
CREATE TABLE id_mapping_users (
    old_id text PRIMARY KEY,
    new_id serial NOT NULL
);

CREATE TABLE id_mapping_chat_logs (
    old_id text PRIMARY KEY,
    new_id serial NOT NULL
);

CREATE TABLE id_mapping_analytics_events (
    old_id text PRIMARY KEY,
    new_id serial NOT NULL
);

CREATE TABLE id_mapping_media (
    old_id text PRIMARY KEY,
    new_id serial NOT NULL
);

CREATE TABLE id_mapping_reviews (
    old_id text PRIMARY KEY,
    new_id serial NOT NULL
);

CREATE TABLE id_mapping_favorites (
    old_id text PRIMARY KEY,
    new_id serial NOT NULL
);

CREATE TABLE id_mapping_sessions (
    old_id text PRIMARY KEY,
    new_id serial NOT NULL
);

-- Populate mapping tables
INSERT INTO id_mapping_users (old_id)
SELECT id FROM users ORDER BY id;

INSERT INTO id_mapping_chat_logs (old_id)
SELECT id FROM chat_logs ORDER BY id;

INSERT INTO id_mapping_analytics_events (old_id)
SELECT id FROM analytics_events ORDER BY id;

INSERT INTO id_mapping_media (old_id)
SELECT id FROM media ORDER BY id;

INSERT INTO id_mapping_reviews (old_id)
SELECT id FROM reviews ORDER BY id;

INSERT INTO id_mapping_favorites (old_id)
SELECT id FROM favorites ORDER BY id;

INSERT INTO id_mapping_sessions (old_id)
SELECT id FROM sessions ORDER BY id;

-- Add new integer ID columns
ALTER TABLE users ADD COLUMN integer_id serial;
ALTER TABLE chat_logs ADD COLUMN integer_id serial;
ALTER TABLE analytics_events ADD COLUMN integer_id serial;
ALTER TABLE media ADD COLUMN integer_id serial;
ALTER TABLE reviews ADD COLUMN integer_id serial;
ALTER TABLE favorites ADD COLUMN integer_id serial;
ALTER TABLE sessions ADD COLUMN integer_id serial;

-- Update foreign key columns in related tables
-- Check if columns exist before updating

-- For sessions (if user_id exists)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'sessions' AND column_name = 'user_id'
    ) THEN
        EXECUTE '
        UPDATE sessions s
        SET user_id = (SELECT new_id FROM id_mapping_users WHERE old_id = s.user_id)
        WHERE user_id IS NOT NULL;
        ';
    END IF;
END $$;

-- Modify column types for foreign keys (if they exist)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'sessions' AND column_name = 'user_id'
    ) THEN
        EXECUTE 'ALTER TABLE sessions ALTER COLUMN user_id TYPE integer USING user_id::integer;';
    END IF;
END $$;

-- Drop old primary key constraints
ALTER TABLE users DROP CONSTRAINT users_pkey;
ALTER TABLE chat_logs DROP CONSTRAINT chat_logs_pkey;
ALTER TABLE analytics_events DROP CONSTRAINT analytics_events_pkey;
ALTER TABLE media DROP CONSTRAINT media_pkey;
ALTER TABLE reviews DROP CONSTRAINT reviews_pkey;
ALTER TABLE favorites DROP CONSTRAINT favorites_pkey;
ALTER TABLE sessions DROP CONSTRAINT sessions_pkey;

-- Rename ID columns
ALTER TABLE users DROP COLUMN id;
ALTER TABLE users RENAME COLUMN integer_id TO id;

ALTER TABLE chat_logs DROP COLUMN id;
ALTER TABLE chat_logs RENAME COLUMN integer_id TO id;

ALTER TABLE analytics_events DROP COLUMN id;
ALTER TABLE analytics_events RENAME COLUMN integer_id TO id;

ALTER TABLE media DROP COLUMN id;
ALTER TABLE media RENAME COLUMN integer_id TO id;

ALTER TABLE reviews DROP COLUMN id;
ALTER TABLE reviews RENAME COLUMN integer_id TO id;

ALTER TABLE favorites DROP COLUMN id;
ALTER TABLE favorites RENAME COLUMN integer_id TO id;

ALTER TABLE sessions DROP COLUMN id;
ALTER TABLE sessions RENAME COLUMN integer_id TO id;

-- Add primary key constraints
ALTER TABLE users ADD PRIMARY KEY (id);
ALTER TABLE chat_logs ADD PRIMARY KEY (id);
ALTER TABLE analytics_events ADD PRIMARY KEY (id);
ALTER TABLE media ADD PRIMARY KEY (id);
ALTER TABLE reviews ADD PRIMARY KEY (id);
ALTER TABLE favorites ADD PRIMARY KEY (id);
ALTER TABLE sessions ADD PRIMARY KEY (id);

-- Add foreign key constraints (if they exist)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'sessions' AND column_name = 'user_id'
    ) THEN
        EXECUTE '
        ALTER TABLE sessions
        ADD CONSTRAINT sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL;
        ';
    END IF;
END $$;

-- Clean up mapping tables
DROP TABLE id_mapping_users;
DROP TABLE id_mapping_chat_logs;
DROP TABLE id_mapping_analytics_events;
DROP TABLE id_mapping_media;
DROP TABLE id_mapping_reviews;
DROP TABLE id_mapping_favorites;
DROP TABLE id_mapping_sessions;

-- Commit transaction
COMMIT;
