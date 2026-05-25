# Build Plan

This plan is intentionally sequential. Each phase depends on the previous one, and each phase ends with a checkpoint test or validation step.

## Phase 0 - Foundation and decisions

Goal: freeze the product scope and environment assumptions before coding real behavior.

Tasks:
- Confirm the MVP vertical: AI sales automation.
- Confirm local development stack: Docker Compose for Postgres, Redis, and Qdrant.
- Confirm LLM providers and keys: Grok first, then add other providers later if needed.
- Confirm billing flow and Stripe account readiness.
- Defer Kubernetes until after the MVP is validated unless deployment scale forces an earlier need.

Checkpoint:
- Documentation review approved.
- Local `.env.example` matches the chosen services.
- All required services are either available locally or stubbed for development.

## Phase 1 - Repository and runtime skeleton

Goal: make the repo runnable end to end with no business logic.

Implementation checklist:
- Create and validate the root files: `.env.example`, `.gitignore`, `docker-compose.yml`, `Makefile`, `README.md`.
- Create and validate the frontend bootstrap files: `frontend/package.json`, `frontend/next.config.mjs`, `frontend/tsconfig.json`, `frontend/postcss.config.mjs`, `frontend/tailwind.config.ts`, `frontend/.eslintrc.json`, `frontend/next-env.d.ts`, `frontend/src/app/layout.tsx`, `frontend/src/app/page.tsx`, `frontend/src/app/globals.css`.
- Create and validate the backend bootstrap files: `backend/pyproject.toml`, `backend/requirements.txt`, `backend/Dockerfile`, `backend/app/__init__.py`, `backend/app/main.py`, `backend/app/core/__init__.py`, `backend/app/core/config.py`, `backend/app/api/v1/__init__.py`, `backend/app/api/v1/health.py`.
- Create the repo scaffolding directories: `shared/`, `infra/`, `scripts/`, and `docs/`.
- Document the architecture and delivery order in `docs/architecture.md` and `docs/BUILD_PLAN.md`.

Validation checklist:
- Run `docker compose config` from the repo root and confirm it resolves `postgres`, `redis`, and `qdrant`.
- Run `python -m py_compile backend\\app\\main.py backend\\app\\api\\v1\\health.py backend\\app\\core\\config.py` and confirm there are no syntax errors.
- Run `npm run build` in `frontend/` after installing dependencies and confirm the app compiles.
- Run `npm run lint` in `frontend/` after installing dependencies and confirm the bootstrap files satisfy the lint rules.
- Start the backend with `uvicorn app.main:app --host 0.0.0.0 --port 8000` and confirm `GET /health` returns `{\"status\":\"ok\"}`.

Checkpoint:
- `docker compose config` succeeds.
- Frontend and backend startup commands exist and work.
- Basic import, syntax, build, and lint validation passes for the bootstrap code.

## Phase 2 - Identity, tenancy, and access control

Goal: secure the platform before exposing automation execution.

Implementation checklist:
- Add authentication primitives in `backend/app/auth/jwt.py`, `backend/app/auth/rbac.py`, `backend/app/auth/middleware.py`, and `backend/app/core/security.py`.
- Add tenant scoping helpers in `backend/app/tenancy/tenant_context.py`, `backend/app/tenancy/tenant_router.py`, `backend/app/tenancy/tenant_limits.py`, and `backend/app/tenancy/usage_meter.py`.
- Add core identity models and repositories in `backend/app/database/models/user.py`, `backend/app/database/models/tenant.py`, `backend/app/database/models/workspace.py`, and `backend/app/database/repositories/`.
- Add audit logging and request context support in `backend/app/core/logging.py` and `backend/app/core/dependencies.py`.
- Add API endpoints for login, current-user lookup, and tenant-aware access control in `backend/app/api/v1/auth.py`, `backend/app/api/v1/users.py`, `backend/app/api/v1/tenants.py`, and `backend/app/api/v1/workspaces.py`.
- Add integration tests in `backend/app/tests/integration/test_auth.py`, `backend/app/tests/integration/test_tenancy.py`, and `backend/app/tests/integration/test_rbac.py`.

Validation checklist:
- Run auth integration tests and confirm login, token verification, and current-user lookup succeed for valid credentials.
- Run tenant isolation tests and confirm tenant-scoped queries cannot return another tenant’s records.
- Run RBAC tests and confirm each role is allowed only the operations it should have.
- Run unauthorized-access tests and confirm protected routes return the expected HTTP status codes.
- Run `python -m py_compile` over the touched backend files and confirm there are no syntax errors.

Checkpoint:
- Authentication integration tests pass.
- Tenant isolation tests prove one tenant cannot read another tenant’s data.
- Unauthorized access returns the expected HTTP status codes.
- RBAC rules are enforced by tests, not just by code review.

## Phase 3 - Core data model and persistence

Goal: establish durable system state before any orchestration logic.

Implementation checklist:
- Add SQLAlchemy models in `backend/app/database/models/user.py`, `backend/app/database/models/tenant.py`, `backend/app/database/models/workspace.py`, `backend/app/database/models/workflow.py`, `backend/app/database/models/execution.py`, `backend/app/database/models/integration.py`, and `backend/app/database/models/usage.py`.
- Add database session and connection helpers in `backend/app/database/connection.py` and `backend/app/database/session.py`.
- Add repository abstractions in `backend/app/database/repositories/user_repository.py`, `backend/app/database/repositories/tenant_repository.py`, `backend/app/database/repositories/workspace_repository.py`, `backend/app/database/repositories/workflow_repository.py`, `backend/app/database/repositories/execution_repository.py`, and `backend/app/database/repositories/base.py`.
- Add Alembic migration scaffolding in `backend/app/database/migrations/` and create the initial schema migration for the core tables.
- Add durable checkpoint storage in `backend/app/memory/short_term/checkpoint_store.py` and `backend/app/orchestrator/workflow_runner.py`.
- Add repository and migration tests in `backend/app/tests/integration/test_migrations.py`, `backend/app/tests/integration/test_repository_crud.py`, and `backend/app/tests/integration/test_checkpoint_resume.py`.

Validation checklist:
- Run migrations against a clean database and confirm the core tables are created with the expected columns and foreign keys.
- Run CRUD tests for users, tenants, workspaces, workflows, and executions and confirm create, read, update, and delete operations behave correctly.
- Run checkpoint-resume tests and confirm workflow execution state is restored after a simulated process restart.
- Run `python -m py_compile` over the touched backend persistence files and confirm there are no syntax errors.

Checkpoint:
- Migration tests pass against a clean database.
- CRUD tests pass for the core entities.
- Workflow execution state survives process restarts.
- Persistence code is structured so the orchestration layer can depend on it without in-memory state.

## Phase 4 - Workflow API and execution contract

Goal: define the public contract for running automations.

Implementation checklist:
- Add workflow API routes in `backend/app/api/v1/workflows.py`, `backend/app/api/v1/executions.py`, and `backend/app/api/v1/automations.py`.
- Add request and response schemas in `shared/schemas/workflow.py`, `shared/schemas/execution.py`, and `shared/dto/workflow_requests.py`.
- Add workflow service logic in `backend/app/orchestrator/engine.py`, `backend/app/orchestrator/workflow_runner.py`, `backend/app/orchestrator/execution_manager.py`, and `backend/app/state/workflow_state.py`.
- Add request validation, quota checks, and idempotency guards in `backend/app/core/dependencies.py`, `backend/app/billing/quota_manager.py`, and `backend/app/tenancy/usage_meter.py`.
- Add execution status and progress retrieval handlers in `backend/app/api/v1/executions.py` with polling or streaming support.
- Add integration tests in `backend/app/tests/integration/test_workflow_create.py`, `backend/app/tests/integration/test_workflow_run.py`, `backend/app/tests/integration/test_execution_status.py`, and `backend/app/tests/integration/test_idempotency.py`.

Validation checklist:
- Run workflow creation and run API tests and confirm valid payloads create executions and invalid payloads fail with clear errors.
- Run execution status tests and confirm progress can be retrieved by polling or streaming while the workflow is running.
- Run idempotency tests and confirm duplicate submissions do not create duplicate executions.
- Run quota and request validation tests and confirm blocked tenants receive the expected response codes.
- Run `python -m py_compile` over the touched backend workflow API and orchestration files and confirm there are no syntax errors.

Checkpoint:
- API contract tests pass.
- Invalid payloads fail cleanly.
- Duplicate submissions do not create duplicate executions.
- Workflow submission is safe to expose to the async queue layer in the next phase.

## Phase 5 - Queueing and worker orchestration

Goal: move all real work off the request thread.

Implementation checklist:
- Add queue primitives in `backend/app/workers/celery.py`, `backend/app/orchestrator/event_bus.py`, and `backend/app/orchestrator/scheduler.py`.
- Add worker entrypoints in `backend/app/workers/workflow_worker.py`, `backend/app/workers/tool_worker.py`, `backend/app/workers/retry_worker.py`, and `backend/app/workers/cleanup_worker.py`.
- Add retry and recovery logic in `backend/app/orchestrator/retry_manager.py` and `backend/app/orchestrator/execution_manager.py`.
- Add dead-letter handling and notification dispatch in `backend/app/orchestrator/engine.py` and `backend/app/observability/alerts.py`.
- Add queue-backed workflow state transitions in `backend/app/state/execution_state.py` and `backend/app/state/shared_state.py`.
- Add integration tests in `backend/app/tests/integration/test_queue_enqueue.py`, `backend/app/tests/integration/test_worker_processing.py`, `backend/app/tests/integration/test_retry_policy.py`, and `backend/app/tests/integration/test_dead_letter.py`.

Validation checklist:
- Run queue-enqueue tests and confirm a workflow request is persisted to Redis or the configured queue backend instead of executing inline.
- Run worker-processing tests and confirm a queued workflow is picked up and completed by a worker process.
- Run retry-policy tests and confirm exponential backoff and retry limits behave as expected.
- Run dead-letter tests and confirm permanently failing jobs are routed to the dead-letter path.
- Run a request-latency smoke test and confirm synchronous API handling remains fast while work is processed asynchronously.
- Run `python -m py_compile` over the touched worker and queue files and confirm there are no syntax errors.

Checkpoint:
- A queued workflow can be picked up and completed by a worker.
- Retry and dead-letter tests pass.
- Synchronous request handling remains fast under load.
- The system is ready for the LLM gateway phase without blocking requests on long-running tasks.

## Phase 6 - LLM gateway and model routing

Goal: avoid direct model calls from application code.

Implementation checklist:
- Add the provider abstraction in `backend/app/llm/router.py`, `backend/app/llm/prompt_manager.py`, `backend/app/llm/cost_tracker.py`, and `backend/app/llm/token_tracker.py`.
- Add Grok/xAI provider support in `backend/app/llm/providers/grok_provider.py` and wire provider selection into `backend/app/llm/providers/`.
- Add fallback provider support in `backend/app/llm/providers/openai_provider.py`, `backend/app/llm/providers/anthropic_provider.py`, and `backend/app/llm/providers/gemini_provider.py` so the router can switch providers if Grok is unavailable.
- Add model routing policy in `backend/app/orchestrator/engine.py` and `backend/app/core/constants.py` for cheap, standard, and high-confidence task tiers.
- Add cost and token accounting hooks in `backend/app/observability/metrics.py` and `backend/app/observability/logging.py`.
- Add integration tests in `backend/app/tests/integration/test_llm_routing.py`, `backend/app/tests/integration/test_llm_fallback.py`, `backend/app/tests/integration/test_cost_tracking.py`, and `backend/app/tests/integration/test_token_tracking.py`.

Validation checklist:
- Run provider routing tests and confirm cheap, standard, and expensive tasks map to the intended provider.
- Run fallback tests and confirm a failed Grok provider call switches to the configured backup provider.
- Run cost-tracking tests and confirm each request records the correct provider, token usage, and cost metadata.
- Run token-tracking tests and confirm prompt and completion tokens are captured for every model call.
- Run `python -m py_compile` over the touched LLM gateway files and confirm there are no syntax errors.

Checkpoint:
- Provider unit tests cover routing decisions.
- A failed primary provider falls back to the configured backup.
- Cost accounting records each request.
- Grok is the primary provider path for the MVP, with fallback providers available for resilience.

## Phase 7 - LangGraph orchestration engine

Goal: implement the core reasoning pipeline.

Implementation checklist:
- Add graph definitions in `backend/app/graphs/base_graph.py`, `backend/app/graphs/automation_graph.py`, `backend/app/graphs/customer_support_graph.py`, `backend/app/graphs/lead_generation_graph.py`, and `backend/app/graphs/graph_registry.py`.
- Add orchestration engine code in `backend/app/orchestrator/engine.py`, `backend/app/orchestrator/workflow_runner.py`, and `backend/app/orchestrator/execution_manager.py`.
- Add reusable nodes in `backend/app/nodes/planning_node.py`, `backend/app/nodes/routing_node.py`, `backend/app/nodes/tool_execution_node.py`, `backend/app/nodes/validation_node.py`, `backend/app/nodes/retrieval_node.py`, `backend/app/nodes/memory_node.py`, `backend/app/nodes/approval_node.py`, and `backend/app/nodes/fallback_node.py`.
- Add agent implementations in `backend/app/agents/supervisor/agent.py`, `backend/app/agents/planner/agent.py`, `backend/app/agents/researcher/agent.py`, `backend/app/agents/executor/agent.py`, `backend/app/agents/validator/agent.py`, `backend/app/agents/memory/agent.py`, and `backend/app/agents/summarizer/agent.py`.
- Add workflow state objects in `backend/app/state/workflow_state.py`, `backend/app/state/execution_state.py`, and `backend/app/state/shared_state.py`.
- Add approval and recovery support in `backend/app/nodes/approval_node.py`, `backend/app/orchestrator/retry_manager.py`, and `backend/app/memory/short_term/checkpoint_store.py`.
- Add graph simulation and recovery tests in `backend/app/tests/integration/test_graph_routing.py`, `backend/app/tests/integration/test_graph_checkpoint_resume.py`, `backend/app/tests/integration/test_human_approval.py`, and `backend/app/tests/integration/test_graph_recovery.py`.

Validation checklist:
- Run graph simulation tests and confirm each branch routes to the expected node or agent.
- Run checkpoint-resume tests and confirm a paused workflow continues from its persisted state after a restart.
- Run human-approval tests and confirm workflows pause, wait, and resume correctly when an approval decision is submitted.
- Run recovery tests and confirm validation failures and tool failures trigger the expected fallback or retry path.
- Run `python -m py_compile` over the touched graph, agent, node, and state files and confirm there are no syntax errors.

Checkpoint:
- Graph simulation tests prove each branch behaves as expected.
- Failure recovery resumes from checkpoints.
- Human approval pauses and resumes correctly.
- The orchestration engine is ready for the first production workflow vertical.

## Phase 8 - Tool layer and first vertical workflow

Goal: ship one valuable automation that can be sold.

Implementation checklist:
- Add the first vertical workflow in `backend/app/automations/lead_generation/execution_engine.py`, `backend/app/graphs/lead_generation_graph.py`, and `backend/app/orchestrator/workflow_runner.py`.
- Add lead research and enrichment logic in `backend/app/tools/browser/search_tool.py`, `backend/app/tools/browser/scraper.py`, `backend/app/tools/browser/playwright_tool.py`, and `backend/app/agents/researcher/retrieval.py`.
- Add outreach tools in `backend/app/tools/communication/gmail_tool.py`, `backend/app/tools/communication/slack_tool.py`, and `backend/app/automations/actions/send_email.py`.
- Add CRM and productivity tools in `backend/app/tools/crm/hubspot_tool.py`, `backend/app/tools/crm/salesforce_tool.py`, `backend/app/tools/productivity/sheets_tool.py`, `backend/app/tools/productivity/airtable_tool.py`, and `backend/app/tools/productivity/notion_tool.py`.
- Add lead scoring and personalization logic in `backend/app/agents/planner/planning_engine.py`, `backend/app/agents/executor/execution_engine.py`, and `backend/app/orchestrator/engine.py`.
- Add execution logs and result persistence in `backend/app/database/models/execution.py`, `backend/app/database/repositories/execution_repository.py`, and `backend/app/observability/logging.py`.
- Add sandbox and end-to-end tests in `backend/app/tests/integration/test_lead_generation_workflow.py`, `backend/app/tests/integration/test_email_send.py`, `backend/app/tests/integration/test_tool_validation.py`, and `backend/app/tests/integration/test_execution_trace.py`.

Validation checklist:
- Run sandbox end-to-end workflow tests and confirm lead discovery, scoring, personalized email generation, and outbound logging all complete successfully.
- Run tool validation tests and confirm tool timeouts, permission checks, and bad inputs fail safely.
- Run execution trace tests and confirm the workflow emits a complete trace across planning, execution, validation, and persistence.
- Run result-persistence tests and confirm workflow outputs are saved and queryable after completion.
- Run `python -m py_compile` over the touched workflow, tool, and persistence files and confirm there are no syntax errors.

Checkpoint:
- End-to-end workflow test passes in a sandbox environment.
- Tool timeout and validation tests pass.
- The workflow produces a complete execution trace.
- The first sellable vertical is ready to build on observability and admin operations.

## Phase 9 - Observability and admin operations

Goal: make the system supportable in production.

Implementation checklist:
- Add structured logging in `backend/app/observability/logging.py` and `backend/app/core/logging.py`.
- Add tracing hooks in `backend/app/observability/tracing.py` and `backend/app/observability/langsmith.py`.
- Add metrics collection in `backend/app/observability/metrics.py`, `backend/app/observability/alerts.py`, and `backend/app/observability/metrics.py`.
- Add admin query and reporting helpers in `backend/app/api/v1/analytics.py`, `backend/app/api/v1/workflows.py`, and `backend/app/api/v1/executions.py` for workflow history and failure inspection.
- Add workflow and tool call correlation propagation in `backend/app/orchestrator/engine.py`, `backend/app/orchestrator/workflow_runner.py`, `backend/app/nodes/tool_execution_node.py`, and `backend/app/tools/`.
- Add observability integration tests in `backend/app/tests/integration/test_logging_context.py`, `backend/app/tests/integration/test_tracing_spans.py`, `backend/app/tests/integration/test_metrics_emission.py`, and `backend/app/tests/integration/test_admin_workflow_history.py`.

Validation checklist:
- Run logging-context tests and confirm tenant, workspace, workflow, and execution IDs are present in emitted logs.
- Run tracing tests and confirm each node and tool call creates a trace span with the expected parent-child relationship.
- Run metrics tests and confirm latency, success rate, cost, and retry metrics are emitted for successful and failed executions.
- Run admin-history tests and confirm workflow history, failures, and trace references are queryable from the admin surfaces.
- Run `python -m py_compile` over the touched observability, API, and orchestration files and confirm there are no syntax errors.

Checkpoint:
- Logs include tenant and workflow correlation IDs.
- Metrics are emitted for one successful and one failed execution.
- A failed run can be diagnosed from trace data alone.
- The platform is supportable enough to add billing and subscription enforcement next.

## Phase 10 - Billing and subscriptions

Goal: turn the product into a real SaaS.

Implementation checklist:
- Add billing services in `backend/app/billing/stripe_service.py`, `backend/app/billing/plans.py`, and `backend/app/billing/quota_manager.py`.
- Add subscription and usage persistence in `backend/app/database/models/usage.py`, `backend/app/database/models/tenant.py`, and `backend/app/database/repositories/usage_repository.py`.
- Add billing API routes in `backend/app/api/v1/billing.py`, `backend/app/api/v1/usage.py`, and `backend/app/api/v1/webhooks.py`.
- Add Stripe webhook handlers and event processing in `backend/app/integrations/stripe/` and `backend/app/automations/actions/update_crm.py` or related billing update handlers.
- Add quota and usage enforcement in `backend/app/core/dependencies.py`, `backend/app/tenancy/tenant_limits.py`, and `backend/app/tenancy/usage_meter.py`.
- Add billing and subscription tests in `backend/app/tests/integration/test_stripe_subscription.py`, `backend/app/tests/integration/test_billing_webhooks.py`, `backend/app/tests/integration/test_quota_enforcement.py`, and `backend/app/tests/integration/test_usage_limits.py`.

Validation checklist:
- Run Stripe webhook tests and confirm subscription created, updated, canceled, and payment-failed events are handled correctly.
- Run subscription-state tests and confirm product access changes when a tenant moves between active, past-due, canceled, and trial states.
- Run quota-enforcement tests and confirm plan limits block or throttle the expected operations.
- Run usage-limit tests and confirm overage handling and usage counters are persisted and enforced.
- Run `python -m py_compile` over the touched billing, webhook, and quota files and confirm there are no syntax errors.

Checkpoint:
- Billing webhook tests pass.
- Subscription state controls product access.
- Quotas block overuse correctly.
- The product is ready for hardening and release-readiness work next.

## Phase 11 - Hardening and release readiness

Goal: prepare for external customers.

Implementation checklist:
- Add rate limiting in `backend/app/core/dependencies.py`, `backend/app/tenancy/tenant_limits.py`, and `backend/app/api/v1/` route guards.
- Add secrets management in `backend/app/core/security.py`, `backend/app/integrations/`, and infrastructure configuration under `infra/`.
- Add backup and restore procedures in `scripts/backup.py`, `scripts/restore.py`, and `docs/deployment.md`.
- Add disaster recovery notes in `docs/deployment.md` and `docs/architecture.md`.
- Add security review and penetration-test checklist in `docs/deployment.md` and `README.md`.
- Add hardening tests in `backend/app/tests/integration/test_rate_limiting.py`, `backend/app/tests/integration/test_backup_restore.py`, `backend/app/tests/integration/test_secret_handling.py`, and `backend/app/tests/integration/test_release_smoke.py`.

Validation checklist:
- Run load and smoke tests and confirm the platform remains stable under expected customer traffic.
- Run rate-limit tests and confirm abusive traffic is throttled or blocked.
- Run backup and restore tests and confirm system state can be recovered into a clean environment.
- Run secret-handling tests and confirm no credentials are logged or stored in plaintext.
- Run security-review checks and confirm open issues are tracked, closed, or explicitly accepted before launch.
- Run `python -m py_compile` over the touched hardening, scripts, and API guard files and confirm there are no syntax errors.

Checkpoint:
- Load and smoke tests pass.
- Backup and restore are documented and rehearsed.
- Security review items are closed or tracked.
- The release is ready for external customers.

## Implementation rule

Do not expand to the next phase until the checkpoint for the current phase is green.
