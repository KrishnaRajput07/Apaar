-- APAAR Pramaan — database initialisation
-- Extensions + seat claim function + audit chain helpers

CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "fuzzystrmatch";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── claim_seat function ──────────────────────────────────────────
-- Atomically claims a slot in a pool, handling overflow.
CREATE OR REPLACE FUNCTION claim_seat(
    p_pool_id      TEXT,
    p_student_id   TEXT,
    p_academic_year TEXT DEFAULT '2026-27'
) RETURNS TABLE(slot_no INTEGER, over_by INTEGER, cap INTEGER, pool_status TEXT)
LANGUAGE plpgsql
AS $$
DECLARE
    v_cap           INTEGER;
    v_claimed       INTEGER;
    v_slot          INTEGER;
    v_over          INTEGER := 0;
    v_status        TEXT;
BEGIN
    -- Lock the pool row
    SELECT approved_intake, claimed INTO v_cap, v_claimed
    FROM seat_pools
    WHERE id = p_pool_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Pool % not found', p_pool_id;
    END IF;

    v_slot    := v_claimed + 1;
    v_claimed := v_claimed + 1;

    IF v_claimed > v_cap THEN
        v_over   := v_claimed - v_cap;
        v_status := 'BREACH';
    ELSIF v_claimed >= v_cap * 0.95 THEN
        v_status := 'WARNING';
    ELSE
        v_status := 'OK';
    END IF;

    -- Update the pool
    UPDATE seat_pools
    SET claimed = v_claimed, status = v_status
    WHERE id = p_pool_id;

    RETURN QUERY SELECT v_slot, v_over, v_cap, v_status;
END;
$$;

-- ── Audit chain sequence ────────────────────────────────────────
CREATE SEQUENCE IF NOT EXISTS audit_chain_1_seq START 1;
CREATE SEQUENCE IF NOT EXISTS audit_chain_2_seq START 1;
CREATE SEQUENCE IF NOT EXISTS audit_chain_3_seq START 1;
