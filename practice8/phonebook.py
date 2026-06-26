import psycopg2
from connect import get_connection


def view_contacts():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM contacts")
    rows = cursor.fetchall()

    for row in rows:
        print(row)

    cursor.close()
    conn.close()


def search_contact():
    pattern = input("Enter name or phone: ")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM search_contacts(%s)", (pattern,))
    rows = cursor.fetchall()

    for row in rows:
        print(row)

    cursor.close()
    conn.close()


def add_contact():
    name = input("Enter first name: ")
    phone = input("Enter phone: ")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("CALL upsert_contact(%s, %s)", (name, phone))

    conn.commit()
    cursor.close()
    conn.close()

    print("Contact added/updated")


def delete_contact():
    value = input("Enter name or phone to delete: ")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("CALL delete_contact(%s)", (value,))

    conn.commit()
    cursor.close()
    conn.close()

    print("Contact deleted")


def paginate():
    limit = int(input("Limit: "))
    offset = int(input("Offset: "))

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM get_contacts_paginated(%s, %s)",
        (limit, offset)
    )

    rows = cursor.fetchall()

    for row in rows:
        print(row)

    cursor.close()
    conn.close()


def menu():
    while True:
        print("\n--- PHONEBOOK MENU ---")
        print("1. Add/Update contact")
        print("2. View contacts")
        print("3. Search contact")
        print("4. Delete contact")
        print("5. Pagination")
        print("6. Exit")

        choice = input("Choose an option: ")

        if choice == "1":
            add_contact()
        elif choice == "2":
            view_contacts()
        elif choice == "3":
            search_contact()
        elif choice == "4":
            delete_contact()
        elif choice == "5":
            paginate()
        elif choice == "6":
            print("Goodbye")
            break
        else:
            print("Invalid choice")


if __name__ == "__main__":
    menu()