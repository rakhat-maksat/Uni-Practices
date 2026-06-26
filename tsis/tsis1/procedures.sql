-- ── 1. add_phone ─────────────────────────────────────────────
-- Adds a phone number to an existing contact (looked up by name).
CREATE OR REPLACE PROCEDURE add_phone(
    p_contact_name VARCHAR,
    p_phone        VARCHAR,
    p_type         VARCHAR   -- 'home' | 'work' | 'mobile'
)
LANGUAGE plpgsql AS $$
DECLARE
    v_contact_id INTEGER;
BEGIN
    -- Validate phone type
    IF p_type NOT IN ('home', 'work', 'mobile') THEN
        RAISE EXCEPTION 'Invalid phone type "%". Must be home, work, or mobile.', p_type;
    END IF;

    -- Find the contact
    SELECT id INTO v_contact_id
    FROM contacts
    WHERE name ILIKE p_contact_name
    LIMIT 1;

    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Contact "%" not found.', p_contact_name;
    END IF;

    -- Insert phone
    INSERT INTO phones (contact_id, phone, type)
    VALUES (v_contact_id, p_phone, p_type);

    RAISE NOTICE 'Phone % (%) added to contact "%".', p_phone, p_type, p_contact_name;
END;
$$;


-- ── 2. move_to_group ─────────────────────────────────────────
-- Moves a contact to a group, creating the group if needed.
CREATE OR REPLACE PROCEDURE move_to_group(
    p_contact_name VARCHAR,
    p_group_name   VARCHAR
)
LANGUAGE plpgsql AS $$
DECLARE
    v_contact_id INTEGER;
    v_group_id   INTEGER;
BEGIN
    -- Upsert the group
    INSERT INTO groups (name) VALUES (p_group_name)
    ON CONFLICT (name) DO NOTHING;

    SELECT id INTO v_group_id FROM groups WHERE name = p_group_name;

    -- Find the contact
    SELECT id INTO v_contact_id
    FROM contacts
    WHERE name ILIKE p_contact_name
    LIMIT 1;

    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Contact "%" not found.', p_contact_name;
    END IF;

    -- Move
    UPDATE contacts SET group_id = v_group_id WHERE id = v_contact_id;

    RAISE NOTICE 'Contact "%" moved to group "%".', p_contact_name, p_group_name;
END;
$$;


-- ── 3. search_contacts ───────────────────────────────────────
-- Extended pattern search: matches name, email, AND any phone
-- in the phones table (replaces / extends the Practice 8 version
-- which only searched the old single-phone column).
CREATE OR REPLACE FUNCTION search_contacts(p_query TEXT)
RETURNS TABLE (
    contact_id  INTEGER,
    name        VARCHAR,
    email       VARCHAR,
    birthday    DATE,
    group_name  VARCHAR,
    phone       VARCHAR,
    phone_type  VARCHAR
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT ON (c.id, ph.id)
           c.id,
           c.name,
           c.email,
           c.birthday,
           g.name      AS group_name,
           ph.phone,
           ph.type     AS phone_type
    FROM   contacts c
    LEFT JOIN groups g  ON g.id  = c.group_id
    LEFT JOIN phones ph ON ph.contact_id = c.id
    WHERE  c.name  ILIKE '%' || p_query || '%'
       OR  c.email ILIKE '%' || p_query || '%'
       OR  ph.phone ILIKE '%' || p_query || '%'
    ORDER BY c.id, ph.id;
END;
$$;