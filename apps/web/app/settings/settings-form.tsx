"use client";

import Link from "next/link";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { engine } from "@/lib/engine";

const MIN_GOAL = 5;
const MAX_GOAL = 50;
const SWEET_SPOT_MIN = 15;
const SWEET_SPOT_MAX = 25;
const WARNING_THRESHOLD = 35;

export default function SettingsForm({
  token,
  initialGoal,
}: {
  token: string;
  initialGoal: number;
}) {
  const [goal, setGoal] = useState<number>(initialGoal);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<{ kind: "ok" | "err"; text: string } | null>(null);

  async function save() {
    setSaving(true);
    setStatus(null);
    try {
      const updated = await engine.patchProfile(token, { daily_goal: goal });
      setGoal(updated.daily_goal);
      setStatus({ kind: "ok", text: "Saved." });
    } catch (e) {
      setStatus({ kind: "err", text: String(e) });
    } finally {
      setSaving(false);
    }
  }

  const inSweetSpot = goal >= SWEET_SPOT_MIN && goal <= SWEET_SPOT_MAX;
  const aboveRecommended = goal > WARNING_THRESHOLD;

  return (
    <div className="flex w-full max-w-2xl flex-col gap-8">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Settings</h1>
          <p className="text-sm text-muted-foreground">Pace your practice.</p>
        </div>
        <Link href="/dashboard">
          <Button variant="outline" size="sm">
            Back
          </Button>
        </Link>
      </header>

      <section className="rounded-lg border p-6">
        <div className="flex items-baseline justify-between">
          <label htmlFor="daily-goal" className="text-sm font-semibold">
            Daily review goal
          </label>
          <span className="text-3xl font-semibold tabular-nums">{goal}</span>
        </div>

        <input
          id="daily-goal"
          type="range"
          min={MIN_GOAL}
          max={MAX_GOAL}
          value={goal}
          onChange={(e) => setGoal(Number(e.target.value))}
          className="mt-4 w-full accent-foreground"
        />
        <div className="mt-1 flex justify-between text-xs text-muted-foreground">
          <span>{MIN_GOAL}</span>
          <span>
            recommended {SWEET_SPOT_MIN}–{SWEET_SPOT_MAX}
          </span>
          <span>{MAX_GOAL}</span>
        </div>

        {inSweetSpot && (
          <p className="mt-3 inline-block rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-700">
            ✓ In the sweet spot
          </p>
        )}
        {aboveRecommended && (
          <p className="mt-3 inline-block rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-800">
            ⚠ Above the recommended range — short-term gains, long-term fade
          </p>
        )}

        <div className="mt-5 rounded-md bg-muted/40 p-4 text-sm leading-relaxed">
          <p className="font-semibold">Why the {MAX_GOAL} cap?</p>
          <p className="mt-2 text-muted-foreground">
            Spaced repetition works because your brain needs gaps between reviews to consolidate
            memory. Doing more than ~{SWEET_SPOT_MAX} cards/day means you&apos;ll <em>feel</em>{" "}
            ready faster, but the knowledge won&apos;t stick — and you&apos;ll hit a false 100%
            before the exam.
          </p>
          <p className="mt-2 text-muted-foreground">
            <span className="font-medium text-foreground">
              {SWEET_SPOT_MIN}–{SWEET_SPOT_MAX}/day
            </span>{" "}
            is the proven sweet spot for long-term retention. You can always come back and study
            more later — the engine will queue extra cards in the right order.
          </p>
        </div>

        <div className="mt-6 flex items-center gap-3">
          <Button onClick={save} disabled={saving || goal === initialGoal}>
            {saving ? "Saving…" : "Save"}
          </Button>
          {status && (
            <span className={`text-sm ${status.kind === "ok" ? "text-green-600" : "text-red-600"}`}>
              {status.text}
            </span>
          )}
        </div>
      </section>
    </div>
  );
}
