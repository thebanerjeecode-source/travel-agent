import TripForm from "@/components/TripForm";

export default function HomePage() {
  return (
    <div className="grid gap-10 lg:grid-cols-[1fr_320px]">
      <section>
        <h1 className="text-3xl font-bold text-ink">Plan your next trip</h1>
        <p className="mt-2 max-w-xl text-ink-muted">
          Describe where you want to go in plain English. Seven AI agents build a day-by-day
          itinerary with lodging, logistics, budget, and validation.
        </p>
        <div className="mt-8">
          <TripForm />
        </div>
      </section>
      <aside className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm h-fit">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-ink-muted">
          How it works
        </h2>
        <ol className="mt-4 space-y-3 text-sm text-ink-muted">
          <li>1. Intent Parser extracts destinations, budget, preferences</li>
          <li>2. Planning agents research, build days, find stays & routes</li>
          <li>3. Budget Analyst and Validator review the final plan</li>
        </ol>
        <p className="mt-4 text-xs text-ink-muted">
          Tip: enable dry-run for instant offline demos without API keys.
        </p>
      </aside>
    </div>
  );
}
