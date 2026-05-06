import { redirect } from "next/navigation";
import { brand } from "@/brand.config";
import { Button } from "@/components/ui/button";
import { createClient } from "@/lib/supabase/server";
import { signOut } from "./actions";

export default async function DashboardPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  return (
    <main className="flex min-h-screen flex-col items-center p-8">
      <div className="flex w-full max-w-2xl flex-col gap-8">
        <header className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-semibold">{brand.name}</h1>
            <p className="text-sm text-muted-foreground">Signed in as {user.email}</p>
          </div>
          <form action={signOut}>
            <Button type="submit" variant="outline" size="sm">
              Sign out
            </Button>
          </form>
        </header>

        <section className="rounded-lg border p-6">
          <p className="text-sm text-muted-foreground">Exam Readiness</p>
          <p className="mt-2 text-5xl font-semibold tabular-nums">—</p>
          <p className="mt-3 text-sm text-muted-foreground">
            Take the diagnostic to see your readiness score.
          </p>
        </section>
      </div>
    </main>
  );
}
