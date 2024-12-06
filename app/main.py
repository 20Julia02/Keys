from fastapi import FastAPI
from app.routers import session, user, unauthorizedUser, auth, device, permission, room, note, operation
from fastapi.middleware.cors import CORSMiddleware
from app.database import create_tables

app = FastAPI()

create_tables()

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://192.168.0.200:8080"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, #tutaj powinna byc tylko domena frontu
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(user.router)
app.include_router(unauthorizedUser.router)
app.include_router(auth.router)
app.include_router(device.router)
app.include_router(permission.router)
app.include_router(room.router)
app.include_router(session.router)
app.include_router(note.router)
app.include_router(operation.router)
