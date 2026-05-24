"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import AgentTrace from "@/components/AgentTrace";
import ItineraryView from "@/components/ItineraryView";
import { fetchPlan, markdownUrl } from "@/lib/api";
import type { PlanResponse } from "@/lib/types";

export default function PlanPage() {
  const params = useParams<{ sessionId: string }>();
  const sessionId = params.sessionId;
  const [plan, setPlan] = useState<PlanResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      if (!sessionId) return;

      if (typeof window !== "undefined") {
        const cached = sessionStorage.getItem(`plan:${sessionId}`);
        if (cached) {
          try {
            setPlan(JSON.parse(cached) as PlanResponse);
            setLoading(false);
            return;
          } catch {
            sessionStorage.removeItem(`plan:${sessionId}`);
          }
        }
      }

      try {
        const data = await fetchPlan(sessionId);
        setPlan(data);
        if (typeof window !== "undefined") {
          sessionStorage.setItem(`plan:${sessionId}`, JSON.stringify(data));
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load plan");
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, [sessionId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-ink-muted">
        Loading itinerary…
      </div>
    );
  }

  if (error || !plan) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-red-700">
        {error ?? "Plan not found"}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <a href="/" className="text-sm text-accent hover:underline">
          ← New trip
        </a>
        <div className="flex gap-3">
          <a
            href={markdownUrl(sessionId)}
            className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm hover:border-accent"
            download
          >
            Download Markdown
          </a>
          <button
            type="button"
            onClick={() => {
              const blob = new Blob([JSON.stringify(plan.trip_plan, null, 2)], {
                type: "application/json",
              });
              const url = URL.createObjectURL(blob);
              const a = document.createElement("a");
              a.href = url;
              a.download = `trip-${sessionId.slice(0, 8)}.json`;
              a.click();
              URL.revokeObjectURL(url);
            }}
            className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm hover:border-accent"
          >
            Download JSON
          </button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
        <AgentTrace trace={plan.trace} />
        <ItineraryView plan={plan} />
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4 text-xs text-ink-muted">
        Groq: {plan.quota.groq.rpd_used}/{plan.quota.groq.rpd_limit} RPD · Gemini:{" "}
        {plan.quota.gemini.rpd_used}/{plan.quota.gemini.rpd_limit} RPD
      </div>
    </div>
  );
}
