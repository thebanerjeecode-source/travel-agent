import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Travel Planner",
  description: "Multi-agent trip planning — day-by-day itineraries with budget and validation",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen">
          <header className="border-b border-slate-200 bg-white/80 backdrop-blur sticky top-0 z-10">
            <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
              <a href="/" className="flex items-center gap-2 font-semibold text-ink">
                <span className="text-xl" aria-hidden>
                  ✈
                </span>
                AI Travel Planner
              </a>
              <nav className="flex gap-4 text-sm text-ink-muted">
                <a href="/" className="hover:text-accent">
                  New trip
                </a>
                <a href="/demo" className="hover:text-accent">
                  Demo
                </a>
              </nav>
            </div>
          </header>
          <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
        </div>
      </body>
    </html>
  );
}
