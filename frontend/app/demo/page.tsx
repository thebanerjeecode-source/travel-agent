"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { createPlan } from "@/lib/api";

const DEMO_REQUEST =
  "Plan a 5-day trip to Japan. Tokyo + Kyoto. $3,000 budget. Love food and temples, hate crowds.";

export default function DemoPage() {
  const router = useRouter();
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;

    async function run() {
      try {
        const result = await createPlan({ request: DEMO_REQUEST, dry_run: true });
        if (typeof window !== "undefined") {
          sessionStorage.setItem(`plan:${result.session_id}`, JSON.stringify(result));
        }
        router.replace(`/plan/${result.session_id}`);
      } catch {
        router.replace("/?demo=failed");
      }
    }
    void run();
  }, [router]);

  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <span className="mb-4 inline-block h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent" />
      <h1 className="text-xl font-semibold text-ink">Running offline demo…</h1>
      <p className="mt-2 text-ink-muted">Japan 5-day itinerary with zero API calls.</p>
    </div>
  );
}
