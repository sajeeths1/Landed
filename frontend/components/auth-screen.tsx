"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { LandedWordmark } from "@/components/landed-logo";
import { BellRing, ClipboardList, Target } from "lucide-react";
import { supabase } from "@/lib/supabase";

const HIGHLIGHTS = [
  { icon: Target, title: "Jobs matched to your skills", text: "CS internships and new-grad roles, scored against what you know." },
  { icon: ClipboardList, title: "Every application in one place", text: "Save, apply, interview, offer. Always know where things stand." },
  { icon: BellRing, title: "Alerts before deadlines", text: "Hear about new roles at your favourite companies first." },
];

/** The signed-out landing page: Landed logo and highlights, plus email + password sign in / sign up (Supabase Auth). */
export function AuthScreen() {
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ text: string; isError: boolean } | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!supabase) return;
    setBusy(true);
    setMessage(null);

    const { data, error } =
      mode === "signin"
        ? await supabase.auth.signInWithPassword({ email, password })
        : await supabase.auth.signUp({ email, password });

    if (error) {
      setMessage({ text: error.message, isError: true });
    } else if (mode === "signup" && !data.session) {
      // Supabase's "Confirm email" setting is on: the user must click the email link first.
      setMessage({ text: "Check your email for a confirmation link, then sign in.", isError: false });
    }
    // On success, the page notices the new session and shows the dashboard.
    setBusy(false);
  }

  return (
    <main className="grid min-h-screen bg-background lg:grid-cols-[1.1fr_1fr]">
      {/* Left: the brand story. On phones it sits above the form, shorter. */}
      <section className="relative flex flex-col justify-center overflow-hidden bg-brand-950 px-6 py-10 text-white sm:px-12 lg:py-16">
        <div aria-hidden="true" className="pointer-events-none absolute -bottom-40 -left-24 hidden h-72 w-72 rounded-full bg-brand-500/15 lg:block" />
        <div aria-hidden="true" className="pointer-events-none absolute -bottom-32 -right-20 hidden h-80 w-80 rounded-full bg-brand-400/10 lg:block" />
        <div className="relative mx-auto w-full max-w-lg">
          {/* The tagline is centred under the word "Landed" (the logo image has a little extra room on its left). */}
          <div className="w-56 sm:w-72">
            <LandedWordmark tone="dark" className="w-full" />
            <p className="mt-3 pl-[7%] text-center text-sm font-medium uppercase tracking-[0.25em] text-brand-300">
              <span className="mr-[-0.25em]">Soar to success</span>
            </p>
          </div>
          <h1 className="mt-8 text-3xl font-semibold tracking-tight sm:text-4xl">
            Find your CS role. <span className="text-brand-300">Land the offer.</span>
          </h1>
          <p className="mt-3 text-brand-100/80">
            Landed gathers internships and new-grad jobs from hundreds of companies and helps you track every application.
          </p>
          <ul className="mt-8 hidden gap-5 sm:grid">
            {HIGHLIGHTS.map((item) => (
              <li className="flex gap-4" key={item.title}>
                <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-white/10 text-brand-300 ring-1 ring-white/10">
                  <item.icon className="h-5 w-5" aria-hidden="true" />
                </span>
                <span>
                  <span className="block font-medium">{item.title}</span>
                  <span className="block text-sm text-brand-100/70">{item.text}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* Right: sign in / sign up */}
      <section className="flex items-center justify-center px-4 py-10 sm:px-8">
        <Card className="w-full max-w-sm shadow-lift">
          <CardHeader>
            <CardTitle className="text-xl">{mode === "signin" ? "Welcome back" : "Create your account"}</CardTitle>
            <CardDescription>{mode === "signin" ? "Sign in to pick up where you left off." : "It takes a minute. Then add your skills to see matching jobs."}</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="grid gap-4" onSubmit={handleSubmit}>
              <label className="grid gap-1.5 text-sm font-medium">
                Email
                <Input
                  autoComplete="email"
                  required
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                />
              </label>
              <label className="grid gap-1.5 text-sm font-medium">
                Password
                <Input
                  autoComplete={mode === "signin" ? "current-password" : "new-password"}
                  minLength={6}
                  required
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                />
              </label>
              {message ? (
                <p className={`text-sm ${message.isError ? "text-red-600" : "text-emerald-700"}`}>
                  {message.text}
                </p>
              ) : null}
              <Button disabled={busy} type="submit">
                {busy ? "Please wait…" : mode === "signin" ? "Sign in" : "Sign up"}
              </Button>
            </form>
            <button
              className="mt-4 w-full text-center text-sm font-medium text-primary hover:underline"
              type="button"
              onClick={() => {
                setMode(mode === "signin" ? "signup" : "signin");
                setMessage(null);
              }}
            >
              {mode === "signin" ? "New here? Create an account" : "Already have an account? Sign in"}
            </button>
          </CardContent>
        </Card>
      </section>
    </main>
  );
}
