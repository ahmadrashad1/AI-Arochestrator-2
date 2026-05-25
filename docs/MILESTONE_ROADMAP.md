# Milestone Roadmap

This roadmap compresses the full build plan into delivery milestones. Each milestone builds on the previous one and should not start until its checkpoint is green.

## Milestone 1 - Foundation

Implementation checklist:
- Create the root scaffold files: `.env.example`, `.gitignore`, `docker-compose.yml`, `Makefile`, and `README.md`.
- Create the frontend bootstrap files: `frontend/package.json`, `frontend/next.config.mjs`, `frontend/tsconfig.json`, `frontend/postcss.config.mjs`, `frontend/tailwind.config.ts`, `frontend/.eslintrc.json`, `frontend/next-env.d.ts`, `frontend/src/app/layout.tsx`, `frontend/src/app/page.tsx`, and `frontend/src/app/globals.css`.
- Create the backend bootstrap files: `backend/pyproject.toml`, `backend/requirements.txt`, `backend/Dockerfile`, `backend/app/__init__.py`, `backend/app/main.py`, `backend/app/core/__init__.py`, `backend/app/core/config.py`, `backend/app/api/v1/__init__.py`, and `backend/app/api/v1/health.py`.
- Create the repository scaffolding folders: `shared/`, `infra/`, `scripts/`, and `docs/`.
- Document the architecture and delivery path in `docs/architecture.md` and `docs/BUILD_PLAN.md`.

Validation checklist:
- Run `docker compose config` and confirm `postgres`, `redis`, and `qdrant` resolve.
- Run `python -m py_compile backend\\app\\main.py backend\\app\\api\\v1\\health.py backend\\app\\core\\config.py` and confirm there are no syntax errors.
- Run `npm run build` in `frontend/` after installing dependencies and confirm the app compiles.
- Run `npm run lint` in `frontend/` after installing dependencies and confirm the bootstrap files satisfy the lint rules.
- Start the backend with `uvicorn app.main:app --host 0.0.0.0 --port 8000` and confirm `GET /health` returns `{"status":"ok"}`.

## Milestone 2 - Identity and Tenant Isolation

Implementation checklist:
- Add authentication primitives in `backend/app/auth/jwt.py`, `backend/app/auth/rbac.py`, `backend/app/auth/middleware.py`, and `backend/app/core/security.py`.
- Add tenant scoping helpers in `backend/app/tenancy/tenant_context.py`, `backend/app/tenancy/tenant_router.py`, `backend/app/tenancy/tenant_limits.py`, and `backend/app/tenancy/usage_meter.py`.
- Add identity models and repository entry points in `backend/app/database/models/user.py`, `backend/app/database/models/tenant.py`, `backend/app/database/models/workspace.py`, and `backend/app/database/repositories/`.
- Add audit logging and request context support in `backend/app/core/logging.py` and `backend/app/core/dependencies.py`.
- Add API endpoints for login, current-user lookup, and tenant-aware access control in `backend/app/api/v1/auth.py`, `backend/app/api/v1/users.py`, `backend/app/api/v1/tenants.py`, and `backend/app/api/v1/workspaces.py`.

Validation checklist:
- Run auth integration tests and confirm login, token verification, and current-user lookup succeed for valid credentials.
- Run tenant isolation tests and confirm tenant-scoped queries cannot return another tenant’s records.
- Run RBAC tests and confirm each role is allowed only the operations it should have.
- Run unauthorized-access tests and confirm protected routes return the expected HTTP status codes.
- Run `python -m py_compile` over the touched backend files and confirm there are no syntax errors.

## Milestone 3 - Durable Data Layer

Implementation checklist:
- Add SQLAlchemy models in `backend/app/database/models/user.py`, `backend/app/database/models/tenant.py`, `backend/app/database/models/workspace.py`, `backend/app/database/models/workflow.py`, `backend/app/database/models/execution.py`, `backend/app/database/models/integration.py`, and `backend/app/database/models/usage.py`.
- Add database session and connection helpers in `backend/app/database/connection.py` and `backend/app/database/session.py`.
- Add repository abstractions in `backend/app/database/repositories/user_repository.py`, `backend/app/database/repositories/tenant_repository.py`, `backend/app/database/repositories/workspace_repository.py`, `backend/app/database/repositories/workflow_repository.py`, `backend/app/database/repositories/execution_repository.py`, and `backend/app/database/repositories/base.py`.
- Add Alembic migration scaffolding in `backend/app/database/migrations/` and create the initial schema migration for the core tables.
- Add durable checkpoint storage in `backend/app/memory/short_term/checkpoint_store.py` and `backend/app/orchestrator/workflow_runner.py`.

Validation checklist:
- Run migrations against a clean database and confirm the core tables are created with the expected columns and foreign keys.
- Run CRUD tests for users, tenants, workspaces, workflows, and executions and confirm create, read, update, and delete operations behave correctly.
- Run checkpoint-resume tests and confirm workflow execution state is restored after a simulated process restart.
- Run `python -m py_compile` over the touched backend persistence files and confirm there are no syntax errors.

## Milestone 4 - Workflow API Contract

Implementation checklist:
- Add workflow API routes in `backend/app/api/v1/workflows.py`, `backend/app/api/v1/executions.py`, and `backend/app/api/v1/automations.py`.
- Add request and response schemas in `shared/schemas/workflow.py`, `shared/schemas/execution.py`, and `shared/dto/workflow_requests.py`.
- Add workflow service logic in `backend/app/orchestrator/engine.py`, `backend/app/orchestrator/workflow_runner.py`, `backend/app/orchestrator/execution_manager.py`, and `backend/app/state/workflow_state.py`.
- Add request validation, quota checks, and idempotency guards in `backend/app/core/dependencies.py`, `backend/app/billing/quota_manager.py`, and `backend/app/tenancy/usage_meter.py`.
- Add execution status and progress retrieval handlers in `backend/app/api/v1/executions.py` with polling or streaming support.

Validation checklist:
- Run workflow creation and run API tests and confirm valid payloads create executions and invalid payloads fail with clear errors.
- Run execution status tests and confirm progress can be retrieved by polling or streaming while the workflow is running.
- Run idempotency tests and confirm duplicate submissions do not create duplicate executions.
- Run quota and request validation tests and confirm blocked tenants receive the expected response codes.
- Run `python -m py_compile` over the touched backend workflow API and orchestration files and confirm there are no syntax errors.

## Milestone 5 - Async Orchestration

Implementation checklist:
- Add queue primitives in `backend/app/workers/celery.py`, `backend/app/orchestrator/event_bus.py`, and `backend/app/orchestrator/scheduler.py`.
- Add worker entrypoints in `backend/app/workers/workflow_worker.py`, `backend/app/workers/tool_worker.py`, `backend/app/workers/retry_worker.py`, and `backend/app/workers/cleanup_worker.py`.
- Add retry and recovery logic in `backend/app/orchestrator/retry_manager.py` and `backend/app/orchestrator/execution_manager.py`.
- Add dead-letter handling and notification dispatch in `backend/app/orchestrator/engine.py` and `backend/app/observability/alerts.py`.
- Add queue-backed workflow state transitions in `backend/app/state/execution_state.py` and `backend/app/state/shared_state.py`.

Validation checklist:
- Run queue-enqueue tests and confirm a workflow request is persisted to Redis or the configured queue backend instead of executing inline.
- Run worker-processing tests and confirm a queued workflow is picked up and completed by a worker process.
- Run retry-policy tests and confirm exponential backoff and retry limits behave as expected.
- Run dead-letter tests and confirm permanently failing jobs are routed to the dead-letter path.
- Run a request-latency smoke test and confirm synchronous API handling remains fast while work is processed asynchronously.
- Run `python -m py_compile` over the touched worker and queue files and confirm there are no syntax errors.

## Milestone 6 - LLM Gateway

Implementation checklist:
- Add the provider abstraction in `backend/app/llm/router.py`, `backend/app/llm/prompt_manager.py`, `backend/app/llm/cost_tracker.py`, and `backend/app/llm/token_tracker.py`.
- Add Grok/xAI provider support in `backend/app/llm/providers/grok_provider.py` and wire provider selection into `backend/app/llm/providers/`.
- Add fallback provider support in `backend/app/llm/providers/openai_provider.py`, `backend/app/llm/providers/anthropic_provider.py`, and `backend/app/llm/providers/gemini_provider.py`.
- Add model routing policy in `backend/app/orchestrator/engine.py` and `backend/app/core/constants.py` for cheap, standard, and high-confidence task tiers.
- Add cost and token accounting hooks in `backend/app/observability/metrics.py` and `backend/app/observability/logging.py`.

Validation checklist:
- Run provider routing tests and confirm cheap, standard, and expensive tasks map to the intended provider.
- Run fallback tests and confirm a failed Grok provider call switches to the configured backup provider.
- Run cost-tracking tests and confirm each request records the correct provider, token usage, and cost metadata.
- Run token-tracking tests and confirm prompt and completion tokens are captured for every model call.
- Run `python -m py_compile` over the touched LLM gateway files and confirm there are no syntax errors.

## Milestone 7 - Reasoning Engine

Implementation checklist:
- Add graph definitions in `backend/app/graphs/base_graph.py`, `backend/app/graphs/automation_graph.py`, `backend/app/graphs/customer_support_graph.py`, `backend/app/graphs/lead_generation_graph.py`, and `backend/app/graphs/graph_registry.py`.
- Add orchestration engine code in `backend/app/orchestrator/engine.py`, `backend/app/orchestrator/workflow_runner.py`, and `backend/app/orchestrator/execution_manager.py`.
- Add reusable nodes in `backend/app/nodes/planning_node.py`, `backend/app/nodes/routing_node.py`, `backend/app/nodes/tool_execution_node.py`, `backend/app/nodes/validation_node.py`, `backend/app/nodes/retrieval_node.py`, `backend/app/nodes/memory_node.py`, `backend/app/nodes/approval_node.py`, and `backend/app/nodes/fallback_node.py`.
- Add agent implementations in `backend/app/agents/supervisor/agent.py`, `backend/app/agents/planner/agent.py`, `backend/app/agents/researcher/agent.py`, `backend/app/agents/executor/agent.py`, `backend/app/agents/validator/agent.py`, `backend/app/agents/memory/agent.py`, and `backend/app/agents/summarizer/agent.py`.
- Add workflow state objects in `backend/app/state/workflow_state.py`, `backend/app/state/execution_state.py`, and `backend/app/state/shared_state.py`.
- Add approval and recovery support in `backend/app/nodes/approval_node.py`, `backend/app/orchestrator/retry_manager.py`, and `backend/app/memory/short_term/checkpoint_store.py`.

Validation checklist:
- Run graph simulation tests and confirm each branch routes to the expected node or agent.
- Run checkpoint-resume tests and confirm a paused workflow continues from its persisted state after a restart.
- Run human-approval tests and confirm workflows pause, wait, and resume correctly when an approval decision is submitted.
- Run recovery tests and confirm validation failures and tool failures trigger the expected fallback or retry path.
- Run `python -m py_compile` over the touched graph, agent, node, and state files and confirm there are no syntax errors.

## Milestone 8 - First Sellable Workflow

Implementation checklist:
- Add the first vertical workflow in `backend/app/automations/lead_generation/execution_engine.py`, `backend/app/graphs/lead_generation_graph.py`, and `backend/app/orchestrator/workflow_runner.py`.
- Add lead research and enrichment logic in `backend/app/tools/browser/search_tool.py`, `backend/app/tools/browser/scraper.py`, `backend/app/tools/browser/playwright_tool.py`, and `backend/app/agents/researcher/retrieval.py`.
- Add outreach tools in `backend/app/tools/communication/gmail_tool.py`, `backend/app/tools/communication/slack_tool.py`, and `backend/app/automations/actions/send_email.py`.
- Add CRM and productivity tools in `backend/app/tools/crm/hubspot_tool.py`, `backend/app/tools/crm/salesforce_tool.py`, `backend/app/tools/productivity/sheets_tool.py`, `backend/app/tools/productivity/airtable_tool.py`, and `backend/app/tools/productivity/notion_tool.py`.
- Add lead scoring and personalization logic in `backend/app/agents/planner/planning_engine.py`, `backend/app/agents/executor/execution_engine.py`, and `backend/app/orchestrator/engine.py`.
- Add execution logs and result persistence in `backend/app/database/models/execution.py`, `backend/app/database/repositories/execution_repository.py`, and `backend/app/observability/logging.py`.

Validation checklist:
- Run sandbox end-to-end workflow tests and confirm lead discovery, scoring, personalized email generation, and outbound logging all complete successfully.
- Run tool validation tests and confirm tool timeouts, permission checks, and bad inputs fail safely.
- Run execution trace tests and confirm the workflow emits a complete trace across planning, execution, validation, and persistence.
- Run result-persistence tests and confirm workflow outputs are saved and queryable after completion.
- Run `python -m py_compile` over the touched workflow, tool, and persistence files and confirm there are no syntax errors.

## Milestone 9 - Observability and Operations

Implementation checklist:
- Add structured logging in `backend/app/observability/logging.py` and `backend/app/core/logging.py`.
- Add tracing hooks in `backend/app/observability/tracing.py` and `backend/app/observability/langsmith.py`.
- Add metrics collection in `backend/app/observability/metrics.py` and `backend/app/observability/alerts.py`.
- Add admin query and reporting helpers in `backend/app/api/v1/analytics.py`, `backend/app/api/v1/workflows.py`, and `backend/app/api/v1/executions.py`.
- Add workflow and tool call correlation propagation in `backend/app/orchestrator/engine.py`, `backend/app/orchestrator/workflow_runner.py`, and `backend/app/nodes/tool_execution_node.py`.

Validation checklist:
- Run logging-context tests and confirm tenant, workspace, workflow, and execution IDs are present in emitted logs.
- Run tracing tests and confirm each node and tool call creates a trace span with the expected parent-child relationship.
- Run metrics tests and confirm latency, success rate, cost, and retry metrics are emitted for successful and failed executions.
- Run admin-history tests and confirm workflow history, failures, and trace references are queryable from the admin surfaces.
- Run `python -m py_compile` over the touched observability, API, and orchestration files and confirm there are no syntax errors.

## Milestone 10 - Billing and Subscription Control

Implementation checklist:
- Add billing services in `backend/app/billing/stripe_service.py`, `backend/app/billing/plans.py`, and `backend/app/billing/quota_manager.py`.
- Add subscription and usage persistence in `backend/app/database/models/usage.py`, `backend/app/database/models/tenant.py`, and `backend/app/database/repositories/usage_repository.py`.
- Add billing API routes in `backend/app/api/v1/billing.py`, `backend/app/api/v1/usage.py`, and `backend/app/api/v1/webhooks.py`.
- Add Stripe webhook handlers and event processing in `backend/app/integrations/stripe/`.
- Add quota and usage enforcement in `backend/app/core/dependencies.py`, `backend/app/tenancy/tenant_limits.py`, and `backend/app/tenancy/usage_meter.py`.

Validation checklist:
- Run Stripe webhook tests and confirm subscription created, updated, canceled, and payment-failed events are handled correctly.
- Run subscription-state tests and confirm product access changes when a tenant moves between active, past-due, canceled, and trial states.
- Run quota-enforcement tests and confirm plan limits block or throttle the expected operations.
- Run usage-limit tests and confirm overage handling and usage counters are persisted and enforced.
- Run `python -m py_compile` over the touched billing, webhook, and quota files and confirm there are no syntax errors.

## Milestone 11 - Hardening and Launch Readiness

Implementation checklist:
- Add rate limiting in `backend/app/core/dependencies.py`, `backend/app/tenancy/tenant_limits.py`, and `backend/app/api/v1/` route guards.
- Add secrets management in `backend/app/core/security.py`, `backend/app/integrations/`, and infrastructure configuration under `infra/`.
- Add backup and restore procedures in `scripts/backup.py`, `scripts/restore.py`, and `docs/deployment.md`.
- Add disaster recovery notes in `docs/deployment.md` and `docs/architecture.md`.
- Add security review and penetration-test checklist in `docs/deployment.md` and `README.md`.

Validation checklist:
- Run load and smoke tests and confirm the platform remains stable under expected customer traffic.
- Run rate-limit tests and confirm abusive traffic is throttled or blocked.
- Run backup and restore tests and confirm system state can be recovered into a clean environment.
- Run secret-handling tests and confirm no credentials are logged or stored in plaintext.
- Run security-review checks and confirm open issues are tracked, closed, or explicitly accepted before launch.
- Run `python -m py_compile` over the touched hardening, scripts, and API guard files and confirm there are no syntax errors.

## Execution Rule

Do not move to the next milestone until the current checkpoint is green.
