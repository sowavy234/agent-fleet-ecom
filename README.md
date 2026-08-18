# agent-fleet-ecom
Scaffold for an E‑commerce Agent Fleet: FastAPI backend with local auth, Next.js frontend, agent definitions, and Docker Compose.

This scaffold supports a NO-API mode (CSV inputs) so you can run without third-party API keys.

Components:
- backend/: FastAPI API for missions, agents, events, and local email/password auth
- frontend/: Next.js + TypeScript + Tailwind dashboard skeleton
- .github/agents/: agent definition YAML for Planner, Scraper, Sourcer, Validator, Analyst, Integrator
- docker-compose.yml to run services locally (backend, frontend, postgres)

Local-auth flow:
- Admin creates user entries (name + email + phone) via POST /admin/users or via seeded DB
- On first login, user sets their password via the frontend flow

Run (local):
- docker compose up --build

