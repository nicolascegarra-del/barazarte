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

Los artistas se crean desde la línea de comandos (no hay registro público):
```bash
docker compose exec backend python -m app.cli create-artist --email artista@ejemplo.com --name "Nombre"
```

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

## Deploy
Coolify sobre VPS. Pendiente de configurar (ver checklist de deploy de Klyp).

## Estado
Frontend y backend creados; la integración completa con Docker (Postgres, MinIO, envío real de emails) aún no está verificada de punta a punta.
