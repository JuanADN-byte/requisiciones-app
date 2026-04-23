# routes/usuario.py
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from config.database import usuarios
from schemas.usuario import UsuarioCreate, Usuario, Login
from datetime import datetime, timedelta
from jose import jwt
from typing import Optional
from config.database import empresas
from utils.security import hash_password, verify_password
from dotenv import load_dotenv
import os

router = APIRouter(prefix="/api/usuarios")


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/usuarios/login", auto_error=False)
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "clave_por_defecto_solo_dev")
ALGORITHM = "HS256"

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    if not token:
        return None 
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        correo: str = payload.get("sub")
        if not correo:
            raise HTTPException(401, "Token inválido")
        user = await usuarios.find_one({"correo": correo})
        if not user:
            raise HTTPException(401, "Usuario no encontrado")
        user["id"] = str(user["_id"])
        user.pop("_id", None)
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")

@router.post("/registro", response_model=Usuario)
async def registro(
    usuario: UsuarioCreate,
    current_user: Optional[dict] = Depends(get_current_user)
):
    count = await usuarios.count_documents({})

# Si hay usuarios, verificar si es registro de nueva empresa o creación por admin
    if count > 0:
    # Si no viene empresa en el payload → es creación por admin (requiere token)
        if not usuario.empresa:
            if not current_user or current_user["rol"] != "admin":
                raise HTTPException(status_code=403, detail="Solo admins pueden crear usuarios")
        else:
            # Viene empresa → es registro de nueva empresa, se permite sin token
            # Verificar que esa empresa no tenga ya un admin
            empresa_existente = await empresas.find_one({"nombre": usuario.empresa})
            if empresa_existente:
                admin_existente = await usuarios.find_one({
                    "empresa_id": str(empresa_existente["_id"]),
                    "rol": "admin"
                })
                if admin_existente:
                    raise HTTPException(status_code=400, detail="Esta empresa ya tiene un administrador")

    # 📧 Verificar correo
    existe = await usuarios.find_one({"correo": usuario.correo})
    if existe:
        raise HTTPException(status_code=400, detail="Correo ya registrado")

    # 🏢 MANEJO DE EMPRESA
    if count == 0 or usuario.empresa:
        # Primer usuario O nueva empresa desde registro público
        empresa = await empresas.find_one({"nombre": usuario.empresa})

        if not empresa:
            nueva_empresa = {
            "nombre": usuario.empresa,
            "fecha_creacion": datetime.utcnow()
            }
            result_empresa = await empresas.insert_one(nueva_empresa)
            empresa_id = str(result_empresa.inserted_id)
        else:
            empresa_id = str(empresa["_id"])

        rol = "admin"

    else:
    # Creación de usuario por admin → usa empresa del admin
        empresa_id = current_user["empresa_id"]
        rol = usuario.rol

    # 👤 Crear usuario
    nuevo = {
        "nombre": usuario.nombre,
        "correo": usuario.correo,
        "rol": rol,
        "password": hash_password(usuario.password),
        "fecha_registro": datetime.utcnow(),
        "empresa_id": empresa_id
    }

    result = await usuarios.insert_one(nuevo)
    creado = await usuarios.find_one({"_id": result.inserted_id})

    return {
    "id": str(creado["_id"]),
    "nombre": creado.get("nombre"),
    "correo": creado.get("correo"),
    "rol": creado.get("rol"),
    "empresa_id": creado.get("empresa_id"),
    "fecha_registro": creado.get("fecha_registro")
}

@router.post("/login")
async def login(form: Login):
    user = await usuarios.find_one({"correo": form.correo})

    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    if "password" not in user:
        raise HTTPException(status_code=500, detail="Error en datos del usuario")

    if not verify_password(form.password, user["password"]):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    token = create_access_token({"sub": user["correo"]})

    return {
        "access_token": token,
        "token_type": "bearer"
    }

# --- PERFIL DEL USUARIO ACTUAL ---
@router.get("/perfil")
async def perfil(current_user: dict = Depends(get_current_user)):
    # Remover contraseña del response
    user = current_user.copy()
    user.pop("contraseña", None)
    return user

# --- LISTAR USUARIOS DE LA EMPRESA ---
@router.get("/lista")
async def listar_usuarios(current_user: dict = Depends(get_current_user)):
    if not current_user or current_user["rol"] != "admin":
        raise HTTPException(status_code=403, detail="Solo admins pueden ver usuarios")
    
    lista = await usuarios.find({"empresa_id": current_user["empresa_id"]}).to_list(100)
    return [
        {
            "id": str(u["_id"]),
            "nombre": u.get("nombre"),
            "correo": u.get("correo"),
            "rol": u.get("rol")
        }
        for u in lista
    ]

# --- ELIMINAR USUARIO ---
@router.delete("/{usuario_id}")
async def eliminar_usuario(usuario_id: str, current_user: dict = Depends(get_current_user)):
    if not current_user or current_user["rol"] != "admin":
        raise HTTPException(status_code=403, detail="Solo admins pueden eliminar usuarios")
    
    if usuario_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="No puedes eliminarte a ti mismo")

    from bson import ObjectId
    resultado = await usuarios.delete_one({"_id": ObjectId(usuario_id), "empresa_id": current_user["empresa_id"]})
    
    if resultado.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return {"mensaje": "Usuario eliminado correctamente"}

# --- RESETEAR CONTRASEÑA ---
@router.patch("/{usuario_id}/resetear-password")
async def resetear_password(usuario_id: str, current_user: dict = Depends(get_current_user)):
    if not current_user or current_user["rol"] != "admin":
        raise HTTPException(status_code=403, detail="Solo admins pueden resetear contraseñas")

    if usuario_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Usa el perfil para cambiar tu propia contraseña")

    from bson import ObjectId
    resultado = await usuarios.update_one(
        {"_id": ObjectId(usuario_id), "empresa_id": current_user["empresa_id"]},
        {"$set": {"password": hash_password("0000")}}
    )

    if resultado.matched_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return {"mensaje": "Contraseña reseteada a 0000"}

# --- CAMBIAR PROPIA CONTRASEÑA ---
@router.patch("/mi-password")
async def cambiar_mi_password(data: dict, current_user: dict = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="No autenticado")

    if not verify_password(data.get("password_actual"), current_user["password"]):
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")

    from bson import ObjectId
    await usuarios.update_one(
        {"_id": ObjectId(current_user["id"])},
        {"$set": {"password": hash_password(data.get("password_nueva"))}}
    )
    return {"mensaje": "Contraseña actualizada correctamente"}