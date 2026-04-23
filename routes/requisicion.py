# routes/requisicion.py
from fastapi import APIRouter, Depends, HTTPException
from schemas.requisicion import RequisicionCreate, Requisicion
from routes.usuario import get_current_user
from typing import List
from datetime import datetime
from bson import ObjectId
from config.database import requisiciones
from pydantic import BaseModel
from typing import Optional

aprobado_por_supervisor: Optional[str] = "pendiente"

def requisicion_helper(req) -> dict:
    return {
        "id": str(req["_id"]),
        "estado": req.get("estado"),
        "aprobado_por_supervisor": req.get("aprobado_por_supervisor"),  # 👈 IMPORTANTE
    }


class EstadoUpdate(BaseModel):
    estado: str
    comentarios_tecnico: str | None = None

# ← ¡PRIMERO!
router = APIRouter(prefix="/api/requisiciones")

@router.get("/", response_model=List[Requisicion])
async def get_requisiciones(current_user: dict = Depends(get_current_user)):
    if current_user["rol"] in ["admin", "tecnico", "supervisor"]:
        docs = await requisiciones.find({"empresa_id": current_user["empresa_id"]}).to_list(100)
    else:
        docs = await requisiciones.find({"usuario_id": current_user["id"]}).to_list(100)

    result = []
    for doc in docs:
        item = {
            "id": str(doc["_id"]),
            "tipo_equipo": doc.get("tipo_equipo", ""),
            "problema_descripcion": doc.get("problema_descripcion", ""),
            "usuario_id": str(doc["usuario_id"]),
            "usuario_nombre": doc.get("usuario_nombre", "Anónimo"),
            "estado": doc.get("estado", "pendiente"),
            "empresa_id": current_user["empresa_id"],
            "aprobado_por_supervisor": doc.get("aprobado_por_supervisor", "pendiente"),
            "fecha_solicitud": doc.get("fecha_solicitud"),
            "comentarios_tecnico": doc.get("comentarios_tecnico", ""),
            "equipo_id": str(doc["equipo_id"]) if doc.get("equipo_id") else None,
            "motivo_rechazo": doc.get("motivo_rechazo", "")
        }
        result.append(item)
    return result

@router.post("/", response_model=Requisicion)
async def crear_requisicion(
    req: RequisicionCreate,
    current_user: dict = Depends(get_current_user)
):
    if current_user["rol"] not in ["solicitante", "tecnico", "admin", "supervisor"]:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    doc = req.dict()
    doc.update({
        "usuario_id": current_user["id"],
        "usuario_nombre": current_user["nombre"],
        "empresa_id": current_user["empresa_id"],
        "estado": "pendiente",
        "aprobado_por": None,
        "rechazado_por": None,
        "motivo_rechazo": None,
        "fecha_aprobacion": None,
        "fecha_rechazo": None,
        "fecha_solicitud": datetime.utcnow(),
        "empresa_id": current_user["empresa_id"],
        "comentarios_tecnico": ""
    })
    result = await requisiciones.insert_one(doc)
    creado = await requisiciones.find_one({"_id": result.inserted_id})
    creado["id"] = str(creado["_id"])
    creado.pop("_id", None)
    return creado

@router.patch("/{req_id}/estado", response_model=Requisicion)
async def cambiar_estado(
    req_id: str,
    data: EstadoUpdate,
    current_user: dict = Depends(get_current_user)
):
    if current_user["rol"] not in ["tecnico", "admin", "supervisor"]:  # Añadido "supervisor"
        raise HTTPException(status_code=403, detail="No autorizado")

    estado = data.estado
    if not estado:
        raise HTTPException(status_code=400, detail="Estado requerido")

    # Validar estados según rol
    valid_states = ["pendiente", "en_proceso", "completada"]
    if current_user["rol"] in ["tecnico", "admin"]:
        valid_states.append("aprobada")  # Tecnico y Admin pueden usar todos los estados
    elif current_user["rol"] == "supervisor":
        if estado != "aprobada":
            raise HTTPException(status_code=403, detail="El supervisor solo puede aprobar requisiciones")
    
    if estado not in valid_states:
        raise HTTPException(status_code=400, detail="Estado inválido")

    result = await requisiciones.update_one(
        {"_id": ObjectId(req_id)},
        {"$set": {
            "estado": estado,
            "comentarios_tecnico": data.comentarios_tecnico or ""
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Requisición no encontrada")

    actualizada = await requisiciones.find_one({"_id": ObjectId(req_id)})
    return {
        "id": str(actualizada["_id"]),
        "tipo_equipo": actualizada.get("tipo_equipo", ""),
        "problema_descripcion": actualizada.get("problema_descripcion", ""),
        "usuario_id": str(actualizada["usuario_id"]),
        "usuario_nombre": actualizada.get("usuario_nombre", "Anónimo"),
        "estado": actualizada.get("estado", "pendiente"),
        "empresa_id": actualizada.get("empresa_id", ""),
        "aprobado_por_supervisor": actualizada.get("aprobado_por_supervisor", "pendiente"),
        "fecha_solicitud": actualizada.get("fecha_solicitud"),
        "comentarios_tecnico": actualizada.get("comentarios_tecnico", ""),
        "equipo_id": str(actualizada["equipo_id"]) if actualizada.get("equipo_id") else None
    }
    
@router.patch("/{id}/aprobacion")
async def cambiar_aprobacion(id: str, data: dict, user=Depends(get_current_user)):

    if user["rol"] != "supervisor":
        raise HTTPException(status_code=403, detail="No autorizado")

    if data.get("aprobado_por_supervisor") not in ["aprobado", "rechazado"]:
        raise HTTPException(status_code=400, detail="Valor inválido")

    result = await requisiciones.update_one(
    {"_id": ObjectId(id)},
    {"$set": {
        "aprobado_por_supervisor": data["aprobado_por_supervisor"],
        "motivo_rechazo": data.get("motivo_rechazo", "")
    }}
)

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="No encontrada")

    return {"msg": "Aprobación actualizada"}

print(">>> routes/requisicion.py CARGADO CORRECTAMENTE <<<")
print("Rutas registradas:", [r.path for r in router.routes if hasattr(r, 'path')])

@router.put("/requisiciones/{id}/aprobar")
async def aprobar_requisicion(id: str, user=Depends(get_current_user)):
    if user["rol"] != "supervisor":
        raise HTTPException(403, "Solo supervisores pueden aprobar")

    await requisiciones.update_one(
        {"_id": ObjectId(id)},
        {
            "$set": {
                "estado": "aprobado",
                "aprobado_por": user["nombre"],
                "fecha_aprobacion": datetime.utcnow()
            }
        }
    )

    return {"msg": "Requisición aprobada"}