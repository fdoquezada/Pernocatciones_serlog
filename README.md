# 🌙 Sistema de Control de Pernoctaciones

## Estructura del proyecto

```
pernoctaciones/
├── config/              → Configuración Django
├── apps/
│   ├── core/            → Modelos principales + dashboard
│   ├── tms/             → Carga y filtrado del archivo TMS
│   ├── notificaciones/  → Envío de mails a transportes
│   ├── transportes/     → Página pública para transportes (token)
│   ├── validacion/      → Validación turno noche
│   └── reportes/        → Reporte de cierre + envío a jefatura
└── templates/           → Todas las vistas HTML
```

---

## Instalación local

### 1. Clonar y crear entorno virtual
```bash
git clone <tu-repositorio>
cd pernoctaciones
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
pip install dj-database-url     # Agregar al requirements.txt también
```

### 3. Crear archivo .env
```bash
cp .env.example .env
```
Edita `.env` con tus valores:
```
SECRET_KEY=genera-una-clave-segura-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3        # Para desarrollo local
SENDGRID_API_KEY=tu-api-key
DEFAULT_FROM_EMAIL=pernoctaciones@tuempresa.cl
EMAIL_JEFATURA=jefatura@tuempresa.cl
DOMINIO=http://localhost:8000
```

### 4. Crear base de datos y superusuario
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 5. Correr el servidor
```bash
python manage.py runserver
```
Abre http://localhost:8000

---

## Despliegue en Railway

### 1. Crear proyecto en Railway
- Ir a https://railway.app
- Nuevo proyecto → Deploy from GitHub repo

### 2. Agregar PostgreSQL
- En Railway: New → Database → PostgreSQL
- Se genera automáticamente la variable `DATABASE_URL`

### 3. Variables de entorno en Railway
En tu servicio Django, ir a Variables y agregar:
```
SECRET_KEY=<clave-segura>
DEBUG=False
ALLOWED_HOSTS=tuapp.railway.app
DATABASE_URL=<se llena automático con PostgreSQL>
SENDGRID_API_KEY=<tu-api-key>
DEFAULT_FROM_EMAIL=pernoctaciones@tuempresa.cl
EMAIL_JEFATURA=jefatura@tuempresa.cl
DOMINIO=https://tuapp.railway.app
```

### 4. Primer deploy
Railway detecta el `Procfile` y ejecuta:
```
web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

### 5. Crear superusuario en producción
```bash
railway run python manage.py createsuperuser
```

---

## Configurar SendGrid (gratis hasta 100 mails/día)

1. Crear cuenta en https://sendgrid.com
2. Settings → API Keys → Create API Key (Full Access)
3. Copiar la clave en `SENDGRID_API_KEY`
4. Verificar el dominio o email remitente en SendGrid

---

## Crear usuarios y transportes

### Usuarios
En `/admin/auth/user/` crear:
- **Administrador**: `is_staff = True`, `is_superuser = True`
- **Operador turno**: solo `is_active = True`

### Transportes
En `/admin/core/transporte/` registrar cada empresa de transporte con su email.
El sistema actualiza el email automáticamente si el operador lo corrige al enviar un mail.

---

## Flujo completo del sistema

```
1. TURNO TARDE
   └── Subir archivo TMS → /tms/cargar/
   └── Revisar tabla filtrada → /tms/revision/
   └── Confirmar → crea registros en BD

2. MEDIODÍA
   └── Enviar mails a transportes → /notificaciones/enviar/
   └── Cada transporte recibe link único

3. TRANSPORTE RESPONDE
   └── Abre link del mail → /transporte/<token>/
   └── Llena lugar + hora ETA (o marca sin señal)

4. TURNO NOCHE — Primera validación
   └── Verificar llegada antes 00:00 → /validacion/primera/
   └── Botones CUMPLE / NO CUMPLE / SIN SEÑAL
   └── Si hay atraso: activar extensión horaria

5. TURNO NOCHE — Segunda validación
   └── Ingresar hora de salida → /validacion/ocho-horas/
   └── Sistema calcula horas automáticamente
   └── Marca CUMPLE / NO CUMPLE 8 horas

6. CIERRE DE TURNO
   └── Ver reporte con KPIs → /reportes/cierre/
   └── Enviar reporte a jefatura/cliente
```

---

## URLs del sistema

| URL | Descripción |
|-----|-------------|
| `/` | Dashboard con estadísticas del día |
| `/tms/cargar/` | Subir archivo TMS |
| `/tms/revision/` | Revisar equipos filtrados |
| `/notificaciones/enviar/` | Enviar mails a transportes |
| `/transporte/<token>/` | Formulario público del transporte |
| `/validacion/primera/` | Validar llegada antes 00:00 |
| `/validacion/ocho-horas/` | Validar 8 horas de descanso |
| `/reportes/cierre/` | Reporte de cierre + envío |
| `/admin/` | Panel de administración |
