import csv
import io
import re
from database import execute_query

class PhoneNumber:
    def __init__(self, phoneID=None, contactID=None, phoneNumber="", phoneType="Mobile"):
        self.phoneID = phoneID
        self.contactID = contactID
        self.phoneNumber = phoneNumber
        self.phoneType = phoneType

    def addPhoneNumber(self):
        return execute_query(
            "INSERT INTO PHONE_NUMBERS (contactID, phoneNumber, phoneType) VALUES (?, ?, ?)",
            (self.contactID, self.phoneNumber, self.phoneType)
        )

    def updatePhoneNumber(self):
        execute_query(
            "UPDATE PHONE_NUMBERS SET phoneNumber=?, phoneType=? WHERE phoneID=?",
            (self.phoneNumber, self.phoneType, self.phoneID)
        )

    @staticmethod
    def deletePhoneNumber(phoneID: int):
        execute_query("DELETE FROM PHONE_NUMBERS WHERE phoneID = ?", (phoneID,))

class Contact:
    def __init__(self, contactID=None, userID=None, fullName="", email="",
                 address="", note="", isBlocked=0):
        self.contactID = contactID
        self.userID = userID
        self.fullName = fullName
        self.email = email
        self.address = address
        self.note = note
        self.isBlocked = isBlocked

    @staticmethod
    def validate_contact_info(fullName: str, phoneNumber: str, email: str = ""):
        if not fullName or not fullName.strip():
            return False, "Full name is mandatory."
        if not phoneNumber or not phoneNumber.strip():
            return False, "Phone number is mandatory."
        if not re.match(r"^[0-9+\-\s]{8,20}$", phoneNumber.strip()):
            return False, "Invalid phone number format."
        if email and email.strip() and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email.strip()):
            return False, "Invalid email format."
        return True, "Valid"

    @staticmethod
    def check_duplicates(userID: int, fullName: str, phoneNumber: str, exclude_contactID: int = None):
        # FR-14: Duplicate Name, Different Phone Number
        # FR-15: Duplicate Phone Number, Different Name
        name_query = "SELECT contactID, fullName FROM CONTACTS WHERE userID = ? AND LOWER(fullName) = LOWER(?)"
        name_params = [userID, fullName.strip()]
        if exclude_contactID:
            name_query += " AND contactID != ?"
            name_params.append(exclude_contactID)
        same_name = execute_query(name_query, tuple(name_params), fetch="one")

        phone_query = """
            SELECT c.contactID, c.fullName, p.phoneNumber
            FROM CONTACTS c
            JOIN PHONE_NUMBERS p ON c.contactID = p.contactID
            WHERE c.userID = ? AND p.phoneNumber = ?
        """
        phone_params = [userID, phoneNumber.strip()]
        if exclude_contactID:
            phone_query += " AND c.contactID != ?"
            phone_params.append(exclude_contactID)
        same_phone = execute_query(phone_query, tuple(phone_params), fetch="one")

        return {"same_name": same_name, "same_phone": same_phone}

    def addContact(self, phoneNumber: str, phoneType: str = "Mobile", groupID: int = None):
        valid, msg = self.validate_contact_info(self.fullName, phoneNumber, self.email)
        if not valid:
            return False, msg, None

        contact_id = execute_query(
            """INSERT INTO CONTACTS (userID, fullName, email, address, note, isBlocked)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (self.userID, self.fullName.strip(), self.email.strip(), self.address.strip(), self.note.strip(), 0)
        )
        self.contactID = contact_id

        pn = PhoneNumber(contactID=contact_id, phoneNumber=phoneNumber.strip(), phoneType=phoneType)
        pn.addPhoneNumber()

        if groupID:
            execute_query(
                "INSERT OR IGNORE INTO CONTACT_GROUPS (contactID, groupID) VALUES (?, ?)",
                (contact_id, groupID)
            )
        return True, "Contact added successfully.", contact_id

    def updateContact(self, phoneNumber: str, phoneType: str = "Mobile", groupID: int = None):
        valid, msg = self.validate_contact_info(self.fullName, phoneNumber, self.email)
        if not valid:
            return False, msg

        execute_query(
            """UPDATE CONTACTS SET fullName=?, email=?, address=?, note=?
               WHERE contactID=? AND userID=?""",
            (self.fullName.strip(), self.email.strip(), self.address.strip(), self.note.strip(),
             self.contactID, self.userID)
        )

        existing_phone = execute_query(
            "SELECT phoneID FROM PHONE_NUMBERS WHERE contactID = ? ORDER BY phoneID ASC LIMIT 1",
            (self.contactID,), fetch="one"
        )
        if existing_phone:
            execute_query(
                "UPDATE PHONE_NUMBERS SET phoneNumber=?, phoneType=? WHERE phoneID=?",
                (phoneNumber.strip(), phoneType, existing_phone["phoneID"])
            )
        else:
            PhoneNumber(contactID=self.contactID, phoneNumber=phoneNumber.strip(), phoneType=phoneType).addPhoneNumber()

        execute_query("DELETE FROM CONTACT_GROUPS WHERE contactID = ?", (self.contactID,))
        if groupID:
            execute_query(
                "INSERT OR IGNORE INTO CONTACT_GROUPS (contactID, groupID) VALUES (?, ?)",
                (self.contactID, groupID)
            )
        return True, "Contact updated successfully."

    @staticmethod
    def deleteContact(contactID: int, userID: int):
        existing = execute_query(
            "SELECT contactID FROM CONTACTS WHERE contactID = ? AND userID = ?",
            (contactID, userID), fetch="one"
        )
        if not existing:
            return False, "Contact not found or unauthorized."
        execute_query("DELETE FROM CONTACTS WHERE contactID = ? AND userID = ?", (contactID, userID))
        return True, "Contact deleted successfully."

    @staticmethod
    def viewContact(contactID: int, userID: int):
        contact = execute_query(
            "SELECT * FROM CONTACTS WHERE contactID = ? AND userID = ?",
            (contactID, userID), fetch="one"
        )
        if not contact:
            return None
        phones = execute_query(
            "SELECT * FROM PHONE_NUMBERS WHERE contactID = ? ORDER BY phoneID ASC",
            (contactID,), fetch="all"
        )
        groups = execute_query(
            """SELECT g.groupID, g.groupName FROM GROUPS g
               JOIN CONTACT_GROUPS cg ON g.groupID = cg.groupID
               WHERE cg.contactID = ?""",
            (contactID,), fetch="all"
        )
        contact["phones"] = phones
        contact["primaryPhone"] = phones[0]["phoneNumber"] if phones else ""
        contact["groups"] = groups
        return contact

    @staticmethod
    def getContacts(userID: int, keyword: str = "", groupID: int = None, sort_order: str = "ASC",
                    page: int = 1, per_page: int = 30, include_blocked: bool = False):
        order = "DESC" if sort_order.upper() == "DESC" else "ASC"
        offset = (max(1, page) - 1) * per_page

        query = """
            SELECT DISTINCT c.*,
                   (SELECT p.phoneNumber FROM PHONE_NUMBERS p WHERE p.contactID = c.contactID ORDER BY p.phoneID ASC LIMIT 1) AS primaryPhone
            FROM CONTACTS c
            LEFT JOIN PHONE_NUMBERS p ON c.contactID = p.contactID
            LEFT JOIN CONTACT_GROUPS cg ON c.contactID = cg.contactID
            WHERE c.userID = ?
        """
        params = [userID]
        if not include_blocked:
            query += " AND c.isBlocked = 0"
        if keyword and keyword.strip():
            kw = f"%{keyword.strip()}%"
            query += " AND (c.fullName LIKE ? OR p.phoneNumber LIKE ?)"
            params.extend([kw, kw])
        if groupID:
            query += " AND cg.groupID = ?"
            params.append(groupID)

        query += f" ORDER BY c.fullName COLLATE NOCASE {order} LIMIT ? OFFSET ?"
        params.extend([per_page, offset])

        return execute_query(query, tuple(params), fetch="all")

    @staticmethod
    def exportContactsCSV(userID: int) -> str:
        contacts = Contact.getContacts(userID, per_page=100000, include_blocked=True)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Full Name", "Phone Number", "Email", "Address", "Note"])
        for c in contacts:
            writer.writerow([c["fullName"], c["primaryPhone"] or "", c["email"] or "", c["address"] or "", c["note"] or ""])
        return output.getvalue()

    @staticmethod
    def importContactsCSV(userID: int, csv_text: str):
        reader = csv.DictReader(io.StringIO(csv_text))
        imported = 0
        skipped = 0
        for row in reader:
            name = (row.get("Full Name") or row.get("fullName") or "").strip()
            phone = (row.get("Phone Number") or row.get("phoneNumber") or "").strip()
            email = (row.get("Email") or row.get("email") or "").strip()
            address = (row.get("Address") or row.get("address") or "").strip()
            note = (row.get("Note") or row.get("note") or "").strip()
            ok, _, _ = Contact(userID=userID, fullName=name, email=email, address=address, note=note).addContact(phone)
            if ok:
                imported += 1
            else:
                skipped += 1
        return imported, skipped
