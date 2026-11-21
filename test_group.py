import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database
from models.user_model import User
from models.contact_model import Contact
from models.group_model import Group, BlockedContact

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

def test_group_crud_and_delete_preserves_contacts():
    g = Group(userID=UID, groupName="Family", description="Relatives")
    ok, _ = g.createGroup()
    assert ok is True
    ok_c, _, cid = Contact(userID=UID, fullName="Manh Tien").addContact("0964845333", groupID=g.groupID)
    assert ok_c is True

    groups = Group.viewGroups(UID)
    assert groups[0]["memberCount"] == 1

    # Delete group -> contact must still exist
    ok_d, _ = Group.deleteGroup(g.groupID, UID)
    assert ok_d is True
    assert Contact.viewContact(cid, UID) is not None

def test_block_and_unblock_contact():
    _, _, cid = Contact(userID=UID, fullName="Spammer").addContact("0912345678")
    ok_b, _ = BlockedContact.blockContact(cid, UID)
    assert ok_b is True
    assert len(BlockedContact.viewBlockedContacts(UID)) == 1
    # Blocked contacts hidden from default home list
    assert len(Contact.getContacts(UID)) == 0

    ok_u, _ = BlockedContact.unblockContact(cid, UID)
    assert ok_u is True
    assert len(BlockedContact.viewBlockedContacts(UID)) == 0
    assert len(Contact.getContacts(UID)) == 1
