from fastapi import FastAPI, Response
from contextlib import asynccontextmanager

from app.api.v1.auth import router as auth_router
from app.api.v1.tenants import router as tenants_router
from app.api.v1.users import router as users_router
from app.api.v1.workspaces import router as workspaces_router
from app.auth.middleware import RequestContextMiddleware
from app.api.v1.automations import router as automations_router
from app.api.v1.executions import router as executions_router
from app.api.v1.workflows import router as workflows_router
from app.api.v1.admin import router as admin_router
from app.workers.reaper import reaper


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        reaper.start()
    except Exception:
        pass
    try:
        yield
    finally:
        try:
            reaper.stop()
        except Exception:
            pass


app = FastAPI(title="AI Orchestrator SaaS API", version="0.2.0", lifespan=lifespan)
from app.observability import metrics

app.add_middleware(RequestContextMiddleware)


@app.get("/metrics")
def metrics_endpoint() -> Response:
    if metrics.generate_latest is None:
        return Response(content="", media_type=metrics.CONTENT_TYPE_LATEST)
    return Response(content=metrics.generate_latest(), media_type=metrics.CONTENT_TYPE_LATEST)


app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(tenants_router, prefix="/api/v1")
app.include_router(workspaces_router, prefix="/api/v1")
app.include_router(workflows_router, prefix="/api/v1")
app.include_router(automations_router, prefix="/api/v1")
app.include_router(executions_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

