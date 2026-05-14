#!/usr/bin/env python3
"""
main.py — Finance Follow-Up Agent
Usage:
    python main.py                     # dry-run on sample_invoices.csv
    python main.py --send              # real send (uses EMAIL_MODE in .env)
    python main.py --file my_data.csv  # custom data file
    python main.py --file data.xlsx --send
"""

import argparse
import sys

import config
from config import validate_config
from agent.trigger_logic import run_agent


def main():
    parser = argparse.ArgumentParser(
        description="Finance Follow-Up Email Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--file", "-f",
        default=None,
        help="Path to CSV/Excel invoice file (default: DATA_FILE in .env)",
    )
    parser.add_argument(
        "--send",
        action="store_true",
        default=False,
        help="Actually send emails (default is dry-run)",
    )
    args = parser.parse_args()

    # ── Config validation ─────────────────────────────────────────────────────
    issues = validate_config()
    if issues:
        print("[Config] ⚠  Configuration issues found:")
        for issue in issues:
            print(f"   • {issue}")
        if not config.ANTHROPIC_API_KEY:
            print("\nSet ANTHROPIC_API_KEY in your .env file to proceed.\n")
            sys.exit(1)

    dry_run = not args.send
    if dry_run:
        print("[Mode] Running in DRY-RUN mode — no emails will be sent.\n"
              "       Pass --send flag to enable real delivery.\n")

    run_agent(data_file=args.file, dry_run_override=dry_run)


if __name__ == "__main__":
    main()
