import { createServerClient } from "@supabase/ssr";
import type { Database } from "@tradepass/shared-types";
import { type NextRequest, NextResponse } from "next/server";
import { env } from "@/lib/env";

export async function updateSession(request: NextRequest) {
  let supabaseResponse = NextResponse.next({ request });

  const supabase = createServerClient<Database>(env.SUPABASE_URL, env.SUPABASE_ANON_KEY, {
    cookies: {
      getAll() {
        return request.cookies.getAll();
      },
      setAll(cookiesToSet) {
        for (const { name, value } of cookiesToSet) {
          request.cookies.set(name, value);
        }
        supabaseResponse = NextResponse.next({ request });
        for (const { name, value, options } of cookiesToSet) {
          supabaseResponse.cookies.set(name, value, options);
        }
      },
    },
  });

  // Touch the session so cookie refresh happens before any server component
  // renders. Required for SSR auth to work correctly.
  await supabase.auth.getUser();

  return supabaseResponse;
}
