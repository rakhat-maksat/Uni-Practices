import psycopg2
import csv
from connect import get_connection


def insert_contacts_from_csv(filename):
    conn = get_connection()
    if not conn:
        print("DB connection failed")
        return

    cursor = conn.cursor()

    with open(filename, newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)

        for person in reader:
            cursor.execute("""
                INSERT INTO contacts (first_name, last_name, phone, email)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (phone) DO NOTHING
            """, (
                person['first_name'],
                person['last_name'],
                person['phone'],
                person['email']
            ))

    conn.commit()
    cursor.close()
    conn.close()

    print("CSV data inserted successfully")


def add_contact():
    conn = get_connection()
    if not conn:
        print("DB connection failed")
        return

    cursor = conn.cursor()

    first_name = input("First name: ")
    last_name = input("Last name: ")
    phone = input("Phone: ")
    email = input("Email: ")

    cursor.execute("""
        INSERT INTO contacts (first_name, last_name, phone, email)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (phone) DO NOTHING
    """, (first_name, last_name, phone, email))

    conn.commit()
    cursor.close()
    conn.close()

    print("Contact added")


def view_contacts():
    conn = get_connection()
    if not conn:
        print("DB connection failed")
        return

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM contacts")
    rows = cursor.fetchall()

    for row in rows:
        print(row)

    cursor.close()
    conn.close()


def search_contact():
    keyword = input("Enter name or phone prefix: ")

    conn = get_connection()
    if not conn:
        print("DB connection failed")
        return

    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM contacts
        WHERE first_name ILIKE %s OR phone LIKE %s
    """, (f"%{keyword}%", f"{keyword}%"))

    rows = cursor.fetchall()

    for row in rows:
        print(row)

    cursor.close()
    conn.close()


def update_contact():
    phone = input("Enter phone of contact to update: ")
    new_name = input("New first name (leave empty to skip): ")
    new_phone = input("New phone (leave empty to skip): ")

    conn = get_connection()
    if not conn:
        print("DB connection failed")
        return

    cursor = conn.cursor()

    old_phone = phone

    if new_name:
        cursor.execute("""
            UPDATE contacts
            SET first_name = %s
            WHERE phone = %s
        """, (new_name, old_phone))

    if new_phone:
        cursor.execute("""
            UPDATE contacts
            SET phone = %s
            WHERE phone = %s
        """, (new_phone, old_phone))

    conn.commit()
    cursor.close()
    conn.close()

    print("Contact updated")


def delete_contact():
    phone = input("Enter phone to delete: ")

    conn = get_connection()
    if not conn:
        print("DB connection failed")
        return

    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM contacts
        WHERE phone = %s
    """, (phone,))

    conn.commit()
    cursor.close()
    conn.close()

    print("Contact deleted")


def menu():
    while True:
        print("\n--- PHONEBOOK MENU ---")
        print("1. Add contact")
        print("2. View contacts")
        print("3. Search contact")
        print("4. Update contact")
        print("5. Delete contact")
        print("6. Import CSV")
        print("7. Exit")

        choice = input("Choose an option: ")

        if choice == "1":
            add_contact()
        elif choice == "2":
            view_contacts()
        elif choice == "3":
            search_contact()
        elif choice == "4":
            update_contact()
        elif choice == "5":
            delete_contact()
        elif choice == "6":
            filename = input("Enter CSV file name: ")
            insert_contacts_from_csv(filename)
        elif choice == "7":
            print("Goodbye")
            break
        else:
            print("Invalid choice")


if __name__ == "__main__":
    menu()