import sqlite3
import hashlib

DB_NAME = "phonebook.db"

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def get_connection(db_path: str = None):
    conn = sqlite3.connect(db_path or DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path: str = None):
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # 1. USERS table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS USERS (
        userID INTEGER PRIMARY KEY AUTOINCREMENT,
        fullName VARCHAR(100) NOT NULL,
        dateOfBirth DATE,
        gender VARCHAR(10),
        address VARCHAR(255),
        phoneNumber VARCHAR(20) NOT NULL,
        password VARCHAR(255) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        role VARCHAR(20) DEFAULT 'User'
    );
    """)

    # 2. CONTACTS table (with isBlocked for Blocked Contacts feature)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS CONTACTS (
        contactID INTEGER PRIMARY KEY AUTOINCREMENT,
        userID INTEGER NOT NULL,
        fullName VARCHAR(100) NOT NULL,
        email VARCHAR(100),
        address VARCHAR(255),
        note TEXT,
        isBlocked BOOLEAN DEFAULT 0,
        FOREIGN KEY (userID) REFERENCES USERS(userID) ON DELETE CASCADE
    );
    """)

    # 3. PHONE_NUMBERS table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS PHONE_NUMBERS (
        phoneID INTEGER PRIMARY KEY AUTOINCREMENT,
        contactID INTEGER NOT NULL,
        phoneNumber VARCHAR(20) NOT NULL,
        phoneType VARCHAR(30) DEFAULT 'Mobile',
        FOREIGN KEY (contactID) REFERENCES CONTACTS(contactID) ON DELETE CASCADE
    );
    """)

    # 4. GROUPS table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS GROUPS (
        groupID INTEGER PRIMARY KEY AUTOINCREMENT,
        userID INTEGER NOT NULL,
        groupName VARCHAR(100) NOT NULL,
        description TEXT,
        FOREIGN KEY (userID) REFERENCES USERS(userID) ON DELETE CASCADE
    );
    """)

    # 5. CONTACT_GROUPS table (Composite Primary Key)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS CONTACT_GROUPS (
        contactID INTEGER NOT NULL,
        groupID INTEGER NOT NULL,
        PRIMARY KEY (contactID, groupID),
        FOREIGN KEY (contactID) REFERENCES CONTACTS(contactID) ON DELETE CASCADE,
        FOREIGN KEY (groupID) REFERENCES GROUPS(groupID) ON DELETE CASCADE
    );
    """)

    # Seed default Admin account if not exists
    cursor.execute("SELECT userID FROM USERS WHERE email = ?", ("admin@phonebook.com",))
    if not cursor.fetchone():
        cursor.execute(
            """INSERT INTO USERS (fullName, dateOfBirth, gender, address, phoneNumber, password, email, role)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("System Admin", "1995-01-01", "Other", "HQ", "0900000000",
             hash_password("admin123"), "admin@phonebook.com", "Admin")
        )

    conn.commit()
    conn.close()

def execute_query(query: str, params: tuple = (), fetch: str = None, db_path: str = None):
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(query, params)
    result = None
    if fetch == "one":
        row = cursor.fetchone()
        result = dict(row) if row else None
    elif fetch == "all":
        result = [dict(r) for r in cursor.fetchall()]
    else:
        conn.commit()
        result = cursor.lastrowid
    conn.close()
    return result
