Sample Tool: echo

This repository includes a tiny sample tool used for Phase 5 integration testing.

- Module: `backend/app/tools/echo_tool.py`
- Registry: `backend/app/tools/registry.py`

Usage:

- When an execution is submitted with `input_payload` containing a `tool_request` object, the `WorkflowRunner` will publish a `tool.execution.requested` job.
- The job payload looks like: `{ "execution_id": "execution_xxx", "tool_name": "echo", "input_payload": { ... } }`.
- The `tool_worker` will call the tool registry which will import `app.tools.echo_tool` and call its `run` function.

Example `input_payload` to send when running an automation:

{
  "tool_request": {
    "tool_name": "echo",
    "input_payload": {"msg": "hello"}
  }
}

The `echo` tool returns a JSON object with the shape `{ "tool": "echo", "received": <your payload> }`.
