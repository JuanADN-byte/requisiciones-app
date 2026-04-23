from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from typing import Optional

class EstadoRequisicion(str, Enum):
    PENDIENTE = "pendiente"
    EN_PROCESO = "en_proceso"
    COMPLETADA = "completada"
    APROBADA = "aprobada"  # Nuevo estado para Supervisor

class RequisicionCreate(BaseModel):
    tipo_equipo: str
    problema_descripcion: str

class Requisicion(BaseModel):
    id: str
    tipo_equipo: str
    problema_descripcion: str
    usuario_id: str
    usuario_nombre: str
    estado: EstadoRequisicion = EstadoRequisicion.PENDIENTE  # Usar Enum
    empresa_id: Optional[str] = None
    aprobado_por_supervisor: Optional[str] = None
    fecha_solicitud: datetime
    comentarios_tecnico: str = ""
    equipo_id: Optional[str] = None
    motivo_rechazo: Optional[str] = ""

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}  # Serializa datetime a ISO