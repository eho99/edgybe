'use client'

import { useEffect, useState } from 'react'
import apiClient from '@/lib/apiClient'
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
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Spinner } from "@/components/ui/spinner"

interface AuthenticatedMember {
  user: {
    id: string
    email: string
  }
  org_id: string
  role: string
}

interface OrganizationMembership {
  org_id: string
  role: string
  organization_name: string
  joined_at: string
}

export default function DashboardPage() {
  const [data, setData] = useState<AuthenticatedMember | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [memberships, setMemberships] = useState<OrganizationMembership[]>([])

  useEffect(() => {
    const fetchData = async () => {
      try {
        // First, get user's organization memberships
        const membershipsResponse = await apiClient('/api/v1/organizations/my-memberships')
        const membershipsData = membershipsResponse as OrganizationMembership[]
        setMemberships(membershipsData)
        
        if (membershipsData.length === 0) {
          setError('You are not a member of any organizations')
          return
        }
        
        // Use the first organization (you could add logic to select a specific one)
        const orgId = membershipsData[0].org_id
        
        const response = await apiClient(`/api/v1/organizations/${orgId}/protected-data`)
        const result = response as AuthenticatedMember
        setData(result)
      } catch (err: unknown) {
        setError((err as Error).message)
      }
    }

    fetchData()
  }, [])

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Alert variant="destructive" className="max-w-md">
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>
            {error}
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Spinner />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <Card>
        <CardHeader>
          <CardTitle>Dashboard</CardTitle>
          <CardDescription>Welcome, {data.user.email}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Current Organization</CardTitle>
            </CardHeader>
            <CardContent>
              <p><strong>Organization:</strong> {memberships.find(m => m.org_id === data.org_id)?.organization_name}</p>
              <p><strong>Role:</strong> {data.role}</p>
            </CardContent>
          </Card>

          {memberships.length > 1 && (
            <Card>
              <CardHeader>
                <CardTitle>Your Organizations</CardTitle>
              </CardHeader>
              <CardContent>
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
                        <TableCell>{membership.role}</TableCell>
                        <TableCell>{new Date(membership.joined_at).toLocaleDateString()}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Raw Data</CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="bg-gray-100 p-4 rounded text-sm overflow-auto">
                {JSON.stringify(data, null, 2)}
              </pre>
            </CardContent>
          </Card>
        </CardContent>
      </Card>
    </div>
  )
}

