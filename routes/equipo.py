from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def test_equipo():
    return {"message": "Ruta de equipos funcionando"}