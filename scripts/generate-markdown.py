#!/usr/bin/env python3
"""Render merged tech-news-digest JSON into a Chinese markdown report."""

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from config_loader import load_merged_topics

SOURCE_LABELS = {
    "rss": "RSS",
    "twitter": "X",
    "web": "Web",
    "github": "GitHub Release",
    "github_trending": "GitHub Trending",
    "reddit": "Reddit",
}


def load_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_topic_metadata(defaults_dir: Path, config_dir: Optional[Path]) -> List[Dict[str, Any]]:
    topics = load_merged_topics(defaults_dir, config_dir)
    return [topic for topic in topics if topic.get("id")]


def iter_articles(merged: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    for topic in merged.get("topics", {}).values():
        for article in topic.get("articles", []):
            if isinstance(article, dict):
                yield article


def source_link(article: Dict[str, Any]) -> str:
    return (
        article.get("link")
        or article.get("reddit_url")
        or article.get("external_url")
        or ""
    )


def clean_text(value: Any, limit: int = 180) -> str:
    text = " ".join(str(value or "").split())
    if not text:
        return ""
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip(" ,.;:") + "..."


def escape_markdown(text: str) -> str:
    return text.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def format_count(value: Any) -> str:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return "0"

    if number >= 1_000_000:
        return f"{number / 1_000_000:.1f}M"
    if number >= 1_000:
        return f"{number / 1_000:.1f}K"
    return str(number)


def format_score(article: Dict[str, Any]) -> int:
    try:
        return int(round(float(article.get("quality_score", 0))))
    except (TypeError, ValueError):
        return 0


def article_summary(article: Dict[str, Any], limit: int = 140) -> str:
    text = (
        article.get("full_text")
        or article.get("summary")
        or article.get("snippet")
        or ""
    )
    cleaned = clean_text(text, limit=limit)
    if cleaned:
        return cleaned
    return f"来源：{SOURCE_LABELS.get(article.get('source_type', ''), article.get('source_type', '未知来源') or '未知来源')}"


def article_source_name(article: Dict[str, Any]) -> str:
    return (
        article.get("display_name")
        or article.get("source_name")
        or SOURCE_LABELS.get(article.get("source_type", ""), article.get("source_type", "未知来源"))
    )


def render_article_line(article: Dict[str, Any]) -> str:
    title = escape_markdown(clean_text(article.get("title", "未命名条目"), limit=120))
    link = source_link(article)
    source_name = clean_text(article_source_name(article), limit=48)
    summary = clean_text(article_summary(article), limit=140)
    score = format_score(article)
    return f"- 🔥{score} [{title}]({link}) | {source_name} | {summary}"


def build_executive_summary(
    merged: Dict[str, Any],
    articles: List[Dict[str, Any]],
    min_topic_score: int,
) -> List[str]:
    input_sources = merged.get("input_sources", {})
    eligible = [article for article in articles if format_score(article) >= min_topic_score]
    top_titles = [clean_text(article.get("title", ""), limit=48) for article in eligible[:3] if article.get("title")]
    lines = [
        (
            f"- 本次去重后保留 {merged.get('output_stats', {}).get('total_articles', 0)} 条内容，"
            f"覆盖 X {input_sources.get('twitter_articles', 0)}、GitHub Release {input_sources.get('github_articles', 0)}、"
            f"GitHub Trending {input_sources.get('github_trending', 0)}、Reddit {input_sources.get('reddit_posts', 0)}、"
            f"Web {input_sources.get('web_articles', 0)}。"
        )
    ]
    if top_titles:
        lines.append(f"- 当前最值得优先看的话题包括：{'；'.join(top_titles)}。")
    else:
        lines.append("- 当前没有达到日报输出门槛的条目。")
    return lines


def render_topic_sections(
    merged: Dict[str, Any],
    topic_meta: List[Dict[str, Any]],
    top_per_topic: int,
    min_topic_score: int,
) -> List[str]:
    sections: List[str] = []
    topics = merged.get("topics", {})
    known_topic_ids = set()

    for topic in topic_meta:
        topic_id = topic["id"]
        known_topic_ids.add(topic_id)
        topic_articles = topics.get(topic_id, {}).get("articles", [])
        filtered = [
            article for article in topic_articles
            if format_score(article) >= min_topic_score and source_link(article)
        ]
        if not filtered:
            continue
        sections.append(f"## {topic.get('emoji', '•')} {topic.get('label', topic_id)}")
        for article in filtered[:top_per_topic]:
            sections.append(render_article_line(article))
        sections.append("")

    for topic_id, topic_payload in topics.items():
        if topic_id in known_topic_ids:
            continue
        topic_articles = topic_payload.get("articles", [])
        filtered = [
            article for article in topic_articles
            if format_score(article) >= min_topic_score and source_link(article)
        ]
        if not filtered:
            continue
        sections.append(f"## • {topic_id}")
        for article in filtered[:top_per_topic]:
            sections.append(render_article_line(article))
        sections.append("")

    return sections


def render_kol_section(articles: List[Dict[str, Any]], limit: int = 8) -> List[str]:
    items = [article for article in articles if article.get("source_type") == "twitter" and source_link(article)]
    if not items:
        return []

    lines = ["## 📢 KOL 更新"]
    for article in items[:limit]:
        link = source_link(article)
        handle_match = re.search(r"(?:x|twitter)\.com/([^/]+)/status/", link)
        handle = handle_match.group(1) if handle_match else ""
        metrics = article.get("metrics", {})
        metrics_text = (
            f"👁 {format_count(metrics.get('impression_count', 0))} | "
            f"💬 {format_count(metrics.get('reply_count', 0))} | "
            f"🔁 {format_count(metrics.get('retweet_count', 0))} | "
            f"❤️ {format_count(metrics.get('like_count', 0))}"
        )
        name = clean_text(article_source_name(article), limit=40)
        if handle:
            name = f"{name} (@{handle})"
        lines.append(
            f"- **{escape_markdown(name)}** | {clean_text(article_summary(article), limit=120)} | `{metrics_text}` | [原文]({link})"
        )
    lines.append("")
    return lines


def render_github_releases(articles: List[Dict[str, Any]]) -> List[str]:
    items = [article for article in articles if article.get("source_type") == "github" and source_link(article)]
    if not items:
        return []

    lines = ["## 📦 GitHub Releases"]
    for article in items:
        title = escape_markdown(clean_text(article.get("title", "未命名发布"), limit=110))
        lines.append(
            f"- [{title}]({source_link(article)}) | {clean_text(article_source_name(article), limit=48)} | {clean_text(article_summary(article), limit=120)}"
        )
    lines.append("")
    return lines


def render_github_trending(articles: List[Dict[str, Any]]) -> List[str]:
    items = [article for article in articles if article.get("source_type") == "github_trending" and source_link(article)]
    if not items:
        return []

    ranked = sorted(items, key=lambda article: int(article.get("daily_stars_est", 0) or 0), reverse=True)
    selected: List[Dict[str, Any]] = []
    for index, article in enumerate(ranked):
        if index < 5 or int(article.get("daily_stars_est", 0) or 0) > 50:
            selected.append(article)

    lines = ["## 🐙 GitHub Trending"]
    for article in selected:
        title = escape_markdown(clean_text(article.get("title", "未命名仓库"), limit=110))
        stars = format_count(article.get("stars", 0))
        daily = format_count(article.get("daily_stars_est", 0))
        language = clean_text(article.get("language") or "Unknown", limit=24)
        description = clean_text(article_summary(article), limit=120)
        lines.append(
            f"- [{title}]({source_link(article)}) | ⭐ {stars} (+{daily}/day) | {language} | {description}"
        )
    lines.append("")
    return lines


def render_footer(merged: Dict[str, Any]) -> List[str]:
    input_sources = merged.get("input_sources", {})
    zero_notes = [
        ("RSS", input_sources.get("rss_articles", 0)),
        ("X", input_sources.get("twitter_articles", 0)),
        ("Reddit", input_sources.get("reddit_posts", 0)),
        ("Web", input_sources.get("web_articles", 0)),
        ("GitHub Release", input_sources.get("github_articles", 0)),
        ("GitHub Trending", input_sources.get("github_trending", 0)),
    ]
    lines = [
        "---",
        "## 采集统计",
        (
            f"- RSS {input_sources.get('rss_articles', 0)} | X {input_sources.get('twitter_articles', 0)} | "
            f"Reddit {input_sources.get('reddit_posts', 0)} | Web {input_sources.get('web_articles', 0)} | "
            f"GitHub Release {input_sources.get('github_articles', 0)} | "
            f"GitHub Trending {input_sources.get('github_trending', 0)} | "
            f"去重后 {merged.get('output_stats', {}).get('total_articles', 0)}"
        ),
    ]
    zero_items = [name for name, count in zero_notes if int(count or 0) == 0]
    if zero_items:
        lines.append(f"- 覆盖提醒：本期以下来源没有产出可用条目：{'、'.join(zero_items)}。")
    return lines


def build_report(
    merged: Dict[str, Any],
    topic_meta: List[Dict[str, Any]],
    report_date: str,
    top_per_topic: int = 5,
    min_topic_score: int = 5,
) -> str:
    all_articles = sorted(iter_articles(merged), key=format_score, reverse=True)

    sections: List[str] = [f"# 科技情报日报 | {report_date}", "", "## 执行摘要"]
    sections.extend(build_executive_summary(merged, all_articles, min_topic_score=min_topic_score))
    sections.append("")
    sections.extend(render_topic_sections(merged, topic_meta, top_per_topic, min_topic_score))
    sections.extend(render_kol_section(all_articles))
    sections.extend(render_github_releases(all_articles))
    sections.extend(render_github_trending(all_articles))
    sections.extend(render_footer(merged))
    return "\n".join(section for section in sections if section is not None).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render merged JSON into a markdown daily report")
    script_dir = Path(__file__).resolve().parent
    parser.add_argument("--input", "-i", type=Path, required=True, help="Merged JSON input file")
    parser.add_argument("--defaults", type=Path, default=script_dir.parent / "config" / "defaults", help="Defaults config dir")
    parser.add_argument("--config", type=Path, default=None, help="Optional user config overlay dir")
    parser.add_argument("--output", "-o", type=Path, default=None, help="Markdown output file")
    parser.add_argument("--date", required=True, help="Report date in YYYY-MM-DD")
    parser.add_argument("--top-per-topic", type=int, default=5, help="Max items per topic section")
    parser.add_argument("--min-topic-score", type=int, default=5, help="Minimum score in topic sections")
    args = parser.parse_args()

    merged = load_json(args.input)
    topic_meta = load_topic_metadata(args.defaults, args.config)
    markdown = build_report(
        merged,
        topic_meta,
        report_date=args.date,
        top_per_topic=args.top_per_topic,
        min_topic_score=args.min_topic_score,
    )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(markdown, encoding="utf-8")
        print(args.output)
        return 0

    print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
