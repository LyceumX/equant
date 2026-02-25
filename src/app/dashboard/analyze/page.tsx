import { auth } from "@clerk/nextjs/server";
import { redirect } from "next/navigation";
import Link from "next/link";
import { AnalyzeClient } from "./AnalyzeClient";
import { AuthNav } from "@/app/components/AuthNav";

export const metadata = { title: "AI Stock Analysis — eQuant" };

export default async function AnalyzePage() {
  const { userId } = await auth();
  if (!userId) redirect("/");

  const backendConfigured = Boolean(process.env.BACKEND_URL);

  return (
    <div className="min-h-screen bg-zinc-950">
      {/* ── Nav ─────────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-10 border-b border-zinc-800 bg-zinc-950/90 backdrop-blur">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-6 py-3">
          <div className="flex items-center gap-4">
            <Link
              href="/"
              className="text-sm text-zinc-400 hover:text-zinc-100 transition-colors"
            >
              ← Home
            </Link>
            <span className="text-zinc-700">|</span>
            <span className="text-sm font-semibold text-zinc-100">
              AI Stock Analysis
            </span>
          </div>
          <AuthNav />
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-6 py-10">
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight text-zinc-100">
            AI Stock Analysis
          </h1>
          <p className="mt-2 text-zinc-400">
            Enter any ticker to get real-time market data, technical indicators,
            fundamentals, and an AI-generated summary.
          </p>
        </div>

        {/* Backend not configured warning */}
        {!backendConfigured && (
          <div className="mb-6 rounded-xl border border-yellow-500/30 bg-yellow-500/10 px-5 py-4 text-sm text-yellow-400">
            <strong>Backend not connected.</strong> Set{" "}
            <code className="rounded bg-yellow-500/20 px-1 py-0.5 font-mono text-xs">
              BACKEND_URL
            </code>{" "}
            in your environment to a running FastAPI instance (e.g.{" "}
            <code className="rounded bg-yellow-500/20 px-1 py-0.5 font-mono text-xs">
              http://localhost:8000
            </code>
            ) to enable live analysis.
          </div>
        )}

        <AnalyzeClient />
      </main>
    </div>
  );
}
