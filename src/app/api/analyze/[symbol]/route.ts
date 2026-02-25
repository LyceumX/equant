import { auth } from "@clerk/nextjs/server";
import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL ?? "";

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ symbol: string }> },
) {
  const { symbol } = await params;

  if (!BACKEND_URL) {
    return NextResponse.json(
      {
        error:
          "Backend not configured. Set BACKEND_URL in environment variables.",
      },
      { status: 503 },
    );
  }

  // Forward the Clerk JWT so the FastAPI backend can verify the user.
  const { getToken } = await auth();
  const token = await getToken();

  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const upstream = await fetch(
      `${BACKEND_URL}/api/v1/analyze/${encodeURIComponent(symbol)}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        // Don't cache — market data should always be fresh
        cache: "no-store",
      },
    );

    const body = await upstream.json();

    if (!upstream.ok) {
      return NextResponse.json(body, { status: upstream.status });
    }

    return NextResponse.json(body);
  } catch (err) {
    console.error("analyze proxy error:", err);
    return NextResponse.json(
      { error: "Failed to reach backend API." },
      { status: 502 },
    );
  }
}
