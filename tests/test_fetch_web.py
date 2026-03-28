#!/usr/bin/env python3
"""Tests for fetch-web.py."""

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

spec = importlib.util.spec_from_file_location("fetch_web", SCRIPTS_DIR / "fetch-web.py")
fetch_web = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetch_web)


class FakeHTTPResponse:
    def __init__(self, payload, headers=None):
        self.payload = payload
        self.headers = headers or {}

    def read(self):
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class TestFetchWebProviders(unittest.TestCase):
    def test_search_topic_tavily_returns_standardized_shape(self):
        topic = {
            "id": "llm",
            "search": {
                "queries": ["llm latest news", "gpt updates"],
                "must_include": ["gpt"],
                "exclude": ["rumor"],
            },
        }
        tavily_results = [
            {
                "query": "llm latest news",
                "status": "ok",
                "total": 2,
                "results": [
                    {"title": "GPT ships", "link": "https://example.com/1", "snippet": "gpt news", "date": "2026-03-28T00:00:00+00:00"},
                    {"title": "Rumor only", "link": "https://example.com/2", "snippet": "gpt rumor", "date": "2026-03-28T00:00:00+00:00"},
                ],
            },
            {
                "query": "gpt updates",
                "status": "error",
                "total": 0,
                "results": [],
            },
        ]

        with patch.object(fetch_web, "search_tavily", side_effect=tavily_results):
            result = fetch_web.search_topic_tavily(topic, "tvly-key", days=2)

        self.assertEqual(result["topic_id"], "llm")
        self.assertEqual(result["queries_executed"], 2)
        self.assertEqual(result["queries_ok"], 1)
        self.assertEqual(len(result["query_stats"]), 2)
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["articles"][0]["topics"], ["llm"])

    def test_search_topic_xcrawl_maps_results_to_articles(self):
        topic = {
            "id": "ai-agent",
            "search": {
                "queries": ["ai agent news"],
                "must_include": ["agent"],
                "exclude": ["directory"],
            },
        }

        with patch.object(
            fetch_web,
            "search_xcrawl",
            return_value={
                "query": "ai agent news",
                "status": "ok",
                "total": 2,
                "results": [
                    {
                        "title": "Agent framework ships",
                        "link": "https://example.com/agent",
                        "snippet": "agent framework release",
                        "date": "2026-03-28T00:00:00+00:00",
                        "source": "xcrawl",
                    },
                    {
                        "title": "Agent directory",
                        "link": "https://example.com/directory",
                        "snippet": "agent directory",
                        "date": "2026-03-28T00:00:00+00:00",
                        "source": "xcrawl",
                    },
                ],
            },
        ):
            result = fetch_web.search_topic_xcrawl(topic, "xcrawl-key")

        self.assertEqual(result["topic_id"], "ai-agent")
        self.assertEqual(result["queries_executed"], 1)
        self.assertEqual(result["queries_ok"], 1)
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["articles"][0]["source"], "xcrawl")
        self.assertEqual(result["articles"][0]["topics"], ["ai-agent"])

    def test_main_auto_uses_xcrawl_when_tavily_and_brave_are_missing(self):
        topic = {
            "id": "llm",
            "search": {"queries": ["llm latest news"], "must_include": [], "exclude": []},
        }
        payload = {
            "search_id": "job-1",
            "endpoint": "search",
            "version": "v1",
            "status": "completed",
            "query": "llm latest news",
            "data": {
                "status": "success",
                "data": [
                    {
                        "title": "LLM release",
                        "url": "https://example.com/llm-release",
                        "description": "Large model update",
                    }
                ],
                "startedAt": "2026-03-28T00:00:00Z",
                "endedAt": "2026-03-28T00:00:01Z",
                "credits_used": 2,
            },
            "started_at": "2026-03-28T00:00:00Z",
            "ended_at": "2026-03-28T00:00:01Z",
            "total_credits_used": 2,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "web.json"
            argv = ["fetch-web.py", "--output", str(output_path)]
            env = {
                "WEB_SEARCH_BACKEND": "auto",
                "XCRAWL_API_KEY": "xcrawl-key",
            }
            with patch.object(fetch_web, "load_topics", return_value=[topic]), \
                 patch.object(fetch_web, "urlopen", return_value=FakeHTTPResponse(payload)), \
                 patch.object(sys, "argv", argv), \
                 patch.dict(fetch_web.os.environ, env, clear=True):
                exit_code = fetch_web.main()

            self.assertEqual(exit_code, 0)
            with open(output_path, "r", encoding="utf-8") as f:
                data = json.load(f)

        self.assertEqual(data["api_used"], "xcrawl")
        self.assertEqual(data["topics_ok"], 1)
        self.assertEqual(data["total_articles"], 1)
        self.assertEqual(data["topics"][0]["topic_id"], "llm")

    def test_main_explicit_xcrawl_keeps_xcrawl_priority(self):
        topic = {
            "id": "crypto",
            "search": {"queries": ["crypto latest news"], "must_include": [], "exclude": []},
        }
        payload = {
            "search_id": "job-2",
            "endpoint": "search",
            "version": "v1",
            "status": "completed",
            "query": "crypto latest news",
            "data": {
                "status": "success",
                "data": [
                    {
                        "title": "Crypto infra update",
                        "url": "https://example.com/crypto",
                        "description": "Exchange infra ships",
                    }
                ],
                "startedAt": "2026-03-28T00:00:00Z",
                "endedAt": "2026-03-28T00:00:01Z",
                "credits_used": 2,
            },
            "started_at": "2026-03-28T00:00:00Z",
            "ended_at": "2026-03-28T00:00:01Z",
            "total_credits_used": 2,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "web.json"
            argv = ["fetch-web.py", "--output", str(output_path)]
            env = {
                "WEB_SEARCH_BACKEND": "xcrawl",
                "XCRAWL_API_KEY": "xcrawl-key",
                "TAVILY_API_KEY": "tvly-key",
                "BRAVE_API_KEY": "brave-key",
            }
            with patch.object(fetch_web, "load_topics", return_value=[topic]), \
                 patch.object(fetch_web, "urlopen", return_value=FakeHTTPResponse(payload)), \
                 patch.object(sys, "argv", argv), \
                 patch.dict(fetch_web.os.environ, env, clear=True):
                exit_code = fetch_web.main()

            self.assertEqual(exit_code, 0)
            with open(output_path, "r", encoding="utf-8") as f:
                data = json.load(f)

        self.assertEqual(data["api_used"], "xcrawl")
        self.assertEqual(data["topics_ok"], 1)


if __name__ == "__main__":
    unittest.main()
