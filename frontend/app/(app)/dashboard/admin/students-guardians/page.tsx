"use client"

import { useCurrentUserRole } from "@/hooks/useCurrentUserRole"
import { CreateStudentGuardianForm } from "@/components/ui/CreateStudentGuardianForm"
import { PageLoader } from "@/components/ui/page-loader"
import { ErrorDisplay } from "@/components/error/ErrorDisplay"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { StudentGuardianProfileManager } from "@/components/ui/StudentGuardianProfileManager"

export default function StudentsGuardiansPage() {
  const { orgId, role, isLoading, error } = useCurrentUserRole()

  if (isLoading) {
    return <PageLoader text="Loading..." />
  }

  if (error) {
    return (
      <ErrorDisplay
        error={error instanceof Error ? error : new Error("Failed to load page")}
        title="Failed to load page"
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
        <h1 className="text-3xl font-bold tracking-tight">Students & Guardians</h1>
        <p className="text-muted-foreground">
          Create and manage student and guardian relationships.
        </p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Create Student-Guardian Relationship</CardTitle>
          <CardDescription>
            Link students with their guardians in the system.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <CreateStudentGuardianForm orgId={orgId} />
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Manage Profiles</CardTitle>
          <CardDescription>Edit existing student and guardian records.</CardDescription>
        </CardHeader>
        <CardContent>
          <StudentGuardianProfileManager orgId={orgId} />
        </CardContent>
      </Card>
    </div>
  )
}

