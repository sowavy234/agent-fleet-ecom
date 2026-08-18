CI & Local Build

What was done:
- Added frontend/public/CNAME with "krushed-diamonds" and committed.
- Created GitHub Actions workflow (.github/workflows/ci.yml) to build backend and frontend on push.

Note: This environment has no Docker or docker-compose available, so containers couldn't be built here.

Local run (recommended):
1. Install Docker and Docker Compose v2 (or use docker-compose). Then from repo root:
   docker compose up --build

Quick dev without Docker:
- Backend: 
  python3 -m venv .venv && source .venv/bin/activate
  pip install -r backend/requirements.txt
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

- Frontend (requires Node >=18 and pnpm):
  cd frontend
  pnpm install
  pnpm dev

Auth seed & login (HTTP):
- Seeded users exist in backend/data/users.json. Set passwords via POST /auth/set-password {"email":"owner@example.com","password":"yourpass"}
- Login: POST /auth/login {"email":"owner@example.com","password":"yourpass"}

CI: pushes to main will run the build workflow; check Actions tab for logs and artifacts.
