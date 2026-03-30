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

    def test_auto_falls_back_to_bird_when_api_credentials_are_missing(self):
        backend_cls = getattr(fetch_twitter, "BirdBackend", None)
        self.assertIsNotNone(backend_cls, "BirdBackend should exist")
        with mock.patch.dict(os.environ, {"BIRD_CLI": "bird"}, clear=True):
            with mock.patch.object(fetch_twitter, "check_bird_cli", return_value=(True, None)):
                backend = fetch_twitter.select_backend("auto")
        self.assertIsInstance(backend, backend_cls)

    def test_auto_prefers_api_backends_before_bird(self):
        with mock.patch.dict(
            os.environ,
            {
                "GETX_API_KEY": "test-getx-key",
                "BIRD_CLI": "bird",
            },
            clear=True,
        ):
            with mock.patch.object(fetch_twitter, "check_bird_cli", return_value=(True, None)):
                backend = fetch_twitter.select_backend("auto")
        self.assertIsInstance(backend, fetch_twitter.GetXApiBackend)

    def test_bird_backend_unavailable_returns_none(self):
        with mock.patch.dict(os.environ, {"BIRD_CLI": "bird"}, clear=True):
            with mock.patch.object(fetch_twitter, "check_bird_cli", return_value=(False, "missing")):
                backend = fetch_twitter.select_backend("bird")
        self.assertIsNone(backend)


class TestBirdBackendExecution(unittest.TestCase):
    def _make_source(self, handle: str):
        return {
            "id": f"{handle}-twitter",
            "name": handle,
            "handle": handle,
            "priority": True,
            "topics": ["llm"],
        }

    def test_uses_default_pacing_config(self):
        backend_cls = getattr(fetch_twitter, "BirdBackend", None)
        self.assertIsNotNone(backend_cls, "BirdBackend should exist")

        backend = backend_cls(cli_command="bird")

        self.assertEqual(backend.max_workers, 1)
        self.assertEqual(backend.request_interval_sec, 2.0)
        self.assertEqual(backend.batch_size, 25)
        self.assertEqual(backend.batch_cooldown_sec, 900.0)
        self.assertEqual(backend.cooldown_429_sec, 900.0)
        self.assertEqual(backend.max_consecutive_429, 0)

    def test_reads_pacing_config_from_env(self):
        backend_cls = getattr(fetch_twitter, "BirdBackend", None)
        self.assertIsNotNone(backend_cls, "BirdBackend should exist")

        with mock.patch.dict(os.environ, {
            "BIRD_MAX_WORKERS": "2",
            "BIRD_REQUEST_INTERVAL_SEC": "1.5",
            "BIRD_BATCH_SIZE": "5",
            "BIRD_BATCH_COOLDOWN_SEC": "12",
            "BIRD_429_COOLDOWN_SEC": "33",
            "BIRD_MAX_CONSECUTIVE_429": "4",
        }, clear=True):
            backend = backend_cls(cli_command="bird")

        self.assertEqual(backend.max_workers, 2)
        self.assertEqual(backend.request_interval_sec, 1.5)
        self.assertEqual(backend.batch_size, 5)
        self.assertEqual(backend.batch_cooldown_sec, 12.0)
        self.assertEqual(backend.cooldown_429_sec, 33.0)
        self.assertEqual(backend.max_consecutive_429, 4)

    def test_preserves_zero_for_disabled_consecutive_429_guard(self):
        backend_cls = getattr(fetch_twitter, "BirdBackend", None)
        self.assertIsNotNone(backend_cls, "BirdBackend should exist")

        with mock.patch.dict(os.environ, {
            "BIRD_MAX_CONSECUTIVE_429": "0",
        }, clear=True):
            backend = backend_cls(cli_command="bird")

        self.assertEqual(backend.max_consecutive_429, 0)

    def test_fetch_all_processes_sources_in_order(self):
        backend_cls = getattr(fetch_twitter, "BirdBackend", None)
        self.assertIsNotNone(backend_cls, "BirdBackend should exist")
        backend = backend_cls(cli_command="bird")
        backend.request_interval_sec = 0.0
        backend.batch_size = 99
        backend.batch_cooldown_sec = 0.0
        backend.cooldown_429_sec = 0.0
        sources = [self._make_source("a"), self._make_source("b")]
        cutoff = fetch_twitter.datetime(2026, 3, 27, tzinfo=fetch_twitter.timezone.utc)
        seen = []

        def fake_fetch(source, _cutoff):
            seen.append(source["handle"])
            return {
                "source_id": source["id"],
                "source_type": "twitter",
                "name": source["name"],
                "handle": source["handle"],
                "priority": True,
                "topics": ["llm"],
                "status": "ok",
                "attempts": 1,
                "count": 1,
                "articles": [{"metrics": {"like_count": 1}}],
            }

        with mock.patch.object(backend, "_fetch_user_tweets", side_effect=fake_fetch):
            with mock.patch.object(fetch_twitter.time, "sleep"):
                results = backend.fetch_all(sources, cutoff)

        self.assertEqual(seen, ["a", "b"])
        self.assertEqual(len(results), 2)

    def test_fetch_all_uses_single_worker(self):
        backend_cls = getattr(fetch_twitter, "BirdBackend", None)
        self.assertIsNotNone(backend_cls, "BirdBackend should exist")
        backend = backend_cls(cli_command="bird")
        self.assertEqual(backend.max_workers, 1)

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

        sources = [self._make_source("sama")]
        cutoff = fetch_twitter.datetime(2026, 3, 27, tzinfo=fetch_twitter.timezone.utc)
        with mock.patch.object(backend, "_fetch_user_tweets", return_value=result_item):
            with mock.patch.object(fetch_twitter.time, "sleep"):
                results = backend.fetch_all(sources, cutoff)

        self.assertEqual(len(results), 1)

    def test_fetch_all_sleeps_between_accounts(self):
        backend_cls = getattr(fetch_twitter, "BirdBackend", None)
        backend = backend_cls(cli_command="bird")
        backend.request_interval_sec = 1.5
        backend.batch_size = 99
        backend.batch_cooldown_sec = 0.0
        backend.cooldown_429_sec = 0.0
        sources = [self._make_source("a"), self._make_source("b")]
        cutoff = fetch_twitter.datetime(2026, 3, 27, tzinfo=fetch_twitter.timezone.utc)
        ok_item = {
            "source_type": "twitter",
            "priority": True,
            "topics": ["llm"],
            "status": "ok",
            "attempts": 1,
            "count": 1,
            "articles": [],
        }

        with mock.patch.object(backend, "_fetch_user_tweets", side_effect=[
            {**ok_item, "source_id": "a-twitter", "name": "a", "handle": "a"},
            {**ok_item, "source_id": "b-twitter", "name": "b", "handle": "b"},
        ]):
            with mock.patch.object(fetch_twitter.time, "sleep") as sleep_mock:
                backend.fetch_all(sources, cutoff)

        sleep_mock.assert_any_call(1.5)

    def test_fetch_all_sleeps_after_batch_boundary(self):
        backend_cls = getattr(fetch_twitter, "BirdBackend", None)
        backend = backend_cls(cli_command="bird")
        backend.request_interval_sec = 0.0
        backend.batch_size = 2
        backend.batch_cooldown_sec = 12.0
        backend.cooldown_429_sec = 0.0
        sources = [self._make_source("a"), self._make_source("b"), self._make_source("c")]
        cutoff = fetch_twitter.datetime(2026, 3, 27, tzinfo=fetch_twitter.timezone.utc)
        ok_item = {
            "source_type": "twitter",
            "priority": True,
            "topics": ["llm"],
            "status": "ok",
            "attempts": 1,
            "count": 1,
            "articles": [],
        }

        with mock.patch.object(backend, "_fetch_user_tweets", side_effect=[
            {**ok_item, "source_id": "a-twitter", "name": "a", "handle": "a"},
            {**ok_item, "source_id": "b-twitter", "name": "b", "handle": "b"},
            {**ok_item, "source_id": "c-twitter", "name": "c", "handle": "c"},
        ]):
            with mock.patch.object(fetch_twitter.time, "sleep") as sleep_mock:
                backend.fetch_all(sources, cutoff)

        sleep_mock.assert_any_call(12.0)

    def test_fetch_all_applies_429_cooldown(self):
        backend_cls = getattr(fetch_twitter, "BirdBackend", None)
        backend = backend_cls(cli_command="bird")
        backend.request_interval_sec = 0.0
        backend.batch_size = 99
        backend.batch_cooldown_sec = 0.0
        backend.cooldown_429_sec = 33.0
        sources = [self._make_source("a"), self._make_source("b")]
        cutoff = fetch_twitter.datetime(2026, 3, 27, tzinfo=fetch_twitter.timezone.utc)

        with mock.patch.object(backend, "_fetch_user_tweets", side_effect=[
            {
                "source_id": "a-twitter",
                "source_type": "twitter",
                "name": "a",
                "handle": "a",
                "priority": True,
                "topics": ["llm"],
                "status": "error",
                "attempts": 1,
                "error": "[err] Failed to fetch tweets: HTTP 429: Rate limit exceeded",
                "count": 0,
                "articles": [],
            },
            {
                "source_id": "a-twitter",
                "source_type": "twitter",
                "name": "a",
                "handle": "a",
                "priority": True,
                "topics": ["llm"],
                "status": "ok",
                "attempts": 1,
                "count": 1,
                "articles": [],
            },
            {
                "source_id": "b-twitter",
                "source_type": "twitter",
                "name": "b",
                "handle": "b",
                "priority": True,
                "topics": ["llm"],
                "status": "ok",
                "attempts": 1,
                "count": 1,
                "articles": [],
            },
        ]):
            with mock.patch.object(fetch_twitter.time, "sleep") as sleep_mock:
                backend.fetch_all(sources, cutoff)

        sleep_mock.assert_any_call(33.0)

    def test_fetch_all_retries_same_source_after_429_until_recovered(self):
        backend_cls = getattr(fetch_twitter, "BirdBackend", None)
        backend = backend_cls(cli_command="bird")
        backend.request_interval_sec = 0.0
        backend.batch_size = 99
        backend.batch_cooldown_sec = 0.0
        backend.cooldown_429_sec = 900.0
        backend.max_consecutive_429 = 0
        sources = [self._make_source("a"), self._make_source("b")]
        cutoff = fetch_twitter.datetime(2026, 3, 27, tzinfo=fetch_twitter.timezone.utc)
        rate_limit_item = {
            "source_type": "twitter",
            "priority": True,
            "topics": ["llm"],
            "status": "error",
            "attempts": 1,
            "error": "[err] Failed to fetch tweets: HTTP 429: Rate limit exceeded",
            "count": 0,
            "articles": [],
        }
        ok_item = {
            "source_type": "twitter",
            "priority": True,
            "topics": ["llm"],
            "status": "ok",
            "attempts": 1,
            "count": 1,
            "articles": [],
        }

        with mock.patch.object(backend, "_fetch_user_tweets", side_effect=[
            {**rate_limit_item, "source_id": "a-twitter", "name": "a", "handle": "a"},
            {**ok_item, "source_id": "a-twitter", "name": "a", "handle": "a"},
            {**ok_item, "source_id": "b-twitter", "name": "b", "handle": "b"},
        ]) as fetch_mock:
            with mock.patch.object(fetch_twitter.time, "sleep"):
                results = backend.fetch_all(sources, cutoff)

        self.assertEqual(fetch_mock.call_count, 3)
        self.assertEqual([item["handle"] for item in results], ["a", "b"])
        self.assertEqual(results[0]["status"], "ok")
        self.assertEqual(results[1]["status"], "ok")

    def test_fetch_all_applies_batch_cooldown_after_25_sources(self):
        backend_cls = getattr(fetch_twitter, "BirdBackend", None)
        backend = backend_cls(cli_command="bird")
        backend.request_interval_sec = 0.0
        backend.batch_size = 25
        backend.batch_cooldown_sec = 900.0
        backend.cooldown_429_sec = 0.0
        backend.max_consecutive_429 = 0
        sources = [self._make_source(f"s{i}") for i in range(26)]
        cutoff = fetch_twitter.datetime(2026, 3, 27, tzinfo=fetch_twitter.timezone.utc)
        ok_item = {
            "source_type": "twitter",
            "priority": True,
            "topics": ["llm"],
            "status": "ok",
            "attempts": 1,
            "count": 1,
            "articles": [],
        }
        side_effect = [
            {**ok_item, "source_id": f"s{i}-twitter", "name": f"s{i}", "handle": f"s{i}"}
            for i in range(26)
        ]

        with mock.patch.object(backend, "_fetch_user_tweets", side_effect=side_effect):
            with mock.patch.object(fetch_twitter.time, "sleep") as sleep_mock:
                backend.fetch_all(sources, cutoff)

        sleep_mock.assert_any_call(900.0)


if __name__ == "__main__":
    unittest.main()
