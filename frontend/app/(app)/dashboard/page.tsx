"use client"

import { useCurrentUserRole } from "@/hooks/useCurrentUserRole"
import { PageSkeletonLoader } from "@/components/ui/page-skeleton-loader"
import { ErrorDisplay } from "@/components/error/ErrorDisplay"
import { ReferralStatsPanel } from "@/components/dashboard/ReferralStatsPanel"
import { useReferralConfig } from "@/hooks/useReferrals"

export default function DashboardPage() {
  const { orgId, memberships, isLoading, error } = useCurrentUserRole()
  const { config } = useReferralConfig(orgId)

  if (isLoading) {
    return <PageSkeletonLoader contentType="stats" showActions={false} />
  }

  if (error) {
    return (
      <ErrorDisplay
        error={error instanceof Error ? error : new Error("Failed to load dashboard")}
        title="Failed to load dashboard"
      />
    )
  }

  if (!orgId || !memberships || memberships.length === 0) {
    return (
      <ErrorDisplay
        error={new Error("You are not a member of any organizations")}
        title="No organizations"
      />
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Referral Dashboard</h1>
        <p className="text-muted-foreground">
          Explore key referral trends and dig into recent submissions.
        </p>
      </div>

      <ReferralStatsPanel orgId={orgId} config={config} />
    </div>
  )
}
