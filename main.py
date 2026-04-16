"""
De-anonymization red-team attack runner.

Usage:
    python main.py data/synthetic_sample.json               # attack all records
    python main.py data/synthetic_sample.json --id synth_001
    python main.py data/synthetic_sample.json --id synth_001 --verbose
"""

# Load .env into os.environ before any ADK/google-genai imports,
# since those libraries read GOOGLE_API_KEY and GOOGLE_GENAI_USE_VERTEXAI
# directly from the environment at client-init time.
from dotenv import load_dotenv
load_dotenv()

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# google-genai types for constructing messages
from google.genai import types as genai_types

from cost_tracker import CostTracker
from deanonymize import root_agent
from models import AttackResult, IdentityRow

console = Console()
APP_NAME = "deanonymize"


def _build_initial_message(identity_row: IdentityRow, max_iterations: int) -> str:
    return (
        "Perform a de-anonymization assessment on the following synthetic identity record.\n\n"
        f"IDENTITY RECORD:\n{identity_row.to_agent_input()}\n\n"
        f"You have a maximum of {max_iterations} total agent calls. Begin your analysis."
    )


def _extract_usage(event) -> tuple[str, int, int]:
    """Return (agent_name, input_tokens, output_tokens) from an ADK event."""
    agent_name = getattr(event, "author", "unknown") or "unknown"

    usage = getattr(event, "usage_metadata", None)
    if usage is None:
        return agent_name, 0, 0

    input_tokens = getattr(usage, "prompt_token_count", 0) or 0
    output_tokens = getattr(usage, "candidates_token_count", 0) or 0
    return str(agent_name), input_tokens, output_tokens


def _print_event_verbose(event) -> None:
    author = getattr(event, "author", "?")
    content = getattr(event, "content", None)
    if content and hasattr(content, "parts") and content.parts:
        text = getattr(content.parts[0], "text", "") or ""
        if text.strip():
            prefix = f"[dim cyan][{author}][/dim cyan]"
            console.print(f"{prefix} {text[:300]}{'…' if len(text) > 300 else ''}")


async def run_attack(identity_row: IdentityRow, verbose: bool = False) -> AttackResult:
    from config import settings

    tracker = CostTracker()
    session_service = InMemorySessionService()

    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id="researcher",
    )

    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    user_message = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=_build_initial_message(identity_row, settings.max_iterations))],
    )

    final_response = ""

    async for event in runner.run_async(
        user_id="researcher",
        session_id=session.id,
        new_message=user_message,
    ):
        agent_name, inp, out = _extract_usage(event)
        if inp or out:
            tracker.record_usage(agent_name, inp, out)

        if hasattr(event, "is_final_response") and event.is_final_response():
            content = getattr(event, "content", None)
            if content and hasattr(content, "parts") and content.parts:
                final_response = getattr(content.parts[0], "text", "") or ""

        if verbose:
            _print_event_verbose(event)

    return AttackResult(
        identity_row_id=identity_row.id,
        success=bool(final_response.strip()),
        findings=final_response,
        summary=final_response,
        iterations_used=tracker.total_agent_calls,
        total_input_tokens=tracker.input_tokens,
        total_output_tokens=tracker.output_tokens,
        cost_usd=tracker.estimated_cost_usd,
        agent_call_counts=tracker.agent_calls,
    )


def _print_result(result: AttackResult) -> None:
    console.print(
        Panel(
            result.findings or "[italic]No findings returned.[/italic]",
            title=f"[bold green]Report — {result.identity_row_id}[/bold green]",
            expand=False,
        )
    )

    table = Table(title="Cost & Usage", show_header=False, box=None)
    table.add_column("Metric", style="bold")
    table.add_column("Value")
    table.add_row("Iterations used", str(result.iterations_used))
    table.add_row("Input tokens", f"{result.total_input_tokens:,}")
    table.add_row("Output tokens", f"{result.total_output_tokens:,}")
    table.add_row("Estimated cost", f"${result.cost_usd:.6f} USD")
    for agent, count in result.agent_call_counts.items():
        table.add_row(f"  {agent} calls", str(count))
    console.print(table)


def _run_with_backoff(identity: IdentityRow, verbose: bool, max_retries: int = 4) -> AttackResult:
    """Run a single attack with exponential backoff on 429 rate-limit errors."""
    delay = 10  # seconds, doubles each retry
    for attempt in range(max_retries + 1):
        try:
            return asyncio.run(run_attack(identity, verbose=verbose))
        except Exception as e:
            is_rate_limit = "429" in str(e) or "resource exhausted" in str(e).lower()
            if is_rate_limit and attempt < max_retries:
                console.print(
                    f"[yellow]Rate limit hit — waiting {delay}s before retry "
                    f"({attempt + 1}/{max_retries})…[/yellow]"
                )
                time.sleep(delay)
                delay *= 2
            else:
                raise


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Red-team de-anonymization attack runner"
    )
    parser.add_argument("input", help="Path to JSON file with identity row(s)")
    parser.add_argument(
        "--id", dest="identity_id", help="Attack only this identity ID (default: all)"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Stream agent events to stdout"
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory to write result JSON files (default: current dir)",
    )
    args = parser.parse_args()

    raw = json.loads(Path(args.input).read_text())
    raw_rows = raw if isinstance(raw, list) else [raw]
    identities = [IdentityRow(**r) for r in raw_rows]

    if args.identity_id:
        identities = [i for i in identities if i.id == args.identity_id]
        if not identities:
            console.print(f"[red]Identity '{args.identity_id}' not found in {args.input}[/red]")
            sys.exit(1)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for identity in identities:
        console.rule(f"[yellow]Attacking: {identity.id}[/yellow]")

        result = _run_with_backoff(identity, verbose=args.verbose)

        _print_result(result)

        out_path = output_dir / f"result_{identity.id}.json"
        out_path.write_text(result.model_dump_json(indent=2))
        console.print(f"[dim]Saved → {out_path}[/dim]\n")


if __name__ == "__main__":
    main()
