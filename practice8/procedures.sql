CREATE OR REPLACE PROCEDURE insert_many_contacts(
    names TEXT[],
    phones TEXT[]
)
LANGUAGE plpgsql
AS $$
DECLARE
    i INT;
BEGIN
    FOR i IN 1..array_length(names, 1) LOOP

        IF phones[i] !~ '^\+\d{10,15}$' THEN
            RAISE NOTICE 'Invalid phone: %', phones[i];
        ELSE
            INSERT INTO contacts(first_name, phone)
            VALUES (names[i], phones[i])
            ON CONFLICT (phone) DO NOTHING;
        END IF;

    END LOOP;
END;
$$;