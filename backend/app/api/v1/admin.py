from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends

from app.tools import quota
from app.core.dependencies import require_permission

router = APIRouter()


require_admin_quotas = require_permission("admin:quotas")


@router.get("/admin/quotas")
def list_quotas(_: dict = Depends(require_admin_quotas)):
    return quota.list_quotas()


@router.post("/admin/quotas/{tool_name}")
def set_quota(tool_name: str, executions_limit: int | None = None, cpu_seconds_limit: float | None = None, _: dict = Depends(require_admin_quotas)):
    try:
        quota.set_quota(tool_name, executions_limit=executions_limit, cpu_seconds_limit=cpu_seconds_limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"ok": True}


@router.post("/admin/run_tool")
def run_tool_endpoint(body: dict, _: dict = Depends(require_admin_quotas)):
    from app.tools.registry import run_tool

    tool_name = body.get("tool_name")
    payload = body.get("payload")
    sandbox = body.get("sandbox", False)
    timeout = body.get("timeout_seconds", 30)
    try:
        res = run_tool(tool_name, payload, timeout_seconds=timeout, sandbox=sandbox)
        return {"ok": True, "result": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
