# main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from routes import usuario, requisicion

app = FastAPI(title="Requisiciones - Sistema de Requisiciones", version="1.0.0")
app.router.redirect_slashes = False

# ✅ CORS (IMPORTANTE)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# RUTAS SIN PREFIX
app.include_router(usuario.router, tags=["usuarios"])
app.include_router(requisicion.router, tags=["requisiciones"])

# FRONTEND
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home():
    return FileResponse("static/index.html")

@app.get("/dashboard")
def dashboard():
    return FileResponse("static/dashboard.html")
