"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { engine, type ReviewResponse, type StartSessionResponse } from "@/lib/engine";

type Phase =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "answering"; pickedId: string | null }
  | { kind: "rating"; pickedId: string }
  | { kind: "revealed"; pickedId: string; review: ReviewResponse }
  | { kind: "done" };

export default function StudyClient({ token }: { token: string }) {
  const [session, setSession] = useState<StartSessionResponse | null>(null);
  const [index, setIndex] = useState(0);
  const [correctCount, setCorrectCount] = useState(0);
  const [phase, setPhase] = useState<Phase>({ kind: "loading" });
  const startedAtRef = useRef<number>(Date.now());

  useEffect(() => {
    let cancelled = false;
    engine
      .startSession(token, "study", 10)
      .then((s) => {
        if (cancelled) return;
        if (s.questions.length === 0) {
          setPhase({ kind: "error", message: "No questions available." });
          return;
        }
        setSession(s);
        startedAtRef.current = Date.now();
        setPhase({ kind: "answering", pickedId: null });
      })
      .catch((e) => {
        if (cancelled) return;
        setPhase({ kind: "error", message: String(e) });
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  const current = session?.questions[index] ?? null;

  function pickOption(id: string) {
    if (phase.kind !== "answering") return;
    setPhase({ kind: "rating", pickedId: id });
  }

  async function rate(knewIt: boolean) {
    if (phase.kind !== "rating" || !current || !session) return;
    const elapsed = Math.max(1, Math.round((Date.now() - startedAtRef.current) / 1000));
    const pickedId = phase.pickedId;
    setPhase({ kind: "loading" });
    try {
      const review = await engine.postReview(token, {
        question_id: current.id,
        session_id: session.session_id,
        picked_option_id: pickedId,
        rated_knew_it: knewIt,
        time_taken_seconds: elapsed,
      });
      if (review.answered_correct) setCorrectCount((c) => c + 1);
      setPhase({ kind: "revealed", pickedId, review });
    } catch (e) {
      setPhase({ kind: "error", message: String(e) });
    }
  }

  function next() {
    if (!session) return;
    if (index + 1 >= session.questions.length) {
      setPhase({ kind: "done" });
      return;
    }
    setIndex((i) => i + 1);
    startedAtRef.current = Date.now();
    setPhase({ kind: "answering", pickedId: null });
  }

  if (phase.kind === "loading") return <Center>Loading…</Center>;
  if (phase.kind === "error") {
    return (
      <Center>
        <p className="text-red-600">{phase.message}</p>
        <Link href="/dashboard" className="mt-4 underline">
          Back to dashboard
        </Link>
      </Center>
    );
  }
  if (phase.kind === "done" || !current || !session) {
    return (
      <Center>
        <p className="text-2xl font-semibold">Session complete</p>
        <p className="mt-1 text-muted-foreground">
          {correctCount} / {session?.questions.length ?? 0} correct
        </p>
        <Link href="/dashboard" className="mt-6">
          <Button>Back to dashboard</Button>
        </Link>
      </Center>
    );
  }

  const revealed = phase.kind === "revealed";
  const correctId = revealed ? phase.review.correct_answer : null;
  const pickedId = phase.kind === "rating" || phase.kind === "revealed" ? phase.pickedId : null;

  return (
    <main className="flex min-h-screen flex-col items-center p-6">
      <div className="flex w-full max-w-2xl flex-col gap-6">
        <header className="flex items-center justify-between text-sm text-muted-foreground">
          <span>
            Question {index + 1} of {session.questions.length}
          </span>
          <Link href="/dashboard" className="underline">
            Exit
          </Link>
        </header>

        <div className="rounded-lg border p-6">
          <p className="text-xs uppercase tracking-wide text-muted-foreground">
            {current.topic_slug}
          </p>
          <p className="mt-3 text-lg leading-snug">{current.body}</p>
        </div>

        <div className="flex flex-col gap-2">
          {current.options.map((opt, idx) => {
            const isPicked = pickedId === opt.id;
            const isCorrect = correctId === opt.id;
            const showCorrect = revealed && isCorrect;
            const showWrong = revealed && isPicked && !isCorrect;
            // Visible label comes from array position so options A/B/C/D
            // always appear in order on screen, even though the engine
            // shuffled the underlying option ids per session.
            const visibleLabel = String.fromCharCode(65 + idx);
            return (
              <button
                type="button"
                key={opt.id}
                disabled={phase.kind !== "answering"}
                onClick={() => pickOption(opt.id)}
                className={`rounded-md border p-4 text-left transition ${
                  showCorrect
                    ? "border-green-500 bg-green-50"
                    : showWrong
                      ? "border-red-500 bg-red-50"
                      : isPicked
                        ? "border-foreground"
                        : phase.kind === "answering"
                          ? "hover:bg-muted"
                          : ""
                }`}
              >
                <span className="font-mono text-xs text-muted-foreground">{visibleLabel}. </span>
                {opt.text}
              </button>
            );
          })}
        </div>

        {phase.kind === "rating" && (
          <div className="rounded-lg border bg-muted/40 p-4">
            <p className="text-sm font-semibold">Before we reveal — how confident are you?</p>
            <div className="mt-3 flex gap-2">
              <Button variant="outline" className="flex-1" onClick={() => rate(false)}>
                Wasn&apos;t sure
              </Button>
              <Button className="flex-1" onClick={() => rate(true)}>
                Knew it
              </Button>
            </div>
          </div>
        )}

        {revealed && (
          <>
            <div className="rounded-lg border bg-muted/40 p-4 text-sm">
              <p className="font-semibold">
                {phase.review.answered_correct ? "Correct" : "Not quite"}
              </p>
              <p className="mt-1 text-muted-foreground">
                Next review in {phase.review.interval_days}{" "}
                {phase.review.interval_days === 1 ? "day" : "days"}.
              </p>
            </div>
            <Button onClick={next} className="w-full">
              {index + 1 >= session.questions.length ? "Finish" : "Next"}
            </Button>
          </>
        )}
      </div>
    </main>
  );
}

function Center({ children }: { children: React.ReactNode }) {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-6 text-center">
      {children}
    </main>
  );
}
