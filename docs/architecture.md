# Architecture

The platform is organized as a monorepo with a Next.js frontend, a FastAPI backend, shared contracts, and infrastructure definitions.

Key boundaries:

- `frontend/` owns user experience, billing screens, and workflow management UI.
- `backend/` owns auth, tenancy, orchestration, workers, integrations, and persistence.
- `shared/` owns DTOs, enums, and payload contracts.
- `infra/` owns Docker, Kubernetes, and deployment automation.

The production sequencing starts with a narrow MVP workflow, then expands into the broader orchestration platform.
