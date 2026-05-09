import Link from "next/link";
import { redirect } from "next/navigation";
import { brand } from "@/brand.config";
import { Button } from "@/components/ui/button";
import { engine, type ReadinessResponse } from "@/lib/engine";
import { createClient } from "@/lib/supabase/server";
import { signOut } from "./actions";

async function loadReadiness(token: string): Promise<ReadinessResponse | null> {
  try {
    return await engine.getReadiness(token);
  } catch {
    return null;
  }
}

export default async function DashboardPage() {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session) {
    redirect("/login");
  }

  const readiness = await loadReadiness(session.access_token);
  const headlinePct = readiness ? readiness.readiness_percent : null;

  return (
    <main className="flex min-h-screen flex-col items-center p-8">
      <div className="flex w-full max-w-2xl flex-col gap-8">
        <header className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-semibold">{brand.name}</h1>
            <p className="text-sm text-muted-foreground">Signed in as {session.user.email}</p>
          </div>
          <form action={signOut}>
            <Button type="submit" variant="outline" size="sm">
              Sign out
            </Button>
          </form>
        </header>

        <section className="rounded-lg border p-6">
          <p className="text-sm text-muted-foreground">Exam Readiness</p>
          <p className="mt-2 text-5xl font-semibold tabular-nums">
            {headlinePct === null ? "—" : `${headlinePct}%`}
          </p>
          {readiness && readiness.questions_due_now > 0 && (
            <p className="mt-3 text-sm text-muted-foreground">
              {readiness.questions_due_now}{" "}
              {readiness.questions_due_now === 1 ? "question" : "questions"} due for review.
            </p>
          )}
          {readiness && readiness.questions_due_now === 0 && (
            <p className="mt-3 text-sm text-muted-foreground">
              All caught up. Ready for a fresh batch?
            </p>
          )}
          {readiness === null && (
            <p className="mt-3 text-sm text-red-600">
              Engine offline — start the API to see your score.
            </p>
          )}
          <Link href="/study" className="mt-6 block">
            <Button className="w-full">Start studying</Button>
          </Link>
        </section>

        {readiness && readiness.topics.length > 0 && (
          <section className="rounded-lg border">
            <h2 className="border-b p-4 text-sm font-semibold">By topic</h2>
            <ul>
              {readiness.topics.map((t) => (
                <li
                  key={t.slug}
                  className="flex items-center justify-between border-b p-4 last:border-b-0"
                >
                  <div>
                    <p className="text-sm font-medium">{t.name}</p>
                    <p className="text-xs text-muted-foreground">
                      Weight {t.weight} · {t.questions_seen} seen
                    </p>
                  </div>
                  <p className="text-sm tabular-nums">{t.mastery_percent}%</p>
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </main>
  );
}
