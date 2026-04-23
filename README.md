#  Sistema de Gestión de Requisiciones

Aplicación web desarrollada para la gestión eficiente de requisiciones dentro de una organización. Permite administrar usuarios, equipos y solicitudes, optimizando los procesos internos mediante una interfaz sencilla y un backend estructurado.

---

##  Tecnologías utilizadas

* **Backend:** Python + FastAPI
* **Frontend:** HTML, CSS, JavaScript
* **Base de datos:** (Configurable desde `.env`)
* **Autenticación:** Manejo de seguridad en `utils/security.py`
* **Arquitectura:** Modular (routes, schemas, config)

---

##  Estructura del proyecto

```
envia_requisiciones/
│
├── main.py                # Punto de entrada de la aplicación
├── auth.py                # Lógica de autenticación
│
├── config/
│   └── database.py        # Configuración de base de datos
│
├── routes/                # Endpoints de la API
│   ├── usuario.py
│   ├── equipo.py
│   └── requisicion.py
│
├── schemas/               # Modelos de datos
│   ├── usuario.py
│   ├── equipo.py
│   └── requisicion.py
│
├── utils/
│   └── security.py        # Funciones de seguridad
│
├── static/                # Frontend
│   ├── index.html
│   ├── dashboard.html
│   ├── script.js
│   └── favicon.ico
│
└── .gitignore
```

---

##  Instalación y ejecución

### 1. Clonar el repositorio

```
git clone https://github.com/TU_USUARIO/requisiciones-app.git
cd requisiciones-app
```

### 2. Crear entorno virtual

```
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```

### 3. Instalar dependencias

```
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Crear archivo `.env` basado en `.env.example`

Ejemplo:

```
DATABASE_URL=tu_base_de_datos
SECRET_KEY=tu_clave_secreta
```

### 5. Ejecutar el servidor

```
uvicorn main:app --reload
```

### 6. Acceder a la aplicación

* Frontend: http://localhost:8000/static/index.html
* Documentación API: http://localhost:8000/docs

---

##  Seguridad

* Uso de variables de entorno para proteger credenciales
* Implementación de funciones de seguridad en el backend
* Exclusión de archivos sensibles mediante `.gitignore`

---

##  Funcionalidades principales

* Gestión de usuarios
* Administración de equipos
* Creación y seguimiento de requisiciones
* Interfaz web para interacción del usuario

---

##  Estado del proyecto

🚧 En desarrollo — Se están implementando mejoras en autenticación, validaciones y experiencia de usuario.

---

##  Autor

Desarrollado por **David Neira**
Estudiante de Ingeniería de Software

---

##  Notas

Este proyecto forma parte de un portafolio personal con fines académicos y profesionales.
