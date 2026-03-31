#!/usr/bin/env python3
"""Tests for generate-markdown.py."""

import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
MODULE_PATH = SCRIPTS_DIR / "generate-markdown.py"
sys.path.insert(0, str(SCRIPTS_DIR))

spec = importlib.util.spec_from_file_location("generate_markdown", MODULE_PATH)
generate_markdown = importlib.util.module_from_spec(spec)
sys.modules["generate_markdown"] = generate_markdown
spec.loader.exec_module(generate_markdown)


class TestGenerateMarkdown(unittest.TestCase):
    def test_build_report_includes_required_sections_and_zero_notes(self):
        merged = {
            "input_sources": {
                "rss_articles": 0,
                "twitter_articles": 1,
                "web_articles": 1,
                "github_articles": 1,
                "github_trending": 1,
                "reddit_posts": 0,
            },
            "output_stats": {"total_articles": 4},
            "topics": {
                "llm": {
                    "articles": [
                        {
                            "title": "Sam Altman 讨论新模型发布",
                            "link": "https://x.com/sama/status/123",
                            "snippet": "提到模型能力提升和推理成本下降。",
                            "source_type": "twitter",
                            "display_name": "Sam Altman",
                            "source_name": "OpenAI CEO",
                            "quality_score": 12,
                            "metrics": {
                                "impression_count": 12345,
                                "reply_count": 23,
                                "retweet_count": 45,
                                "like_count": 678,
                            },
                        },
                        {
                            "title": "新开源大模型训练方案",
                            "link": "https://example.com/llm",
                            "snippet": "聚焦训练效率和推理成本。",
                            "source_type": "web",
                            "source_name": "Example",
                            "quality_score": 9,
                        },
                    ]
                },
                "ai-agent": {
                    "articles": [
                        {
                            "title": "acme/agent-framework v1.2.0",
                            "link": "https://github.com/acme/agent-framework/releases/tag/v1.2.0",
                            "snippet": "新增多代理调度与恢复机制。",
                            "source_type": "github",
                            "source_name": "acme/agent-framework",
                            "quality_score": 8,
                        },
                        {
                            "title": "acme/agent-framework: Agent orchestration toolkit",
                            "link": "https://github.com/acme/agent-framework",
                            "snippet": "支持多代理编排。",
                            "source_type": "github_trending",
                            "source_name": "github-trending",
                            "quality_score": 7,
                            "stars": 2300,
                            "daily_stars_est": 88,
                            "language": "Python",
                        },
                    ]
                },
            },
        }
        topic_meta = [
            {"id": "llm", "emoji": "🧠", "label": "LLM / 大模型"},
            {"id": "ai-agent", "emoji": "🤖", "label": "AI Agent"},
        ]

        markdown = generate_markdown.build_report(merged, topic_meta, "2026-03-31")

        self.assertIn("# 科技情报日报 | 2026-03-31", markdown)
        self.assertIn("## 📢 KOL 更新", markdown)
        self.assertIn("## 📦 GitHub Releases", markdown)
        self.assertIn("## 🐙 GitHub Trending", markdown)
        self.assertIn("覆盖提醒：本期以下来源没有产出可用条目：RSS、Reddit。", markdown)

    def test_topic_section_respects_score_threshold_and_order(self):
        merged = {
            "input_sources": {},
            "output_stats": {"total_articles": 3},
            "topics": {
                "llm": {
                    "articles": [
                        {"title": "高分条目", "link": "https://example.com/a", "source_type": "web", "source_name": "A", "quality_score": 9},
                        {"title": "低分条目", "link": "https://example.com/b", "source_type": "web", "source_name": "B", "quality_score": 4},
                        {"title": "中分条目", "link": "https://example.com/c", "source_type": "web", "source_name": "C", "quality_score": 7},
                    ]
                }
            },
        }
        topic_meta = [{"id": "llm", "emoji": "🧠", "label": "LLM / 大模型"}]

        markdown = generate_markdown.build_report(merged, topic_meta, "2026-03-31")

        self.assertIn("高分条目", markdown)
        self.assertIn("中分条目", markdown)
        self.assertNotIn("低分条目", markdown)
        self.assertLess(markdown.index("高分条目"), markdown.index("中分条目"))


if __name__ == "__main__":
    unittest.main()
