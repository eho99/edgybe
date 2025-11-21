"use client"

import { useCurrentUserRole } from "@/hooks/useCurrentUserRole"
import { AccountList } from "@/components/ui/AccountList"
import { PageLoader } from "@/components/ui/page-loader"
import { ErrorDisplay } from "@/components/error/ErrorDisplay"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export default function AccountsPage() {
  const { orgId, role, isLoading, error } = useCurrentUserRole()

  if (isLoading) {
    return <PageLoader text="Loading accounts..." />
  }

  if (error) {
    return (
      <ErrorDisplay
        error={error instanceof Error ? error : new Error("Failed to load accounts")}
        title="Failed to load accounts"
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
        <h1 className="text-3xl font-bold tracking-tight">Accounts</h1>
        <p className="text-muted-foreground">
          Manage user accounts and their roles in your organization.
        </p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Account Management</CardTitle>
          <CardDescription>
            View and manage all user accounts in your organization.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <AccountList orgId={orgId} />
        </CardContent>
      </Card>
    </div>
  )
}

