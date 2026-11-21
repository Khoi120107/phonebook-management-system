from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from models.group_model import Group, BlockedContact

router = APIRouter(tags=["Groups & Blocked Contacts"])
templates = Jinja2Templates(directory="views/templates")

@router.get("/groups")
def groups_page(request: Request, msg: str = "", error: str = ""):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    groups = Group.viewGroups(user_id)
    return templates.TemplateResponse(request=request, name="groups.html", context={"groups": groups, "msg": msg, "error": error})

@router.post("/groups/add")
def add_group(request: Request, groupName: str = Form(...), description: str = Form("")):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    ok, msg = Group(userID=user_id, groupName=groupName, description=description).createGroup()
    param = f"msg={msg}" if ok else f"error={msg}"
    return RedirectResponse(url=f"/groups?{param}", status_code=303)

@router.post("/groups/{group_id}/edit")
def edit_group(request: Request, group_id: int, groupName: str = Form(...), description: str = Form("")):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    ok, msg = Group(groupID=group_id, userID=user_id, groupName=groupName, description=description).updateGroup()
    param = f"msg={msg}" if ok else f"error={msg}"
    return RedirectResponse(url=f"/groups?{param}", status_code=303)

@router.post("/groups/{group_id}/delete")
def delete_group(request: Request, group_id: int):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    ok, msg = Group.deleteGroup(group_id, user_id)
    param = f"msg={msg}" if ok else f"error={msg}"
    return RedirectResponse(url=f"/groups?{param}", status_code=303)

@router.get("/blocked")
def blocked_page(request: Request, msg: str = "", error: str = ""):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    blocked = BlockedContact.viewBlockedContacts(user_id)
    return templates.TemplateResponse(request=request, name="blocked.html", context={"blocked": blocked, "msg": msg, "error": error})

@router.post("/contacts/{contact_id}/block")
def block_contact(request: Request, contact_id: int):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    ok, msg = BlockedContact.blockContact(contact_id, user_id)
    return RedirectResponse(url=f"/blocked?msg={msg}", status_code=303)

@router.post("/contacts/{contact_id}/unblock")
def unblock_contact(request: Request, contact_id: int):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    ok, msg = BlockedContact.unblockContact(contact_id, user_id)
    return RedirectResponse(url=f"/blocked?msg={msg}", status_code=303)
