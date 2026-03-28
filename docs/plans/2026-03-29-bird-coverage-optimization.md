# Bird Coverage Optimization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Improve Bird backend coverage for the default Twitter source set by slowing request bursts and reacting to rate limits without changing downstream output format.

**Architecture:** Keep `scripts/fetch-twitter.py` as the only compatibility layer for Bird. Add Bird-specific pacing controls, cooldown behavior, and stop conditions inside `BirdBackend.fetch_all`, then validate with unit tests and a real full-source Bird run.

**Tech Stack:** Python 3.9 standard library, `unittest`, Bird CLI

---

### Task 1: Record pacing controls in code and docs

**Files:**
- Modify: `scripts/fetch-twitter.py`
- Modify: `.env.example`
- Modify: `README.md`
- Modify: `README_CN.md`

**Step 1: Write the failing test**

Add tests in `tests/test_fetch_twitter.py` asserting Bird execution can read pacing config from environment and defaults to serialized execution.

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_fetch_twitter.TestBirdBackendExecution -v`
Expected: FAIL because Bird pacing config helpers do not exist yet.

**Step 3: Write minimal implementation**

Add Bird-specific helpers and defaults:
- `BIRD_MAX_WORKERS` default `1`
- `BIRD_REQUEST_INTERVAL_SEC` default `2.0`
- `BIRD_BATCH_SIZE` default `8`
- `BIRD_BATCH_COOLDOWN_SEC` default `30.0`
- `BIRD_429_COOLDOWN_SEC` default `90.0`
- `BIRD_MAX_CONSECUTIVE_429` default `3`

Expose them only inside Bird backend and document them in env/docs.

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_fetch_twitter.TestBirdBackendExecution -v`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/fetch-twitter.py tests/test_fetch_twitter.py .env.example README.md README_CN.md
git commit -m "feat(twitter): add Bird pacing controls | tune rate-limit strategy safely | allow runtime coverage experiments"
```

### Task 2: Add Bird pacing, batch cooldown, and 429-aware backoff

**Files:**
- Modify: `scripts/fetch-twitter.py`
- Test: `tests/test_fetch_twitter.py`

**Step 1: Write the failing test**

Add tests covering:
- sleep between successful Bird account fetches
- batch cooldown after each batch boundary
- cooldown after a `429` error
- stop remaining fetches after configured consecutive `429` threshold

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_fetch_twitter.TestBirdBackendExecution -v`
Expected: FAIL because current Bird fetch loop only serializes execution and does not pace or cool down.

**Step 3: Write minimal implementation**

Inside `BirdBackend.fetch_all`:
- replace executor-driven loop with explicit ordered iteration
- call `_fetch_user_tweets` one source at a time
- sleep `BIRD_REQUEST_INTERVAL_SEC` after each fetch unless stopping
- sleep `BIRD_BATCH_COOLDOWN_SEC` after every `BIRD_BATCH_SIZE` accounts
- detect `429` from error strings, apply `BIRD_429_COOLDOWN_SEC`
- if consecutive `429` count reaches threshold, stop the round and mark remaining sources as skipped/error due to rate limit guard

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_fetch_twitter.TestBirdBackendExecution -v`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/fetch-twitter.py tests/test_fetch_twitter.py
git commit -m "fix(twitter): add Bird cooldown pacing | reduce repeated 429 bursts | improve end-to-end source coverage"
```

### Task 3: Verify Bird coverage with real default Twitter sources

**Files:**
- Modify: `docs/guide/configuration-and-operations.md`
- Modify: `docs/reports/2026-03-29-bird-coverage-optimization.md`

**Step 1: Write the failing test**

No new unit test. This task is verified by a full Bird experiment and documentation output.

**Step 2: Run experiment to establish baseline**

Run Bird full-source test with `24h` window:

```bash
bash scripts/test-pipeline.sh --only twitter --twitter-backend bird --hours 24 --keep
```

Capture:
- sources total
- sources ok
- sources with articles
- sources error
- total articles
- elapsed time
- first account index where `429` appears

**Step 3: Update docs with measured result**

Write a short report in `docs/reports/2026-03-29-bird-coverage-optimization.md` with:
- what changed
- measured before/after coverage
- measured before/after runtime
- recommendation for default Bird usage

Update operations guide with new Bird pacing env vars.

**Step 4: Run final verification**

Run:

```bash
python3 -m unittest tests.test_merge tests.test_config tests.test_fetch_twitter -v
python3 scripts/validate-config.py --defaults config/defaults --verbose
```

Expected: PASS

**Step 5: Commit**

```bash
git add docs/guide/configuration-and-operations.md docs/reports/2026-03-29-bird-coverage-optimization.md
git commit -m "docs(twitter): report Bird coverage tuning | record measured rate-limit tradeoffs | guide runtime configuration"
```
