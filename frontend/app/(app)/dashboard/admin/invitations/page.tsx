"use client"

import { useCurrentUserRole } from "@/hooks/useCurrentUserRole"
import { InvitationList } from "@/components/ui/InvitationList"
import { PageLoader } from "@/components/ui/page-loader"
import { ErrorDisplay } from "@/components/error/ErrorDisplay"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export default function InvitationsPage() {
  const { orgId, role, isLoading, error } = useCurrentUserRole()

  if (isLoading) {
    return <PageLoader text="Loading invitations..." />
  }

  if (error) {
    return (
      <ErrorDisplay
        error={error instanceof Error ? error : new Error("Failed to load invitations")}
        title="Failed to load invitations"
      />
    )
  }

  if (role !== "admin") {
    return (
      <ErrorDisplay
        error={new Error("You don't have permission to access this page")}
        title="Access Denied"
      />
    )
  }

  if (!orgId) {
    return (
      <ErrorDisplay
        error={new Error("No organization found")}
        title="Organization Error"
      />
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Invitations</h1>
        <p className="text-muted-foreground">
          Manage and track invitations sent to team members.
        </p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Invitation Management</CardTitle>
          <CardDescription>
            View, resend, and cancel invitations for your organization.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <InvitationList orgId={orgId} />
        </CardContent>
      </Card>
    </div>
  )
}

