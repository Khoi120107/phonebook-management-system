from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import io
from models.contact_model import Contact, PhoneNumber
from models.group_model import Group

router = APIRouter(tags=["Contacts & Import/Export"])
templates = Jinja2Templates(directory="views/templates")

@router.get("/")
def home(request: Request, q: str = "", group_id: str = "", sort: str = "ASC", page: int = 1, msg: str = ""):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    gid = int(group_id) if group_id.isdigit() else None
    contacts = Contact.getContacts(user_id, keyword=q, groupID=gid, sort_order=sort, page=page, per_page=30)
    groups = Group.viewGroups(user_id)
    return templates.TemplateResponse(request=request, name="home.html", context={"contacts": contacts,
        "groups": groups,
        "q": q,
        "selected_group": gid,
        "sort": sort,
        "page": page,
        "msg": msg
    })

@router.get("/contacts/add")
def add_contact_page(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    groups = Group.viewGroups(user_id)
    return templates.TemplateResponse(request=request, name="contact_form.html", context={"groups": groups, "contact": None, "error": "", "dup_warning": None
    })

@router.post("/contacts/add")
def add_contact_submit(
    request: Request,
    fullName: str = Form(...),
    phoneNumber: str = Form(...),
    phoneType: str = Form("Mobile"),
    email: str = Form(""),
    address: str = Form(""),
    note: str = Form(""),
    groupID: str = Form(""),
    dup_action: str = Form("")
):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    gid = int(groupID) if groupID.isdigit() else None
    groups = Group.viewGroups(user_id)
    form_data = {"fullName": fullName, "primaryPhone": phoneNumber, "phoneType": phoneType,
                 "email": email, "address": address, "note": note, "groupID": gid}

    valid, vmsg = Contact.validate_contact_info(fullName, phoneNumber, email)
    if not valid:
        return templates.TemplateResponse(request=request, name="contact_form.html", context={"groups": groups, "contact": form_data, "error": vmsg, "dup_warning": None
        })

    # Duplicate handling (FR-14 & FR-15)
    if not dup_action:
        dups = Contact.check_duplicates(user_id, fullName, phoneNumber)
        if dups["same_phone"]:
            return templates.TemplateResponse(request=request, name="contact_form.html", context={"groups": groups, "contact": form_data, "error": "",
                "dup_warning": {
                    "type": "same_phone",
                    "existing_id": dups["same_phone"]["contactID"],
                    "existing_name": dups["same_phone"]["fullName"],
                    "message": f"Phone number '{phoneNumber}' already exists under contact '{dups['same_phone']['fullName']}'."
                }
            })
        if dups["same_name"]:
            return templates.TemplateResponse(request=request, name="contact_form.html", context={"groups": groups, "contact": form_data, "error": "",
                "dup_warning": {
                    "type": "same_name",
                    "existing_id": dups["same_name"]["contactID"],
                    "existing_name": dups["same_name"]["fullName"],
                    "message": f"Contact name '{fullName}' already exists with a different phone number."
                }
            })
    elif dup_action.startswith("append_phone:"):
        target_cid = int(dup_action.split(":")[1])
        PhoneNumber(contactID=target_cid, phoneNumber=phoneNumber.strip(), phoneType=phoneType).addPhoneNumber()
        return RedirectResponse(url=f"/contacts/{target_cid}?msg=Phone+number+appended+to+existing+contact", status_code=303)
    elif dup_action.startswith("update_name:"):
        target_cid = int(dup_action.split(":")[1])
        c = Contact(contactID=target_cid, userID=user_id, fullName=fullName, email=email, address=address, note=note)
        c.updateContact(phoneNumber, phoneType, gid)
        return RedirectResponse(url=f"/contacts/{target_cid}?msg=Existing+contact+updated", status_code=303)

    c = Contact(userID=user_id, fullName=fullName, email=email, address=address, note=note)
    ok, msg, _ = c.addContact(phoneNumber, phoneType, gid)
    if not ok:
        return templates.TemplateResponse(request=request, name="contact_form.html", context={"groups": groups, "contact": form_data, "error": msg, "dup_warning": None
        })
    return RedirectResponse(url="/?msg=Contact+added+successfully", status_code=303)

@router.get("/contacts/{contact_id}")
def view_contact_detail(request: Request, contact_id: int, msg: str = ""):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    contact = Contact.viewContact(contact_id, user_id)
    if not contact:
        return RedirectResponse(url="/?msg=Contact+not+found", status_code=303)
    return templates.TemplateResponse(request=request, name="contact_detail.html", context={"contact": contact, "msg": msg})

@router.get("/contacts/{contact_id}/edit")
def edit_contact_page(request: Request, contact_id: int):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    contact = Contact.viewContact(contact_id, user_id)
    if not contact:
        return RedirectResponse(url="/", status_code=303)
    groups = Group.viewGroups(user_id)
    contact["groupID"] = contact["groups"][0]["groupID"] if contact["groups"] else None
    return templates.TemplateResponse(request=request, name="contact_form.html", context={"groups": groups, "contact": contact, "error": "", "dup_warning": None
    })

@router.post("/contacts/{contact_id}/edit")
def edit_contact_submit(
    request: Request,
    contact_id: int,
    fullName: str = Form(...),
    phoneNumber: str = Form(...),
    phoneType: str = Form("Mobile"),
    email: str = Form(""),
    address: str = Form(""),
    note: str = Form(""),
    groupID: str = Form("")
):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    gid = int(groupID) if groupID.isdigit() else None
    c = Contact(contactID=contact_id, userID=user_id, fullName=fullName, email=email, address=address, note=note)
    ok, msg = c.updateContact(phoneNumber, phoneType, gid)
    if not ok:
        groups = Group.viewGroups(user_id)
        contact = Contact.viewContact(contact_id, user_id)
        return templates.TemplateResponse(request=request, name="contact_form.html", context={"groups": groups, "contact": contact, "error": msg, "dup_warning": None
        })
    return RedirectResponse(url=f"/contacts/{contact_id}?msg=Contact+updated+successfully", status_code=303)

@router.post("/contacts/{contact_id}/delete")
def delete_contact_submit(request: Request, contact_id: int):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    Contact.deleteContact(contact_id, user_id)
    return RedirectResponse(url="/?msg=Contact+deleted+successfully", status_code=303)

@router.get("/export")
def export_contacts(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    csv_data = Contact.exportContactsCSV(user_id)
    return StreamingResponse(
        io.StringIO(csv_data),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=contacts.csv"}
    )

@router.post("/import")
async def import_contacts(request: Request, file: UploadFile = File(...)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    content = (await file.read()).decode("utf-8", errors="ignore")
    imported, skipped = Contact.importContactsCSV(user_id, content)
    return RedirectResponse(url=f"/?msg=Imported+{imported}+contacts+(skipped+{skipped})", status_code=303)
