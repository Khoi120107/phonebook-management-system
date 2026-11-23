import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database
from models.user_model import User

def setup_function():
    database.DB_NAME = "test_phonebook.db"
    if os.path.exists(database.DB_NAME):
        os.remove(database.DB_NAME)
    database.init_db()

def teardown_function():
    if os.path.exists("test_phonebook.db"):
        os.remove("test_phonebook.db")

def test_register_and_login_success():
    u = User(fullName="John", email="john@gmail.com", phoneNumber="0987654321", password="123456")
    ok, msg = u.register()
    assert ok is True
    user, lmsg = User.login("john@gmail.com", "123456")
    assert user is not None
    assert user["fullName"] == "John"

def test_login_wrong_password():
    u = User(fullName="John", email="john@gmail.com", phoneNumber="0987654321", password="123456")
    u.register()
    user, lmsg = User.login("john@gmail.com", "wrongpass")
    assert user is None
    assert "Invalid username or password" in lmsg

def test_register_duplicate_email():
    User(fullName="John", email="john@gmail.com", phoneNumber="0987654321", password="123456").register()
    ok, msg = User(fullName="John 2", email="john@gmail.com", phoneNumber="0911111111", password="123456").register()
    assert ok is False
    assert "already exists" in msg

def test_update_profile_and_reset_password():
    u = User(fullName="John", email="john@gmail.com", phoneNumber="0987654321", password="123456")
    u.register()
    u.fullName = "John Updated"
    ok, _ = u.updateProfile()
    assert ok is True
    assert User.get_by_id(u.userID)["fullName"] == "John Updated"
    ok_r, msg_r = User.resetPassword("john@gmail.com")
    assert ok_r is True
    assert "New password generated" in msg_r

def test_admin_view_and_delete_user():
    u = User(fullName="Student", email="student@gmail.com", phoneNumber="0987654321", password="123456")
    u.register()
    users = User.viewUserAccounts()
    assert len(users) >= 2
    ok, _ = User.deleteUserAccount(u.userID)
    assert ok is True
    assert User.get_by_id(u.userID) is None
