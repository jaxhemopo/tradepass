"use client";

import { useState, useTransition } from "react";
import { Button } from "@/components/ui/button";
import { sendMagicLink, signInWithGoogle } from "./actions";

export function LoginForm() {
  const [pending, startTransition] = useTransition();
  const [message, setMessage] = useState<{ kind: "ok" | "err"; text: string } | null>(null);

  function onMagicLinkSubmit(formData: FormData) {
    setMessage(null);
    startTransition(async () => {
      const result = await sendMagicLink(formData);
      if (result.error) {
        setMessage({ kind: "err", text: result.error });
      } else if (result.sent) {
        setMessage({ kind: "ok", text: "Check your email for the login link." });
      }
    });
  }

  return (
    <div className="flex flex-col gap-6 w-full max-w-sm">
      <form action={onMagicLinkSubmit} className="flex flex-col gap-3">
        <label htmlFor="email" className="text-sm font-medium">
          Email
        </label>
        <input
          id="email"
          name="email"
          type="email"
          required
          autoComplete="email"
          placeholder="you@example.com"
          className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
        />
        <Button type="submit" disabled={pending}>
          {pending ? "Sending…" : "Send magic link"}
        </Button>
      </form>

      <div className="flex items-center gap-3 text-xs text-muted-foreground">
        <div className="h-px flex-1 bg-border" />
        or
        <div className="h-px flex-1 bg-border" />
      </div>

      <form action={signInWithGoogle}>
        <Button type="submit" variant="outline" className="w-full" disabled={pending}>
          Continue with Google
        </Button>
      </form>

      {message && (
        <p className={`text-sm ${message.kind === "ok" ? "text-green-600" : "text-red-600"}`}>
          {message.text}
        </p>
      )}
    </div>
  );
}
