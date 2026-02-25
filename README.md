# eQuant — AI-Assisted Quantitative Stock Analysis Platform

A lightweight, AI-powered stock analysis and quantitative research web platform built with a **Next.js frontend** and a **FastAPI Python backend**, designed to run end-to-end in **GitHub Codespaces**.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│              GitHub Codespaces                  │
│                                                 │
│  ┌─────────────────┐    ┌────────────────────┐  │
│  │  frontend/      │    │  backend/          │  │
│  │  Next.js 14     │───▶│  FastAPI + Uvicorn │  │
│  │  (port 3000)    │    │  (port 8000)       │  │
│  └────────┬────────┘    └────────┬───────────┘  │
│           │                      │              │
│      Clerk Auth            Supabase DB          │
│      (JWT)                 (PostgreSQL)         │
│                            AI APIs              │
│                            (OpenAI/DeepSeek/    │
│                             Google)             │
└─────────────────────────────────────────────────┘
```

**Core strategy:** Heavy data fetching + AI API calls, light local computation. Qlib/FinRL are integrated via Pandas-based mocks in Phase 1 and swapped for real implementations in Phase 2.

---

## Tech Stack

### Frontend

| Layer            | Technology                                      |
| ---------------- | ----------------------------------------------- |
| Framework        | Next.js 14 (App Router, TypeScript strict mode) |
| Styling          | Tailwind CSS + shadcn/ui                        |
| Auth             | Clerk (`@clerk/nextjs`)                         |
| State / Requests | TanStack Query + Axios                          |
| Charts           | TradingView Lightweight Charts / Recharts       |

### Backend

| Layer           | Technology                                            |
| --------------- | ----------------------------------------------------- |
| Framework       | FastAPI + Uvicorn                                     |
| Language        | Python 3.10+                                          |
| Validation      | Pydantic v2                                           |
| Scraping        | httpx (async) + BeautifulSoup4                        |
| Quant (Phase 1) | Pure Pandas/NumPy mocks for RSI, MACD, MA             |
| Quant (Phase 2) | pyqlib (feature engineering) + finrl (backtesting)    |
| AI              | OpenAI SDK — compatible with OpenAI, DeepSeek, Google |

### Infrastructure

| Layer           | Technology                       |
| --------------- | -------------------------------- |
| Database        | Supabase (PostgreSQL)            |
| Dev environment | GitHub Codespaces + devcontainer |
| Auth tokens     | Clerk JWT verified via JWKS      |

---

## Repository Structure

```
/
├── .devcontainer/
│   ├── devcontainer.json       # Ubuntu 24.04, Node 20, Python 3.10
│   └── setup.sh                # Installs system libs + pip + npm deps
│
├── frontend/                   # Next.js app (App Router)
│   └── src/
│       ├── app/                # Pages: (auth), dashboard, etc.
│       ├── components/         # shadcn/ui components
│       ├── lib/                # Supabase client, API helpers
│       └── types/              # TypeScript interfaces
│
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI entry point, middleware, routers
│   │   ├── core/
│   │   │   ├── config.py       # pydantic-settings: all env vars + AI provider routing
│   │   │   └── deps.py         # JWT auth (Clerk JWKS) + Premium guard (Supabase)
│   │   ├── schemas/
│   │   │   ├── analysis.py     # AnalyzeResponse Pydantic models
│   │   │   └── backtest.py     # BacktestRequest / BacktestResponse models
│   │   ├── api/v1/
│   │   │   ├── analyze.py      # GET /api/v1/analyze/{symbol}
│   │   │   └── backtest.py     # POST /api/v1/backtest  (Premium)
│   │   └── services/
│   │       ├── data_fetcher.py # Yahoo Finance async fetch + mock fallback
│   │       ├── scraper.py      # HiStock financial report scraper (defensive)
│   │       ├── qlib_wrapper.py # RSI, MACD, MA — Pandas mock (Phase 1)
│   │       ├── finrl_mock.py   # MA-crossover backtest engine — Pandas mock (Phase 1)
│   │       └── ai_analyzer.py  # Prompt assembly + LLM call + template fallback
│   ├── requirements.txt
│   ├── .env                    # Live credentials (git-ignored)
│   └── .env.example            # Template for all required variables
│
└── README.md
```

---

## API Endpoints

### `GET /api/v1/analyze/{symbol}` — Stock Diagnosis

Requires: Clerk JWT Bearer token.

Parallel-fetches market data + fundamentals → computes technical indicators → calls AI for summary.

```json
{
  "symbol": "2330.TW",
  "market_data": {
    "latest_price": 850.0,
    "price_change_pct": 1.32,
    "volume": 28500000,
    "technical_indicators": {
      "rsi": 65.2,
      "macd": "bullish",
      "ma20": 840.5,
      "ma60": 795.0
    }
  },
  "fundamental_data": {
    "monthly_revenue_growth_yoy": "28.5%",
    "gross_margin": "53%",
    "pe_ratio": 22.5,
    "eps": 37.8
  },
  "ai_summary": "该股基本面强劲，营收大幅增长，技术面呈多头排列，短期看涨。",
  "is_premium_analysis_available": true
}
```

### `POST /api/v1/backtest` — Strategy Simulation _(Premium)_

Requires: Clerk JWT + Premium role in Supabase `profiles` table.

Returns HTTP 403 `"Upgrade to Premium to unlock."` for free-tier users.

```json
// Request
{ "symbol": "2330.TW", "ma_short": 20, "ma_long": 60, "take_profit_pct": 0.15, "stop_loss_pct": 0.08, "lookback_days": 365 }

// Response
{
  "strategy": "MA-Crossover (20/60)",
  "metrics": { "total_return_pct": 8.32, "max_drawdown_pct": -12.5, "sharpe_ratio": 1.12, "num_trades": 14, "win_rate_pct": 57.14 },
  "equity_curve": [{ "date": "2024-01-15", "equity": 108320.5 }, "..."]
}
```

### `GET /health` — Health Check

No auth required. Returns `{ "status": "ok", "version": "1.0.0" }`.

---

## Local Development

### Prerequisites

- GitHub Codespaces **or** Docker (devcontainer) — all deps auto-installed via `setup.sh`
- Alternatively: Node 20 + Python 3.10 + `build-essential cmake libopenblas-dev`

### 1. Start the Codespace

The `.devcontainer/setup.sh` automatically runs on container creation:

- Installs system libs: `build-essential`, `cmake`, `libopenblas-dev`, `liblapack-dev`
- Runs `pip install -r backend/requirements.txt`
- Runs `npm install` in `frontend/`

### 2. Configure environment variables

**Frontend** (already populated in `.env.local`):

```bash
# Keys already set — see .env.local
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_...
NEXT_PUBLIC_SUPABASE_URL=https://dmeflcgyozehczbnvrck.supabase.co
# ...
```

**Backend** — copy and edit:

```bash
cp backend/.env.example backend/.env
```

Key variables in `backend/.env`:

```bash
SUPABASE_URL="https://dmeflcgyozehczbnvrck.supabase.co"
SUPABASE_SERVICE_ROLE_KEY="eyJ..."
CLERK_ISSUER="https://clerk.equant.us.ci"
CLERK_SECRET_KEY="sk_live_..."

# Choose AI provider: "openai" | "deepseek" | "google"
AI_PROVIDER="openai"
OPENAI_API_KEY="sk-proj-..."
DEEPSEEK_API_KEY="sk-..."
GOOGLE_GENERATIVE_AI_API_KEY="AIza..."
```

### 3. Run the backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

Swagger UI: http://localhost:8000/docs

### 4. Run the frontend

```bash
cd frontend   # or root if not yet restructured to monorepo
npm run dev
```

App: http://localhost:3000

---

## Supabase Schema

Run in Supabase SQL Editor:

```sql
-- User accounts (synced from Clerk on first login)
create table if not exists public.users (
  id          bigint generated always as identity primary key,
  clerk_id    text unique not null,
  email       text not null,
  full_name   text,
  created_at  timestamptz default now() not null,
  updated_at  timestamptz default now() not null
);
create index if not exists users_clerk_id_idx on public.users (clerk_id);

-- Subscription tiers (used by Premium guard in deps.py)
create table if not exists public.profiles (
  user_id     text primary key,   -- Clerk sub (JWT "sub" claim)
  role        text not null default 'free'  -- 'free' | 'premium'
);
```

---

## AI Provider Switching

Switch between providers by changing a single line in `backend/.env` — no code changes required:

| `AI_PROVIDER` | Endpoint used                                             | Model env var    |
| ------------- | --------------------------------------------------------- | ---------------- |
| `"openai"`    | `https://api.openai.com/v1`                               | `OPENAI_MODEL`   |
| `"deepseek"`  | `https://api.deepseek.com/v1`                             | `DEEPSEEK_MODEL` |
| `"google"`    | `https://generativelanguage.googleapis.com/v1beta/openai` | `GOOGLE_MODEL`   |

The `config.py` `ai_api_key`, `ai_api_base_url`, and `ai_model` properties resolve automatically.

---

## Defensive Programming Notes

- **Scraper** (`scraper.py`): every parse step is wrapped in `try-except`. On any failure it returns a graceful fallback dict with `_scrape_failed: true` — never crashes the API process.
- **Data fetcher** (`data_fetcher.py`): falls back to deterministic seeded mock OHLCV data if Yahoo Finance is unreachable.
- **AI analyzer** (`ai_analyzer.py`): falls back to a template-generated summary if the LLM API call fails or no key is configured.
- **qlib_wrapper / finrl_mock**: pure Pandas Phase 1 implementations — swap to real Qlib/FinRL in Phase 2 without touching routes or schemas.

---

## Roadmap

| Phase   | Status      | Scope                                                                                                                                 |
| ------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 1 | ✅ Complete | Devcontainer, FastAPI skeleton, Pydantic schemas, Pandas-based quant mocks, multi-provider AI, Clerk JWT auth, Supabase Premium guard |
| Phase 2 | 🔜 Planned  | Replace Pandas mocks with real Qlib feature expressions + FinRL `StockTradingEnv`; add Redis JWKS cache; build Next.js dashboard UI   |
| Phase 3 | 🔜 Planned  | Premium deep-AI stock screener; portfolio optimizer; alert system                                                                     |
