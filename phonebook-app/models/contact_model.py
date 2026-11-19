from database import get_connection, execute_query


class PhoneNumber:
    def __init__(self, phoneNumber, phoneType="Mobile", phoneID=None, contactID=None):
        self.phoneID = phoneID
        self.contactID = contactID
        self.phoneNumber = phoneNumber.strip()
        self.phoneType = (phoneType or "Mobile").strip()

    def addPhoneNumber(self):
        query = "INSERT INTO PHONE_NUMBERS (contactID, phoneNumber, phoneType) VALUES (?, ?, ?)"
        self.phoneID = execute_query(query, (self.contactID, self.phoneNumber, self.phoneType))
        return self

    def updatePhoneNumber(self, newPhone, newType):
        self.phoneNumber = newPhone.strip()
        self.phoneType = newType.strip()
        query = "UPDATE PHONE_NUMBERS SET phoneNumber = ?, phoneType = ? WHERE phoneID = ?"
        execute_query(query, (self.phoneNumber, self.phoneType, self.phoneID))
        return True

    def deletePhoneNumber(self):
        if not self.phoneID:
            return False
        execute_query("DELETE FROM PHONE_NUMBERS WHERE phoneID = ?", (self.phoneID,))
        return True

    def to_dict(self):
        return {
            "phoneID": self.phoneID,
            "contactID": self.contactID,
            "phoneNumber": self.phoneNumber,
            "phoneType": self.phoneType,
        }


class Contact:
    def __init__(
        self,
        userID,
        fullName,
        email="",
        address="",
        note="",
        isBlocked=False,
        contactID=None,
        phoneNumbers=None,
        groupIDs=None,
    ):
        self.contactID = contactID
        self.userID = userID
        self.fullName = fullName.strip()
        self.email = (email or "").strip()
        self.address = (address or "").strip()
        self.note = (note or "").strip()
        self.isBlocked = bool(isBlocked)
        self.phoneNumbers = phoneNumbers if phoneNumbers else []
        self.groupIDs = groupIDs if groupIDs else []

    def addContact(self):
        return ContactModel().add(self)

    def updateContact(self):
        return ContactModel().update(self)

    def deleteContact(self):
        return ContactModel().delete(self.userID, self.contactID)

    @staticmethod
    def viewContact(userID, contactID):
        return ContactModel().get_by_id(userID, contactID)

    @staticmethod
    def searchContact(userID, keyword):
        return ContactModel().search(userID, keyword)

    @staticmethod
    def sortContact(userID, order="ASC", page=1, page_size=30, groupID=None):
        return ContactModel().get_list(userID, page, page_size, order, groupID)

    @staticmethod
    def importContacts(controller, userID, content, file_type="csv"):
        if file_type == "vcf":
            return controller.import_vcf(userID, content)
        return controller.import_csv(userID, content)

    @staticmethod
    def exportContacts(controller, userID, file_type="csv"):
        if file_type == "vcf":
            return controller.export_vcf(userID)
        return controller.export_csv(userID)

    def to_dict(self):
        return {
            "contactID": self.contactID,
            "userID": self.userID,
            "fullName": self.fullName,
            "email": self.email,
            "address": self.address,
            "note": self.note,
            "isBlocked": self.isBlocked,
            "phoneNumbers": [p.to_dict() for p in self.phoneNumbers],
            "groupIDs": self.groupIDs,
        }


class ContactModel:
    def _get_phones(self, contactID):
        rows = execute_query(
            "SELECT phoneID, contactID, phoneNumber, phoneType FROM PHONE_NUMBERS WHERE contactID = ?",
            (contactID,),
            fetch="all",
        )
        return [
            PhoneNumber(r["phoneNumber"], r["phoneType"], r["phoneID"], r["contactID"])
            for r in rows
        ]

    def _get_groups(self, contactID):
        rows = execute_query(
            "SELECT groupID FROM CONTACT_GROUPS WHERE contactID = ?",
            (contactID,),
            fetch="all",
        )
        return [r["groupID"] for r in rows]

    def _to_contact(self, row):
        return Contact(
            contactID=row["contactID"],
            userID=row["userID"],
            fullName=row["fullName"],
            email=row["email"] or "",
            address=row["address"] or "",
            note=row["note"] or "",
            isBlocked=bool(row["isBlocked"]),
            phoneNumbers=self._get_phones(row["contactID"]),
            groupIDs=self._get_groups(row["contactID"]),
        )

    def find_by_name(self, userID, fullName):
        rows = execute_query(
            "SELECT * FROM CONTACTS WHERE userID = ? AND LOWER(fullName) = LOWER(?)",
            (userID, fullName.strip()),
            fetch="all",
        )
        return [self._to_contact(r) for r in rows]

    def find_by_phone(self, userID, phoneNumber):
        row = execute_query(
            """
            SELECT c.* FROM CONTACTS c
            JOIN PHONE_NUMBERS p ON c.contactID = p.contactID
            WHERE c.userID = ? AND p.phoneNumber = ?
            LIMIT 1
            """,
            (userID, phoneNumber.strip()),
            fetch="one",
        )
        return self._to_contact(row) if row else None

    def get_list(self, userID, page=1, page_size=30, sort_order="ASC", groupID=None):
        order = "DESC" if sort_order.upper() == "DESC" else "ASC"
        offset = (max(page, 1) - 1) * page_size

        if groupID is not None:
            total = execute_query(
                """
                SELECT COUNT(*) FROM CONTACTS c
                JOIN CONTACT_GROUPS cg ON c.contactID = cg.contactID
                WHERE c.userID = ? AND c.isBlocked = 0 AND cg.groupID = ?
                """,
                (userID, groupID),
                fetch="one",
            )[0]
            rows = execute_query(
                f"""
                SELECT c.* FROM CONTACTS c
                JOIN CONTACT_GROUPS cg ON c.contactID = cg.contactID
                WHERE c.userID = ? AND c.isBlocked = 0 AND cg.groupID = ?
                ORDER BY c.fullName COLLATE NOCASE {order}
                LIMIT ? OFFSET ?
                """,
                (userID, groupID, page_size, offset),
                fetch="all",
            )
        else:
            total = execute_query(
                "SELECT COUNT(*) FROM CONTACTS WHERE userID = ? AND isBlocked = 0",
                (userID,),
                fetch="one",
            )[0]
            rows = execute_query(
                f"""
                SELECT * FROM CONTACTS
                WHERE userID = ? AND isBlocked = 0
                ORDER BY fullName COLLATE NOCASE {order}
                LIMIT ? OFFSET ?
                """,
                (userID, page_size, offset),
                fetch="all",
            )

        items = [self._to_contact(r).to_dict() for r in rows]
        return {
            "total": total,
            "page": page,
            "pageSize": page_size,
            "sortOrder": order,
            "items": items,
        }

    def get_by_id(self, userID, contactID):
        row = execute_query(
            "SELECT * FROM CONTACTS WHERE userID = ? AND contactID = ?",
            (userID, contactID),
            fetch="one",
        )
        return self._to_contact(row) if row else None

    def search(self, userID, keyword):
        kw = f"%{keyword.strip()}%"
        rows = execute_query(
            """
            SELECT DISTINCT c.* FROM CONTACTS c
            LEFT JOIN PHONE_NUMBERS p ON c.contactID = p.contactID
            WHERE c.userID = ? AND c.isBlocked = 0
              AND (c.fullName LIKE ? OR p.phoneNumber LIKE ? OR c.email LIKE ?)
            ORDER BY c.fullName COLLATE NOCASE ASC
            """,
            (userID, kw, kw, kw),
            fetch="all",
        )
        return [self._to_contact(r) for r in rows]

    def add(self, contact):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO CONTACTS (userID, fullName, email, address, note, isBlocked)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (contact.userID, contact.fullName, contact.email, contact.address, contact.note, contact.isBlocked),
        )
        contact.contactID = cursor.lastrowid

        for phone in contact.phoneNumbers:
            cursor.execute(
                "INSERT INTO PHONE_NUMBERS (contactID, phoneNumber, phoneType) VALUES (?, ?, ?)",
                (contact.contactID, phone.phoneNumber, phone.phoneType),
            )
            phone.phoneID = cursor.lastrowid
            phone.contactID = contact.contactID

        for gid in contact.groupIDs:
            cursor.execute(
                "INSERT OR IGNORE INTO CONTACT_GROUPS (contactID, groupID) VALUES (?, ?)",
                (contact.contactID, gid),
            )

        conn.commit()
        conn.close()
        return contact

    def update(self, contact):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE CONTACTS
            SET fullName = ?, email = ?, address = ?, note = ?, isBlocked = ?
            WHERE contactID = ? AND userID = ?
            """,
            (
                contact.fullName,
                contact.email,
                contact.address,
                contact.note,
                contact.isBlocked,
                contact.contactID,
                contact.userID,
            ),
        )
        if cursor.rowcount == 0:
            conn.close()
            return False

        # Cập nhật lại SĐT và nhóm
        cursor.execute("DELETE FROM PHONE_NUMBERS WHERE contactID = ?", (contact.contactID,))
        for phone in contact.phoneNumbers:
            cursor.execute(
                "INSERT INTO PHONE_NUMBERS (contactID, phoneNumber, phoneType) VALUES (?, ?, ?)",
                (contact.contactID, phone.phoneNumber, phone.phoneType),
            )
            phone.phoneID = cursor.lastrowid
            phone.contactID = contact.contactID

        cursor.execute("DELETE FROM CONTACT_GROUPS WHERE contactID = ?", (contact.contactID,))
        for gid in contact.groupIDs:
            cursor.execute(
                "INSERT OR IGNORE INTO CONTACT_GROUPS (contactID, groupID) VALUES (?, ?)",
                (contact.contactID, gid),
            )

        conn.commit()
        conn.close()
        return True

    def delete(self, userID, contactID):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM CONTACTS WHERE contactID = ? AND userID = ?", (contactID, userID))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted