"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  type ExactValueAnswer,
  engine,
  type ReviewResponse,
  type StartSessionResponse,
  type StudyQuestion,
} from "@/lib/engine";

type Picked = string | string[];

type Phase =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "answering" }
  | { kind: "rating"; picked: Picked }
  | { kind: "revealed"; picked: Picked; review: ReviewResponse }
  | { kind: "done" };

const FIRST_MULTI_FLAG = "tradepass.shown_multi_tooltip_v1";

export default function StudyClient({ token }: { token: string }) {
  const [session, setSession] = useState<StartSessionResponse | null>(null);
  const [index, setIndex] = useState(0);
  const [correctCount, setCorrectCount] = useState(0);
  const [phase, setPhase] = useState<Phase>({ kind: "loading" });
  const [showMultiTooltip, setShowMultiTooltip] = useState(false);

  // Per-question working state while answering. Reset on next().
  const [singlePick, setSinglePick] = useState<string | null>(null);
  const [multiPicks, setMultiPicks] = useState<Set<string>>(new Set());
  const [exactInput, setExactInput] = useState<string>("");
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
        setPhase({ kind: "answering" });
      })
      .catch((e) => {
        if (cancelled) return;
        setPhase({ kind: "error", message: String(e) });
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  // First-time multi-select onboarding tooltip.
  const current = session?.questions[index] ?? null;
  useEffect(() => {
    if (!current || current.question_type !== "multiple_select") return;
    if (phase.kind !== "answering") return;
    try {
      const seen = window.localStorage.getItem(FIRST_MULTI_FLAG);
      if (!seen) setShowMultiTooltip(true);
    } catch {
      // localStorage blocked — silently skip
    }
  }, [current, phase.kind]);

  function dismissMultiTooltip() {
    setShowMultiTooltip(false);
    try {
      window.localStorage.setItem(FIRST_MULTI_FLAG, "1");
    } catch {
      // ignore
    }
  }

  function pickSingle(id: string) {
    if (phase.kind !== "answering" || !current) return;
    setSinglePick(id);
    setPhase({ kind: "rating", picked: id });
  }

  function toggleMulti(id: string) {
    if (phase.kind !== "answering") return;
    setMultiPicks((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function submitMulti() {
    if (phase.kind !== "answering" || multiPicks.size === 0) return;
    setPhase({ kind: "rating", picked: Array.from(multiPicks) });
  }

  function submitExact() {
    if (phase.kind !== "answering" || !exactInput.trim()) return;
    setPhase({ kind: "rating", picked: exactInput.trim() });
  }

  async function rate(knewIt: boolean) {
    if (phase.kind !== "rating" || !current || !session) return;
    const elapsed = Math.max(1, Math.round((Date.now() - startedAtRef.current) / 1000));
    const picked = phase.picked;
    setPhase({ kind: "loading" });
    try {
      const review = await engine.postReview(token, {
        question_id: current.id,
        session_id: session.session_id,
        picked_answer: picked,
        rated_knew_it: knewIt,
        time_taken_seconds: elapsed,
      });
      if (review.answered_correct) setCorrectCount((c) => c + 1);
      setPhase({ kind: "revealed", picked, review });
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
    setSinglePick(null);
    setMultiPicks(new Set());
    setExactInput("");
    startedAtRef.current = Date.now();
    setPhase({ kind: "answering" });
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

  return (
    <main className="flex min-h-screen flex-col items-center p-6">
      <div className="flex w-full max-w-2xl flex-col gap-5">
        <header className="flex items-center justify-between text-sm text-muted-foreground">
          <span>
            Question {index + 1} of {session.questions.length}
          </span>
          <Link href="/dashboard" className="underline">
            Exit
          </Link>
        </header>

        <TypeBadge type={current.question_type} />

        <div className="rounded-lg border p-6">
          <p className="text-xs uppercase tracking-wide text-muted-foreground">
            {current.topic_slug}
          </p>
          <p className="mt-3 text-lg leading-snug">{current.body}</p>
        </div>

        {current.question_type === "multiple_select" && (
          <MultiInstructionBanner pulseFor={showMultiTooltip} onDismiss={dismissMultiTooltip} />
        )}

        <QuestionBody
          question={current}
          phase={phase}
          singlePick={singlePick}
          multiPicks={multiPicks}
          exactInput={exactInput}
          onPickSingle={pickSingle}
          onToggleMulti={toggleMulti}
          onChangeExact={setExactInput}
          onSubmitMulti={submitMulti}
          onSubmitExact={submitExact}
        />

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

        {phase.kind === "revealed" && (
          <>
            <RevealPanel question={current} picked={phase.picked} review={phase.review} />
            <Button onClick={next} className="w-full">
              {index + 1 >= session.questions.length ? "Finish" : "Next"}
            </Button>
          </>
        )}
      </div>
    </main>
  );
}

function TypeBadge({ type }: { type: StudyQuestion["question_type"] }) {
  const { label, classes } = (() => {
    if (type === "multiple_select")
      return {
        label: "Select all that apply",
        classes: "bg-amber-100 text-amber-900 border-amber-300",
      };
    if (type === "exact_value")
      return {
        label: "Type the exact value",
        classes: "bg-blue-100 text-blue-900 border-blue-300",
      };
    return {
      label: "Single choice",
      classes: "bg-muted text-muted-foreground border-muted-foreground/20",
    };
  })();
  return (
    <div
      className={`inline-flex w-fit items-center rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wide ${classes}`}
    >
      {label}
    </div>
  );
}

function MultiInstructionBanner({
  pulseFor,
  onDismiss,
}: {
  pulseFor: boolean;
  onDismiss: () => void;
}) {
  return (
    <div className="rounded-lg border-2 border-amber-300 bg-amber-50 p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-amber-900">
            ☑ Select <span className="underline">all</span> correct answers
          </p>
          <p className="mt-1 text-xs text-amber-900/80">
            Usually 2 or 3. Tick each one, then hit Submit.
          </p>
        </div>
        {pulseFor && (
          <Button
            variant="outline"
            size="sm"
            className="shrink-0 border-amber-300 bg-white"
            onClick={onDismiss}
          >
            Got it
          </Button>
        )}
      </div>
    </div>
  );
}

function QuestionBody({
  question,
  phase,
  singlePick,
  multiPicks,
  exactInput,
  onPickSingle,
  onToggleMulti,
  onChangeExact,
  onSubmitMulti,
  onSubmitExact,
}: {
  question: StudyQuestion;
  phase: Phase;
  singlePick: string | null;
  multiPicks: Set<string>;
  exactInput: string;
  onPickSingle: (id: string) => void;
  onToggleMulti: (id: string) => void;
  onChangeExact: (v: string) => void;
  onSubmitMulti: () => void;
  onSubmitExact: () => void;
}) {
  const revealed = phase.kind === "revealed";
  const correctIds = correctIdsFor(question, revealed ? phase.review.correct_answer : null);
  const lockedPicked = phase.kind === "rating" || phase.kind === "revealed" ? phase.picked : null;

  if (question.question_type === "exact_value") {
    return (
      <ExactValueBlock
        question={question}
        value={exactInput}
        onChange={onChangeExact}
        onSubmit={onSubmitExact}
        phase={phase}
        lockedPicked={typeof lockedPicked === "string" ? lockedPicked : null}
      />
    );
  }

  const isMulti = question.question_type === "multiple_select";

  return (
    <>
      <div className="flex flex-col gap-2">
        {(question.options ?? []).map((opt, idx) => {
          const visibleLabel = String.fromCharCode(65 + idx);
          const isPicked = isMulti
            ? multiPicks.has(opt.id) ||
              (Array.isArray(lockedPicked) && lockedPicked.includes(opt.id))
            : singlePick === opt.id || lockedPicked === opt.id;
          const isCorrect = revealed && correctIds.includes(opt.id);
          const showCorrect = revealed && isCorrect;
          const showWrong = revealed && isPicked && !isCorrect;
          const showMissed = revealed && !isPicked && isCorrect;
          const disabled = phase.kind !== "answering";

          return (
            <button
              type="button"
              key={opt.id}
              disabled={disabled}
              onClick={() => (isMulti ? onToggleMulti(opt.id) : onPickSingle(opt.id))}
              className={`flex items-start gap-3 rounded-md border p-4 text-left transition ${
                showCorrect
                  ? "border-green-500 bg-green-50"
                  : showWrong
                    ? "border-red-500 bg-red-50"
                    : showMissed
                      ? "border-green-300 bg-green-50/60"
                      : isPicked
                        ? "border-foreground border-2"
                        : disabled
                          ? ""
                          : "hover:bg-muted"
              }`}
            >
              {isMulti ? (
                <span
                  className={`mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded border-2 text-sm font-bold ${
                    isPicked
                      ? "border-foreground bg-foreground text-background"
                      : "border-muted-foreground/60 bg-background"
                  }`}
                  aria-hidden="true"
                >
                  {isPicked ? "✓" : ""}
                </span>
              ) : (
                <span
                  className={`mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-2 ${
                    isPicked ? "border-foreground" : "border-muted-foreground/40"
                  }`}
                  aria-hidden="true"
                >
                  {isPicked && <span className="h-3 w-3 rounded-full bg-foreground" />}
                </span>
              )}
              <span className="flex-1">
                <span className="font-mono text-xs text-muted-foreground">{visibleLabel}. </span>
                {opt.text}
              </span>
            </button>
          );
        })}
      </div>

      {isMulti && phase.kind === "answering" && (
        <Button className="w-full" disabled={multiPicks.size === 0} onClick={onSubmitMulti}>
          {multiPicks.size === 0
            ? "Tick all correct answers, then Submit"
            : `Submit (${multiPicks.size} selected)`}
        </Button>
      )}
    </>
  );
}

function ExactValueBlock({
  question,
  value,
  onChange,
  onSubmit,
  phase,
  lockedPicked,
}: {
  question: StudyQuestion;
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  phase: Phase;
  lockedPicked: string | null;
}) {
  const revealed = phase.kind === "revealed";
  const correct = revealed && phase.kind === "revealed" ? phase.review.correct_answer : null;
  const exactCorrect = correct && !Array.isArray(correct) ? (correct as ExactValueAnswer) : null;
  const userTyped = lockedPicked ?? value;
  const disabled = phase.kind !== "answering";

  return (
    <>
      <div className="rounded-md border p-4">
        <label className="text-sm font-medium" htmlFor="exact-input">
          Your answer{question.unit ? ` (${question.unit})` : ""}
        </label>
        <input
          id="exact-input"
          type="text"
          inputMode="decimal"
          autoComplete="off"
          disabled={disabled}
          value={disabled ? userTyped : value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && value.trim()) onSubmit();
          }}
          className="mt-2 h-11 w-full rounded-md border border-input bg-background px-3 text-base shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          placeholder={question.unit ? `e.g. 11.5` : "Type the value"}
        />
        {revealed && exactCorrect && (
          <p className="mt-3 text-sm text-muted-foreground">
            Accepted: {exactCorrect.answers.join(" / ")}
            {exactCorrect.unit ? ` ${exactCorrect.unit}` : ""}
            {exactCorrect.tolerance > 0 && ` · ±${Math.round(exactCorrect.tolerance * 100)}%`}
          </p>
        )}
      </div>
      {phase.kind === "answering" && (
        <Button className="w-full" disabled={!value.trim()} onClick={onSubmit}>
          Submit
        </Button>
      )}
    </>
  );
}

function RevealPanel({
  question,
  picked,
  review,
}: {
  question: StudyQuestion;
  picked: Picked;
  review: ReviewResponse;
}) {
  let summary = "";
  if (question.question_type === "exact_value") {
    const c = review.correct_answer as ExactValueAnswer;
    summary = review.answered_correct
      ? "Correct"
      : `Not quite — accepted: ${c.answers.join(", ")}${c.unit ? ` ${c.unit}` : ""}`;
  } else if (question.question_type === "multiple_select") {
    const correctIds = correctIdsFor(question, review.correct_answer);
    const pickedIds = Array.isArray(picked) ? picked : [];
    const missed = correctIds.filter((id) => !pickedIds.includes(id));
    const extra = pickedIds.filter((id) => !correctIds.includes(id));
    if (review.answered_correct) {
      summary = "Correct — all required options selected.";
    } else if (missed.length && extra.length) {
      summary = `Not quite — missed ${missed.length}, extra ${extra.length}.`;
    } else if (missed.length) {
      summary = `Not quite — missed ${missed.length} required.`;
    } else {
      summary = `Not quite — selected ${extra.length} that weren't required.`;
    }
  } else {
    summary = review.answered_correct ? "Correct" : "Not quite";
  }

  return (
    <div className="rounded-lg border bg-muted/40 p-4 text-sm">
      <p className="font-semibold">{summary}</p>
      <p className="mt-1 text-muted-foreground">
        Next review in {review.interval_days} {review.interval_days === 1 ? "day" : "days"}.
      </p>
    </div>
  );
}

function correctIdsFor(
  question: StudyQuestion,
  correct: ReviewResponse["correct_answer"] | null,
): string[] {
  if (!correct) return [];
  if (question.question_type === "exact_value") return [];
  return Array.isArray(correct) ? correct : [];
}

function Center({ children }: { children: React.ReactNode }) {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-6 text-center">
      {children}
    </main>
  );
}
