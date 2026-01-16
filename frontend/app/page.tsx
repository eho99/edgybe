import Link from "next/link";
import {
  ArrowRight,
  BarChart3,
  ClipboardList,
  Users,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { createClient } from "@/lib/supabase/server";

export default async function HomePage() {
  const supabase = await createClient();
  const { data: claimsData, error: claimsError } = await supabase.auth.getClaims();
  const isAuthenticated = !claimsError && Boolean(claimsData?.claims);

  return (
    <main className="min-h-screen bg-white text-slate-900">
      <div className="px-4">
        <header className="max-w-6xl mx-auto w-full py-6 flex items-center justify-between">
          <div className="text-xl font-semibold">AdminReferral</div>
          <div className="flex items-center gap-3">
            <Button asChild variant="ghost">
              <Link href="/login">Log in</Link>
            </Button>
            {isAuthenticated && (
              <Button asChild>
                <Link href="/dashboard">Dashboard</Link>
              </Button>
            )}
          </div>
        </header>

        <div className="max-w-6xl mx-auto w-full py-10 md:py-20">
          {/* Hero Section */}
          <section className="flex flex-col md:flex-row items-center gap-8 mb-20">
            <div className="flex-1 space-y-6">
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold leading-tight">
                Transform Classroom Management with Confidence
              </h1>
              <p className="text-lg md:text-xl text-muted-foreground">
                The complete behavioral management solution that empowers
                educators to create thriving learning environments.
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <Button size="lg" asChild>
                  <Link href={isAuthenticated ? "/dashboard" : "/login"}>
                    {isAuthenticated ? "Go to Dashboard" : "Login or Request Demo"}
                  </Link>
                </Button>
                <Button size="lg" variant="outline" asChild>
                  <Link href="#features">
                    Learn More
                  </Link>
                </Button>
              </div>
            </div>
            <div className="flex-1">
              <img
                src="/dashboard-preview.png"
                alt="Platform Dashboard"
                className="rounded-lg shadow-xl w-full"
              />
            </div>
          </section>

          {/* Features Section */}
          <section id="features" className="mb-20">
            <h2 className="text-3xl font-bold text-center mb-12">
              Comprehensive Behavioral Management
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <Card>
                <CardHeader>
                  <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mb-4">
                    <ClipboardList className="h-6 w-6 text-primary" />
                  </div>
                  <CardTitle>Real-time Tracking</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">
                    Monitor student behavior patterns with intuitive dashboards
                    and receive alerts for concerning trends.
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mb-4">
                    <Users className="h-6 w-6 text-primary" />
                  </div>
                  <CardTitle>Collaborative Tools</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">
                    Connect teachers, administrators, and support staff with
                    shared resources and communication channels.
                  </p>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mb-4">
                    <BarChart3 className="h-6 w-6 text-primary" />
                  </div>
                  <CardTitle>Data-Driven Insights</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">
                    Generate comprehensive reports and analytics to inform
                    interventions and measure progress over time.
                  </p>
                </CardContent>
              </Card>
            </div>
          </section>

          {/* How It Works */}
          <section id="how-it-works" className="mb-20">
            <h2 className="text-3xl font-bold text-center mb-12">How It Works</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {[
                {
                  step: 1,
                  title: "Setup Your School",
                  description:
                    "Quick onboarding for administrators and teachers with custom configuration.",
                },
                {
                  step: 2,
                  title: "Track Behaviors",
                  description:
                    "Record and categorize student behaviors with our intuitive mobile and desktop apps.",
                },
                {
                  step: 3,
                  title: "Analyze Patterns",
                  description:
                    "Identify trends and triggers with our powerful analytics dashboard.",
                },
                {
                  step: 4,
                  title: "Implement Solutions",
                  description:
                    "Apply evidence-based interventions and measure their effectiveness.",
                },
              ].map((item) => (
                <div key={item.step} className="text-center">
                  <div className="w-16 h-16 bg-primary text-primary-foreground rounded-full flex items-center justify-center mx-auto mb-4 text-xl font-bold">
                    {item.step}
                  </div>
                  <h3 className="text-lg font-semibold mb-2">{item.title}</h3>
                  <p className="text-muted-foreground">{item.description}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Dashboard Access for Existing Customers */}
          <section className="mb-20 text-center">
            <div className="bg-muted p-8 rounded-xl">
              <h2 className="text-2xl font-bold mb-4">Already a Customer?</h2>
              <p className="text-muted-foreground mb-6">
                Access your school's dashboard to continue managing classroom
                behavior
              </p>
              <Button asChild size="lg">
                <Link href="/dashboard" className="flex items-center gap-2">
                  Head to Dashboard <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
            </div>
          </section>

          {/* Call to Action */}
          <section className="text-center bg-primary text-primary-foreground p-12 rounded-xl">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Ready to Transform Your School&apos;s Approach to Behavior Management?
            </h2>
            <p className="text-lg md:text-xl mb-8 max-w-3xl mx-auto">
              Be among the first to pioneer a new era of classroom management and
              shape the future of education.
            </p>
            <div className="flex flex-col sm:flex-row justify-center gap-4">
              <Button size="lg" variant="secondary" asChild>
                <Link href="/login">
                  Schedule a Demo
                </Link>
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="bg-transparent border-primary-foreground hover:bg-primary-foreground/10 text-primary-foreground"
                asChild
              >
                <Link href={isAuthenticated ? "/dashboard" : "/login"}>
                  {isAuthenticated ? "Go to Dashboard" : "View Pricing"}
                </Link>
              </Button>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}