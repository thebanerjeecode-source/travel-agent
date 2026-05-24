"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { createPlan } from "@/lib/api";

const EXAMPLES = [
  {
    label: "Japan 5-day",
    text: "Plan a 5-day trip to Japan. Tokyo + Kyoto. $3,000 budget. Love food and temples, hate crowds.",
  },
  {
    label: "Jaipur 4-day",
    text: "Plan a 4-day trip to Jaipur. $1,200 budget. Love forts and street food, hate crowds.",
  },
  {
    label: "Europe 10-day",
    text: "10 days in Europe. Paris and Rome. $5,000. Art and history.",
  },
];

interface TripFormProps {
  initialRequest?: string;
  defaultDryRun?: boolean;
}

export default function TripForm({
  initialRequest = "",
  defaultDryRun = false,
}: TripFormProps) {
  const router = useRouter();
  const [request, setRequest] = useState(initialRequest);
  const [dryRun, setDryRun] = useState(defaultDryRun);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!request.trim()) {
      setError("Please describe your trip.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await createPlan({ request: request.trim(), dry_run: dryRun });
      if (typeof window !== "undefined") {
        sessionStorage.setItem(`plan:${result.session_id}`, JSON.stringify(result));
      }
      router.push(`/plan/${result.session_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create plan");
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label htmlFor="request" className="mb-2 block text-sm font-medium text-ink">
          Describe your trip
        </label>
        <textarea
          id="request"
          rows={5}
          value={request}
          onChange={(e) => setRequest(e.target.value)}
          placeholder="Plan a 5-day trip to Tokyo and Kyoto with a $3,000 budget..."
          className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-ink shadow-sm placeholder:text-slate-400"
          disabled={loading}
        />
      </div>

      <div className="flex flex-wrap gap-2">
        {EXAMPLES.map((ex) => (
          <button
            key={ex.label}
            type="button"
            onClick={() => setRequest(ex.text)}
            disabled={loading}
            className="rounded-full border border-slate-200 bg-white px-3 py-1 text-sm text-ink-muted hover:border-accent hover:text-accent disabled:opacity-50"
          >
            {ex.label}
          </button>
        ))}
      </div>

      <label className="flex items-center gap-2 text-sm text-ink-muted">
        <input
          type="checkbox"
          checked={dryRun}
          onChange={(e) => setDryRun(e.target.checked)}
          disabled={loading}
          className="rounded border-slate-300 text-accent focus:ring-accent"
        />
        Dry-run mode (offline demo — no API keys needed)
      </label>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={loading}
        className="inline-flex items-center gap-2 rounded-xl bg-accent px-6 py-3 font-medium text-white shadow-sm hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {loading ? (
          <>
            <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
            Planning your trip…
          </>
        ) : (
          "Generate itinerary"
        )}
      </button>

      {loading && (
        <p className="text-sm text-ink-muted">
          This usually takes 30–90 seconds for live runs. Dry-run completes in a few seconds.
        </p>
      )}
    </form>
  );
}
