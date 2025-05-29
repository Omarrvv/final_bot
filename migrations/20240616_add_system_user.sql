-- Migration: Add System User
-- Date: 2024-06-16
-- Adds a system user for data generation and system operations

-- 1. Check if system user already exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM users WHERE id = 'system') THEN
        -- Create system user
        INSERT INTO users (
            id, username, email, password_hash, salt, role, 
            created_at, updated_at, last_login, preferences
        ) VALUES (
            'system', 'system', 'system@example.com', 'not_applicable', 'not_applicable', 'system',
            NOW(), NOW(), NOW(), '{}'::jsonb
        );
        
        RAISE NOTICE 'System user created successfully';
    ELSE
        RAISE NOTICE 'System user already exists';
    END IF;
END $$;
