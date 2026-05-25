export default function HomePage() {
  return (
    <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-100">
      <section className="mx-auto flex min-h-[80vh] max-w-4xl flex-col justify-center gap-6 rounded-3xl border border-white/10 bg-white/5 p-8 shadow-2xl shadow-cyan-950/30 backdrop-blur">
        <p className="text-sm uppercase tracking-[0.35em] text-cyan-300">AI Orchestrator SaaS</p>
        <h1 className="max-w-2xl text-4xl font-semibold tracking-tight sm:text-6xl">
          Production scaffold ready for the first vertical MVP.
        </h1>
        <p className="max-w-2xl text-base leading-7 text-slate-300 sm:text-lg">
          The repo is wired for the foundation phase: frontend shell, backend health route,
          shared docs, and local infrastructure are in place so implementation can start from a
          stable base.
        </p>
      </section>
    </main>
  );
}
