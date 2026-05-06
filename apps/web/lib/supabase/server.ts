import { createServerClient } from "@supabase/ssr";
import type { Database } from "@tradepass/shared-types";
import { cookies } from "next/headers";
import { env } from "@/lib/env";

export async function createClient() {
  const cookieStore = await cookies();

  return createServerClient<Database>(env.SUPABASE_URL, env.SUPABASE_ANON_KEY, {
    cookies: {
      getAll() {
        return cookieStore.getAll();
      },
      setAll(cookiesToSet) {
        try {
          for (const { name, value, options } of cookiesToSet) {
            cookieStore.set(name, value, options);
          }
        } catch {
          // setAll called from a Server Component — middleware refreshes the
          // session, so this is safe to ignore.
        }
      },
    },
  });
}
