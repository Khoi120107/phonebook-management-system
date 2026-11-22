import re
import secrets
import string
from database import execute_query, hash_password

class User:
    def __init__(self, userID=None, fullName="", dateOfBirth=None, gender="",
                 address="", phoneNumber="", password="", email="", role="User"):
        self.userID = userID
        self.fullName = fullName
        self.dateOfBirth = dateOfBirth
        self.gender = gender
        self.address = address
        self.phoneNumber = phoneNumber
        self.password = password
        self.email = email
        self.role = role

    @staticmethod
    def validate_account_info(fullName: str, email: str, phoneNumber: str, password: str, check_duplicate=True):
        if not fullName or not email or not phoneNumber or not password:
            return False, "Missing mandatory fields."
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            return False, "Invalid email format."
        if not re.match(r"^[0-9+\-\s]{8,20}$", phoneNumber):
            return False, "Invalid phone number format."
        if len(password) < 6:
            return False, "Password must be at least 6 characters."
        if check_duplicate:
            existing = execute_query("SELECT userID FROM USERS WHERE email = ?", (email,), fetch="one")
            if existing:
                return False, "Email address already exists."
        return True, "Valid"

    def register(self):
        valid, msg = self.validate_account_info(self.fullName, self.email, self.phoneNumber, self.password)
        if not valid:
            return False, msg
        hashed_pw = hash_password(self.password)
        user_id = execute_query(
            """INSERT INTO USERS (fullName, dateOfBirth, gender, address, phoneNumber, password, email, role)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (self.fullName, self.dateOfBirth, self.gender, self.address,
             self.phoneNumber, hashed_pw, self.email, self.role)
        )
        self.userID = user_id
        return True, "Registration is completed successfully."

    @staticmethod
    def login(email: str, password: str):
        if not email or not password:
            return None, "Invalid username or password."
        user = execute_query("SELECT * FROM USERS WHERE email = ?", (email,), fetch="one")
        if not user or user["password"] != hash_password(password):
            return None, "Invalid username or password."
        return user, "User logs in successfully."

    @staticmethod
    def get_by_id(userID: int):
        return execute_query("SELECT * FROM USERS WHERE userID = ?", (userID,), fetch="one")

    def updateProfile(self):
        if not self.fullName or not self.phoneNumber:
            return False, "Full name and phone number are mandatory."
        if self.password:
            if len(self.password) < 6:
                return False, "Password must be at least 6 characters."
            execute_query(
                """UPDATE USERS SET fullName=?, dateOfBirth=?, gender=?, address=?, phoneNumber=?, password=?
                   WHERE userID=?""",
                (self.fullName, self.dateOfBirth, self.gender, self.address,
                 self.phoneNumber, hash_password(self.password), self.userID)
            )
        else:
            execute_query(
                """UPDATE USERS SET fullName=?, dateOfBirth=?, gender=?, address=?, phoneNumber=?
                   WHERE userID=?""",
                (self.fullName, self.dateOfBirth, self.gender, self.address,
                 self.phoneNumber, self.userID)
            )
        return True, "Profile updated successfully."

    @staticmethod
    def resetPassword(email: str):
        user = execute_query("SELECT userID FROM USERS WHERE email = ?", (email,), fetch="one")
        if not user:
            return False, "Email does not exist in the system."
        alphabet = string.ascii_letters + string.digits
        new_password = "".join(secrets.choice(alphabet) for _ in range(8))
        execute_query(
            "UPDATE USERS SET password = ? WHERE email = ?",
            (hash_password(new_password), email)
        )
        return True, f"New password generated: {new_password}"

    @staticmethod
    def viewUserAccounts():
        return execute_query(
            "SELECT userID, fullName, dateOfBirth, gender, address, phoneNumber, email, role FROM USERS ORDER BY userID ASC",
            fetch="all"
        )

    @staticmethod
    def deleteUserAccount(userID: int):
        user = execute_query("SELECT userID, role FROM USERS WHERE userID = ?", (userID,), fetch="one")
        if not user:
            return False, "User account not found."
        if user["role"] == "Admin":
            return False, "Cannot delete Admin account."
        execute_query("DELETE FROM USERS WHERE userID = ?", (userID,))
        return True, "User account deleted successfully."
