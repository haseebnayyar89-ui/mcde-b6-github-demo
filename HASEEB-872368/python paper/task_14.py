"""Task 14 | Command-Line Contact Manager

Storage functions (JSON file) and business-logic functions are kept separate.
If contacts.json is corrupt, the program stops with a message and never
overwrites the file.
"""
import json
import os

FILE_NAME = "contacts.json"


# ---------------- storage ----------------
def load_contacts():
    """Return the list of contacts. Raises ValueError if the file is corrupt."""
    if not os.path.exists(FILE_NAME):
        return []
    with open(FILE_NAME, "r", encoding="utf-8") as file:
        text = file.read()
    if text.strip() == "":
        return []
    try:
        contacts = json.loads(text)
    except json.JSONDecodeError:
        raise ValueError(FILE_NAME + " is corrupt. Fix or move the file, it was not changed.")
    if not isinstance(contacts, list):
        raise ValueError(FILE_NAME + " must contain a list of contacts.")
    return contacts


def save_contacts(contacts):
    with open(FILE_NAME, "w", encoding="utf-8") as file:
        json.dump(contacts, file, indent=2)


# ---------------- business logic ----------------
def find_contact(contacts, contact_id):
    for contact in contacts:
        if contact["id"] == contact_id:
            return contact
    return None


def check_contact_data(name, phone, email):
    if name.strip() == "":
        raise ValueError("name must not be empty")
    digits = [c for c in phone if c.isdigit()]
    if len(digits) < 7 or any(not (c.isdigit() or c in "+- ") for c in phone):
        raise ValueError("phone must have at least 7 digits")
    if "@" not in email or "." not in email.split("@")[-1] or email.startswith("@"):
        raise ValueError("email is not valid")


def add_contact(contacts, contact_id, name, phone, email):
    if find_contact(contacts, contact_id) is not None:
        raise ValueError("ID already exists")
    check_contact_data(name, phone, email)
    contacts.append({"id": contact_id, "name": name.strip(), "phone": phone.strip(), "email": email.strip()})


def search_contacts(contacts, text):
    text = text.strip().lower()
    return [c for c in contacts if text in c["name"].lower()]     # case-insensitive


def update_contact(contacts, contact_id, name, phone, email):
    contact = find_contact(contacts, contact_id)
    if contact is None:
        raise ValueError("contact not found")
    # empty input means: keep the old value
    new_name = name if name.strip() else contact["name"]
    new_phone = phone if phone.strip() else contact["phone"]
    new_email = email if email.strip() else contact["email"]
    check_contact_data(new_name, new_phone, new_email)
    contact["name"], contact["phone"], contact["email"] = new_name.strip(), new_phone.strip(), new_email.strip()


def delete_contact(contacts, contact_id):
    contact = find_contact(contacts, contact_id)
    if contact is None:
        raise ValueError("contact not found")
    contacts.remove(contact)


# ---------------- menu ----------------
def read_id(text):
    try:
        value = int(text)
    except ValueError:
        raise ValueError("ID must be a whole number")
    if value <= 0:
        raise ValueError("ID must be greater than zero")
    return value


def show(contacts):
    if not contacts:
        print("No contacts found.")
    for c in contacts:
        print(c["id"], "|", c["name"], "|", c["phone"], "|", c["email"])


def main():
    try:
        contacts = load_contacts()
    except ValueError as error:
        print("Error:", error)
        return

    while True:
        print("\n1) Add  2) Search  3) Update  4) Delete  5) List  0) Exit")
        choice = input("Choose: ").strip()
        try:
            if choice == "1":
                contact_id = read_id(input("ID: "))
                add_contact(contacts, contact_id, input("Name: "), input("Phone: "), input("Email: "))
                save_contacts(contacts)
                print("Contact added.")
            elif choice == "2":
                show(search_contacts(contacts, input("Name to search: ")))
            elif choice == "3":
                contact_id = read_id(input("ID to update: "))
                print("(leave empty to keep the old value)")
                update_contact(contacts, contact_id, input("New name: "), input("New phone: "), input("New email: "))
                save_contacts(contacts)
                print("Contact updated.")
            elif choice == "4":
                delete_contact(contacts, read_id(input("ID to delete: ")))
                save_contacts(contacts)
                print("Contact deleted.")
            elif choice == "5":
                show(contacts)
            elif choice == "0":
                break
            else:
                print("Invalid choice.")
        except ValueError as error:
            print("Error:", error)


if __name__ == "__main__":
    main()
