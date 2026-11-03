"""Command-line entry point for the MAAPS Auditor Agent.

Usage:
    maaps-auditor <audio-file>            # analyze and print the SonicSignature
    maaps-auditor --json <audio-file>     # same, machine-readable JSON
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from .auditor import AuditorAgent


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="maaps-auditor",
        description="Local DSP audio analysis and quality gatekeeper.",
    )
    parser.add_argument("audio", help="Path to the audio file to analyze")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the result as JSON instead of a table",
    )
    args = parser.parse_args(argv)

    agent = AuditorAgent()
    try:
        signature = asyncio.run(agent.analyze(args.audio))
    except FileNotFoundError:
        print(f"error: file not found: {args.audio}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(signature.model_dump(), indent=2, default=str))
    else:
        for key, value in signature.model_dump().items():
            print(f"{key:24s} {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
