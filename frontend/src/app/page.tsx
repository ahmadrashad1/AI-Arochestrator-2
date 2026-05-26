'use client';

import { useEffect, useMemo, useState } from 'react';

type Workflow = {
  id: string;
  name: string;
  description?: string | null;
  status?: string | null;
};

type ExecutionSummary = {
  id: string;
  workflow_id: string;
  status: string;
  progress?: number;
  message?: string;
};

type ExecutionTrace = {
  execution_id: string;
  trace: Array<Record<string, unknown>>;
};

const defaultEmail = 'admin@acme.ai';
const defaultPassword = 'password123';

function apiBase() {
  return process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
}

async function apiFetch<T>(path: string, token?: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBase()}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers || {}),
    },
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export default function HomePage() {
  const [email, setEmail] = useState(defaultEmail);
  const [password, setPassword] = useState(defaultPassword);
  const [token, setToken] = useState('');
  const [tenantName, setTenantName] = useState('');
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState('');
  const [execution, setExecution] = useState<ExecutionSummary | null>(null);
  const [trace, setTrace] = useState<ExecutionTrace | null>(null);
  const [cost, setCost] = useState<Record<string, unknown> | null>(null);
  const [status, setStatus] = useState('Ready to connect to the control plane.');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const savedToken = window.localStorage.getItem('ai-orchestrator-token');
    const savedTenant = window.localStorage.getItem('ai-orchestrator-tenant');
    if (savedToken) {
      setToken(savedToken);
      setTenantName(savedTenant || '');
      void loadDashboard(savedToken);
    }
  }, []);

  const selectedWorkflowName = useMemo(() => workflows.find((workflow) => workflow.id === selectedWorkflow)?.name || 'No workflow selected', [selectedWorkflow, workflows]);

  async function loadDashboard(accessToken: string) {
    const workflowList = await apiFetch<Workflow[]>('/api/v1/workflows', accessToken);
    setWorkflows(workflowList);
    setSelectedWorkflow((current) => current || workflowList[0]?.id || '');
    setStatus(`Loaded ${workflowList.length} workflows.`);
  }

  async function handleLogin() {
    setBusy(true);
    setStatus('Authenticating operator...');
    try {
      const result = await apiFetch<{ access_token: string; tenant: { name: string } }>('/api/v1/auth/login', undefined, {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      setToken(result.access_token);
      setTenantName(result.tenant.name);
      window.localStorage.setItem('ai-orchestrator-token', result.access_token);
      window.localStorage.setItem('ai-orchestrator-tenant', result.tenant.name);
      await loadDashboard(result.access_token);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'Login failed.');
    } finally {
      setBusy(false);
    }
  }

  async function loadExecutionSnapshot(executionId: string, accessToken: string) {
    const executionStatus = await apiFetch<ExecutionSummary>(`/api/v1/executions/${executionId}`, accessToken);
    const executionTrace = await apiFetch<ExecutionTrace>(`/api/v1/executions/${executionId}/trace`, accessToken);
    const executionCost = await apiFetch<Record<string, unknown>>(`/api/v1/executions/${executionId}/cost`, accessToken);
    setExecution(executionStatus);
    setTrace(executionTrace);
    setCost(executionCost);
  }

  async function runWorkflow() {
    if (!selectedWorkflow) {
      setStatus('Select a workflow first.');
      return;
    }

    setBusy(true);
    setStatus('Launching multi-agent automation...');
    try {
      const runResult = await apiFetch<{ id: string; workflow_id: string; status: string }>('/api/v1/automations/' + selectedWorkflow + '/run', token, {
        method: 'POST',
        body: JSON.stringify({
          input_payload: {
            name: 'Taylor',
            company: 'Acme Labs',
            email: 'taylor@acmelabs.ai',
            role: 'Head of Growth',
            research_query: 'lead generation and outreach',
            llm_tier: 'standard',
          },
        }),
      });
      setStatus(`Workflow ${runResult.workflow_id} queued as ${runResult.id}. Fetching execution telemetry...`);
      await loadExecutionSnapshot(runResult.id, token);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : 'Workflow launch failed.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="min-h-screen overflow-hidden bg-[#050816] text-white">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(34,211,238,0.18),_transparent_28%),radial-gradient(circle_at_top_right,_rgba(99,102,241,0.18),_transparent_26%),linear-gradient(180deg,_rgba(5,8,22,0.96),_rgba(2,6,23,1))]" />
      <div className="absolute inset-0 opacity-30 [background-image:linear-gradient(rgba(255,255,255,0.06)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.06)_1px,transparent_1px)] [background-size:48px_48px]" />

      <section className="relative mx-auto flex min-h-screen w-full max-w-7xl flex-col gap-8 px-6 py-8 lg:px-10">
        <header className="flex flex-col gap-4 rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur-xl shadow-[0_0_80px_rgba(34,211,238,0.12)] lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.45em] text-cyan-300/90">AI Orchestrator Control Plane</p>
            <h1 className="mt-3 max-w-3xl text-4xl font-semibold tracking-tight sm:text-6xl">
              Multi-agent automation, instrumented for production and wrapped in a cinematic console.
            </h1>
            <p className="mt-4 max-w-2xl text-sm leading-7 text-slate-300 sm:text-base">
              Log in, launch a workflow, inspect the execution trace, and see cost telemetry in one place.
            </p>
          </div>
          <div className="grid min-w-[16rem] gap-3 rounded-3xl border border-white/10 bg-slate-950/70 p-4 text-sm text-slate-300">
            <div className="flex items-center justify-between gap-4"><span className="text-slate-400">Tenant</span><span className="font-medium text-white">{tenantName || 'Not signed in'}</span></div>
            <div className="flex items-center justify-between gap-4"><span className="text-slate-400">Status</span><span className="font-medium text-cyan-300">{busy ? 'Processing' : 'Idle'}</span></div>
            <div className="flex items-center justify-between gap-4"><span className="text-slate-400">Workflow</span><span className="font-medium text-white">{selectedWorkflowName}</span></div>
          </div>
        </header>

        <div className="grid gap-6 xl:grid-cols-[20rem_minmax(0,1fr)]">
          <aside className="space-y-6 rounded-[2rem] border border-white/10 bg-slate-950/70 p-6 backdrop-blur-xl">
            <div>
              <p className="text-xs uppercase tracking-[0.35em] text-slate-400">Operator Login</p>
              <div className="mt-4 space-y-3">
                <label className="block text-sm text-slate-300">
                  Email
                  <input value={email} onChange={(event) => setEmail(event.target.value)} className="mt-2 w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none placeholder:text-slate-500 focus:border-cyan-400/70" />
                </label>
                <label className="block text-sm text-slate-300">
                  Password
                  <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} className="mt-2 w-full rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-white outline-none placeholder:text-slate-500 focus:border-cyan-400/70" />
                </label>
                <button type="button" onClick={handleLogin} disabled={busy} className="w-full rounded-2xl bg-cyan-400 px-4 py-3 font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-60">
                  {token ? 'Reconnect' : 'Login'}
                </button>
              </div>
            </div>

            <div className="rounded-3xl border border-cyan-400/20 bg-cyan-400/5 p-4 text-sm text-cyan-100">
              Demo credentials are prefilled so you can open the stack and run immediately after Docker starts.
            </div>

            <div className="space-y-3 rounded-3xl border border-white/10 bg-white/5 p-4 text-sm text-slate-300">
              <p className="text-xs uppercase tracking-[0.35em] text-slate-400">Telemetry</p>
              <div className="flex items-center justify-between"><span>Trace</span><span className="text-cyan-300">{trace?.trace.length ?? 0} nodes</span></div>
              <div className="flex items-center justify-between"><span>Cost</span><span className="text-cyan-300">{cost?.llm_usage ? 'ready' : 'pending'}</span></div>
              <div className="flex items-center justify-between"><span>Execution</span><span className="text-cyan-300">{execution?.status ?? 'none'}</span></div>
            </div>
          </aside>

          <section className="space-y-6">
            <div className="grid gap-6 lg:grid-cols-2">
              <div className="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-xs uppercase tracking-[0.35em] text-slate-400">Workflow Control</p>
                    <h2 className="mt-2 text-2xl font-semibold">Launch a vertical workflow</h2>
                  </div>
                  <button type="button" onClick={runWorkflow} disabled={!token || busy || workflows.length === 0} className="rounded-2xl border border-cyan-400/40 bg-cyan-400/10 px-4 py-3 font-semibold text-cyan-100 transition hover:bg-cyan-400/20 disabled:cursor-not-allowed disabled:opacity-50">
                    Run selected workflow
                  </button>
                </div>

                <div className="mt-5 grid gap-4 md:grid-cols-2">
                  <label className="block text-sm text-slate-300 md:col-span-2">
                    Selected workflow
                    <select value={selectedWorkflow} onChange={(event) => setSelectedWorkflow(event.target.value)} className="mt-2 w-full rounded-2xl border border-white/10 bg-slate-950/80 px-4 py-3 text-white outline-none focus:border-cyan-400/70">
                      {workflows.length === 0 ? <option value="">No workflows available yet</option> : null}
                      {workflows.map((workflow) => (
                        <option key={workflow.id} value={workflow.id}>
                          {workflow.name}
                        </option>
                      ))}
                    </select>
                  </label>

                  <div className="rounded-3xl border border-white/10 bg-slate-950/70 p-4">
                    <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Selected workflow</p>
                    <p className="mt-2 text-lg font-medium">{selectedWorkflowName}</p>
                  </div>
                  <div className="rounded-3xl border border-white/10 bg-slate-950/70 p-4">
                    <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Console status</p>
                    <p className="mt-2 text-lg font-medium text-cyan-300">{status}</p>
                  </div>
                </div>
              </div>

              <div className="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
                <p className="text-xs uppercase tracking-[0.35em] text-slate-400">Execution Snapshot</p>
                <div className="mt-4 space-y-3 text-sm text-slate-300">
                  <div className="flex items-center justify-between"><span>ID</span><span className="text-white">{execution?.id ?? '—'}</span></div>
                  <div className="flex items-center justify-between"><span>Status</span><span className="text-cyan-300">{execution?.status ?? '—'}</span></div>
                  <div className="flex items-center justify-between"><span>Progress</span><span className="text-cyan-300">{execution?.progress ?? 0}%</span></div>
                  <div className="flex items-center justify-between"><span>Message</span><span className="text-white">{execution?.message ?? 'Awaiting run.'}</span></div>
                </div>
              </div>
            </div>

            <div className="grid gap-6 xl:grid-cols-2">
              <div className="rounded-[2rem] border border-white/10 bg-slate-950/70 p-6 backdrop-blur-xl">
                <p className="text-xs uppercase tracking-[0.35em] text-slate-400">Trace Timeline</p>
                <div className="mt-4 space-y-3">
                  {(trace?.trace || []).length === 0 ? (
                    <p className="text-sm text-slate-400">Run a workflow to see planner, researcher, validator, and tool steps rendered here.</p>
                  ) : (
                    trace?.trace.map((entry, index) => (
                      <div key={`${index}-${String(entry.stage || entry.node || index)}`} className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-slate-300">
                        <div className="flex items-center justify-between gap-4">
                          <span className="font-medium text-cyan-300">{String(entry.stage || entry.node || entry.agent || 'step')}</span>
                          <span className="text-xs uppercase tracking-[0.3em] text-slate-500">step {index + 1}</span>
                        </div>
                        <pre className="mt-3 overflow-x-auto whitespace-pre-wrap break-words text-xs leading-6 text-slate-300">
                          {JSON.stringify(entry, null, 2)}
                        </pre>
                      </div>
                    ))
                  )}
                </div>
              </div>

              <div className="rounded-[2rem] border border-white/10 bg-slate-950/70 p-6 backdrop-blur-xl">
                <p className="text-xs uppercase tracking-[0.35em] text-slate-400">LLM Cost / Usage</p>
                <div className="mt-4 rounded-3xl border border-cyan-400/20 bg-cyan-400/5 p-4 text-sm text-slate-200">
                  <p className="text-slate-400">Usage summary</p>
                  <p className="mt-2 text-2xl font-semibold text-cyan-300">
                    {cost?.llm_usage ? `Total $${String((cost.llm_usage as { total_cost_usd?: number }).total_cost_usd ?? 0)}` : 'Awaiting execution'}
                  </p>
                  <pre className="mt-4 overflow-x-auto whitespace-pre-wrap break-words text-xs leading-6 text-slate-300">{JSON.stringify(cost, null, 2)}</pre>
                </div>
              </div>
            </div>
          </section>
        </div>
      </section>
    </main>
  );
}