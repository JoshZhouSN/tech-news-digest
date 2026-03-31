---
name: tech-news-digest
description: Generate tech news digests with unified source model, quality scoring, and multi-format output. Six-source data collection from RSS feeds, Twitter/X KOLs, GitHub releases, GitHub Trending, Reddit, and web search. Pipeline-based scripts with retry mechanisms and deduplication. Supports Discord, email, and markdown templates.
version: "3.17.0"
homepage: https://github.com/draco-agent/tech-news-digest
source: https://github.com/draco-agent/tech-news-digest
metadata:
  openclaw:
    requires:
      bins: ["python3"]
    optionalBins: ["mail", "msmtp", "gog", "gh", "openssl", "weasyprint", "bird", "bunx"]
env:
  - name: TWITTER_API_BACKEND
    required: false
    description: "Twitter/X backend: 'auto', 'getxapi', 'twitterapiio', 'official', or 'bird' (auto falls back to Bird when API credentials are unavailable and Bird CLI is usable)"
  - name: GETX_API_KEY
    required: false
    description: GetXAPI key for X/Twitter collection (preferred auto backend)
  - name: X_BEARER_TOKEN
    required: false
    description: Twitter/X API bearer token for KOL monitoring (official backend)
  - name: TWITTERAPI_IO_KEY
    required: false
    description: twitterapi.io API key for KOL monitoring (twitterapiio backend)
  - name: BIRD_CLI
    required: false
    description: Bird CLI command for local X session access (default: bird)
  - name: AUTH_TOKEN
    required: false
    description: Optional X auth_token for Bird when browser cookies are unavailable
  - name: CT0
    required: false
    description: Optional X ct0 token for Bird when browser cookies are unavailable
  - name: TAVILY_API_KEY
    required: false
    description: Tavily Search API key (alternative to Brave)
  - name: WEB_SEARCH_BACKEND
    required: false
    description: "Web search backend: auto (default), tavily, brave, or xcrawl"
  - name: BRAVE_API_KEYS
    required: false
    description: Brave Search API keys (comma-separated for rotation)
  - name: BRAVE_API_KEY
    required: false
    description: Brave Search API key (single key fallback)
  - name: BRAVE_PLAN
    required: false
    description: Optional Brave plan hint for rate-limit behavior (free or pro)
  - name: XCRAWL_API_KEY
    required: false
    description: XCrawl Search API key for explicit XCrawl mode or auto fallback
  - name: GITHUB_TOKEN
    required: false
    description: GitHub token for higher API rate limits (auto-generated from GitHub App if not set)
  - name: GH_APP_ID
    required: false
    description: GitHub App ID for automatic installation token generation
  - name: GH_APP_INSTALL_ID
    required: false
    description: GitHub App Installation ID for automatic token generation
  - name: GH_APP_KEY_FILE
    required: false
    description: Path to GitHub App private key PEM file
tools:
  - python3: Required. Runs data collection and merge scripts.
  - mail: Optional. msmtp-based mail command for email delivery (preferred).
  - gog: Optional. Gmail CLI for email delivery (fallback if mail not available).
files:
  read:
    - config/defaults/: Default source and topic configurations
    - references/: Prompt templates and output templates
    - scripts/: Python pipeline scripts
    - <workspace>/archive/tech-news-digest/: Previous digests for dedup
  write:
    - /tmp/td-*.json: Temporary pipeline intermediate outputs
    - /tmp/td-email.html: Temporary email HTML body
    - /tmp/td-digest.pdf: Generated PDF digest
    - <workspace>/archive/tech-news-digest/: Saved digest archives
---

# Tech News Digest

Automated tech news digest system with unified data source model, quality scoring pipeline, and template-based output generation.

## Quick Start

1. **Configuration Setup**: Default configs are in `config/defaults/`. Copy to workspace for customization:
   ```bash
   mkdir -p workspace/config
   cp config/defaults/sources.json workspace/config/tech-news-digest-sources.json
   cp config/defaults/topics.json workspace/config/tech-news-digest-topics.json
   ```

2. **Environment Variables**: 
   - `GETX_API_KEY` - GetXAPI key for X/Twitter collection (optional, preferred auto backend)
   - `TWITTERAPI_IO_KEY` - twitterapi.io API key (optional, preferred)
   - `X_BEARER_TOKEN` - Twitter/X official API bearer token (optional, fallback)
   - `BIRD_CLI` - Bird CLI command for local X session access (optional, explicit backend or auto fallback when API credentials are unavailable)
   - `AUTH_TOKEN` / `CT0` - Optional X session tokens for Bird when browser cookies are unavailable
   - `TAVILY_API_KEY` - Tavily Search API key (optional, first auto web backend)
   - `XCRAWL_API_KEY` - XCrawl Search API key (optional, explicit backend or auto fallback)
   - `WEB_SEARCH_BACKEND` - Web search backend: auto|tavily|brave|xcrawl (optional, default: auto)
   - `BRAVE_API_KEYS` - Brave Search API keys, comma-separated for rotation (optional)
   - `BRAVE_API_KEY` - Single Brave key fallback (optional)
   - `BRAVE_PLAN` - Brave rate-limit hint: free|pro (optional)
   - `GITHUB_TOKEN` - GitHub personal access token (optional, improves rate limits)

3. **Generate Digest**:
   ```bash
   # Unified pipeline (recommended) — runs all 6 sources in parallel + merge
   python3 scripts/run-pipeline.py \
     --defaults config/defaults \
     --config workspace/config \
     --hours 48 --freshness pd \
     --archive-dir workspace/archive/tech-news-digest/ \
     --output /tmp/td-merged.json --verbose --force
   ```

4. **Use Templates**: Apply Discord, email, or PDF templates to merged output

## Configuration Files

### `sources.json` - Unified Data Sources
```json
{
  "sources": [
    {
      "id": "openai-rss",
      "type": "rss",
      "name": "OpenAI Blog",
      "url": "https://openai.com/blog/rss.xml",
      "enabled": true,
      "priority": true,
      "topics": ["llm", "ai-agent"],
      "note": "Official OpenAI updates"
    },
    {
      "id": "sama-twitter",
      "type": "twitter", 
      "name": "Sam Altman",
      "handle": "sama",
      "enabled": true,
      "priority": true,
      "topics": ["llm", "frontier-tech"],
      "note": "OpenAI CEO"
    }
  ]
}
```

### `topics.json` - Enhanced Topic Definitions
```json
{
  "topics": [
    {
      "id": "llm",
      "emoji": "🧠",
      "label": "LLM / Large Models",
      "description": "Large Language Models, foundation models, breakthroughs",
      "search": {
        "queries": ["LLM latest news", "large language model breakthroughs"],
        "must_include": ["LLM", "large language model", "foundation model"],
        "exclude": ["tutorial", "beginner guide"]
      },
      "display": {
        "max_items": 8,
        "style": "detailed"
      }
    }
  ]
}
```

## Scripts Pipeline

### `run-pipeline.py` - Unified Pipeline (Recommended)
```bash
python3 scripts/run-pipeline.py \
  --defaults config/defaults [--config CONFIG_DIR] \
  --hours 48 --freshness pd \
  --archive-dir workspace/archive/tech-news-digest/ \
  --output /tmp/td-merged.json --verbose --force
```
- **Features**: Runs all 6 fetch steps in parallel, then merges + deduplicates + scores
- **Output**: Final merged JSON ready for report generation (~30s total)
- **Metadata**: Saves per-step timing and counts to `*.meta.json`
- **GitHub Auth**: Auto-generates GitHub App token if `$GITHUB_TOKEN` not set
- **Fallback**: If this fails, run individual scripts below

### Individual Scripts (Fallback)

#### `fetch-rss.py` - RSS Feed Fetcher
```bash
python3 scripts/fetch-rss.py [--defaults DIR] [--config DIR] [--hours 48] [--output FILE] [--verbose]
```
- Parallel fetching (10 workers), retry with backoff, feedparser + regex fallback
- Timeout: 30s per feed, ETag/Last-Modified caching

#### `fetch-twitter.py` - Twitter/X KOL Monitor
```bash
python3 scripts/fetch-twitter.py [--defaults DIR] [--config DIR] [--hours 48] [--output FILE] [--backend auto|getxapi|official|twitterapiio|bird]
```
- Backend auto-detection on current main: `getxapi -> twitterapiio -> official -> bird`
- Bird CLI can be selected explicitly for local X session access (`--backend bird`) and is also the final fallback in `auto`
- Rate limit handling, engagement metrics, retry with backoff

#### `fetch-web.py` - Web Search Engine
```bash
python3 scripts/fetch-web.py [--defaults DIR] [--config DIR] [--freshness pd] [--output FILE]
```
- Auto backend order: `tavily -> brave -> xcrawl -> interface`
- Explicit `tavily` / `brave` / `xcrawl` without valid credentials falls back to interface JSON instead of silently switching providers
- Auto-detects Brave API rate limit: paid plans → parallel queries, free → sequential

#### `fetch-github.py` - GitHub Releases Monitor
```bash
python3 scripts/fetch-github.py [--defaults DIR] [--config DIR] [--hours 168] [--output FILE]
```
- Parallel fetching (10 workers), 30s timeout
- Auth priority: `$GITHUB_TOKEN` → GitHub App auto-generate → `gh` CLI → unauthenticated (60 req/hr)


#### `fetch-github.py --trending` - GitHub Trending Repos
```bash
python3 scripts/fetch-github.py --trending [--hours 48] [--output FILE] [--verbose]
```
- Searches GitHub API for trending repos across 4 topics (LLM, AI Agent, Crypto, Frontier Tech)
- Quality scoring: base 5 + daily_stars_est / 10, max 15

#### `fetch-reddit.py` - Reddit Posts Fetcher
```bash
python3 scripts/fetch-reddit.py [--defaults DIR] [--config DIR] [--hours 48] [--output FILE]
```
- Parallel fetching (4 workers), public JSON API (no auth required)
- 13 subreddits with score filtering


#### `generate-markdown.py` - Deterministic Markdown Daily Report
```bash
python3 scripts/generate-markdown.py \
  --input /tmp/td-merged.json \
  --defaults config/defaults \
  --config workspace/config \
  --date 2026-03-31 \
  --output workspace/archive/tech-news-digest/daily-2026-03-31.md
```
- Renders a Simplified Chinese markdown daily report directly from merged JSON
- Keeps fixed sections for topic picks, KOL updates, GitHub releases, GitHub trending, and footer stats
- Uses source counts from merged metadata, so empty sources are called out instead of fabricated

#### `run-daily-digest.py` - One-Shot Daily Pipeline + Markdown Output
```bash
python3 scripts/run-daily-digest.py \
  --defaults config/defaults \
  --config workspace/config \
  --archive-dir workspace/archive/tech-news-digest \
  --timezone Asia/Shanghai
```
- Runs the collection pipeline for `twitter,github,trending,reddit,web`
- Resolves the report date at runtime from the target timezone
- Writes `daily-YYYY-MM-DD.md` and removes reports older than 90 days

#### `enrich-articles.py` - Article Full-Text Enrichment
```bash
python3 scripts/enrich-articles.py --input merged.json --output enriched.json [--min-score 10] [--max-articles 15] [--verbose]
```
- Fetches full article text for high-scoring articles
- Cloudflare Markdown for Agents (preferred) → HTML extraction (fallback) → Skip (paywalled/social)
- Blog domain whitelist with lower score threshold (≥3)
- Parallel fetching (5 workers, 10s timeout)

#### `merge-sources.py` - Quality Scoring & Deduplication
```bash
python3 scripts/merge-sources.py --rss FILE --twitter FILE --web FILE --github FILE --reddit FILE
```
- Quality scoring, title similarity dedup (85%), previous digest penalty
- Output: topic-grouped articles sorted by score

#### `validate-config.py` - Configuration Validator
```bash
python3 scripts/validate-config.py [--defaults DIR] [--config DIR] [--verbose]
```
- JSON schema validation, topic reference checks, duplicate ID detection

#### `generate-pdf.py` - PDF Report Generator
```bash
python3 scripts/generate-pdf.py --input report.md --output digest.pdf [--verbose]
```
- Converts markdown digest to styled A4 PDF with Chinese typography (Noto Sans CJK SC)
- Emoji icons, page headers/footers, blue accent theme. Requires `weasyprint`.

#### `sanitize-html.py` - Safe HTML Email Converter
```bash
python3 scripts/sanitize-html.py --input report.md --output email.html [--verbose]
```
- Converts markdown to XSS-safe HTML email with inline CSS
- URL whitelist (http/https only), HTML-escaped text content

#### `source-health.py` - Source Health Monitor
```bash
python3 scripts/source-health.py --rss FILE --twitter FILE --github FILE --reddit FILE --web FILE [--verbose]
```
- Tracks per-source success/failure history over 7 days
- Reports unhealthy sources (>50% failure rate)

#### `summarize-merged.py` - Merged Data Summary
```bash
python3 scripts/summarize-merged.py --input merged.json [--top N] [--topic TOPIC]
```
- Human-readable summary of merged data for LLM consumption
- Shows top articles per topic with scores and metrics

## User Customization

### Workspace Configuration Override
Place custom configs in `workspace/config/` to override defaults:

- **Sources**: Append new sources, disable defaults with `"enabled": false`
- **Topics**: Override topic definitions, search queries, display settings
- **Merge Logic**: 
  - Sources with same `id` → user version takes precedence
  - Sources with new `id` → appended to defaults
  - Topics with same `id` → user version completely replaces default

### Example Workspace Override
```json
// workspace/config/tech-news-digest-sources.json
{
  "sources": [
    {
      "id": "simonwillison-rss",
      "enabled": false,
      "note": "Disabled: too noisy for my use case"
    },
    {
      "id": "my-custom-blog", 
      "type": "rss",
      "name": "My Custom Tech Blog",
      "url": "https://myblog.com/rss",
      "enabled": true,
      "priority": true,
      "topics": ["frontier-tech"]
    }
  ]
}
```

## Templates & Output

### Discord Template (`references/templates/discord.md`)
- Bullet list format with link suppression (`<link>`)
- Mobile-optimized, emoji headers
- 2000 character limit awareness

### Email Template (`references/templates/email.md`) 
- Rich metadata, technical stats, archive links
- Executive summary, top articles section
- HTML-compatible formatting

### PDF Template (`references/templates/pdf.md`)
- A4 layout with Noto Sans CJK SC font for Chinese support
- Emoji icons, page headers/footers with page numbers
- Generated via `scripts/generate-pdf.py` (requires `weasyprint`)

## Default Sources (167 total, 165 enabled)

- **RSS Feeds (78)**: AI labs, tech blogs, crypto news, Chinese tech media
- **Twitter/X KOLs (48)**: AI researchers, crypto leaders, tech executives
- **GitHub Repos (28)**: Major open-source projects (LangChain, vLLM, DeepSeek, Llama, etc.)
- **Reddit (13)**: r/MachineLearning, r/LocalLLaMA, r/CryptoCurrency, r/ChatGPT, r/OpenAI, etc.
- **Web Search (4 topics)**: LLM, AI Agent, Crypto, Frontier Tech

All sources pre-configured with appropriate topic tags and priority levels.

## Dependencies

```bash
pip install -r requirements.txt
```

**Optional but Recommended**:
- `feedparser>=6.0.0` - Better RSS parsing (fallback to regex if unavailable)
- `jsonschema>=4.0.0` - Configuration validation

**All scripts work with Python 3.8+ standard library only.**

## Monitoring & Operations

### Health Checks
```bash
# Validate configuration
python3 scripts/validate-config.py --verbose

# Test RSS feeds
python3 scripts/fetch-rss.py --hours 1 --verbose

# Check Twitter API
python3 scripts/fetch-twitter.py --hours 1 --verbose
```

### Archive Management
- The full prompt workflow saves generated digests to `<workspace>/archive/tech-news-digest/`
- Previous digest titles are used for duplicate detection when archive files exist
- Old archive cleanup is handled by the prompt workflow, not by `run-pipeline.py` itself

### Error Handling
- **Network Failures**: Retry with exponential backoff
- **Rate Limits**: Automatic retry with appropriate delays
- **Invalid Content**: Graceful degradation, detailed logging
- **Configuration Errors**: Schema validation with helpful messages

## API Keys & Environment

Set in `~/.zshenv` or similar:
```bash
# Twitter (at least one required for Twitter source)
export GETX_API_KEY="your_key"             # GetXAPI key (preferred auto backend)
export TWITTERAPI_IO_KEY="your_key"        # twitterapi.io key
export X_BEARER_TOKEN="your_bearer_token"  # Official X API v2 fallback
export TWITTER_API_BACKEND="auto"          # auto|getxapi|twitterapiio|official|bird

# Bird (explicit local-session backend, or auto fallback when API credentials are unavailable)
export BIRD_CLI="bird"                     # Or: bunx @steipete/bird
export AUTH_TOKEN=""
export CT0=""

# Web Search (optional, enables web search layer)
export WEB_SEARCH_BACKEND="auto"          # auto|tavily|brave|xcrawl
export TAVILY_API_KEY="tvly-xxx"           # Tavily Search API (free 1000/mo)
export XCRAWL_API_KEY="xcrawl-xxx"         # XCrawl Search API key

# Brave Search (alternative)
export BRAVE_API_KEYS="key1,key2,key3"     # Multiple keys, comma-separated rotation
export BRAVE_API_KEY="key1"                # Single key fallback
export BRAVE_PLAN="free"                   # Override rate limit detection: free|pro

# GitHub (optional, improves rate limits)
export GITHUB_TOKEN="ghp_xxx"              # PAT (simplest)
export GH_APP_ID="12345"                   # Or use GitHub App for auto-token
export GH_APP_INSTALL_ID="67890"
export GH_APP_KEY_FILE="/path/to/key.pem"
```

- **Twitter/X**: `GETX_API_KEY` is the preferred auto backend; `TWITTERAPI_IO_KEY` and `X_BEARER_TOKEN` are API fallbacks; Bird is available for explicit local-session runs and as the final `auto` fallback when available
- **Web Search**: Auto mode tries Tavily, then Brave, then XCrawl, and finally emits interface JSON when no backend is usable
- **GitHub**: Auto-generates token from GitHub App if PAT not set; unauthenticated fallback (60 req/hr)
- **Reddit**: No API key needed (uses public JSON API)

## Cron / Scheduled Task Integration

### OpenClaw Cron (Recommended)

The cron prompt should **NOT** hardcode the pipeline steps. Instead, reference `references/digest-prompt.md` and only pass configuration parameters. This ensures the pipeline logic stays in the skill repo and is consistent across all installations.

#### Daily Digest Cron Prompt
```
Read <SKILL_DIR>/references/digest-prompt.md and follow the complete workflow to generate a daily digest.

Replace placeholders with:
- MODE = daily
- TIME_WINDOW = past 1-2 days
- FRESHNESS = pd
- RSS_HOURS = 48
- ITEMS_PER_SECTION = 3-5
- ENRICH = true
- BLOG_PICKS_COUNT = 3
- EXTRA_SECTIONS = (none)
- SUBJECT = Daily Tech Digest - YYYY-MM-DD
- WORKSPACE = <your workspace path>
- SKILL_DIR = <your skill install path>
- DISCORD_CHANNEL_ID = <your channel id>
- EMAIL = (optional)
- LANGUAGE = English
- TEMPLATE = discord

Follow every step in the prompt template strictly. Do not skip any steps.
```

#### Weekly Digest Cron Prompt
```
Read <SKILL_DIR>/references/digest-prompt.md and follow the complete workflow to generate a weekly digest.

Replace placeholders with:
- MODE = weekly
- TIME_WINDOW = past 7 days
- FRESHNESS = pw
- RSS_HOURS = 168
- ITEMS_PER_SECTION = 10-15
- ENRICH = true
- BLOG_PICKS_COUNT = 3-5
- EXTRA_SECTIONS = 📊 Weekly Trend Summary (2-3 sentences summarizing macro trends)
- SUBJECT = Weekly Tech Digest - YYYY-MM-DD
- WORKSPACE = <your workspace path>
- SKILL_DIR = <your skill install path>
- DISCORD_CHANNEL_ID = <your channel id>
- EMAIL = (optional)
- LANGUAGE = English
- TEMPLATE = discord

Follow every step in the prompt template strictly. Do not skip any steps.
```

#### Why This Pattern?
- **Single source of truth**: Pipeline logic lives in `digest-prompt.md`, not scattered across cron configs
- **Portable**: Same skill on different OpenClaw instances, just change paths and channel IDs
- **Maintainable**: Update the skill → all cron jobs pick up changes automatically
- **Anti-pattern**: Do NOT copy pipeline steps into the cron prompt — it will drift out of sync

#### Multi-Channel Delivery Limitation
OpenClaw enforces **cross-provider isolation**: a single session can only send messages to one provider (e.g., Discord OR Telegram, not both). If you need to deliver digests to multiple platforms, create **separate cron jobs** for each provider:

```
# Job 1: Discord + Email
- DISCORD_CHANNEL_ID = <your-discord-channel-id>
- EMAIL = user@example.com
- TEMPLATE = discord

# Job 2: Telegram DM
- DISCORD_CHANNEL_ID = (none)
- EMAIL = (none)
- TEMPLATE = telegram
```
Replace `DISCORD_CHANNEL_ID` delivery with the target platform's delivery in the second job's prompt.

This is a security feature, not a bug — it prevents accidental cross-context data leakage.

## Security Notes

### Execution Model
This skill uses a **prompt template pattern**: the agent reads `digest-prompt.md` and follows its instructions. This is the standard OpenClaw skill execution model — the agent interprets structured instructions from skill-provided files. All instructions are shipped with the skill bundle and can be audited before installation.

### Network Access
The Python scripts make outbound requests to:
- RSS feed URLs (configured in `tech-news-digest-sources.json`)
- Twitter/X API (`api.x.com`, `api.twitterapi.io`, or `api.getxapi.com`)
- XCrawl Search API (`run.xcrawl.com`)
- Brave Search API (`api.search.brave.com`)
- Tavily Search API (`api.tavily.com`)
- GitHub API (`api.github.com`)
- Reddit JSON API (`reddit.com`)

When Bird is used, the external `bird` CLI may also read local browser cookies or use `AUTH_TOKEN` / `CT0` to access x.com session data. All API keys are read from environment variables declared in the skill metadata.

### Shell Safety
Email delivery uses `send-email.py` which constructs proper MIME multipart messages with HTML body + optional PDF attachment. Subject formats are hardcoded (`Daily Tech Digest - YYYY-MM-DD`). PDF generation uses `generate-pdf.py` via `weasyprint`. The prompt template explicitly prohibits interpolating untrusted content (article titles, tweet text, etc.) into shell arguments. Email addresses and subjects must be static placeholder values only.

### File Access
Scripts read from `config/` and write to `workspace/archive/`. No files outside the workspace are accessed.

## Support & Troubleshooting

### Common Issues
1. **RSS feeds failing**: Check network connectivity, use `--verbose` for details
2. **Twitter rate limits / Bird failures**: Check selected backend, local X session validity, and Bird pacing variables
3. **Configuration errors**: Run `validate-config.py` for specific issues
4. **No articles found**: Check time window (`--hours`) and source enablement

### Debug Mode
All scripts support `--verbose` flag for detailed logging and troubleshooting.

### Performance Tuning
- **Parallel Workers**: Adjust `MAX_WORKERS` in scripts for your system
- **Timeout Settings**: Increase `TIMEOUT` for slow networks
- **Article Limits**: Adjust `MAX_ARTICLES_PER_FEED` based on needs
## Security Considerations

### Shell Execution
The digest prompt instructs agents to run Python scripts via shell commands. All script paths and arguments are skill-defined constants — no user input is interpolated into commands. Two scripts use `subprocess`:
- `run-pipeline.py` orchestrates child fetch scripts (all within `scripts/` directory)
- `fetch-github.py` has two subprocess calls:
  1. `openssl dgst -sha256 -sign` for JWT signing (only if `GH_APP_*` env vars are set — signs a self-constructed JWT payload, no user content involved)
  2. `gh auth token` CLI fallback (only if `gh` is installed — reads from gh's own credential store)

No user-supplied or fetched content is ever interpolated into subprocess arguments. Email delivery uses `send-email.py` which builds MIME messages programmatically — no shell interpolation. PDF generation uses `generate-pdf.py` via `weasyprint`. Email subjects are static format strings only — never constructed from fetched data.

### Credential & File Access
Python scripts do **not** directly read `~/.config/`, `~/.ssh/`, or any credential files. All API tokens are read from environment variables declared in the skill metadata. The exception is explicit Bird usage: the external `bird` CLI may read local browser cookie stores or use `AUTH_TOKEN` / `CT0` if you provide them. The GitHub auth cascade is:
1. `$GITHUB_TOKEN` env var (you control what to provide)
2. GitHub App token generation (only if you set `GH_APP_ID`, `GH_APP_INSTALL_ID`, and `GH_APP_KEY_FILE` — uses inline JWT signing via `openssl` CLI, no external scripts involved)
3. `gh auth token` CLI (delegates to gh's own secure credential store)
4. Unauthenticated (60 req/hr, safe fallback)

If you prefer no automatic credential discovery, simply set `$GITHUB_TOKEN` and the script will use it directly without attempting steps 2-3.

### Dependency Installation
This skill does **not** install any packages. `requirements.txt` lists optional dependencies (`feedparser`, `jsonschema`) for reference only. All scripts work with Python 3.8+ standard library. Users should install optional deps in a virtualenv if desired — the skill never runs `pip install`.

### Input Sanitization
- URL resolution rejects non-HTTP(S) schemes (javascript:, data:, etc.)
- RSS fallback parsing uses simple, non-backtracking regex patterns (no ReDoS risk)
- All fetched content is treated as untrusted data for display only

### Network Access
Scripts make outbound HTTP requests to configured RSS feeds, Twitter API, GetXAPI, GitHub API, Reddit JSON API, Brave Search API, Tavily Search API, and XCrawl Search API. No inbound connections or listeners are created.
