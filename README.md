# Tech News Digest

> Automated tech news digest from 167 built-in sources (165 enabled), 6 fetch steps, and configurable X plus web search backends.

**English** | [中文](README_CN.md)

[![Tests](https://github.com/draco-agent/tech-news-digest/actions/workflows/test.yml/badge.svg)](https://github.com/draco-agent/tech-news-digest/actions/workflows/test.yml)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![ClawHub](https://img.shields.io/badge/ClawHub-tech--news--digest-blueviolet)](https://clawhub.com/draco-agent/tech-news-digest)
[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Install

### Option A: install in one message

Tell your [OpenClaw](https://openclaw.ai) assistant:

> **"Install tech-news-digest and send a daily digest to #tech-news every morning at 9am"**

More examples:

> "Set up a weekly AI digest, only LLM and AI Agent topics, deliver to Discord #ai-weekly every Monday"

> "Install tech-news-digest, add my RSS feeds, and send crypto news to Telegram"

> "Give me a tech digest right now, skip Twitter sources"

Or install via CLI:

```bash
clawhub install tech-news-digest
```

### Option B: local quick start

```bash
git clone https://github.com/draco-agent/tech-news-digest.git
cd tech-news-digest

python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt

cp .env.example .env
# edit .env, then export it into your shell
set -a
source .env
set +a

mkdir -p workspace/config workspace/archive/tech-news-digest
python3 scripts/validate-config.py --defaults config/defaults --verbose

python3 scripts/run-pipeline.py \
  --defaults config/defaults \
  --config workspace/config \
  --hours 48 \
  --freshness pd \
  --archive-dir workspace/archive/tech-news-digest \
  --output /tmp/td-merged.json \
  --verbose
```

What to expect:

- Merged digest JSON at `/tmp/td-merged.json`
- Pipeline metadata at `/tmp/td-merged.meta.json`
- Optional user overrides in `workspace/config/`
- Without X or web-search credentials, the pipeline still runs, but Twitter/X and web search may contribute `0` items on the first run

## What You Get

A scored, deduplicated digest built from 167 built-in sources:

| Layer | Count | Notes |
|-------|------:|-------|
| RSS | 78 feeds | OpenAI, Anthropic, Ben's Bites, HN, 36Kr, CoinDesk, YouTube-via-RSS |
| X accounts | 48 | KOL/account timelines via API backends or Bird CLI fallback in auto mode |
| Web search | 4 topics | Tavily, Brave, or XCrawl with freshness control |
| GitHub | 28 repos | Releases plus trending coverage in the pipeline |
| Reddit | 13 subs | r/MachineLearning, r/LocalLLaMA, r/CryptoCurrency, and more |

### Pipeline

```text
run-pipeline.py
  -> fetch-rss.py
  -> fetch-twitter.py
  -> fetch-github.py
  -> fetch-github.py --trending
  -> fetch-reddit.py
  -> fetch-web.py
  -> merge-sources.py
  -> enrich-articles.py (optional)
  -> downstream templates / delivery
```

Quality scoring favors priority sources, cross-source confirmation, recency, engagement, and topic fit, then penalizes already-reported items.

## X and Web Backends

These are the two search-related additions you need to understand before running the project.

### X via Bird

- `TWITTER_API_BACKEND=auto` tries `getxapi -> twitterapiio -> official -> bird`
- Bird still supports explicit opt-in with `--backend bird` or `TWITTER_API_BACKEND=bird`
- Bird reads your local X session through the Bird CLI, browser cookies, or `AUTH_TOKEN` plus `CT0`
- In `auto` mode, Bird is only used when API credentials are unavailable and the Bird CLI session is usable

Install Bird if you want the local-session path:

```bash
npm install -g @steipete/bird
# or keep the repo dependency-free and run it on demand
export BIRD_CLI="bunx @steipete/bird"
bird whoami --plain
```

Run only the X layer with Bird:

```bash
python3 scripts/fetch-twitter.py \
  --defaults config/defaults \
  --config workspace/config \
  --hours 24 \
  --backend bird \
  --output /tmp/td-twitter.json \
  --verbose
```

Useful Bird pacing knobs:

- `BIRD_MAX_WORKERS=1`
- `BIRD_REQUEST_INTERVAL_SEC=2.0`
- `BIRD_BATCH_SIZE=25`
- `BIRD_BATCH_COOLDOWN_SEC=900`
- `BIRD_429_COOLDOWN_SEC=900`
- `BIRD_MAX_CONSECUTIVE_429=0`

### Web search via XCrawl

- `WEB_SEARCH_BACKEND=auto` tries `tavily -> brave -> xcrawl -> interface`
- If you explicitly set `tavily`, `brave`, or `xcrawl` without valid credentials, the script falls back to `interface` JSON instead of silently switching providers
- `XCRAWL_API_KEY` enables XCrawl directly or as the third fallback in `auto`

Run only the web layer:

```bash
python3 scripts/fetch-web.py \
  --defaults config/defaults \
  --config workspace/config \
  --freshness pd \
  --output /tmp/td-web.json \
  --verbose
```

Check three fields in the output:

- `api_used`
- `topics_ok`
- `topics[].articles[]`

## Configuration

- Defaults live in `config/defaults/sources.json` and `config/defaults/topics.json`
- User overlays live in `workspace/config/tech-news-digest-sources.json` and `workspace/config/tech-news-digest-topics.json`
- Overlay rules:
  - matching `id` replaces the default entry
  - new `id` appends a new entry
  - `"enabled": false` disables a built-in source

Example overlay:

```json
{
  "sources": [
    {
      "id": "my-blog",
      "type": "rss",
      "enabled": true,
      "url": "https://myblog.com/feed",
      "topics": ["llm"]
    },
    {
      "id": "openai-blog",
      "enabled": false
    }
  ]
}
```

## Environment Variables

Use `.env.example` as the reference list, then export the values into your shell before running the scripts.

```bash
# X API backends
export GETX_API_KEY=""
export TWITTERAPI_IO_KEY=""
export X_BEARER_TOKEN=""
export TWITTER_API_BACKEND="auto"

# Bird backend for local X session
export BIRD_CLI="bird"
export AUTH_TOKEN=""
export CT0=""
export BIRD_MAX_WORKERS="1"
export BIRD_REQUEST_INTERVAL_SEC="2.0"
export BIRD_BATCH_SIZE="25"
export BIRD_BATCH_COOLDOWN_SEC="900"
export BIRD_429_COOLDOWN_SEC="900"
export BIRD_MAX_CONSECUTIVE_429="0"

# Web search backends
export TAVILY_API_KEY=""
export BRAVE_API_KEYS=""
export BRAVE_API_KEY=""
export XCRAWL_API_KEY=""
export WEB_SEARCH_BACKEND="auto"
export BRAVE_PLAN="free"

# GitHub
export GITHUB_TOKEN=""
```

## Common Commands

Validate config:

```bash
python3 scripts/validate-config.py --defaults config/defaults --verbose
```

Run the full pipeline:

```bash
python3 scripts/run-pipeline.py \
  --defaults config/defaults \
  --config workspace/config \
  --hours 48 \
  --freshness pd \
  --archive-dir workspace/archive/tech-news-digest \
  --output /tmp/td-merged.json \
  --verbose
```

Run a lightweight smoke test:

```bash
bash scripts/test-pipeline.sh --only rss,github,web --hours 24
```

Run unit tests:

```bash
python3 -m unittest discover -s tests -v
```

Current offline test baseline: 67 tests passing.

## Dependencies

Core:

```bash
python3 -m pip install -r requirements.txt
```

- `feedparser` for robust RSS parsing
- `jsonschema` for config validation

Optional:

```bash
python3 -m pip install weasyprint
```

- `weasyprint` enables PDF generation

## Repository

**GitHub**: [github.com/draco-agent/tech-news-digest](https://github.com/draco-agent/tech-news-digest)

## Featured In

- [Awesome OpenClaw Use Cases](https://github.com/hesamsheikh/awesome-openclaw-usecases)

## License

MIT License. See [LICENSE](LICENSE).
