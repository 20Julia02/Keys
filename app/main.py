from fastapi import FastAPI
from app.routers import user, unauthorizedUser, auth, device, permission, room, approve, note
from fastapi.middleware.cors import CORSMiddleware
from app.database import create_tables

app = FastAPI()

create_tables()

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:8080"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
app.include_router(approve.router)
app.include_router(note.router)
