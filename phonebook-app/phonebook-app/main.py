from fastapi import FastAPI
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
