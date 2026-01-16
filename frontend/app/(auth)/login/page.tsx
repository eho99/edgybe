'use client'

import Link from "next/link";
import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";

import {
  Alert,
  AlertDescription,
  AlertTitle,
} from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createClient } from "@/lib/supabase/client";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [resetEmail, setResetEmail] = useState("");
  const [resetMessage, setResetMessage] = useState<string | null>(null);
  const [isResetting, setIsResetting] = useState(false);
  const [hasSession, setHasSession] = useState(false);

  const router = useRouter();
  const supabase = createClient();

  useEffect(() => {
    const checkSession = async () => {
      const { data } = await supabase.auth.getSession();
      setHasSession(!!data.session);
    };

    checkSession();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setHasSession(!!session);
    });

    return () => {
      subscription?.unsubscribe();
    };
  }, [supabase]);

  const handleLogin = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const { error: signInError } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (signInError) {
      setError(signInError.message);
    } else {
      router.push("/dashboard");
    }

    setIsSubmitting(false);
  };

  const handleForgotPassword = async (e: FormEvent) => {
    e.preventDefault();
    setResetMessage(null);
    setIsResetting(true);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/users/request-password-reset`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ email: resetEmail }),
        }
      );

      const data = await response.json();

      if (response.ok) {
        setResetMessage(
          data.message || "Password reset email sent successfully"
        );
        setResetEmail("");
      } else {
        setResetMessage(data.detail || "Failed to send password reset email");
      }
    } catch {
      setResetMessage(
        "Failed to send password reset email. Please try again."
      );
    } finally {
      setIsResetting(false);
    }
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-2 bg-gray-50">
      <div className="relative hidden lg:flex items-center justify-center bg-gradient-to-br from-primary/10 via-white to-primary/10 p-12">
        <div className="absolute inset-0 bg-slate-100 opacity-80" />
        <div className="relative z-10 max-w-lg space-y-6">
          <p className="text-sm uppercase tracking-wide text-primary font-semibold">
            AdminReferral
          </p>
          <h1 className="text-4xl font-bold leading-tight">
            Purpose-built for modern school behavior teams
          </h1>
          <p className="text-lg text-muted-foreground">
            Monitor, collaborate, and act with confidence. Keep every stakeholder
            aligned with real-time insights and workflows designed for educators.
          </p>
          <ul className="space-y-3 text-muted-foreground">
            <li className="flex items-start gap-3">
              <span className="mt-1 h-2 w-2 rounded-full bg-primary" />
              Streamlined referrals and documentation.
            </li>
            <li className="flex items-start gap-3">
              <span className="mt-1 h-2 w-2 rounded-full bg-primary" />
              Actionable analytics to spot trends early.
            </li>
            <li className="flex items-start gap-3">
              <span className="mt-1 h-2 w-2 rounded-full bg-primary" />
              Secure, role-aware access for your whole team.
            </li>
          </ul>
        </div>
      </div>

      <div className="flex items-center justify-center p-6">
        <Card className="w-full max-w-md shadow-lg">
          <CardHeader className="space-y-2 text-center">
            <p className="text-sm text-muted-foreground">Welcome back</p>
            <CardTitle className="text-2xl font-semibold">
              Sign in to AdminReferral
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {hasSession && (
              <Alert>
                <AlertTitle>Already signed in</AlertTitle>
                <AlertDescription className="space-y-3">
                  <p>
                    You&apos;re currently signed in. Continue to your dashboard or
                    sign in with a different account below.
                  </p>
                  <Button asChild size="sm" variant="secondary">
                    <Link href="/dashboard">Go to Dashboard</Link>
                  </Button>
                </AlertDescription>
              </Alert>
            )}

            {showForgotPassword ? (
              <form className="space-y-5" onSubmit={handleForgotPassword}>
                <div className="space-y-2 text-left">
                  <Label htmlFor="reset-email">Email address</Label>
                  <Input
                    id="reset-email"
                    name="reset-email"
                    type="email"
                    autoComplete="email"
                    required
                    placeholder="Enter your email address"
                    value={resetEmail}
                    onChange={(e) => setResetEmail(e.target.value)}
                  />
                </div>

                {resetMessage && (
                  <Alert
                    variant={
                      resetMessage.includes("sent") ? "default" : "destructive"
                    }
                  >
                    <AlertTitle>
                      {resetMessage.includes("sent") ? "Success" : "Error"}
                    </AlertTitle>
                    <AlertDescription>{resetMessage}</AlertDescription>
                  </Alert>
                )}

                <div className="space-y-2">
                  <Button
                    type="submit"
                    className="w-full"
                    disabled={isResetting}
                  >
                    {isResetting ? "Sending..." : "Send reset link"}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    className="w-full"
                    onClick={() => {
                      setShowForgotPassword(false);
                      setResetEmail("");
                      setResetMessage(null);
                    }}
                  >
                    Back to login
                  </Button>
                </div>
              </form>
            ) : (
              <form className="space-y-5" onSubmit={handleLogin}>
                <div className="space-y-2 text-left">
                  <Label htmlFor="email">Email address</Label>
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    autoComplete="email"
                    required
                    placeholder="Email address"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>
                <div className="space-y-2 text-left">
                  <Label htmlFor="password">Password</Label>
                  <Input
                    id="password"
                    name="password"
                    type="password"
                    autoComplete="current-password"
                    required
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                </div>

                {error && (
                  <Alert variant="destructive">
                    <AlertTitle>Error</AlertTitle>
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                <Button
                  type="submit"
                  className="w-full"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? "Signing in..." : "Sign in"}
                </Button>

                <div className="flex items-center justify-between text-sm">
                  <button
                    type="button"
                    onClick={() => setShowForgotPassword(true)}
                    className="text-primary hover:underline"
                  >
                    Forgot password?
                  </button>
                  <Link
                    href="/"
                    className="text-muted-foreground hover:text-primary"
                  >
                    Back to landing
                  </Link>
                </div>
              </form>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
