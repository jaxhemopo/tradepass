import { redirect } from "next/navigation";
import { brand } from "@/brand.config";
import { createClient } from "@/lib/supabase/server";
import { LoginForm } from "./login-form";

export default async function LoginPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (user) {
    redirect("/dashboard");
  }

  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <div className="flex w-full max-w-sm flex-col items-center gap-8">
        <div className="flex flex-col items-center gap-2 text-center">
          <h1 className="text-2xl font-semibold">{brand.name}</h1>
          <p className="text-sm text-muted-foreground">{brand.tagline}</p>
        </div>
        <LoginForm />
      </div>
    </main>
  );
}
