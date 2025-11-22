"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useCurrentUserRole } from "@/hooks/useCurrentUserRole"
import { PageLoader } from "@/components/ui/page-loader"
import { ErrorDisplay } from "@/components/error/ErrorDisplay"

export default function ReferralsPage() {
  const { isLoading, error } = useCurrentUserRole()

  if (isLoading) {
    return <PageLoader text="Loading referrals..." />
  }

  if (error) {
    return (
      <ErrorDisplay
        error={error instanceof Error ? error : new Error("Failed to load referrals")}
        title="Failed to load referrals"
      />
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Referrals</h1>
        <p className="text-muted-foreground">
          Manage and track referrals for your organization.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Referral Overview</CardTitle>
          <CardDescription>
            Referral management features will be available here soon.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            This section will contain referral tracking, management, and reporting features.
            Check back soon for updates!
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

