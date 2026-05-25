from __future__ import annotations

from importlib import import_module
from typing import Any, Callable, Tuple
import asyncio
import concurrent.futures
import multiprocessing
import os
import sys
import platform
try:
    import resource
except Exception:
    resource = None
import json
import logging
import inspect
import textwrap
from time import perf_counter
import subprocess
import os

from app.observability import metrics
from app.tools import quota

logger = logging.getLogger("app.tools.registry")


def _resolve_tool_spec(tool_name: str) -> Tuple[str, str, str]:
    """Return (spec_type, module_name, attr_name)
    spec_type: 'function' or 'class'
    module_name: full module import path
    attr_name: function name or 'Tool' for class-based tools
    """
    normalized = tool_name.replace("/", ".").strip(".")
    candidates = [f"app.tools.{normalized}_tool", f"app.tools.{normalized}"]
    funcs = ("run", "execute", "process", "process_tool", "run_tool", "execute_tool")
    for mod_name in candidates:
        try:
            mod = import_module(mod_name)
        except ModuleNotFoundError:
            continue
        for fn in funcs:
            if hasattr(mod, fn):
                return ("function", mod_name, fn)
        if hasattr(mod, "Tool"):
            return ("class", mod_name, "Tool")
    raise RuntimeError(f"Tool '{tool_name}' not found")


def _call_tool_spec(spec_type: str, module_name: str, attr_name: str, payload: Any) -> Any:
    mod = import_module(module_name)
    if spec_type == "function":
        fn = getattr(mod, attr_name)
        if asyncio.iscoroutinefunction(fn):
            return asyncio.run(fn(payload))
        return fn(payload)
    else:
        ToolCls = getattr(mod, attr_name)
        inst = ToolCls()
        run_method = getattr(inst, "run")
        if asyncio.iscoroutinefunction(run_method):
            return asyncio.run(run_method(payload))
        return run_method(payload)


def _call_tool_in_process(spec_type: str, module_name: str, attr_name: str, payload: Any, q: multiprocessing.Queue) -> None:
    try:
        # Run inside a fresh process to improve isolation
        import importlib
        import asyncio as _asyncio
        # Apply POSIX resource limits early in the child process
        try:
            _setup_resource_limits()
        except Exception:
            pass

        mod = importlib.import_module(module_name)
        if spec_type == "function":
            fn = getattr(mod, attr_name)
            if _asyncio.iscoroutinefunction(fn):
                res = _asyncio.run(fn(payload))
            else:
                res = fn(payload)
        else:
            ToolCls = getattr(mod, attr_name)
            inst = ToolCls()
            run_method = getattr(inst, "run")
            if _asyncio.iscoroutinefunction(run_method):
                res = _asyncio.run(run_method(payload))
            else:
                res = run_method(payload)
        q.put((True, res))
    except Exception as e:
        q.put((False, repr(e)))


def _setup_resource_limits():
    """Apply conservative resource limits in the current process (POSIX only).

    Sets CPU time and address space limits to reduce risk of runaway tool code.
    """
    if resource is None:
        return
    try:
        # CPU: 10 seconds
        resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
    except Exception:
        pass
    try:
        # Limit virtual memory to 256MB
        soft, hard = 256 * 1024 * 1024, 256 * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (soft, hard))
    except Exception:
        pass


def run_tool(tool_name: str, payload: Any, *, timeout_seconds: int = 30, sandbox: bool | str = False) -> Any:
    """Locate and execute a tool by name with optional timeout and sandboxing.

    - If `sandbox` is False (default), synchronous functions run inline and async functions
      are awaited via `asyncio.run()`. A blocking call may be wrapped in a threadpool
      to enforce `timeout_seconds`.
    - If `sandbox` is True, the tool is executed in a spawned process for isolation;
      the result is returned if the process completes before `timeout_seconds`.
    """
    spec_type, module_name, attr_name = _resolve_tool_spec(tool_name)

    # enforce pre-call quota
    try:
        quota.check_quota(tool_name)
    except Exception as e:
        raise RuntimeError(f"quota check failed: {e}")

    # normalize sandbox option: True -> 'process', 'container' supported
    sandbox_mode = None
    if sandbox is True:
        sandbox_mode = "process"
    elif isinstance(sandbox, str):
        sandbox_mode = sandbox
    elif sandbox is False:
        sandbox_mode = None

    if sandbox_mode == "process":
        ctx = multiprocessing.get_context("spawn")
        q: multiprocessing.Queue = ctx.Queue()
        p = ctx.Process(target=_call_tool_in_process, args=(spec_type, module_name, attr_name, payload, q))

        # measure wall time and child rusage
        start = perf_counter()
        r_before = None
        if resource is not None:
            try:
                r_before = resource.getrusage(resource.RUSAGE_CHILDREN)
            except Exception:
                r_before = None

        p.start()
        p.join(timeout=timeout_seconds)
        if p.is_alive():
            p.terminate()
            p.join()
            metrics.record_tool_execution(tool_name, False, duration_seconds=timeout_seconds)
            raise TimeoutError(f"Tool '{tool_name}' timed out after {timeout_seconds} seconds (sandbox)")
        try:
            ok, res = q.get_nowait()
        except Exception:
            metrics.record_tool_execution(tool_name, False)
            quota.record_usage(tool_name, executions=1, cpu_seconds=0.0)
            raise RuntimeError(f"Tool '{tool_name}' failed without result (sandbox)")

        duration = perf_counter() - start
        cpu_seconds = None
        mem_bytes = None
        if resource is not None:
            try:
                r_after = resource.getrusage(resource.RUSAGE_CHILDREN)
                if r_before is not None:
                    cpu_seconds = (r_after.ru_utime - r_before.ru_utime) + (r_after.ru_stime - r_before.ru_stime)
                    # ru_maxrss is in kilobytes on many Unix systems
                    mem_bytes = int(max(0, r_after.ru_maxrss) * 1024)
            except Exception:
                cpu_seconds = None
                mem_bytes = None

        metrics.record_tool_execution(tool_name, bool(ok), duration_seconds=duration, cpu_seconds=cpu_seconds, memory_bytes=mem_bytes)
        # record usage (best-effort): use measured cpu_seconds when available else fall back to wall duration
        quota.record_usage(tool_name, executions=1, cpu_seconds=cpu_seconds if cpu_seconds is not None else duration)
        if not ok:
            quota.record_usage(tool_name, executions=1, cpu_seconds=0.0)
            raise RuntimeError(f"Tool '{tool_name}' raised in sandbox: {res}")
        quota.record_usage(tool_name, executions=1, cpu_seconds=cpu_seconds if cpu_seconds is not None else duration)
        return res

    if sandbox_mode == "container":
        # run tool inside a short-lived docker container; ship the tool source as text
        source_module = import_module(module_name)
        tool_source = inspect.getsource(source_module)
        inline_runner = textwrap.dedent(r'''
            import asyncio
            import importlib
            import json
            import os
            import subprocess
            import sys
            import time
            import types

            try:
                import psutil
            except Exception:
                psutil = None

            subprocess.run([sys.executable, "-m", "pip", "install", "psutil"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            data = json.load(sys.stdin)
            module = data.get("module")
            attr = data.get("attr")
            payload = data.get("payload")
            source = data.get("source")

            module_obj = types.ModuleType(module)
            module_obj.__dict__["__name__"] = module
            exec(source, module_obj.__dict__)
            sys.modules[module] = module_obj

            def call_callable(module_name, attr_name, value):
                mod = sys.modules[module_name]
                target = getattr(mod, attr_name)
                if isinstance(target, type):
                    inst = target()
                    fn = getattr(inst, "run")
                    if asyncio.iscoroutinefunction(fn):
                        return asyncio.run(fn(value))
                    return fn(value)
                if asyncio.iscoroutinefunction(target):
                    return asyncio.run(target(value))
                return target(value)

            start = time.time()
            proc = psutil.Process() if psutil is not None else None
            cpu_before = None
            rss_before = None
            if proc is not None:
                try:
                    cpu_before = proc.cpu_times()
                    rss_before = proc.memory_info().rss
                except Exception:
                    cpu_before = None
                    rss_before = None

            try:
                result = call_callable(module, attr, payload)
                ok = True
                error = None
            except Exception as exc:
                result = None
                ok = False
                error = {
                    "message": repr(exc),
                    "cwd": os.getcwd(),
                    "sys_path": sys.path,
                }

            duration = time.time() - start
            cpu_seconds = None
            memory_bytes = None
            if proc is not None:
                try:
                    cpu_after = proc.cpu_times()
                    rss_after = proc.memory_info().rss
                    if cpu_before is not None:
                        cpu_seconds = (cpu_after.user - cpu_before.user) + (cpu_after.system - cpu_before.system)
                    memory_bytes = int(max(rss_before or 0, rss_after))
                except Exception:
                    cpu_seconds = None
                    memory_bytes = None

            print(json.dumps({"ok": ok, "result": result, "error": error, "duration": duration, "cpu_seconds": cpu_seconds, "memory_bytes": memory_bytes}, default=str))
        ''').strip()
        cmd = [
            "docker",
            "run",
            "--rm",
            "-i",
            "python:3.11-slim",
            "python",
            "-c",
            inline_runner,
        ]

        payload_env = json.dumps({"module": module_name, "attr": attr_name, "payload": payload, "source": tool_source}, default=str)
        start = perf_counter()
        try:
            proc = subprocess.run(cmd, input=payload_env.encode("utf-8"), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            logger.warning("container tool timed out: %s", tool_name)
            metrics.record_tool_execution(tool_name, False, duration_seconds=timeout_seconds)
            raise TimeoutError(f"Tool '{tool_name}' timed out after {timeout_seconds} seconds (container)")

        duration = perf_counter() - start
        out = proc.stdout.decode("utf-8", errors="ignore")
        try:
            resp = json.loads(out)
        except Exception:
            logger.error("invalid container runner output: %s %s", out, proc.stderr.decode("utf-8", errors="ignore"))
            metrics.record_tool_execution(tool_name, False, duration_seconds=duration)
            quota.record_usage(tool_name, executions=1, cpu_seconds=0.0)
            raise RuntimeError("invalid container runner output")

        ok = resp.get("ok")
        res = resp.get("result") if ok else resp.get("error")
        metrics.record_tool_execution(tool_name, bool(ok), duration_seconds=duration)
        if not ok:
            quota.record_usage(tool_name, executions=1, cpu_seconds=0.0)
            raise RuntimeError(f"Tool '{tool_name}' failed in container: {res}")
        quota.record_usage(tool_name, executions=1, cpu_seconds=duration)
        return res

    # Non-sandbox: call inline but enforce timeout for blocking sync functions
    # Resolve callable for direct invocation
    mod = import_module(module_name)
    if spec_type == "function":
        fn = getattr(mod, attr_name)
        is_coro = asyncio.iscoroutinefunction(fn)
        start = perf_counter()
        r_before = None
        if resource is not None:
            try:
                r_before = resource.getrusage(resource.RUSAGE_SELF)
            except Exception:
                r_before = None

        if is_coro:
            try:
                res = asyncio.run(fn(payload))
                success = True
            except Exception:
                success = False
                raise
            finally:
                duration = perf_counter() - start
                cpu_seconds = None
                mem_bytes = None
                if resource is not None and r_before is not None:
                    try:
                        r_after = resource.getrusage(resource.RUSAGE_SELF)
                        cpu_seconds = (r_after.ru_utime - r_before.ru_utime) + (r_after.ru_stime - r_before.ru_stime)
                        mem_bytes = int(max(0, r_after.ru_maxrss) * 1024)
                    except Exception:
                        cpu_seconds = None
                        mem_bytes = None
                metrics.record_tool_execution(tool_name, success if 'success' in locals() else True, duration_seconds=duration, cpu_seconds=cpu_seconds, memory_bytes=mem_bytes)
                return res
        # sync function: run in threadpool to support timeout
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(fn, payload)
            try:
                res = fut.result(timeout=timeout_seconds)
                success = True
                return res
            except concurrent.futures.TimeoutError:
                success = False
                raise TimeoutError(f"Tool '{tool_name}' timed out after {timeout_seconds} seconds")
            finally:
                duration = perf_counter() - start
                cpu_seconds = None
                mem_bytes = None
                if resource is not None and r_before is not None:
                    try:
                        r_after = resource.getrusage(resource.RUSAGE_SELF)
                        cpu_seconds = (r_after.ru_utime - r_before.ru_utime) + (r_after.ru_stime - r_before.ru_stime)
                        mem_bytes = int(max(0, r_after.ru_maxrss) * 1024)
                    except Exception:
                        cpu_seconds = None
                        mem_bytes = None
                metrics.record_tool_execution(tool_name, success if 'success' in locals() else False, duration_seconds=duration, cpu_seconds=cpu_seconds, memory_bytes=mem_bytes)
    else:
        ToolCls = getattr(mod, attr_name)
        inst = ToolCls()
        run_method = getattr(inst, "run")
        is_coro = asyncio.iscoroutinefunction(run_method)
        start = perf_counter()
        r_before = None
        if resource is not None:
            try:
                r_before = resource.getrusage(resource.RUSAGE_SELF)
            except Exception:
                r_before = None

        if is_coro:
            try:
                res = asyncio.run(run_method(payload))
                success = True
            except Exception:
                success = False
                raise
            finally:
                duration = perf_counter() - start
                cpu_seconds = None
                mem_bytes = None
                if resource is not None and r_before is not None:
                    try:
                        r_after = resource.getrusage(resource.RUSAGE_SELF)
                        cpu_seconds = (r_after.ru_utime - r_before.ru_utime) + (r_after.ru_stime - r_before.ru_stime)
                        mem_bytes = int(max(0, r_after.ru_maxrss) * 1024)
                    except Exception:
                        cpu_seconds = None
                        mem_bytes = None
                metrics.record_tool_execution(tool_name, success if 'success' in locals() else True, duration_seconds=duration, cpu_seconds=cpu_seconds, memory_bytes=mem_bytes)
                return res
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(run_method, payload)
            try:
                res = fut.result(timeout=timeout_seconds)
                success = True
                return res
            except concurrent.futures.TimeoutError:
                success = False
                raise TimeoutError(f"Tool '{tool_name}' timed out after {timeout_seconds} seconds")
            finally:
                duration = perf_counter() - start
                cpu_seconds = None
                mem_bytes = None
                if resource is not None and r_before is not None:
                    try:
                        r_after = resource.getrusage(resource.RUSAGE_SELF)
                        cpu_seconds = (r_after.ru_utime - r_before.ru_utime) + (r_after.ru_stime - r_before.ru_stime)
                        mem_bytes = int(max(0, r_after.ru_maxrss) * 1024)
                    except Exception:
                        cpu_seconds = None
                        mem_bytes = None
                metrics.record_tool_execution(tool_name, success if 'success' in locals() else False, duration_seconds=duration, cpu_seconds=cpu_seconds, memory_bytes=mem_bytes)
