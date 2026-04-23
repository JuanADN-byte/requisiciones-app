from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# === CONFIGURACIÓN DE SEGURIDAD ===
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

SECRET_KEY = "tu_clave_secreta_muy_segura_cambia_esto_123456"  # ¡CÁMBIALO DESPUÉS!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# === FUNCIONES ===
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        rol: str = payload.get("rol")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        return {"sub": user_id, "rol": rol}
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")