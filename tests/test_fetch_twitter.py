#!/usr/bin/env python3
"""Tests for fetch-twitter.py Bird backend behavior."""

import importlib.util
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
MODULE_PATH = SCRIPTS_DIR / "fetch-twitter.py"

spec = importlib.util.spec_from_file_location("fetch_twitter", MODULE_PATH)
fetch_twitter = importlib.util.module_from_spec(spec)
sys.modules["fetch_twitter"] = fetch_twitter
spec.loader.exec_module(fetch_twitter)


class TestBirdBackendParsing(unittest.TestCase):
    def setUp(self):
        self.backend_cls = getattr(fetch_twitter, "BirdBackend", None)
        self.source = {
            "id": "steipete-twitter",
            "name": "Steipete",
            "handle": "steipete",
            "priority": True,
            "topics": ["llm"],
        }
        self.cutoff = fetch_twitter.datetime(2026, 3, 27, tzinfo=fetch_twitter.timezone.utc)

    def test_parses_array_output_and_filters_reply_and_retweet(self):
        self.assertIsNotNone(self.backend_cls, "BirdBackend should exist")
        backend = self.backend_cls(cli_command="bird")
        tweets = [
            {
                "id": "1",
                "text": "Plain tweet",
                "createdAt": "2026-03-28T10:00:00.000Z",
                "url": "https://x.com/steipete/status/1",
                "favoriteCount": 12,
                "retweetCount": 3,
                "replyCount": 1,
                "quoteCount": 0,
                "viewCount": 99,
                "isReply": False,
            },
            {
                "id": "2",
                "text": "reply tweet",
                "createdAt": "2026-03-28T09:00:00.000Z",
                "isReply": True,
            },
            {
                "id": "3",
                "text": "RT @someone retweet",
                "createdAt": "2026-03-28T08:00:00.000Z",
            },
        ]

        articles = backend._parse_tweets_payload(tweets, "steipete", ["llm"], self.cutoff)

        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]["tweet_id"], "1")
        self.assertEqual(articles[0]["metrics"]["like_count"], 12)
        self.assertEqual(articles[0]["metrics"]["retweet_count"], 3)
        self.assertEqual(articles[0]["metrics"]["reply_count"], 1)
        self.assertEqual(articles[0]["metrics"]["quote_count"], 0)
        self.assertEqual(articles[0]["metrics"]["impression_count"], 99)

    def test_parses_wrapped_output(self):
        self.assertIsNotNone(self.backend_cls, "BirdBackend should exist")
        backend = self.backend_cls(cli_command="bird")
        payload = {
            "tweets": [
                {
                    "id": "4",
                    "text": "Wrapped output",
                    "createdAt": "2026-03-28T10:00:00.000Z",
                    "url": "https://x.com/steipete/status/4",
                }
            ],
            "nextCursor": "cursor-1",
        }

        articles = backend._parse_tweets_payload(payload, "steipete", ["llm"], self.cutoff)

        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]["tweet_id"], "4")
        self.assertEqual(articles[0]["link"], "https://x.com/steipete/status/4")

    def test_parses_bird_twitter_style_date_format(self):
        self.assertIsNotNone(self.backend_cls, "BirdBackend should exist")
        backend = self.backend_cls(cli_command="bird")
        payload = [
            {
                "id": "5",
                "text": "Bird date format",
                "createdAt": "Fri Mar 27 19:17:35 +0000 2026",
                "likeCount": 10,
                "retweetCount": 2,
            }
        ]

        articles = backend._parse_tweets_payload(payload, "sama", ["llm"], self.cutoff)

        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]["tweet_id"], "5")


class TestSelectBackend(unittest.TestCase):
    def test_selects_bird_backend_when_requested(self):
        backend_cls = getattr(fetch_twitter, "BirdBackend", None)
        self.assertIsNotNone(backend_cls, "BirdBackend should exist")
        with mock.patch.dict(os.environ, {"BIRD_CLI": "bird"}, clear=True):
            with mock.patch.object(fetch_twitter, "check_bird_cli", return_value=(True, None)):
                backend = fetch_twitter.select_backend("bird")
        self.assertIsInstance(backend, backend_cls)

    def test_auto_does_not_select_bird(self):
        with mock.patch.dict(os.environ, {"BIRD_CLI": "bird"}, clear=True):
            backend = fetch_twitter.select_backend("auto")
        self.assertIsNone(backend)

    def test_bird_backend_unavailable_returns_none(self):
        with mock.patch.dict(os.environ, {"BIRD_CLI": "bird"}, clear=True):
            with mock.patch.object(fetch_twitter, "check_bird_cli", return_value=(False, "missing")):
                backend = fetch_twitter.select_backend("bird")
        self.assertIsNone(backend)


class TestBirdBackendExecution(unittest.TestCase):
    def test_fetch_all_uses_single_worker(self):
        backend_cls = getattr(fetch_twitter, "BirdBackend", None)
        self.assertIsNotNone(backend_cls, "BirdBackend should exist")
        backend = backend_cls(cli_command="bird")
        sources = [
            {
                "id": "sama-twitter",
                "name": "Sam Altman",
                "handle": "sama",
                "priority": True,
                "topics": ["llm"],
            }
        ]
        cutoff = fetch_twitter.datetime(2026, 3, 27, tzinfo=fetch_twitter.timezone.utc)
        captured = {}

        class FakeFuture:
            def __init__(self, value):
                self._value = value

            def result(self):
                return self._value

        class FakeExecutor:
            def __init__(self, max_workers):
                captured["max_workers"] = max_workers

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def submit(self, fn, *args, **kwargs):
                return FakeFuture(fn(*args, **kwargs))

        result_item = {
            "source_id": "sama-twitter",
            "source_type": "twitter",
            "name": "Sam Altman",
            "handle": "sama",
            "priority": True,
            "topics": ["llm"],
            "status": "ok",
            "attempts": 1,
            "count": 1,
            "articles": [{"metrics": {"like_count": 1}}],
        }

        with mock.patch.object(fetch_twitter, "ThreadPoolExecutor", FakeExecutor):
            with mock.patch.object(fetch_twitter, "as_completed", side_effect=lambda futures: list(futures)):
                with mock.patch.object(backend, "_fetch_user_tweets", return_value=result_item):
                    results = backend.fetch_all(sources, cutoff)

        self.assertEqual(captured["max_workers"], 1)
        self.assertEqual(len(results), 1)


if __name__ == "__main__":
    unittest.main()
