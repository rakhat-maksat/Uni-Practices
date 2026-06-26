import csv
import json
import os
import sys
from datetime import date, datetime

import psycopg2
import psycopg2.extras

from connect import get_connection

#  Helpers

PHONE_TYPES  = ("home", "work", "mobile")
SORT_OPTIONS = ("name", "birthday", "created_at")
PAGE_SIZE    = 5


def _ask(prompt: str, default: str = "") -> str:
    val = input(prompt).strip()
    return val if val else default


def _pick(prompt: str, choices: tuple, allow_empty=False) -> str:
    """Ask user to pick one of the given choices."""
    while True:
        print(f"  Options: {', '.join(choices)}" + (" (Enter to skip)" if allow_empty else ""))
        val = input(prompt).strip().lower()
        if allow_empty and val == "":
            return ""
        if val in choices:
            return val
        print("  Invalid choice, try again.")


def _fmt_row(row) -> str:
    """Pretty-print one contact row dict."""
    phones = row.get("phones") or []
    phone_str = ", ".join(
        f"{p['phone']} ({p['type']})" for p in phones
    ) or "—"
    return (
        f"  Name    : {row['name']}\n"
        f"  Email   : {row.get('email') or '—'}\n"
        f"  Birthday: {row.get('birthday') or '—'}\n"
        f"  Group   : {row.get('group_name') or '—'}\n"
        f"  Phones  : {phone_str}\n"
    )


#  DB bootstrap

def init_db():
    """Apply schema.sql and procedures.sql to the database."""
    base = os.path.dirname(__file__)
    with get_connection() as conn, conn.cursor() as cur:
        for fname in ("schema.sql", "procedures.sql"):
            path = os.path.join(base, fname)
            if os.path.exists(path):
                with open(path) as f:
                    cur.execute(f.read())
        conn.commit()
    print("Database initialised.")


#  Core DB helpers (used by multiple features)

def _get_or_create_group(cur, group_name: str) -> int:
    cur.execute(
        "INSERT INTO groups (name) VALUES (%s) ON CONFLICT (name) DO NOTHING",
        (group_name,),
    )
    cur.execute("SELECT id FROM groups WHERE name = %s", (group_name,))
    return cur.fetchone()[0]


def _fetch_contacts_with_phones(cur, contact_ids: list[int]) -> list[dict]:
    """
    Given a list of contact IDs, return full contact dicts
    including a 'phones' list.
    """
    if not contact_ids:
        return []

    cur.execute(
        """
        SELECT c.id, c.name, c.email, c.birthday, c.created_at,
               g.name AS group_name
        FROM   contacts c
        LEFT JOIN groups g ON g.id = c.group_id
        WHERE  c.id = ANY(%s)
        ORDER BY c.name
        """,
        (contact_ids,),
    )
    rows = {r[0]: {
        "id": r[0], "name": r[1], "email": r[2],
        "birthday": r[3], "created_at": r[4],
        "group_name": r[5], "phones": []
    } for r in cur.fetchall()}

    cur.execute(
        "SELECT contact_id, phone, type FROM phones WHERE contact_id = ANY(%s)",
        (contact_ids,),
    )
    for cid, phone, ptype in cur.fetchall():
        rows[cid]["phones"].append({"phone": phone, "type": ptype})

    return list(rows.values())


#  3.1 – Extended contact entry

def add_contact():
    """Console flow: add a new contact with all extended fields."""
    print("\n── Add Contact ──────────────────────────────────")
    name = _ask("Full name: ")
    if not name:
        print("Name is required.")
        return

    email    = _ask("Email (Enter to skip): ")
    birthday = _ask("Birthday YYYY-MM-DD (Enter to skip): ")
    if birthday:
        try:
            datetime.strptime(birthday, "%Y-%m-%d")
        except ValueError:
            print("Invalid date format, skipping birthday.")
            birthday = None

    # Group
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, name FROM groups ORDER BY name")
        groups = cur.fetchall()

    print("  Groups:")
    for gid, gname in groups:
        print(f"    [{gid}] {gname}")
    group_input = _ask("Group id (Enter to skip): ")
    group_id = int(group_input) if group_input.isdigit() else None

    # Phones
    phones = []
    while True:
        ph = _ask("Phone number (Enter to finish): ")
        if not ph:
            break
        ptype = _pick("Phone type: ", PHONE_TYPES)
        phones.append((ph, ptype))

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO contacts (name, email, birthday, group_id)
            VALUES (%s, %s, %s, %s) RETURNING id
            """,
            (name, email or None, birthday or None, group_id),
        )
        cid = cur.fetchone()[0]
        for ph, pt in phones:
            cur.execute(
                "INSERT INTO phones (contact_id, phone, type) VALUES (%s,%s,%s)",
                (cid, ph, pt),
            )
        conn.commit()

    print(f"Contact '{name}' added (id={cid}).")


#  3.2 – Advanced search / filter / sort / paginated navigation

def _build_filter_query(group_name=None, email_query=None,
                        sort_by="name") -> tuple[str, list]:
    """
    Build a SELECT that returns contact IDs matching the filters.
    Returns (sql, params).
    """
    if sort_by not in SORT_OPTIONS:
        sort_by = "name"

    sql = """
        SELECT DISTINCT c.id
        FROM   contacts c
        LEFT JOIN groups g  ON g.id  = c.group_id
        LEFT JOIN phones ph ON ph.contact_id = c.id
        WHERE  TRUE
    """
    params: list = []

    if group_name:
        sql += " AND g.name ILIKE %s"
        params.append(group_name)

    if email_query:
        sql += " AND c.email ILIKE %s"
        params.append(f"%{email_query}%")

    sql += f" ORDER BY c.id"          # stable sub-select order
    return sql, params


def filter_contacts():
    """Console: filter by group and/or email, then sort & paginate."""
    print("\n── Filter & Search ──────────────────────────────")

    # Collect filters
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT name FROM groups ORDER BY name")
        group_names = [r[0] for r in cur.fetchall()]

    print("  Available groups:", ", ".join(group_names))
    group_filter = _ask("Filter by group name (Enter to skip): ")
    email_filter = _ask("Search in email (Enter to skip): ")

    print("  Sort by: name, birthday, created_at")
    sort_by = _ask("Sort by [name]: ", default="name").lower()
    if sort_by not in SORT_OPTIONS:
        sort_by = "name"

    id_sql, params = _build_filter_query(
        group_name=group_filter or None,
        email_query=email_filter or None,
        sort_by=sort_by,
    )

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(id_sql, params)
        all_ids = [r[0] for r in cur.fetchall()]

    if not all_ids:
        print("No contacts found.")
        return

    # Sort the full list after fetching details
    with get_connection() as conn, conn.cursor() as cur:
        contacts = _fetch_contacts_with_phones(cur, all_ids)

    def sort_key(c):
        val = c.get(sort_by)
        if val is None:
            return (1, "")           # nulls last
        return (0, str(val))

    contacts.sort(key=sort_key)

    # Paginated navigation
    total  = len(contacts)
    page   = 0
    pages  = (total - 1) // PAGE_SIZE + 1

    while True:
        start = page * PAGE_SIZE
        chunk = contacts[start: start + PAGE_SIZE]
        print(f"\n  Page {page + 1}/{pages}  (total {total} contacts)\n")
        for c in chunk:
            print(_fmt_row(c))
            print("  " + "─" * 40)

        nav = input("  [n]ext  [p]rev  [q]uit: ").strip().lower()
        if nav == "n":
            if page < pages - 1:
                page += 1
            else:
                print("  Already on last page.")
        elif nav == "p":
            if page > 0:
                page -= 1
            else:
                print("  Already on first page.")
        elif nav == "q":
            break


#  3.3 – Export / Import JSON

def _json_serial(obj):
    """JSON serialiser for date / datetime objects."""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not JSON-serialisable")


def export_json(filepath: str = "contacts_export.json"):
    """Export all contacts (with phones and group) to JSON."""
    filepath = _ask(f"Export file path [{filepath}]: ", default=filepath)

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute("SELECT id FROM contacts ORDER BY name")
        all_ids = [r[0] for r in cur.fetchall()]
        contacts = _fetch_contacts_with_phones(cur, all_ids)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(contacts, f, indent=2, default=_json_serial, ensure_ascii=False)

    print(f"Exported {len(contacts)} contacts to '{filepath}'.")


def import_json(filepath: str = "contacts_export.json"):
    """Import contacts from a JSON file. Prompts on duplicates."""
    filepath = _ask(f"Import file path [{filepath}]: ", default=filepath)
    if not os.path.exists(filepath):
        print(f"File '{filepath}' not found.")
        return

    with open(filepath, encoding="utf-8") as f:
        records = json.load(f)

    inserted = skipped = overwritten = 0

    with get_connection() as conn, conn.cursor() as cur:
        for rec in records:
            name = rec.get("name", "").strip()
            if not name:
                continue

            # Check duplicate
            cur.execute("SELECT id FROM contacts WHERE name ILIKE %s", (name,))
            existing = cur.fetchone()

            if existing:
                choice = input(
                    f"  Contact '{name}' already exists. [s]kip / [o]verwrite? "
                ).strip().lower()
                if choice != "o":
                    skipped += 1
                    continue
                # Overwrite: delete old, re-insert
                cur.execute("DELETE FROM contacts WHERE id = %s", (existing[0],))
                overwritten += 1

            # Resolve group
            group_id = None
            if rec.get("group_name"):
                group_id = _get_or_create_group(cur, rec["group_name"])

            cur.execute(
                """
                INSERT INTO contacts (name, email, birthday, group_id)
                VALUES (%s, %s, %s, %s) RETURNING id
                """,
                (
                    name,
                    rec.get("email"),
                    rec.get("birthday"),
                    group_id,
                ),
            )
            cid = cur.fetchone()[0]

            for ph in rec.get("phones", []):
                cur.execute(
                    "INSERT INTO phones (contact_id, phone, type) VALUES (%s,%s,%s)",
                    (cid, ph["phone"], ph.get("type", "mobile")),
                )
            inserted += 1

        conn.commit()

    print(f"Import done: {inserted} inserted, {overwritten} overwritten, {skipped} skipped.")


#  3.3 – Extended CSV import (Practice 7 base + new fields)

def import_csv(filepath: str = "contacts.csv"):
    """
    Extended CSV importer.
    Expected columns: name, phone, phone_type, email, birthday, group
    """
    filepath = _ask(f"CSV file path [{filepath}]: ", default=filepath)
    if not os.path.exists(filepath):
        print(f"File '{filepath}' not found.")
        return

    inserted = skipped = errors = 0

    with get_connection() as conn, conn.cursor() as cur:
        with open(filepath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = (row.get("name") or "").strip()
                if not name:
                    errors += 1
                    continue

                phone      = (row.get("phone") or "").strip()
                phone_type = (row.get("phone_type") or "mobile").strip().lower()
                email      = (row.get("email") or "").strip() or None
                birthday   = (row.get("birthday") or "").strip() or None
                group_name = (row.get("group") or "").strip() or None

                if phone_type not in PHONE_TYPES:
                    phone_type = "mobile"

                # Validate birthday
                if birthday:
                    try:
                        datetime.strptime(birthday, "%Y-%m-%d")
                    except ValueError:
                        print(f"  Skipping bad birthday '{birthday}' for '{name}'")
                        birthday = None

                # Skip duplicates silently (consistent with bulk-insert from P8)
                cur.execute(
                    "SELECT id FROM contacts WHERE name ILIKE %s", (name,)
                )
                if cur.fetchone():
                    skipped += 1
                    continue

                group_id = _get_or_create_group(cur, group_name) if group_name else None

                cur.execute(
                    """
                    INSERT INTO contacts (name, email, birthday, group_id)
                    VALUES (%s, %s, %s, %s) RETURNING id
                    """,
                    (name, email, birthday, group_id),
                )
                cid = cur.fetchone()[0]

                if phone:
                    cur.execute(
                        "INSERT INTO phones (contact_id, phone, type) VALUES (%s,%s,%s)",
                        (cid, phone, phone_type),
                    )
                inserted += 1

        conn.commit()

    print(f"CSV import done: {inserted} inserted, {skipped} skipped, {errors} errors.")


#  3.4 – Stored procedure wrappers

def call_add_phone():
    """Wrapper for the add_phone stored procedure."""
    print("\n── Add Phone to Contact ─────────────────────────")
    name  = _ask("Contact name: ")
    phone = _ask("Phone number: ")
    ptype = _pick("Phone type: ", PHONE_TYPES)
    try:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("CALL add_phone(%s, %s, %s)", (name, phone, ptype))
            conn.commit()
        print("Done.")
    except Exception as e:
        print(f"Error: {e}")


def call_move_to_group():
    """Wrapper for the move_to_group stored procedure."""
    print("\n── Move Contact to Group ────────────────────────")
    name  = _ask("Contact name: ")
    group = _ask("Group name (will be created if new): ")
    try:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("CALL move_to_group(%s, %s)", (name, group))
            conn.commit()
        print("Done.")
    except Exception as e:
        print(f"Error: {e}")


def call_search_contacts():
    """Wrapper for the search_contacts DB function (name + email + phones)."""
    print("\n── Extended Search ──────────────────────────────")
    query = _ask("Search query (name / email / phone): ")
    try:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM search_contacts(%s)", (query,))
            rows = cur.fetchall()
        if not rows:
            print("No results found.")
            return
        # Group by contact_id for display
        seen: dict[int, dict] = {}
        for cid, name, email, birthday, group_name, phone, phone_type in rows:
            if cid not in seen:
                seen[cid] = {
                    "id": cid, "name": name, "email": email,
                    "birthday": birthday, "group_name": group_name,
                    "phones": []
                }
            if phone:
                seen[cid]["phones"].append({"phone": phone, "type": phone_type})
        for c in seen.values():
            print(_fmt_row(c))
            print("  " + "─" * 40)
    except Exception as e:
        print(f"Error: {e}")


#  Main menu

MENU = """
      PhoneBook    
  1. Add contact (extended)              
  2. Filter / browse contacts            
  3. Extended search (name/email/phone)  
  4. Add phone to contact           
  5. Move contact to group         
  6. Export contacts → JSON              
  7. Import contacts ← JSON              
  8. Import contacts ← CSV   
  9. Initialise / reset database         
  0. Exit                                
"""


def main():
    while True:
        print(MENU)
        choice = input("Choice: ").strip()
        match choice:
            case "1": add_contact()
            case "2": filter_contacts()
            case "3": call_search_contacts()
            case "4": call_add_phone()
            case "5": call_move_to_group()
            case "6": export_json()
            case "7": import_json()
            case "8": import_csv()
            case "9":
                confirm = input("Re-initialise DB? This may alter schema. [y/N]: ")
                if confirm.lower() == "y":
                    init_db()
            case "0":
                print("Bye!")
                sys.exit(0)
            case _:
                print("Unknown option.")


if __name__ == "__main__":
    main()