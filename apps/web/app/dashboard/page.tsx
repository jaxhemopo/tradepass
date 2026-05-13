import Link from "next/link";
import { redirect } from "next/navigation";
import { brand } from "@/brand.config";
import { HelpPopover } from "@/components/help-popover";
import { ProgressMetric } from "@/components/progress-metric";
import { Sparkline } from "@/components/sparkline";
import { Button } from "@/components/ui/button";
import { engine, type Profile, type ReadinessResponse } from "@/lib/engine";
import { createClient } from "@/lib/supabase/server";
import { signOut } from "./actions";

async function loadReadiness(token: string): Promise<ReadinessResponse | null> {
  try {
    return await engine.getReadiness(token);
  } catch {
    return null;
  }
}

async function loadProfile(token: string): Promise<Profile | null> {
  try {
    return await engine.getProfile(token);
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

  const [readiness, profile] = await Promise.all([
    loadReadiness(session.access_token),
    loadProfile(session.access_token),
  ]);
  const headlinePct = readiness ? readiness.readiness_percent : null;
  const dailyGoal = profile?.daily_goal ?? readiness?.daily_goal ?? 20;
  const reviewedToday = readiness?.reviewed_today ?? 0;
  const goalReached = reviewedToday >= dailyGoal;

  return (
    <main className="flex min-h-screen flex-col items-center p-8">
      <div className="flex w-full max-w-2xl flex-col gap-8">
        <header className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-semibold">{brand.name}</h1>
            <p className="text-sm text-muted-foreground">Signed in as {session.user.email}</p>
          </div>
          <div className="flex items-center gap-2">
            <Link href="/settings">
              <Button variant="outline" size="sm">
                Settings
              </Button>
            </Link>
            <form action={signOut}>
              <Button type="submit" variant="outline" size="sm">
                Sign out
              </Button>
            </form>
          </div>
        </header>

        <section className="rounded-lg border p-6">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">Exam Readiness</p>
            <HelpPopover label="How readiness works">
              <p className="font-semibold">How readiness works</p>
              <p className="mt-2 text-muted-foreground">
                Each question has its own review timer. Nail it and the next review pushes further
                out; struggle and it comes back tomorrow. Your readiness % is the weighted average
                across topics — high-weight topics like AS/NZS 3000 count more.
              </p>
              <p className="mt-2 text-muted-foreground">
                Aim for <span className="font-semibold text-foreground">80%+</span> before booking
                the exam.
              </p>
            </HelpPopover>
          </div>

          <p className="mt-2 text-5xl font-semibold tabular-nums">
            {headlinePct === null ? "—" : `${headlinePct}%`}
          </p>

          {readiness && readiness.change_7d !== null && (
            <p className="mt-1 text-sm tabular-nums text-muted-foreground">
              <span
                className={
                  readiness.change_7d > 0
                    ? "text-green-600"
                    : readiness.change_7d < 0
                      ? "text-red-600"
                      : ""
                }
              >
                {readiness.change_7d > 0 ? "↑" : readiness.change_7d < 0 ? "↓" : "→"}{" "}
                {readiness.change_7d > 0 ? "+" : ""}
                {readiness.change_7d}
              </span>{" "}
              this week
            </p>
          )}

          {readiness && readiness.history.length >= 2 && (
            <div className="mt-3">
              <Sparkline data={readiness.history.map((p) => p.readiness_percent)} />
            </div>
          )}

          {readiness && (
            <div className="mt-5 space-y-4">
              <ProgressMetric
                label="Today"
                value={reviewedToday}
                target={dailyGoal}
                accent={goalReached ? "success" : "default"}
                trailing={
                  goalReached ? (
                    <span className="rounded-full bg-green-100 px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wide text-green-700">
                      ✓ Daily Goal Hit
                    </span>
                  ) : null
                }
              />
              <ProgressMetric
                label="Mastered"
                value={readiness.mastered_count}
                target={readiness.total_questions}
                accent="default"
                unit="cards"
              />
            </div>
          )}

          {readiness === null && (
            <p className="mt-3 text-sm text-red-600">
              Engine offline — start the API to see your score.
            </p>
          )}
          <Link href="/study" className="mt-6 block">
            <Button className="w-full">{goalReached ? "Keep going" : "Start studying"}</Button>
          </Link>
        </section>

        {readiness && readiness.topics.length > 0 && (
          <section className="rounded-lg border" id="topics">
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
