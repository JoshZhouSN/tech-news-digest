#!/usr/bin/env python3
"""Run the digest pipeline and render a date-stamped markdown report."""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
from zoneinfo import ZoneInfo


SCRIPTS_DIR = Path(__file__).resolve().parent


def resolve_report_date(date_arg: Optional[str], timezone_name: str) -> str:
    if date_arg:
        return date_arg
    return datetime.now(ZoneInfo(timezone_name)).date().isoformat()


def build_output_path(output_dir: Path, report_prefix: str, report_date: str) -> Path:
    return output_dir / f"{report_prefix}-{report_date}.md"


def build_pipeline_command(args: argparse.Namespace, merged_output: Path) -> List[str]:
    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "run-pipeline.py"),
        "--defaults", str(args.defaults),
        "--hours", str(args.hours),
        "--freshness", args.freshness,
        "--archive-dir", str(args.archive_dir),
        "--output", str(merged_output),
        "--only", args.only,
        "--verbose",
        "--force",
    ]
    if args.config:
        cmd.extend(["--config", str(args.config)])
    if args.twitter_backend:
        cmd.extend(["--twitter-backend", args.twitter_backend])
    return cmd


def build_render_command(args: argparse.Namespace, merged_output: Path, report_output: Path, report_date: str) -> List[str]:
    cmd = [
        sys.executable,
        str(SCRIPTS_DIR / "generate-markdown.py"),
        "--input", str(merged_output),
        "--defaults", str(args.defaults),
        "--output", str(report_output),
        "--date", report_date,
        "--top-per-topic", str(args.top_per_topic),
        "--min-topic-score", str(args.min_topic_score),
    ]
    if args.config:
        cmd.extend(["--config", str(args.config)])
    return cmd


def cleanup_old_reports(output_dir: Path, report_prefix: str, retention_days: int, report_date: str) -> List[Path]:
    removed: List[Path] = []
    cutoff = datetime.fromisoformat(report_date).date() - timedelta(days=retention_days)
    for path in output_dir.glob(f"{report_prefix}-*.md"):
        suffix = path.stem.removeprefix(f"{report_prefix}-")
        try:
            file_date = datetime.fromisoformat(suffix).date()
        except ValueError:
            continue
        if file_date < cutoff:
            path.unlink()
            removed.append(path)
    return removed


def run_command(cmd: List[str]) -> None:
    subprocess.run(cmd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run pipeline + render a markdown digest")
    parser.add_argument("--defaults", type=Path, default=SCRIPTS_DIR.parent / "config" / "defaults", help="Defaults config dir")
    parser.add_argument("--config", type=Path, default=None, help="Optional user config overlay dir")
    parser.add_argument("--archive-dir", type=Path, required=True, help="Archive dir for dedup and report output")
    parser.add_argument("--output-dir", type=Path, default=None, help="Optional override for markdown output dir")
    parser.add_argument("--merged-output", type=Path, default=Path("/tmp/td-merged.json"), help="Intermediate merged JSON path")
    parser.add_argument("--date", type=str, default=None, help="Override report date YYYY-MM-DD")
    parser.add_argument("--timezone", type=str, default="UTC", help="Timezone used to resolve the default report date")
    parser.add_argument("--report-prefix", type=str, default="daily", help="Markdown filename prefix")
    parser.add_argument("--hours", type=int, default=48, help="Pipeline lookback window")
    parser.add_argument("--freshness", type=str, default="pd", help="Web freshness window")
    parser.add_argument("--only", type=str, default="twitter,github,trending,reddit,web", help="Comma-separated source groups")
    parser.add_argument("--twitter-backend", choices=["official", "twitterapiio", "getxapi", "bird", "auto"], default=None)
    parser.add_argument("--top-per-topic", type=int, default=5)
    parser.add_argument("--min-topic-score", type=int, default=5)
    parser.add_argument("--retention-days", type=int, default=90, help="Delete markdown reports older than this many days")
    args = parser.parse_args()

    report_date = resolve_report_date(args.date, args.timezone)
    output_dir = args.output_dir or args.archive_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    args.archive_dir.mkdir(parents=True, exist_ok=True)

    report_output = build_output_path(output_dir, args.report_prefix, report_date)
    run_command(build_pipeline_command(args, args.merged_output))
    run_command(build_render_command(args, args.merged_output, report_output, report_date))

    removed = cleanup_old_reports(output_dir, args.report_prefix, args.retention_days, report_date)
    merged = json.loads(args.merged_output.read_text(encoding="utf-8"))
    stats = merged.get("input_sources", {})
    print(
        json.dumps(
            {
                "report": str(report_output),
                "date": report_date,
                "removed_archives": [str(path) for path in removed],
                "source_counts": {
                    "twitter": stats.get("twitter_articles", 0),
                    "github_releases": stats.get("github_articles", 0),
                    "github_trending": stats.get("github_trending", 0),
                    "reddit": stats.get("reddit_posts", 0),
                    "web": stats.get("web_articles", 0),
                    "merged": merged.get("output_stats", {}).get("total_articles", 0),
                },
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
