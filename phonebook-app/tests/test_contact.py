import os
import pytest
import database
from controllers.contact_controller import ContactController

TEST_DB = "test_phonebook.db"
ctrl = ContactController()


def setup_function():
    # Đổi sang db tạm để chạy test không ảnh hưởng dữ liệu thật
    database.DB_NAME = TEST_DB
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    database.init_db()

    # Tạo sẵn 2 user để thỏa khóa ngoại userID
    database.execute_query(
        "INSERT INTO USERS (userID, fullName, phoneNumber, password, email) VALUES (?, ?, ?, ?, ?)",
        (1, "Nguyen Hau", "0900000001", "123456", "hau@gmail.com"),
    )
    database.execute_query(
        "INSERT INTO USERS (userID, fullName, phoneNumber, password, email) VALUES (?, ?, ?, ?, ?)",
        (2, "Dang Khoi", "0900000002", "123456", "khoi@gmail.com"),
    )


def teardown_function():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)


def test_add_and_detail():
    res = ctrl.add_contact(
        1,
        "Nghiem Son Hoang",
        [{"phoneNumber": "0987654321", "phoneType": "Mobile"}],
        email="sonhoang09@gmail.com",
        address="So 40, Duong Vo Oanh",
        note="Family Member",
    )
    assert res["status"] == "created"

    cid = res["contact"]["contactID"]
    detail = ctrl.get_detail(1, cid)
    assert detail["fullName"] == "Nghiem Son Hoang"
    assert detail["phoneNumbers"][0]["phoneNumber"] == "0987654321"


def test_validate_error():
    with pytest.raises(ValueError):
        ctrl.add_contact(1, "", [{"phoneNumber": "0901234567", "phoneType": "Mobile"}])
    with pytest.raises(ValueError):
        ctrl.add_contact(1, "Nguyen A", [{"phoneNumber": "123", "phoneType": "Mobile"}])
    with pytest.raises(ValueError):
        ctrl.add_contact(1, "Nguyen A", [{"phoneNumber": "0901234567", "phoneType": "Mobile"}], email="sai_email")


def test_pagination_and_sort():
    for i in range(35):
        ctrl.add_contact(1, f"Contact_{35 - i:02d}", [{"phoneNumber": f"09000000{i:02d}", "phoneType": "Mobile"}])

    p1 = ctrl.list_contacts(1, page=1, page_size=30, sort_order="ASC")
    p2 = ctrl.list_contacts(1, page=2, page_size=30, sort_order="ASC")
    p1_desc = ctrl.list_contacts(1, page=1, page_size=30, sort_order="DESC")

    assert p1["total"] == 35
    assert len(p1["items"]) == 30
    assert len(p2["items"]) == 5
    assert p1["items"][0]["fullName"] == "Contact_01"
    assert p1_desc["items"][0]["fullName"] == "Contact_35"


def test_search():
    ctrl.add_contact(1, "Nghiem Son Hoang", [{"phoneNumber": "0987654321", "phoneType": "Mobile"}])
    ctrl.add_contact(1, "An Khanh Huy", [{"phoneNumber": "0379752980", "phoneType": "Work"}])

    assert len(ctrl.search_contacts(1, "Nghiem")) == 1
    assert len(ctrl.search_contacts(1, "037975")) == 1


def test_duplicate_name():
    ctrl.add_contact(1, "Nguyen Hau", [{"phoneNumber": "0901111111", "phoneType": "Mobile"}])

    warn = ctrl.add_contact(1, "Nguyen Hau", [{"phoneNumber": "0902222222", "phoneType": "Work"}])
    assert warn["status"] == "duplicate_name"

    appended = ctrl.add_contact(1, "Nguyen Hau", [{"phoneNumber": "0902222222", "phoneType": "Work"}], action="append")
    assert appended["status"] == "appended"
    assert len(appended["contact"]["phoneNumbers"]) == 2


def test_duplicate_phone():
    ctrl.add_contact(1, "Nguyen Hau", [{"phoneNumber": "0901111111", "phoneType": "Mobile"}])

    warn = ctrl.add_contact(1, "Tran Khoi", [{"phoneNumber": "0901111111", "phoneType": "Mobile"}])
    assert warn["status"] == "duplicate_phone"

    updated = ctrl.add_contact(
        1, "Tran Khoi", [{"phoneNumber": "0901111111", "phoneType": "Mobile"}], action="update_name"
    )
    assert updated["status"] == "updated_name"
    assert updated["contact"]["fullName"] == "Tran Khoi"


def test_update_and_delete():
    res = ctrl.add_contact(1, "Ten Cu", [{"phoneNumber": "0903333333", "phoneType": "Mobile"}])
    cid = res["contact"]["contactID"]

    up = ctrl.update_contact(1, cid, "Ten Moi", [{"phoneNumber": "0904444444", "phoneType": "Home"}])
    assert up["status"] == "updated"
    assert up["contact"]["fullName"] == "Ten Moi"

    assert ctrl.delete_contact(1, cid) is True
    assert ctrl.get_detail(1, cid) is None


def test_csv():
    ctrl.add_contact(1, "An", [{"phoneNumber": "0901000001", "phoneType": "Mobile"}], email="an@mail.com")
    csv_text = ctrl.export_csv(1)
    assert "An" in csv_text

    res = ctrl.import_csv(2, csv_text)
    assert res["imported"] == 1
    assert len(ctrl.list_contacts(2)["items"]) == 1


def test_vcf():
    ctrl.add_contact(1, "Bao", [{"phoneNumber": "0902000002", "phoneType": "Mobile"}], email="bao@mail.com")
    vcf_text = ctrl.export_vcf(1)
    assert "FN:Bao" in vcf_text

    res = ctrl.import_vcf(2, vcf_text)
    assert res["imported"] == 1
    assert len(ctrl.list_contacts(2)["items"]) == 1