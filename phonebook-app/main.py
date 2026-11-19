from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from database import init_db

app = FastAPI(title="Phone Book Management System")

# Khởi tạo 5 bảng CSDL ngay khi chạy app
init_db()

# Kết nối thư mục giao diện cho TV5
app.mount("/static", StaticFiles(directory="views/static"), name="static")
templates = Jinja2Templates(directory="views/templates")

@app.get("/")
def read_root():
    return {"message": "Phone Book Management System is running!"}

# Route cho trang Đăng Nhập 
@app.get("/login", response_class=HTMLResponse)
def show_login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

# Route cho trang Đăng Ký 
@app.get("/register", response_class=HTMLResponse)
def show_register_page(request: Request):
    return templates.TemplateResponse(request=request, name="register.html")

# Route cho trang chủ (Danh bạ)
@app.get("/", response_class=HTMLResponse)
def show_home_page(request: Request):
    return templates.TemplateResponse(request=request, name="home.html", context={"contacts": []})
