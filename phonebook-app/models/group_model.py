from database import execute_query

class Group:
    def __init__(self, groupID=None, userID=None, groupName="", description=""):
        self.groupID = groupID
        self.userID = userID
        self.groupName = groupName
        self.description = description

    def createGroup(self):
        if not self.groupName or not self.groupName.strip():
            return False, "Group name cannot be empty."
        dup = execute_query(
            "SELECT groupID FROM GROUPS WHERE userID = ? AND LOWER(groupName) = LOWER(?)",
            (self.userID, self.groupName.strip()), fetch="one"
        )
        if dup:
            return False, "Group name already exists."
        gid = execute_query(
            "INSERT INTO GROUPS (userID, groupName, description) VALUES (?, ?, ?)",
            (self.userID, self.groupName.strip(), self.description.strip())
        )
        self.groupID = gid
        return True, "Group created successfully."

    def updateGroup(self):
        if not self.groupName or not self.groupName.strip():
            return False, "Group name cannot be empty."
        dup = execute_query(
            "SELECT groupID FROM GROUPS WHERE userID = ? AND LOWER(groupName) = LOWER(?) AND groupID != ?",
            (self.userID, self.groupName.strip(), self.groupID), fetch="one"
        )
        if dup:
            return False, "Group name already exists."
        execute_query(
            "UPDATE GROUPS SET groupName = ?, description = ? WHERE groupID = ? AND userID = ?",
            (self.groupName.strip(), self.description.strip(), self.groupID, self.userID)
        )
        return True, "Group updated successfully."

    @staticmethod
    def deleteGroup(groupID: int, userID: int):
        # Deleting a group removes CONTACT_GROUPS links via ON DELETE CASCADE without deleting CONTACTS
        existing = execute_query(
            "SELECT groupID FROM GROUPS WHERE groupID = ? AND userID = ?",
            (groupID, userID), fetch="one"
        )
        if not existing:
            return False, "Group not found."
        execute_query("DELETE FROM GROUPS WHERE groupID = ? AND userID = ?", (groupID, userID))
        return True, "Group deleted successfully."

    @staticmethod
    def viewGroups(userID: int):
        return execute_query(
            """SELECT g.groupID, g.groupName, g.description,
                      COUNT(cg.contactID) AS memberCount
               FROM GROUPS g
               LEFT JOIN CONTACT_GROUPS cg ON g.groupID = cg.groupID
               WHERE g.userID = ?
               GROUP BY g.groupID
               ORDER BY g.groupName COLLATE NOCASE ASC""",
            (userID,), fetch="all"
        )

class ContactGroup:
    @staticmethod
    def addContactToGroup(contactID: int, groupID: int):
        execute_query(
            "INSERT OR IGNORE INTO CONTACT_GROUPS (contactID, groupID) VALUES (?, ?)",
            (contactID, groupID)
        )

    @staticmethod
    def removeContactFromGroup(contactID: int, groupID: int):
        execute_query(
            "DELETE FROM CONTACT_GROUPS WHERE contactID = ? AND groupID = ?",
            (contactID, groupID)
        )

class BlockedContact:
    @staticmethod
    def viewBlockedContacts(userID: int):
        return execute_query(
            """SELECT c.*,
                      (SELECT p.phoneNumber FROM PHONE_NUMBERS p WHERE p.contactID = c.contactID ORDER BY p.phoneID ASC LIMIT 1) AS primaryPhone
               FROM CONTACTS c
               WHERE c.userID = ? AND c.isBlocked = 1
               ORDER BY c.fullName COLLATE NOCASE ASC""",
            (userID,), fetch="all"
        )

    @staticmethod
    def blockContact(contactID: int, userID: int):
        c = execute_query(
            "SELECT contactID, isBlocked FROM CONTACTS WHERE contactID = ? AND userID = ?",
            (contactID, userID), fetch="one"
        )
        if not c:
            return False, "Contact not found."
        if c["isBlocked"]:
            return False, "Contact is already blocked."
        execute_query("UPDATE CONTACTS SET isBlocked = 1 WHERE contactID = ? AND userID = ?", (contactID, userID))
        return True, "Contact blocked successfully."

    @staticmethod
    def unblockContact(contactID: int, userID: int):
        c = execute_query(
            "SELECT contactID, isBlocked FROM CONTACTS WHERE contactID = ? AND userID = ?",
            (contactID, userID), fetch="one"
        )
        if not c or not c["isBlocked"]:
            return False, "Blocked contact not found."
        execute_query("UPDATE CONTACTS SET isBlocked = 0 WHERE contactID = ? AND userID = ?", (contactID, userID))
        return True, "Contact unblocked successfully."
