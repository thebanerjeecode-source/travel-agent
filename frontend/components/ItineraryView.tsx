import type { PlanResponse } from "@/lib/types";

interface ItineraryViewProps {
  plan: PlanResponse;
}

function formatUsd(amount: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(amount);
}

export default function ItineraryView({ plan }: ItineraryViewProps) {
  const trip = plan.trip_plan;

  if (trip.status === "failed") {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-6">
        <h2 className="text-lg font-semibold text-red-800">Could not process request</h2>
        <p className="mt-2 text-red-700">{plan.error ?? trip.summary}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-ink">{trip.summary}</h1>
            {trip.requirements && (
              <p className="mt-2 text-ink-muted">
                {trip.requirements.duration_days} days ·{" "}
                {trip.requirements.destinations.join(", ")} ·{" "}
                {formatUsd(trip.requirements.budget_usd)} budget
              </p>
            )}
          </div>
          <span
            className={`rounded-full px-3 py-1 text-sm font-medium ${
              trip.validation_passed
                ? "bg-green-100 text-green-800"
                : "bg-amber-100 text-amber-800"
            }`}
          >
            {trip.validation_passed ? "Validation passed" : "Needs review"}
          </span>
        </div>
        {plan.warning && (
          <p className="mt-4 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">
            {plan.warning}
          </p>
        )}
      </div>

      {trip.day_by_day.length > 0 && (
        <section className="space-y-4">
          <h2 className="text-lg font-semibold text-ink">Day-by-day itinerary</h2>
          {trip.day_by_day.map((day) => (
            <article
              key={day.day}
              className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
            >
              <h3 className="font-semibold text-ink">
                Day {day.day} — {day.city}: {day.theme}
              </h3>
              <ul className="mt-3 space-y-2">
                {day.activities.map((act, i) => (
                  <li key={i} className="flex gap-2 text-sm text-ink-muted">
                    <span className="font-medium capitalize text-ink">{act.time}</span>
                    <span>
                      {act.name} ({act.duration_hours}h)
                    </span>
                  </li>
                ))}
              </ul>
            </article>
          ))}
        </section>
      )}

      {trip.neighborhoods_to_stay.length > 0 && (
        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-lg font-semibold text-ink">Where to stay</h2>
          <div className="mt-4 space-y-4">
            {trip.neighborhoods_to_stay.map((stay) => (
              <div key={stay.city}>
                <h3 className="font-medium text-ink">
                  {stay.city} — {stay.recommended_neighborhood} ({stay.nights} nights)
                </h3>
                <p className="text-sm text-ink-muted">{stay.reason}</p>
                {stay.options.length > 0 && (
                  <ul className="mt-2 space-y-1 text-sm">
                    {stay.options.map((opt) => (
                      <li key={opt.name} className="text-ink-muted">
                        {opt.name} — {formatUsd(opt.price_per_night_usd)}/night
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {trip.logistics && trip.logistics.inter_city.length > 0 && (
        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-lg font-semibold text-ink">Logistics</h2>
          <ul className="mt-3 space-y-2 text-sm">
            {trip.logistics.inter_city.map((leg, i) => (
              <li key={i} className="text-ink-muted">
                {leg.from} → {leg.to}: {leg.mode} ({leg.duration_hours}h,{" "}
                {formatUsd(leg.estimated_cost_usd)})
              </li>
            ))}
          </ul>
          {trip.logistics.local_transit_notes && (
            <p className="mt-3 text-sm text-ink-muted">{trip.logistics.local_transit_notes}</p>
          )}
        </section>
      )}

      {trip.budget && (
        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-lg font-semibold text-ink">Budget</h2>
          <p className="mt-2 text-ink-muted">
            Estimated {formatUsd(trip.budget.estimated_total_usd)} of{" "}
            {formatUsd(trip.budget.budget_usd)} budget
            <span
              className={`ml-2 rounded px-2 py-0.5 text-xs font-medium ${
                trip.budget.status === "within_budget"
                  ? "bg-green-100 text-green-800"
                  : "bg-red-100 text-red-800"
              }`}
            >
              {trip.budget.status.replace("_", " ")}
            </span>
          </p>
          {Object.keys(trip.budget.breakdown).length > 0 && (
            <ul className="mt-3 grid gap-2 sm:grid-cols-2 text-sm">
              {Object.entries(trip.budget.breakdown).map(([key, val]) => (
                <li key={key} className="flex justify-between text-ink-muted">
                  <span className="capitalize">{key.replace(/_/g, " ")}</span>
                  <span>{formatUsd(val)}</span>
                </li>
              ))}
            </ul>
          )}
          {trip.budget.savings_suggestions.length > 0 && (
            <div className="mt-4">
              <p className="text-sm font-medium text-ink">Savings suggestions</p>
              <ul className="mt-1 list-disc pl-5 text-sm text-ink-muted">
                {trip.budget.savings_suggestions.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
