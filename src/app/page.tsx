import {
  SignedIn,
  SignedOut,
  SignInButton,
  SignUpButton,
  UserButton,
} from "@clerk/nextjs";
import { auth, currentUser } from "@clerk/nextjs/server";
import { syncUserToSupabase } from "@/lib/syncUserToSupabase";

export default async function Home() {
  const clerkConfigured = Boolean(
    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY && process.env.CLERK_SECRET_KEY,
  );

  if (!clerkConfigured) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-zinc-50 p-6 dark:bg-zinc-950">
        <section className="w-full max-w-xl rounded-2xl border border-zinc-200 bg-white p-8 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
          <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
            Welcome to eQuant
          </h1>
          <p className="mt-3 text-zinc-600 dark:text-zinc-300">
            Add Clerk keys in your environment to enable Register and Log in.
          </p>
        </section>
      </main>
    );
  }

  const { userId } = await auth();

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
    <main className="flex min-h-screen items-center justify-center bg-zinc-50 p-6 dark:bg-zinc-950">
      <section className="w-full max-w-xl rounded-2xl border border-zinc-200 bg-white p-8 shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
          Welcome to eQuant
        </h1>
        <p className="mt-3 text-zinc-600 dark:text-zinc-300">
          Register or log in to continue. Your account is managed with Clerk and
          synced to Supabase.
        </p>

        <SignedOut>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <SignUpButton mode="modal">
              <button className="rounded-lg bg-zinc-900 px-4 py-2.5 text-sm font-medium text-white hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300">
                Register
              </button>
            </SignUpButton>
            <SignInButton mode="modal">
              <button className="rounded-lg border border-zinc-300 px-4 py-2.5 text-sm font-medium text-zinc-900 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-100 dark:hover:bg-zinc-800">
                Log in
              </button>
            </SignInButton>
          </div>
        </SignedOut>

        <SignedIn>
          <div className="mt-8 flex items-center justify-between rounded-lg border border-zinc-200 p-4 dark:border-zinc-800">
            <p className="text-sm text-zinc-700 dark:text-zinc-200">
              You are logged in.
            </p>
            <UserButton />
          </div>
        </SignedIn>
      </section>
    </main>
  );
}
