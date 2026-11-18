import sqlite3

DB_NAME = "phonebook.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    # Bật ràng buộc khóa ngoại trong SQLite
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Bảng USERS
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

    # 2. Bảng CONTACTS (Đã thêm cột isBlocked cho tính năng Blocked Contacts)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS CONTACTS (
        contactID INTEGER PRIMARY KEY AUTOINCREMENT,
        userID INTEGER NOT NULL,
        fullName VARCHAR(100) NOT NULL,
        email VARCHAR(100),
        address VARCHAR(255),
        note TEXT,
        isBlocked BOOLEAN DEFAULT FALSE,
        FOREIGN KEY (userID) REFERENCES USERS(userID) ON DELETE CASCADE
    );
    """)

    # 3. Bảng PHONE_NUMBERS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS PHONE_NUMBERS (
        phoneID INTEGER PRIMARY KEY AUTOINCREMENT,
        contactID INTEGER NOT NULL,
        phoneNumber VARCHAR(20) NOT NULL,
        phoneType VARCHAR(30),
        FOREIGN KEY (contactID) REFERENCES CONTACTS(contactID) ON DELETE CASCADE
    );
    """)

    # 4. Bảng GROUPS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS GROUPS (
        groupID INTEGER PRIMARY KEY AUTOINCREMENT,
        userID INTEGER NOT NULL,
        groupName VARCHAR(100) NOT NULL,
        description TEXT,
        FOREIGN KEY (userID) REFERENCES USERS(userID) ON DELETE CASCADE
    );
    """)

    # 5. Bảng CONTACT_GROUPS (Khóa chính phức hợp)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS CONTACT_GROUPS (
        contactID INTEGER NOT NULL,
        groupID INTEGER NOT NULL,
        PRIMARY KEY (contactID, groupID),
        FOREIGN KEY (contactID) REFERENCES CONTACTS(contactID) ON DELETE CASCADE,
        FOREIGN KEY (groupID) REFERENCES GROUPS(groupID) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()


# Hàm dùng chung hỗ trợ Prepared Statements cho TV2, TV3, TV4
def execute_query(query: str, params: tuple = (), fetch: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)  # Prepared Statement chống SQL Injection
    result = None
    if fetch == "one":
        result = cursor.fetchone()
    elif fetch == "all":
        result = cursor.fetchall()
    else:
        conn.commit()
        result = cursor.lastrowid
    conn.close()
    return result
