import { getSupabaseAdminClient } from "@/lib/supabaseAdmin";

type SyncUserInput = {
  clerkId: string;
  email: string;
  fullName: string | null;
};

export async function syncUserToSupabase(input: SyncUserInput) {
  const supabase = getSupabaseAdminClient();

  if (!supabase || !input.email) {
    return;
  }

  const { error } = await supabase.from("users").upsert(
    {
      clerk_id: input.clerkId,
      email: input.email,
      full_name: input.fullName,
    },
    { onConflict: "clerk_id" },
  );

  if (error) {
    console.error("Failed to sync user to Supabase", error.message);
  }
}
