from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from database import init_db
from controllers import auth_controller, contact_controller, group_controller

app = FastAPI(title="Phone Book Management System")
app.add_middleware(SessionMiddleware, secret_key="phonebook-super-secret-key")

init_db()

app.mount("/static", StaticFiles(directory="views/static"), name="static")

app.include_router(auth_controller.router)
app.include_router(contact_controller.router)
app.include_router(group_controller.router)
