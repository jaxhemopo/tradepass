import { env } from "@/lib/env";

export type QuestionType = "single_choice" | "multiple_select" | "exact_value";

export type Option = { id: string; text: string };

export type StudyQuestion = {
  id: string;
  topic_slug: string;
  question_type: QuestionType;
  body: string;
  options: Option[] | null;
  difficulty: number | null;
  unit?: string | null;
};

export type StartSessionResponse = {
  session_id: string;
  questions: StudyQuestion[];
};

export type ExactValueAnswer = { answers: string[]; unit?: string; tolerance: number };

export type ReviewResponse = {
  // single_choice / multiple_select: string[]
  // exact_value: ExactValueAnswer
  correct_answer: string[] | ExactValueAnswer;
  answered_correct: boolean;
  quality: number;
  repetitions: number;
  interval_days: number;
  due_date: string;
};

export type TopicReadiness = {
  slug: string;
  name: string;
  weight: number;
  questions_seen: number;
  mastery_percent: number;
};

export type ReadinessResponse = {
  readiness_percent: number;
  questions_due_now: number;
  topics: TopicReadiness[];
};

class EngineError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

async function call<T>(path: string, init: RequestInit & { token: string }): Promise<T> {
  const { token, headers, ...rest } = init;
  const res = await fetch(`${env.API_URL}${path}`, {
    ...rest,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...headers,
    },
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new EngineError(`engine ${res.status}: ${detail}`, res.status);
  }
  return res.json() as Promise<T>;
}

export const engine = {
  startSession: (token: string, mode = "study", limit = 10) =>
    call<StartSessionResponse>("/v1/sessions/start", {
      token,
      method: "POST",
      body: JSON.stringify({ mode, limit }),
    }),
  postReview: (
    token: string,
    body: {
      question_id: string;
      session_id?: string;
      // single_choice: option id ("a")
      // multiple_select: option ids (["a","c"])
      // exact_value: raw typed value ("11.5")
      picked_answer: string | string[];
      rated_knew_it: boolean;
      time_taken_seconds: number;
    },
  ) =>
    call<ReviewResponse>("/v1/reviews", {
      token,
      method: "POST",
      body: JSON.stringify(body),
    }),
  getReadiness: (token: string) =>
    call<ReadinessResponse>("/v1/readiness", {
      token,
      method: "GET",
      cache: "no-store",
    }),
};
