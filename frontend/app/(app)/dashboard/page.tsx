'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
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
import { Button } from "@/components/ui/button"
import { InviteMemberForm } from "@/components/ui/InviteMemberForm"
import { InvitationList } from "@/components/ui/InvitationList"
import { AccountList } from "@/components/ui/AccountList"

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
  const [isLoggingOut, setIsLoggingOut] = useState(false)
  const [activeTab, setActiveTab] = useState<'overview' | 'invitations' | 'accounts'>('overview')
  const router = useRouter()
  const supabase = createClient()

  const handleLogout = async () => {
    setIsLoggingOut(true)
    try {
      const { error } = await supabase.auth.signOut()
      if (error) {
        setError(`Logout failed: ${error.message}`)
      } else {
        // Redirect to login page
        router.push('/login')
      }
    } catch (err) {
      setError(`Logout failed: ${err instanceof Error ? err.message : 'Unknown error'}`)
    } finally {
      setIsLoggingOut(false)
    }
  }

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
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <Button 
          onClick={handleLogout} 
          disabled={isLoggingOut}
          variant="outline"
        >
          {isLoggingOut ? 'Logging out...' : 'Logout'}
        </Button>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>Dashboard</CardTitle>
          <CardDescription>Welcome, {data.user.email}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Tab Navigation */}
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('overview')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'overview'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Overview
              </button>
              {data.role === 'admin' && (
                <>
                  <button
                    onClick={() => setActiveTab('invitations')}
                    className={`py-2 px-1 border-b-2 font-medium text-sm ${
                      activeTab === 'invitations'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    Invitations
                  </button>
                  <button
                    onClick={() => setActiveTab('accounts')}
                    className={`py-2 px-1 border-b-2 font-medium text-sm ${
                      activeTab === 'accounts'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    Accounts
                  </button>
                </>
              )}
            </nav>
          </div>

          {/* Tab Content */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
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

          {/* Conditionally render the invite form for admins */}
          {data.role === 'admin' && <InviteMemberForm orgId={data.org_id} />}
            </div>
          )}

          {activeTab === 'invitations' && data.role === 'admin' && (
            <InvitationList orgId={data.org_id} />
          )}

          {activeTab === 'accounts' && data.role === 'admin' && (
            <AccountList orgId={data.org_id} />
          )}
        </CardContent>
      </Card>
    </div>
  )
}

