import type { TraceEntry } from "@/lib/types";

interface AgentTraceProps {
  trace: TraceEntry[];
  active?: boolean;
}

const AGENT_LABELS: Record<string, string> = {
  intent_parser: "Intent Parser",
  destination_research: "Destination Research",
  itinerary_builder: "Itinerary Builder",
  accommodation: "Accommodation",
  logistics: "Logistics",
  budget_analyst: "Budget Analyst",
  validator: "Validator",
};

export default function AgentTrace({ trace, active }: AgentTraceProps) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-ink-muted">
        Agent trace
      </h2>
      {trace.length === 0 ? (
        <p className="text-sm text-ink-muted">
          {active ? "Waiting for agents…" : "No trace available."}
        </p>
      ) : (
        <ol className="space-y-3">
          {trace.map((entry) => (
            <li key={entry.step} className="flex gap-3 text-sm">
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-accent-soft text-xs font-semibold text-accent">
                {entry.step}
              </span>
              <div className="min-w-0">
                <p className="font-medium text-ink">
                  {AGENT_LABELS[entry.agent] ?? entry.agent}
                  <span className="ml-2 font-normal text-ink-muted">
                    {entry.provider}/{entry.model}
                  </span>
                </p>
                <p className="text-ink-muted">{entry.message}</p>
              </div>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
