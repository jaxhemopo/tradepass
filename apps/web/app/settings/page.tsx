import { redirect } from "next/navigation";
import { engine } from "@/lib/engine";
import { createClient } from "@/lib/supabase/server";
import SettingsForm from "./settings-form";

export default async function SettingsPage() {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session) {
    redirect("/login");
  }

  let initialGoal = 20;
  try {
    const profile = await engine.getProfile(session.access_token);
    initialGoal = profile.daily_goal;
  } catch {
    // engine offline — show the form anyway with default
  }

  return (
    <main className="flex min-h-screen flex-col items-center p-8">
      <SettingsForm token={session.access_token} initialGoal={initialGoal} />
    </main>
  );
}
