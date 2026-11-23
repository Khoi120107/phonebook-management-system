import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database
from models.user_model import User
from models.contact_model import Contact

def setup_function():
    database.DB_NAME = "test_phonebook.db"
    if os.path.exists(database.DB_NAME):
        os.remove(database.DB_NAME)
    database.init_db()
    u = User(fullName="Tester", email="tester@gmail.com", phoneNumber="0900000001", password="123456")
    u.register()
    global UID
    UID = u.userID

def teardown_function():
    if os.path.exists("test_phonebook.db"):
        os.remove("test_phonebook.db")

def test_add_view_edit_delete_contact():
    c = Contact(userID=UID, fullName="Nghiem Son Hoang", email="sonhoang09@gmail.com", address="40 Vo Oanh", note="Family")
    ok, _, cid = c.addContact("0987654321")
    assert ok is True
    detail = Contact.viewContact(cid, UID)
    assert detail["fullName"] == "Nghiem Son Hoang"
    assert detail["primaryPhone"] == "0987654321"

    c.fullName = "Nghiem Son Hoang Updated"
    ok_u, _ = c.updateContact("0987654322")
    assert ok_u is True
    assert Contact.viewContact(cid, UID)["primaryPhone"] == "0987654322"

    ok_d, _ = Contact.deleteContact(cid, UID)
    assert ok_d is True
    assert Contact.viewContact(cid, UID) is None

def test_duplicate_name_and_phone_detection():
    Contact(userID=UID, fullName="An Khanh Huy").addContact("0379752980")
    dups_name = Contact.check_duplicates(UID, "An Khanh Huy", "0999999999")
    assert dups_name["same_name"] is not None
    assert dups_name["same_phone"] is None

    dups_phone = Contact.check_duplicates(UID, "Different Name", "0379752980")
    assert dups_phone["same_phone"] is not None
    assert dups_phone["same_name"] is None

def test_search_sort_import_export():
    Contact(userID=UID, fullName="Vu Pham").addContact("0379767890")
    Contact(userID=UID, fullName="An Khanh Huy").addContact("0379752980")
    asc = Contact.getContacts(UID, sort_order="ASC")
    assert asc[0]["fullName"] == "An Khanh Huy"

    res = Contact.getContacts(UID, keyword="Vu")
    assert len(res) == 1

    csv_data = Contact.exportContactsCSV(UID)
    assert "Vu Pham" in csv_data
    imported, skipped = Contact.importContactsCSV(UID, "Full Name,Phone Number,Email,Address,Note\nChu Huan,0907208960,ch@gmail.com,HCM,Friend\n")
    assert imported == 1
    assert skipped == 0
