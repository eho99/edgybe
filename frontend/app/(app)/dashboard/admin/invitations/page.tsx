"use client"

import { useCallback, useState } from "react"
import { InviteMemberForm } from "@/components/ui/InviteMemberForm"
import { useCurrentUserRole } from "@/hooks/useCurrentUserRole"
import { InvitationList } from "@/components/ui/InvitationList"
import { PageLoader } from "@/components/ui/page-loader"
import { ErrorDisplay } from "@/components/error/ErrorDisplay"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export default function InvitationsPage() {
  const [refreshKey, setRefreshKey] = useState(0)
  const { orgId, role, isLoading, error } = useCurrentUserRole()

  const handleInviteSuccess = useCallback(() => {
    setRefreshKey((prev) => prev + 1)
  }, [])

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
          <CardTitle>Invite Internal Users</CardTitle>
          <CardDescription>
            Enter an email and select a role (admin, secretary, or staff) to send an invitation.
            Bulk and CSV uploads are supported too.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <InviteMemberForm orgId={orgId} onSuccess={handleInviteSuccess} />
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Invitation Management</CardTitle>
          <CardDescription>
            View, resend, and cancel pending invitations across your organization.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <InvitationList orgId={orgId} refreshTrigger={refreshKey} />
        </CardContent>
      </Card>
    </div>
  )
}

