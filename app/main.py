from fastapi import FastAPI
from .routers import user, auth, device, permission, room
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()


origins = [
    "http://localhost",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(user.router)
app.include_router(auth.router)
app.include_router(device.router)
app.include_router(permission.router)
app.include_router(room.router)


@app.get("/")
def root():
    return {"message": "Server is running"}
