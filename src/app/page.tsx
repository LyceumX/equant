import { auth, currentUser } from "@clerk/nextjs/server";
import { syncUserToSupabase } from "@/lib/syncUserToSupabase";
import { AuthNav } from "@/app/components/AuthNav";

const clerkEnabled = Boolean(
  process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY && process.env.CLERK_SECRET_KEY,
);

export default async function Home() {
  // Silently sync authenticated users to Supabase — no auth gate.
  const { userId } = clerkEnabled ? await auth() : { userId: null };
  if (userId) {
    const user = await currentUser();
    await syncUserToSupabase({
      clerkId: userId,
      email: user?.emailAddresses?.[0]?.emailAddress ?? "",
      fullName:
        [user?.firstName, user?.lastName].filter(Boolean).join(" ") || null,
    });
  }

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950">
      {/* ── Nav bar ─────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-10 border-b border-zinc-200 bg-white/80 backdrop-blur dark:border-zinc-800 dark:bg-zinc-950/80">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-3">
          <span className="text-lg font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
            eQuant
          </span>
          {clerkEnabled && <AuthNav />}
        </div>
      </header>

      {/* ── Hero ────────────────────────────────────────────────────── */}
      <main className="mx-auto max-w-5xl px-6 py-20">
        <h1 className="text-5xl font-bold tracking-tight text-zinc-900 dark:text-zinc-100">
          Quantitative investing,{" "}
          <span className="text-indigo-600 dark:text-indigo-400">
            simplified.
          </span>
        </h1>
        <p className="mt-6 max-w-2xl text-lg text-zinc-600 dark:text-zinc-400">
          eQuant gives you AI-powered stock analysis and backtesting tools
          previously only available to institutional desks — right in your
          browser, no quant PhD required.
        </p>
        <div className="mt-10 flex flex-wrap gap-4">
          <a
            href="#features"
            className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-indigo-500 transition-colors"
          >
            Explore features
          </a>
          <a
            href="#how-it-works"
            className="rounded-lg border border-zinc-300 px-5 py-2.5 text-sm font-medium text-zinc-900 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-100 dark:hover:bg-zinc-800 transition-colors"
          >
            How it works
          </a>
        </div>

        {/* ── Feature cards ───────────────────────────────────────────── */}
        <section id="features" className="mt-24">
          <h2 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-100">
            Features
          </h2>
          <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {[
              {
                icon: "📈",
                title: "AI Stock Analysis",
                body: "Get instant fundamental and sentiment analysis on any ticker powered by DeepSeek / GPT-4o.",
              },
              {
                icon: "🔁",
                title: "Strategy Backtesting",
                body: "Run historical simulations on custom strategies with realistic slippage and commission models.",
              },
              {
                icon: "🗞️",
                title: "News Scraper",
                body: "Real-time market news aggregation with relevance scoring so you never miss a catalyst.",
              },
              {
                icon: "📊",
                title: "Portfolio Tracker",
                body: "Monitor holdings, P&L, and risk metrics in one unified dashboard.",
              },
              {
                icon: "🤖",
                title: "RL-Powered Signals",
                body: "Reinforcement-learning agents trained offline deliver daily signal suggestions.",
              },
              {
                icon: "🔒",
                title: "Secure & Private",
                body: "Your data lives in your own Supabase project. We never sell or share anything.",
              },
            ].map(({ icon, title, body }) => (
              <div
                key={title}
                className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm dark:border-zinc-800 dark:bg-zinc-900"
              >
                <span className="text-3xl">{icon}</span>
                <h3 className="mt-4 font-semibold text-zinc-900 dark:text-zinc-100">
                  {title}
                </h3>
                <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
                  {body}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* ── How it works ────────────────────────────────────────────── */}
        <section id="how-it-works" className="mt-24">
          <h2 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-100">
            How it works
          </h2>
          <ol className="mt-8 space-y-6">
            {[
              { step: "01", text: "Create a free account in seconds." },
              {
                step: "02",
                text: "Search for any stock ticker or paste a watchlist.",
              },
              {
                step: "03",
                text: "Run an AI analysis or backtest a strategy.",
              },
              {
                step: "04",
                text: "Save results and track your portfolio over time.",
              },
            ].map(({ step, text }) => (
              <li key={step} className="flex items-start gap-5">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-indigo-100 text-sm font-bold text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300">
                  {step}
                </span>
                <p className="pt-2 text-zinc-700 dark:text-zinc-300">{text}</p>
              </li>
            ))}
          </ol>
        </section>

        {/* ── CTA ─────────────────────────────────────────────────────── */}
        <section className="mt-24 rounded-2xl bg-indigo-600 px-8 py-12 text-center dark:bg-indigo-700">
          <h2 className="text-3xl font-bold text-white">
            Ready to start trading smarter?
          </h2>
          <p className="mt-3 text-indigo-100">
            Sign up for free — no credit card required.
          </p>
          {clerkEnabled && (
            <div className="mt-8 inline-flex justify-center">
              <AuthNav />
            </div>
          )}
        </section>
      </main>

      {/* ── Footer ──────────────────────────────────────────────────── */}
      <footer className="mt-24 border-t border-zinc-200 py-8 text-center text-sm text-zinc-500 dark:border-zinc-800 dark:text-zinc-600">
        © {new Date().getFullYear()} eQuant. All rights reserved.
      </footer>
    </div>
  );
}
