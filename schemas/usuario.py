# schemas/usuario.py
from pydantic import BaseModel, EmailStr
from typing import Literal
from datetime import datetime
from typing import Optional

class UsuarioCreate(BaseModel):
    nombre: str
    correo: EmailStr
    rol: Optional[Literal["solicitante", "tecnico", "admin", "supervisor"]] = "solicitante"
    password: str
    empresa: Optional[str] = None

class Usuario(BaseModel):
    id: str
    nombre: str
    correo: EmailStr
    rol: Literal["solicitante", "tecnico", "admin", "supervisor"]
    empresa_id: Optional[str] = None
    fecha_registro: datetime

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

class Login(BaseModel):
    correo: EmailStr
    password: str