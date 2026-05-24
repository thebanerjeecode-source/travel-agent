from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import structlog
import typer
from dotenv import load_dotenv

from src.llm.rate_limiter import RateLimitExceeded, RateLimiter
from src.llm.types import ModelProvider
from src.orchestrator import PHASE_INTENT, PHASE_PLANNING, PHASE_STUB, Orchestrator
from src.plan_output import build_plan_payload, gemini_rpd_warning
from src.render.markdown import render_trip_markdown
from src.render.terminal import render_trip_terminal

load_dotenv()

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
)

app = typer.Typer(no_args_is_help=True, help="AI Travel Planner — multi-agent trip planning")


def _build_output_payload(trip_plan, context) -> dict:
    return build_plan_payload(trip_plan, context)


def _gemini_rpd_warning() -> str | None:
    return gemini_rpd_warning()


def _print_trace(context) -> None:
    typer.echo("\n--- Execution Trace ---", err=True)
    for entry in context.trace:
        typer.echo(
            f"[{entry.step}] {entry.agent} ({entry.provider}/{entry.model}) → {entry.message}",
            err=True,
        )
    groq_usage = RateLimiter.get().usage(ModelProvider.GROQ)
    typer.echo(f"\nGroq quota: {groq_usage.summary()}", err=True)
    gemini_usage = RateLimiter.get().usage(ModelProvider.GEMINI)
    typer.echo(f"Gemini quota: {gemini_usage.summary()}", err=True)
    warning = _gemini_rpd_warning()
    if warning:
        typer.echo(f"⚠ {warning}", err=True)
    if context.data_provenance:
        typer.echo(f"Data sources: {context.data_provenance}", err=True)
    typer.echo("", err=True)


@app.command()
def plan(
    request: str = typer.Argument(..., help="Natural-language travel request"),
    trace: bool = typer.Option(False, "--trace", help="Print agent execution trace"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON to stdout (default: readable text)"),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Save full result (trip plan + trace + metadata) to a JSON file",
    ),
    markdown: Optional[Path] = typer.Option(
        "output/travel-itinerary.md",
        "--markdown",
        "-m",
        help="Save readable itinerary Markdown (use 'none' to skip)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Offline demo — zero API calls, uses stub pipeline",
    ),
    stub: bool = typer.Option(
        False,
        "--stub",
        help="Same as --dry-run (legacy alias)",
    ),
    intent_only: bool = typer.Option(
        False,
        "--intent-only",
        help="Phase 1 only — parse requirements, skip planning agents",
    ),
    planning_only: bool = typer.Option(
        False,
        "--planning-only",
        help="Phase 2 only — skip budget and validation (saves Gemini quota)",
    ),
    data_mode: Optional[str] = typer.Option(
        None,
        "--data-mode",
        help="Data layer mode: seed (offline), live (APIs), auto (default)",
    ),
) -> None:
    """Generate a trip plan from a natural-language request."""
    offline = dry_run or stub
    if offline:
        phase = PHASE_STUB
    elif intent_only:
        phase = PHASE_INTENT
    elif planning_only:
        phase = PHASE_PLANNING
    else:
        phase = None

    orchestrator = (
        Orchestrator(data_mode=data_mode)
        if phase is None
        else Orchestrator(phase=phase, data_mode=data_mode)
    )

    try:
        trip_plan, context = orchestrator.run(request)
    except RateLimitExceeded as exc:
        typer.echo(
            json.dumps(
                {
                    "status": "failed",
                    "error": str(exc),
                    "hint": "Use --dry-run for offline demo or try again tomorrow.",
                },
                indent=2,
            ),
            err=True,
        )
        raise typer.Exit(code=1) from exc

    if trace:
        _print_trace(context)

    payload = _build_output_payload(trip_plan, context)

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2) + "\n")
        typer.echo(f"Saved JSON to {output.resolve()}", err=True)

    md_path = None if (markdown and str(markdown).lower() == "none") else markdown
    if md_path:
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(render_trip_markdown(trip_plan, context))
        typer.echo(f"Saved Markdown to {md_path.resolve()}", err=True)

    if json_output:
        typer.echo(json.dumps(payload["trip_plan"], indent=2))
    else:
        typer.echo(render_trip_terminal(trip_plan, context))

    if trip_plan.status == "failed":
        raise typer.Exit(code=1)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
