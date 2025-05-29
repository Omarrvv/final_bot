-- Rollback: 015_standardize_ids_stage1.sql
-- Purpose: Rollback ID standardization for Stage 1 tables
-- Tables: users, chat_logs, analytics_events, media, reviews, favorites, sessions

-- Begin transaction
BEGIN;

-- Create temporary mapping tables to preserve relationships
CREATE TABLE temp_id_mapping_users (
    integer_id integer PRIMARY KEY,
    text_id text NOT NULL
);

-- Populate mapping tables with current integer IDs and generated text IDs
INSERT INTO temp_id_mapping_users (integer_id, text_id)
SELECT id, 'user_' || id FROM users;

-- Add text ID columns to tables
ALTER TABLE users ADD COLUMN text_id text;
ALTER TABLE chat_logs ADD COLUMN text_id text;
ALTER TABLE analytics_events ADD COLUMN text_id text;
ALTER TABLE media ADD COLUMN text_id text;
ALTER TABLE reviews ADD COLUMN text_id text;
ALTER TABLE favorites ADD COLUMN text_id text;
ALTER TABLE sessions ADD COLUMN text_id text;

-- Populate text ID columns
UPDATE users SET text_id = 'user_' || id;
UPDATE chat_logs SET text_id = 'chat_' || id;
UPDATE analytics_events SET text_id = 'event_' || id;
UPDATE media SET text_id = 'media_' || id;
UPDATE reviews SET text_id = 'review_' || id;
UPDATE favorites SET text_id = 'fav_' || id;
UPDATE sessions SET text_id = 'session_' || id;

-- Update foreign key columns in related tables
-- For chat_logs
ALTER TABLE chat_logs ADD COLUMN text_user_id text;
UPDATE chat_logs c
SET text_user_id = (SELECT text_id FROM temp_id_mapping_users WHERE integer_id = c.user_id)
WHERE user_id IS NOT NULL;

-- For media
ALTER TABLE media ADD COLUMN text_user_id text;
UPDATE media m
SET text_user_id = (SELECT text_id FROM temp_id_mapping_users WHERE integer_id = m.user_id)
WHERE user_id IS NOT NULL;

-- For reviews
ALTER TABLE reviews ADD COLUMN text_user_id text;
UPDATE reviews r
SET text_user_id = (SELECT text_id FROM temp_id_mapping_users WHERE integer_id = r.user_id)
WHERE user_id IS NOT NULL;

-- For favorites
ALTER TABLE favorites ADD COLUMN text_user_id text;
UPDATE favorites f
SET text_user_id = (SELECT text_id FROM temp_id_mapping_users WHERE integer_id = f.user_id)
WHERE user_id IS NOT NULL;

-- For sessions
ALTER TABLE sessions ADD COLUMN text_user_id text;
UPDATE sessions s
SET text_user_id = (SELECT text_id FROM temp_id_mapping_users WHERE integer_id = s.user_id)
WHERE user_id IS NOT NULL;

-- Drop foreign key constraints
ALTER TABLE chat_logs DROP CONSTRAINT chat_logs_user_id_fkey;
ALTER TABLE media DROP CONSTRAINT media_user_id_fkey;
ALTER TABLE reviews DROP CONSTRAINT reviews_user_id_fkey;
ALTER TABLE favorites DROP CONSTRAINT favorites_user_id_fkey;
ALTER TABLE sessions DROP CONSTRAINT sessions_user_id_fkey;

-- Drop primary key constraints
ALTER TABLE users DROP CONSTRAINT users_pkey;
ALTER TABLE chat_logs DROP CONSTRAINT chat_logs_pkey;
ALTER TABLE analytics_events DROP CONSTRAINT analytics_events_pkey;
ALTER TABLE media DROP CONSTRAINT media_pkey;
ALTER TABLE reviews DROP CONSTRAINT reviews_pkey;
ALTER TABLE favorites DROP CONSTRAINT favorites_pkey;
ALTER TABLE sessions DROP CONSTRAINT sessions_pkey;

-- Drop integer ID columns
ALTER TABLE users DROP COLUMN id;
ALTER TABLE chat_logs DROP COLUMN id;
ALTER TABLE analytics_events DROP COLUMN id;
ALTER TABLE media DROP COLUMN id;
ALTER TABLE reviews DROP COLUMN id;
ALTER TABLE favorites DROP COLUMN id;
ALTER TABLE sessions DROP COLUMN id;

-- Rename text ID columns to id
ALTER TABLE users RENAME COLUMN text_id TO id;
ALTER TABLE chat_logs RENAME COLUMN text_id TO id;
ALTER TABLE analytics_events RENAME COLUMN text_id TO id;
ALTER TABLE media RENAME COLUMN text_id TO id;
ALTER TABLE reviews RENAME COLUMN text_id TO id;
ALTER TABLE favorites RENAME COLUMN text_id TO id;
ALTER TABLE sessions RENAME COLUMN text_id TO id;

-- Rename text foreign key columns
ALTER TABLE chat_logs DROP COLUMN user_id;
ALTER TABLE chat_logs RENAME COLUMN text_user_id TO user_id;

ALTER TABLE media DROP COLUMN user_id;
ALTER TABLE media RENAME COLUMN text_user_id TO user_id;

ALTER TABLE reviews DROP COLUMN user_id;
ALTER TABLE reviews RENAME COLUMN text_user_id TO user_id;

ALTER TABLE favorites DROP COLUMN user_id;
ALTER TABLE favorites RENAME COLUMN text_user_id TO user_id;

ALTER TABLE sessions DROP COLUMN user_id;
ALTER TABLE sessions RENAME COLUMN text_user_id TO user_id;

-- Add primary key constraints
ALTER TABLE users ADD PRIMARY KEY (id);
ALTER TABLE chat_logs ADD PRIMARY KEY (id);
ALTER TABLE analytics_events ADD PRIMARY KEY (id);
ALTER TABLE media ADD PRIMARY KEY (id);
ALTER TABLE reviews ADD PRIMARY KEY (id);
ALTER TABLE favorites ADD PRIMARY KEY (id);
ALTER TABLE sessions ADD PRIMARY KEY (id);

-- Add foreign key constraints
ALTER TABLE chat_logs 
    ADD CONSTRAINT chat_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE media 
    ADD CONSTRAINT media_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE reviews 
    ADD CONSTRAINT reviews_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE favorites 
    ADD CONSTRAINT favorites_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE sessions 
    ADD CONSTRAINT sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE SET NULL;

-- Clean up temporary tables
DROP TABLE temp_id_mapping_users;

-- Commit transaction
COMMIT;
