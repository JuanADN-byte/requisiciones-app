# config/database.py
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
import certifi

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME")

if not MONGODB_URL or not DATABASE_NAME:
    raise ValueError("Faltan variables en .env")

client = AsyncIOMotorClient(
    MONGODB_URL,
    tlsCAFile=certifi.where()
)

database = client[DATABASE_NAME]

usuarios = database.get_collection("usuarios")
equipos = database.get_collection("equipos")
requisiciones = database.get_collection("requisiciones")
empresas = database.get_collection("empresas")