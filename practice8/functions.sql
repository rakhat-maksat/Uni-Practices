CREATE OR REPLACE FUNCTION search_contacts(pattern TEXT)
RETURNS TABLE (
    id INT,
    first_name TEXT,
    last_name TEXT,
    phone TEXT,
    email TEXT
)
AS $$
BEGIN
    RETURN QUERY
    SELECT c.id, c.first_name, c.last_name, c.phone, c.email
    FROM contacts c
    WHERE c.first_name ILIKE '%' || pattern || '%'
       OR c.last_name ILIKE '%' || pattern || '%'
       OR c.phone LIKE '%' || pattern || '%';
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION get_contacts_paginated(limit_val INT, offset_val INT)
RETURNS TABLE (
    id INT,
    first_name TEXT,
    last_name TEXT,
    phone TEXT,
    email TEXT
)
AS $$
BEGIN
    RETURN QUERY
    SELECT * FROM contacts
    ORDER BY id
    LIMIT limit_val OFFSET offset_val;
END;
$$ LANGUAGE plpgsql;