from fastapi import FastAPI
from . import models
from .database import engine
from .routers import user


models.Base.metadata.create_all(engine)
models.Base.metadata

app = FastAPI()
app.include_router(user.router)


@app.get("/")
def root():
    return {"message": "Server is running"}
