from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from models.user_model import User

router = APIRouter(tags=["Authentication & Admin"])
templates = Jinja2Templates(directory="views/templates")

@router.get("/login")
def login_page(request: Request, msg: str = "", error: str = ""):
    return templates.TemplateResponse(request=request, name="login.html", context={"msg": msg, "error": error})

@router.post("/login")
def login_submit(request: Request, email: str = Form(...), password: str = Form(...)):
    user, msg = User.login(email, password)
    if not user:
        return templates.TemplateResponse(request=request, name="login.html", context={"error": msg, "msg": ""})
    request.session["user_id"] = user["userID"]
    request.session["user_name"] = user["fullName"]
    request.session["role"] = user["role"]
    return RedirectResponse(url="/", status_code=303)

@router.get("/register")
def register_page(request: Request, error: str = ""):
    return templates.TemplateResponse(request=request, name="register.html", context={"error": error})

@router.post("/register")
def register_submit(
    request: Request,
    fullName: str = Form(...),
    email: str = Form(...),
    phoneNumber: str = Form(...),
    dateOfBirth: str = Form(""),
    gender: str = Form(""),
    address: str = Form(""),
    password: str = Form(...),
    confirmPassword: str = Form(...)
):
    if password != confirmPassword:
        return templates.TemplateResponse(request=request, name="register.html", context={"error": "Passwords do not match."})
    u = User(fullName=fullName, email=email, phoneNumber=phoneNumber,
             dateOfBirth=dateOfBirth, gender=gender, address=address, password=password)
    ok, msg = u.register()
    if not ok:
        return templates.TemplateResponse(request=request, name="register.html", context={"error": msg})
    return RedirectResponse(url="/login?msg=Registration+is+completed+successfully", status_code=303)

@router.get("/reset-password")
def reset_password_page(request: Request):
    return templates.TemplateResponse(request=request, name="reset_password.html", context={"msg": "", "error": ""})

@router.post("/reset-password")
def reset_password_submit(request: Request, email: str = Form(...)):
    ok, msg = User.resetPassword(email)
    if not ok:
        return templates.TemplateResponse(request=request, name="reset_password.html", context={"error": msg, "msg": ""})
    return templates.TemplateResponse(request=request, name="reset_password.html", context={"msg": msg, "error": ""})

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)

@router.get("/profile")
def profile_page(request: Request, msg: str = "", error: str = ""):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    user = User.get_by_id(user_id)
    return templates.TemplateResponse(request=request, name="profile.html", context={"user": user, "msg": msg, "error": error})

@router.post("/profile")
def profile_update(
    request: Request,
    fullName: str = Form(...),
    phoneNumber: str = Form(...),
    dateOfBirth: str = Form(""),
    gender: str = Form(""),
    address: str = Form(""),
    password: str = Form("")
):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    u = User(userID=user_id, fullName=fullName, phoneNumber=phoneNumber,
             dateOfBirth=dateOfBirth, gender=gender, address=address, password=password)
    ok, msg = u.updateProfile()
    user = User.get_by_id(user_id)
    if not ok:
        return templates.TemplateResponse(request=request, name="profile.html", context={"user": user, "error": msg, "msg": ""})
    request.session["user_name"] = fullName
    return templates.TemplateResponse(request=request, name="profile.html", context={"user": user, "msg": msg, "error": ""})

# Admin: Manage User Accounts
@router.get("/admin/users")
def admin_users_page(request: Request, msg: str = "", error: str = ""):
    if request.session.get("role") != "Admin":
        return RedirectResponse(url="/", status_code=303)
    users = User.viewUserAccounts()
    return templates.TemplateResponse(request=request, name="admin_users.html", context={"users": users, "msg": msg, "error": error})

@router.post("/admin/users/{target_id}/delete")
def admin_delete_user(request: Request, target_id: int):
    if request.session.get("role") != "Admin":
        return RedirectResponse(url="/", status_code=303)
    ok, msg = User.deleteUserAccount(target_id)
    param = f"msg={msg}" if ok else f"error={msg}"
    return RedirectResponse(url=f"/admin/users?{param}", status_code=303)
