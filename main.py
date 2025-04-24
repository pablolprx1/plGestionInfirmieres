from fastapi import FastAPI
from app.api.visites import router as visites_router
from app.api.auth import router as auth_router

app = FastAPI()
app.include_router(auth_router, tags=["Authentification"]) # Authentification
app.include_router(visites_router, prefix="/visites", tags=["Visites"]) # Visites
