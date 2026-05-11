// NEXT_PUBLIC_* env vars must be referenced via literal property access
// (process.env.NEXT_PUBLIC_FOO) for Next.js webpack to inline them into the
// client bundle. Dynamic lookups like process.env[name] are NOT inlined and
// resolve to undefined in the browser.

function required(name: string, value: string | undefined): string {
  if (!value) {
    throw new Error(`Missing required env var: ${name}`);
  }
  return value;
}

export const env = {
  SUPABASE_URL: required("NEXT_PUBLIC_SUPABASE_URL", process.env.NEXT_PUBLIC_SUPABASE_URL),
  SUPABASE_ANON_KEY: required("NEXT_PUBLIC_SUPABASE_ANON_KEY", process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY),
  API_URL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001",
};
