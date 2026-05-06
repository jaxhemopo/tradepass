"use server";

import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";

function originFrom(headersList: Headers): string {
  const host = headersList.get("host");
  const protocol = headersList.get("x-forwarded-proto") ?? "http";
  return `${protocol}://${host}`;
}

export async function sendMagicLink(
  formData: FormData,
): Promise<{ error?: string; sent?: boolean }> {
  const email = formData.get("email");
  if (typeof email !== "string" || !email.includes("@")) {
    return { error: "Please enter a valid email." };
  }

  const supabase = await createClient();
  const headersList = await headers();
  const origin = originFrom(headersList);

  const { error } = await supabase.auth.signInWithOtp({
    email,
    options: {
      emailRedirectTo: `${origin}/auth/callback?next=/dashboard`,
    },
  });

  if (error) {
    return { error: error.message };
  }
  return { sent: true };
}

export async function signInWithGoogle(): Promise<void> {
  const supabase = await createClient();
  const headersList = await headers();
  const origin = originFrom(headersList);

  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: "google",
    options: {
      redirectTo: `${origin}/auth/callback?next=/dashboard`,
    },
  });

  if (error || !data.url) {
    redirect(`/login?error=${encodeURIComponent(error?.message ?? "OAuth failed")}`);
  }
  redirect(data.url);
}
