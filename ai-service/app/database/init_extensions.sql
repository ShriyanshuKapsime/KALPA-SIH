-- =============================================================================
-- KALPA Database Initialization Script: Enable PostGIS and Core Extensions
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- Enable pgvector dynamically only if installed in PostgreSQL extension directory
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_available_extensions WHERE name = 'vector'
    ) THEN
        CREATE EXTENSION IF NOT EXISTS "vector";
        RAISE NOTICE 'pgvector extension enabled';
    ELSE
        RAISE NOTICE 'pgvector extension not installed in container image; skipping for Phase 1 baseline';
    END IF;
END $$;

