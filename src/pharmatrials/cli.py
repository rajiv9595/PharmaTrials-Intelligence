"""Command-line entry point for PharmaTrials Intelligence."""
from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from pharmatrials.pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Clinical-trial registry analytics pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser(
        "run", help="Extract, transform, validate, export and optionally load studies"
    )
    run.add_argument(
        "--conditions", nargs="+",
        default=["Type 2 Diabetes", "Breast Cancer", "Hypertension"]
    )
    run.add_argument("--page-size", type=int, default=100)
    run.add_argument(
        "--max-pages", type=int, default=2,
        help="Maximum pages per condition; use 0 for all available pages"
    )
    run.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    run.add_argument(
        "--database-url", default=None,
        help="PostgreSQL SQLAlchemy URL; falls back to DATABASE_URL in .env"
    )
    return parser


def main() -> None:
    load_dotenv()
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    args = build_parser().parse_args()
    max_pages = None if args.max_pages == 0 else args.max_pages
    database_url = args.database_url or os.getenv("DATABASE_URL")
    result = run_pipeline(
        conditions=args.conditions,
        output_dir=args.output_dir,
        page_size=args.page_size,
        max_pages=max_pages,
        database_url=database_url,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
