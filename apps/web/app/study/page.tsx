import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import StudyClient from "./study-client";

export default async function StudyPage() {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session) {
    redirect("/login");
  }

  return <StudyClient token={session.access_token} />;
}
