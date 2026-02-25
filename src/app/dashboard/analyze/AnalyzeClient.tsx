"use client";

import { useState, useRef } from "react";

// ── Types matching the FastAPI AnalyzeResponse schema ──────────────────────
interface TechnicalIndicators {
  rsi: number;
  macd: "bullish" | "bearish" | "neutral" | string;
  ma20: number | null;
  ma60: number | null;
}
interface MarketData {
  latest_price: number;
  price_change_pct: number | null;
  volume: number | null;
  technical_indicators: TechnicalIndicators;
}
interface FundamentalData {
  monthly_revenue_growth_yoy: string | null;
  gross_margin: string | null;
  pe_ratio: number | null;
  eps: number | null;
}
interface AnalyzeResponse {
  symbol: string;
  market_data: MarketData;
  fundamental_data: FundamentalData;
  ai_summary: string;
  is_premium_analysis_available: boolean;
}

// ── Helpers ────────────────────────────────────────────────────────────────
function fmt(n: number | null | undefined, decimals = 2) {
  if (n == null) return "—";
  return n.toLocaleString("en-US", { maximumFractionDigits: decimals });
}
function fmtVol(n: number | null | undefined) {
  if (n == null) return "—";
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(2) + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(1) + "K";
  return String(n);
}

function RsiBadge({ rsi }: { rsi: number }) {
  const label = rsi > 70 ? "Overbought" : rsi < 30 ? "Oversold" : "Neutral";
  const cls =
    rsi > 70
      ? "bg-red-500/15 text-red-400 ring-red-500/20"
      : rsi < 30
        ? "bg-green-500/15 text-green-400 ring-green-500/20"
        : "bg-yellow-500/15 text-yellow-400 ring-yellow-500/20";
  return (
    <span
      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ring-1 ${cls}`}
    >
      {label}
    </span>
  );
}

function MacdBadge({ signal }: { signal: string }) {
  const cls =
    signal === "bullish"
      ? "bg-green-500/15 text-green-400 ring-green-500/20"
      : signal === "bearish"
        ? "bg-red-500/15 text-red-400 ring-red-500/20"
        : "bg-zinc-500/15 text-zinc-400 ring-zinc-500/20";
  return (
    <span
      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ring-1 capitalize ${cls}`}
    >
      {signal}
    </span>
  );
}

function PriceChange({ pct }: { pct: number | null }) {
  if (pct == null) return <span className="text-zinc-400">—</span>;
  const positive = pct >= 0;
  return (
    <span className={positive ? "text-green-400" : "text-red-400"}>
      {positive ? "▲" : "▼"} {Math.abs(pct).toFixed(2)}%
    </span>
  );
}

// ── Main component ─────────────────────────────────────────────────────────
export function AnalyzeClient() {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    const symbol = input.trim().toUpperCase();
    if (!symbol) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch(`/api/analyze/${encodeURIComponent(symbol)}`);
      const data = await res.json();

      if (!res.ok) {
        setError(data?.detail ?? data?.error ?? `Error ${res.status}`);
      } else {
        setResult(data as AnalyzeResponse);
      }
    } catch {
      setError("Could not reach the analysis API. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      {/* ── Search bar ──────────────────────────────────────────────────── */}
      <form onSubmit={handleSearch} className="flex gap-3">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Enter ticker symbol — e.g. AAPL, 2330.TW, TSLA"
          className="flex-1 rounded-xl border border-zinc-700 bg-zinc-900 px-4 py-3 text-sm text-zinc-100 placeholder:text-zinc-500 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/30 transition-colors"
          disabled={loading}
          autoFocus
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="rounded-xl bg-indigo-600 px-6 py-3 text-sm font-semibold text-white hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <svg
                className="h-4 w-4 animate-spin"
                viewBox="0 0 24 24"
                fill="none"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                />
              </svg>
              Analyzing…
            </span>
          ) : (
            "Analyze"
          )}
        </button>
      </form>

      {/* ── Example chips ────────────────────────────────────────────────── */}
      {!result && !loading && (
        <div className="flex flex-wrap gap-2">
          <span className="text-xs text-zinc-500">Try:</span>
          {["AAPL", "TSLA", "NVDA", "2330.TW", "MSFT", "GOOGL"].map((t) => (
            <button
              key={t}
              onClick={() => {
                setInput(t);
                inputRef.current?.focus();
              }}
              className="rounded-lg border border-zinc-800 px-2.5 py-1 text-xs text-zinc-400 hover:border-indigo-500 hover:text-indigo-400 transition-colors"
            >
              {t}
            </button>
          ))}
        </div>
      )}

      {/* ── Error state ──────────────────────────────────────────────────── */}
      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-5 py-4 text-sm text-red-400">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* ── Results ──────────────────────────────────────────────────────── */}
      {result && (
        <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
          {/* Symbol header */}
          <div className="flex items-baseline justify-between">
            <h2 className="text-2xl font-bold tracking-tight text-zinc-100">
              {result.symbol}
            </h2>
            <div className="text-right">
              <span className="text-2xl font-semibold text-zinc-100">
                {fmt(result.market_data.latest_price)}
              </span>
              <span className="ml-3 text-base">
                <PriceChange pct={result.market_data.price_change_pct} />
              </span>
            </div>
          </div>

          {/* Grid: market + technicals */}
          <div className="grid gap-4 sm:grid-cols-2">
            {/* Market Data */}
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5 space-y-3">
              <h3 className="text-xs font-semibold uppercase tracking-widest text-zinc-500">
                Market Data
              </h3>
              <dl className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <dt className="text-zinc-400">Latest Price</dt>
                  <dd className="font-medium text-zinc-100">
                    {fmt(result.market_data.latest_price)}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-zinc-400">Change</dt>
                  <dd>
                    <PriceChange pct={result.market_data.price_change_pct} />
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-zinc-400">Volume</dt>
                  <dd className="font-medium text-zinc-100">
                    {fmtVol(result.market_data.volume)}
                  </dd>
                </div>
              </dl>
            </div>

            {/* Technical Indicators */}
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5 space-y-3">
              <h3 className="text-xs font-semibold uppercase tracking-widest text-zinc-500">
                Technical Indicators
              </h3>
              <dl className="space-y-2 text-sm">
                <div className="flex items-center justify-between">
                  <dt className="text-zinc-400">RSI</dt>
                  <dd className="flex items-center gap-2">
                    <span className="font-medium text-zinc-100">
                      {fmt(result.market_data.technical_indicators.rsi, 1)}
                    </span>
                    <RsiBadge
                      rsi={result.market_data.technical_indicators.rsi}
                    />
                  </dd>
                </div>
                <div className="flex items-center justify-between">
                  <dt className="text-zinc-400">MACD Signal</dt>
                  <dd>
                    <MacdBadge
                      signal={result.market_data.technical_indicators.macd}
                    />
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-zinc-400">MA20</dt>
                  <dd className="font-medium text-zinc-100">
                    {fmt(result.market_data.technical_indicators.ma20)}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-zinc-400">MA60</dt>
                  <dd className="font-medium text-zinc-100">
                    {fmt(result.market_data.technical_indicators.ma60)}
                  </dd>
                </div>
              </dl>
            </div>
          </div>

          {/* Fundamentals */}
          <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5 space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-widest text-zinc-500">
              Fundamentals
            </h3>
            <dl className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm sm:grid-cols-4">
              {[
                {
                  label: "P/E Ratio",
                  value: fmt(result.fundamental_data.pe_ratio, 1),
                },
                { label: "EPS", value: fmt(result.fundamental_data.eps) },
                {
                  label: "Gross Margin",
                  value: result.fundamental_data.gross_margin ?? "—",
                },
                {
                  label: "Rev Growth YoY",
                  value:
                    result.fundamental_data.monthly_revenue_growth_yoy ?? "—",
                },
              ].map(({ label, value }) => (
                <div key={label}>
                  <dt className="text-zinc-500 text-xs">{label}</dt>
                  <dd className="mt-0.5 font-semibold text-zinc-100">
                    {value}
                  </dd>
                </div>
              ))}
            </dl>
          </div>

          {/* AI Summary */}
          <div className="rounded-2xl border border-indigo-500/30 bg-indigo-500/5 p-5 space-y-3">
            <h3 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-indigo-400">
              <svg
                className="h-3.5 w-3.5"
                viewBox="0 0 24 24"
                fill="currentColor"
              >
                <path d="M12 2a10 10 0 100 20A10 10 0 0012 2zm1 17.93V18a1 1 0 00-2 0v1.93A8.001 8.001 0 014.07 13H6a1 1 0 000-2H4.07A8.001 8.001 0 0111 4.07V6a1 1 0 002 0V4.07A8.001 8.001 0 0119.93 11H18a1 1 0 000 2h1.93A8.001 8.001 0 0113 19.93z" />
              </svg>
              AI Analysis
            </h3>
            <p className="text-sm leading-relaxed text-zinc-300">
              {result.ai_summary}
            </p>
          </div>

          {/* New search */}
          <button
            onClick={() => {
              setResult(null);
              setInput("");
              inputRef.current?.focus();
            }}
            className="text-xs text-zinc-500 hover:text-zinc-300 underline transition-colors"
          >
            ← Analyze another symbol
          </button>
        </div>
      )}
    </div>
  );
}
