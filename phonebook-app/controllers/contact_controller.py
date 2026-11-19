import csv
import io
from fastapi import APIRouter, HTTPException, UploadFile, File, Response
from pydantic import BaseModel

from models.contact_model import Contact, PhoneNumber, ContactModel


class PhoneData(BaseModel):
    phoneNumber: str
    phoneType: str = "Mobile"


class ContactData(BaseModel):
    userID: int = 1
    fullName: str
    email: str = ""
    address: str = ""
    note: str = ""
    isBlocked: bool = False
    phoneNumbers: list[PhoneData]
    groupIDs: list[int] = []
    action: str = ""


class ContactController:
    def __init__(self):
        self.model = ContactModel()

    # Kiểm tra dữ liệu đầu vào trước khi lưu
    def validate_contact(self, fullName, phone_list, email=""):
        if not fullName or fullName.strip() == "":
            return "Họ tên không được để trống"
        if not phone_list or len(phone_list) == 0:
            return "Phải có ít nhất một số điện thoại"

        for p in phone_list:
            sdt = p.get("phoneNumber", "").strip()
            sdt_so = sdt.replace(" ", "").replace("-", "").replace("+", "")
            if not sdt_so.isdigit() or len(sdt_so) < 8 or len(sdt_so) > 15:
                return "Số điện thoại không hợp lệ: " + sdt

        if email and email.strip() != "":
            if "@" not in email or "." not in email:
                return "Email không hợp lệ: " + email

        return ""

    def list_contacts(self, userID, page=1, page_size=30, sort_order="ASC", groupID=None):
        return Contact.sortContact(userID, sort_order, page, page_size, groupID)

    def get_detail(self, userID, contactID):
        contact = Contact.viewContact(userID, contactID)
        if contact:
            return contact.to_dict()
        return None

    def search_contacts(self, userID, keyword):
        ds = Contact.searchContact(userID, keyword)
        return [c.to_dict() for c in ds]

    def add_contact(self, userID, fullName, phone_list, email="", address="", note="", groupIDs=None, action=""):
        loi = self.validate_contact(fullName, phone_list, email)
        if loi != "":
            raise ValueError(loi)

        # Kiểm tra trùng SĐT khác tên
        for p in phone_list:
            owner = self.model.find_by_phone(userID, p["phoneNumber"])
            if owner:
                if action == "":
                    return {
                        "status": "duplicate_phone",
                        "message": f"Số {p['phoneNumber']} đã thuộc về {owner.fullName}",
                        "existingContact": owner.to_dict(),
                    }
                if action == "update_name":
                    owner.fullName = fullName.strip()
                    owner.updateContact()
                    return {"status": "updated_name", "contact": owner.to_dict()}
                if action == "merge":
                    owner.fullName = fullName.strip()
                    if email.strip() != "":
                        owner.email = email.strip()
                    if address.strip() != "":
                        owner.address = address.strip()
                    if note.strip() != "":
                        owner.note = note.strip()
                    owner.updateContact()
                    return {"status": "merged", "contact": owner.to_dict()}

        # Kiểm tra trùng tên khác SĐT
        same_names = self.model.find_by_name(userID, fullName)
        if len(same_names) > 0:
            if action == "":
                return {
                    "status": "duplicate_name",
                    "message": f"Tên {fullName} đã tồn tại trong danh bạ",
                    "existingContact": same_names[0].to_dict(),
                }
            if action == "append":
                target = same_names[0]
                for p in phone_list:
                    pn = PhoneNumber(p["phoneNumber"], p.get("phoneType", "Mobile"), contactID=target.contactID)
                    pn.addPhoneNumber()
                updated = self.model.get_by_id(userID, target.contactID)
                return {"status": "appended", "contact": updated.to_dict()}

        # Tạo liên hệ mới
        phones = [PhoneNumber(p["phoneNumber"], p.get("phoneType", "Mobile")) for p in phone_list]
        contact = Contact(
            userID=userID,
            fullName=fullName,
            email=email,
            address=address,
            note=note,
            phoneNumbers=phones,
            groupIDs=groupIDs if groupIDs else [],
        )
        contact.addContact()
        return {"status": "created", "contact": contact.to_dict()}

    def update_contact(self, userID, contactID, fullName, phone_list, email="", address="", note="", isBlocked=False, groupIDs=None):
        existing = self.model.get_by_id(userID, contactID)
        if not existing:
            return None

        loi = self.validate_contact(fullName, phone_list, email)
        if loi != "":
            raise ValueError(loi)

        for p in phone_list:
            owner = self.model.find_by_phone(userID, p["phoneNumber"])
            if owner and owner.contactID != contactID:
                return {
                    "status": "duplicate_phone",
                    "message": f"Số {p['phoneNumber']} đã thuộc về {owner.fullName}",
                }

        phones = [PhoneNumber(p["phoneNumber"], p.get("phoneType", "Mobile")) for p in phone_list]
        contact = Contact(
            contactID=contactID,
            userID=userID,
            fullName=fullName,
            email=email,
            address=address,
            note=note,
            isBlocked=isBlocked,
            phoneNumbers=phones,
            groupIDs=groupIDs if groupIDs is not None else existing.groupIDs,
        )
        contact.updateContact()
        updated = self.model.get_by_id(userID, contactID)
        return {"status": "updated", "contact": updated.to_dict()}

    def delete_contact(self, userID, contactID):
        return self.model.delete(userID, contactID)

    # Xuất / Nhập file CSV
    def export_csv(self, userID):
        data = self.model.get_list(userID, page=1, page_size=10000)["items"]
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["fullName", "phoneNumbers", "email", "address", "note"])
        for c in data:
            phones = ";".join([p["phoneNumber"] for p in c["phoneNumbers"]])
            writer.writerow([c["fullName"], phones, c["email"], c["address"], c["note"]])
        return output.getvalue()

    def import_csv(self, userID, csv_text):
        reader = csv.DictReader(io.StringIO(csv_text))
        imported = 0
        skipped = 0
        for row in reader:
            name = (row.get("fullName") or "").strip()
            raw_phones = (row.get("phoneNumbers") or "").split(";")
            phones = [{"phoneNumber": p.strip(), "phoneType": "Mobile"} for p in raw_phones if p.strip()]
            try:
                res = self.add_contact(
                    userID,
                    name,
                    phones,
                    email=row.get("email", ""),
                    address=row.get("address", ""),
                    note=row.get("note", ""),
                    action="create_new",
                )
                if res["status"] == "created":
                    imported += 1
                else:
                    skipped += 1
            except ValueError:
                skipped += 1
        return {"imported": imported, "skipped": skipped}

    # Xuất / Nhập file VCF (vCard)
    def export_vcf(self, userID):
        data = self.model.get_list(userID, page=1, page_size=10000)["items"]
        lines = []
        for c in data:
            lines.append("BEGIN:VCARD")
            lines.append("VERSION:3.0")
            lines.append("FN:" + c["fullName"])
            for p in c["phoneNumbers"]:
                lines.append("TEL;TYPE=" + p["phoneType"].upper() + ":" + p["phoneNumber"])
            if c["email"]:
                lines.append("EMAIL:" + c["email"])
            if c["address"]:
                lines.append("ADR:;;" + c["address"] + ";;;;")
            if c["note"]:
                lines.append("NOTE:" + c["note"])
            lines.append("END:VCARD")
        return "\n".join(lines)

    def import_vcf(self, userID, vcf_text):
        imported = 0
        skipped = 0
        blocks = vcf_text.split("BEGIN:VCARD")
        for block in blocks[1:]:
            name = ""
            email = ""
            address = ""
            note = ""
            phones = []
            for line in block.splitlines():
                line = line.strip()
                if line.startswith("FN:"):
                    name = line[3:].strip()
                elif line.startswith("TEL"):
                    val = line.split(":", 1)[-1].strip()
                    if val != "":
                        phones.append({"phoneNumber": val, "phoneType": "Mobile"})
                elif line.startswith("EMAIL:"):
                    email = line[6:].strip()
                elif line.startswith("ADR:"):
                    address = line[4:].replace(";", " ").strip()
                elif line.startswith("NOTE:"):
                    note = line[5:].strip()
            try:
                res = self.add_contact(
                    userID, name, phones, email=email, address=address, note=note, action="create_new"
                )
                if res["status"] == "created":
                    imported += 1
                else:
                    skipped += 1
            except ValueError:
                skipped += 1
        return {"imported": imported, "skipped": skipped}


router = APIRouter(prefix="/api/contacts", tags=["Contacts"])
controller = ContactController()


@router.get("/")
def api_list_contacts(userID: int, page: int = 1, pageSize: int = 30, sortOrder: str = "ASC", groupID: int = None):
    return controller.list_contacts(userID, page, pageSize, sortOrder, groupID)


@router.get("/search")
def api_search_contacts(userID: int, keyword: str = ""):
    return controller.search_contacts(userID, keyword)


@router.get("/export/csv")
def api_export_csv(userID: int):
    csv_data = controller.export_csv(userID)
    return Response(
        content=csv_data.encode("utf-8-sig"),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=contacts.csv"},
    )


@router.post("/import/csv")
async def api_import_csv(userID: int, file: UploadFile = File(...)):
    content = (await file.read()).decode("utf-8-sig")
    return controller.import_csv(userID, content)


@router.get("/export/vcf")
def api_export_vcf(userID: int):
    vcf_data = controller.export_vcf(userID)
    return Response(
        content=vcf_data.encode("utf-8"),
        media_type="text/vcard",
        headers={"Content-Disposition": "attachment; filename=contacts.vcf"},
    )


@router.post("/import/vcf")
async def api_import_vcf(userID: int, file: UploadFile = File(...)):
    content = (await file.read()).decode("utf-8")
    return controller.import_vcf(userID, content)


@router.get("/{contactID}")
def api_get_detail(contactID: int, userID: int):
    detail = controller.get_detail(userID, contactID)
    if not detail:
        raise HTTPException(status_code=404, detail="Không tìm thấy liên hệ")
    return detail


@router.post("/")
def api_add_contact(data: ContactData):
    phones = [{"phoneNumber": p.phoneNumber, "phoneType": p.phoneType} for p in data.phoneNumbers]
    try:
        return controller.add_contact(
            data.userID, data.fullName, phones, data.email, data.address, data.note, data.groupIDs, data.action
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{contactID}")
def api_update_contact(contactID: int, userID: int, data: ContactData):
    phones = [{"phoneNumber": p.phoneNumber, "phoneType": p.phoneType} for p in data.phoneNumbers]
    try:
        res = controller.update_contact(
            userID, contactID, data.fullName, phones, data.email, data.address, data.note, data.isBlocked, data.groupIDs
        )
        if res is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy liên hệ")
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{contactID}")
def api_delete_contact(contactID: int, userID: int):
    ok = controller.delete_contact(userID, contactID)
    if not ok:
        raise HTTPException(status_code=404, detail="Không tìm thấy liên hệ để xóa")
    return {"status": "deleted", "contactID": contactID}