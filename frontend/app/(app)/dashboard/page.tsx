"use client"

import { useState } from "react"
import { useCurrentUserRole } from "@/hooks/useCurrentUserRole"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { PageLoader } from "@/components/ui/page-loader"
import { ErrorDisplay } from "@/components/error/ErrorDisplay"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { useErrorHandler } from "@/hooks/useErrorHandler"
import { InviteMemberForm } from "@/components/ui/InviteMemberForm"

export default function DashboardPage() {
  const { role, orgId, memberships, isLoading, error } = useCurrentUserRole()
  const { handleError } = useErrorHandler()
  const [showDevTools, setShowDevTools] = useState(false)

  if (isLoading) {
    return <PageLoader text="Loading dashboard..." />
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

  const currentOrg = memberships.find((m) => m.org_id === orgId) || memberships[0]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Welcome back! Here's an overview of your organization.
        </p>
      </div>

      {/* Statistics Section - Placeholder for future implementation */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Members</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">—</div>
            <p className="text-xs text-muted-foreground">Coming soon</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Referrals</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">—</div>
            <p className="text-xs text-muted-foreground">Coming soon</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Invitations</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">—</div>
            <p className="text-xs text-muted-foreground">Coming soon</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">This Month</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">—</div>
            <p className="text-xs text-muted-foreground">Coming soon</p>
          </CardContent>
        </Card>
      </div>

      {/* Referrals Section */}
      <Card>
        <CardHeader>
          <CardTitle>Referrals</CardTitle>
          <CardDescription>
            Manage and track referrals for your organization.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Referral management features will be available here soon.
          </p>
        </CardContent>
      </Card>

      {/* Current Organization Info */}
      <Card>
        <CardHeader>
          <CardTitle>Current Organization</CardTitle>
          <CardDescription>Your organization details and role</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <p className="text-sm font-medium">Organization</p>
            <p className="text-sm text-muted-foreground">{currentOrg.organization_name}</p>
          </div>
          <div>
            <p className="text-sm font-medium">Role</p>
            <p className="text-sm text-muted-foreground capitalize">{role}</p>
          </div>
          {memberships.length > 1 && (
            <div>
              <p className="text-sm font-medium mb-2">Your Organizations</p>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Organization</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Joined</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {memberships.map((membership) => (
                    <TableRow key={membership.org_id}>
                      <TableCell>{membership.organization_name}</TableCell>
                      <TableCell className="capitalize">{membership.role}</TableCell>
                      <TableCell>
                        {new Date(membership.joined_at).toLocaleDateString()}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Admin Section - Invite Form */}
      {role === "admin" && (
        <Card>
          <CardHeader>
            <CardTitle>Invite Member</CardTitle>
            <CardDescription>Send an invitation to a new team member</CardDescription>
          </CardHeader>
          <CardContent>
            <InviteMemberForm orgId={orgId} />
          </CardContent>
        </Card>
      )}

      {/* Dev Tools Section - Collapsible */}
      <Accordion type="single" collapsible>
        <AccordionItem value="dev-tools">
          <AccordionTrigger className="text-sm text-muted-foreground">
            Dev Tools (Development Only)
          </AccordionTrigger>
          <AccordionContent>
            <Card>
              <CardHeader>
                <CardTitle>Raw Data</CardTitle>
                <CardDescription>Debug information (development only)</CardDescription>
              </CardHeader>
              <CardContent>
                <pre className="bg-muted p-4 rounded text-sm overflow-auto max-h-96">
                  {JSON.stringify(
                    {
                      role,
                      orgId,
                      memberships,
                    },
                    null,
                    2
                  )}
                </pre>
              </CardContent>
            </Card>
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </div>
  )
}
