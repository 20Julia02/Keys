from fastapi import FastAPI
from .routers import user, auth, device, permission

app = FastAPI()
app.include_router(user.router)
app.include_router(auth.router)
app.include_router(device.router)
app.include_router(permission.router)


@app.get("/")
def root():
    return {"message": "Server is running"}
