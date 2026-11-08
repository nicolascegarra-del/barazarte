# BarazArte

Galería online de cuadros con varios artistas. Cada artista sube sus obras desde un panel (pensado primero para móvil) y los visitantes contactan con él por formulario; no hay pago online.

## Requisitos previos
- Node.js 22+ y npm
- Docker y Docker Compose (backend, Postgres, Redis, MinIO, Mailpit)

## Instalación y arranque local
```bash
# Backend y servicios
export JWT_SECRET_KEY=$(openssl rand -hex 32)
docker compose up --build

# Frontend
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Los artistas se registran solos en `/registro` (confirman su email y ya pueden subir obras; límite por defecto: 5 obras).
El primer administrador se crea por línea de comandos (pide la contraseña por teclado):
```bash
docker compose exec backend python -m app.cli create-artist --admin --email admin@ejemplo.com --name "Nombre"
```

El admin (`/admin`) ve estadísticas, gestiona artistas (límite de obras, deshabilitar, resetear contraseña por email) y
configura en `/admin/correo` la única cuenta SMTP con la que se envían todos los emails. En desarrollo, Mailpit
(http://localhost:8025) recoge los emails: usa servidor `mailpit`, puerto `1025`, seguridad "Ninguna".

Notas de desarrollo:
- El almacenamiento S3 local es RustFS (MinIO ya no publica imágenes oficiales en Docker Hub).
- La contraseña SMTP se cifra con una clave derivada de `JWT_SECRET_KEY` (o `SETTINGS_ENCRYPTION_KEY`); si cambia, hay que volver a introducirla.
- Si el frontend corre en otro puerto que el 3000, añádelo a `CORS_ORIGINS` en `docker-compose.yml`.

## Variables de entorno necesarias
- `backend/.env.example`: base de datos, Redis, JWT, MinIO, SMTP, CORS.
- `frontend/.env.example`: `NEXT_PUBLIC_API_URL` (por defecto `http://localhost:8000`).

## Estructura del proyecto
- `frontend/`: Next.js 15 + Tailwind v4 (web pública y panel del artista).
- `backend/`: FastAPI + SQLModel + Celery (API, imágenes, emails).
- `docker-compose.yml`: servicios de desarrollo.

## Comandos útiles
```bash
cd frontend && npm run lint && npx tsc --noEmit && npm run build
cd backend && pytest && ruff check .
```

## Deploy (Coolify)
No uses `docker-compose.yml` (es solo para desarrollo: abre puertos y usa contraseñas de ejemplo).
En Coolify crea un recurso **Docker Compose** apuntando a este repositorio con
**Docker Compose Location** = `/docker-compose.prod.yml` y asigna un dominio HTTPS a cada servicio
(subdominios del mismo dominio, porque la cookie de sesión es `SameSite=Strict`):

| Servicio | Dominio de ejemplo | Puerto |
|---|---|---|
| `frontend` | `https://barazarte.com` | 3000 |
| `backend` | `https://api.barazarte.com` | 8000 |
| `storage` | `https://media.barazarte.com` | 9000 |

Variables de entorno en Coolify (todas obligatorias salvo las de SMTP):

| Variable | Valor |
|---|---|
| `JWT_SECRET_KEY` | `openssl rand -hex 32` (no cambiarla después: cifra la contraseña SMTP guardada) |
| `POSTGRES_PASSWORD` | contraseña larga y aleatoria |
| `S3_ACCESS_KEY` / `S3_SECRET_KEY` | claves del almacenamiento de fotos (elige valores aleatorios) |
| `FRONTEND_URL` | `https://barazarte.com` |
| `API_URL` | `https://api.barazarte.com` |
| `MEDIA_URL` | `https://media.barazarte.com` |
| `SMTP_*`, `MAIL_FROM` | opcionales: el admin configura el correo desde `/admin/correo` |

Primer despliegue: crea el administrador desde el terminal del contenedor `backend`:
```bash
python -m app.cli create-artist --admin --email admin@tudominio.com --name "Tu nombre"
```
Después entra en `/admin/correo` y configura la cuenta SMTP real. Haz una copia de seguridad de Postgres antes de cada migración.

## Estado
Probado en local con Docker: registro y verificación, login, límite de obras, subida de fotos a S3, publicación,
consultas con email al artista, panel de admin y configuración de correo. Pendiente: tests E2E automáticos (Playwright),
revisión responsive completa, política de privacidad real y despliegue en Coolify.
