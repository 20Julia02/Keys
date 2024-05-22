from fastapi import FastAPI
from . import models
from .database import engine
from .routers import user, auth, key, permission


# models.Base.metadata.create_all(engine)
# models.Base.metadata

app = FastAPI()
app.include_router(user.router)
app.include_router(auth.router)
app.include_router(key.router)
app.include_router(permission.router)


@app.get("/")
def root():
    return {"message": "Server is running"}
