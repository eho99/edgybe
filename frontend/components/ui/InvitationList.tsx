'use client'

import { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert'
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { MoreHorizontal, Search, RefreshCw, Mail, X } from 'lucide-react'
import apiClient from '@/lib/apiClient'
import { useErrorHandler } from '@/hooks/useErrorHandler'
import { useToast } from '@/hooks/useToast'
import { Loader } from '@/components/ui/loader'

interface Invitation {
  id: string
  email: string
  role: string
  status: 'pending' | 'accepted' | 'expired' | 'cancelled'
  sent_at: string
  accepted_at?: string
  expires_at: string
  inviter_name?: string
}

interface InvitationListResponse {
  invitations: Invitation[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

interface InvitationStats {
  pending: number
  accepted: number
  expired: number
  cancelled: number
  total: number
}

interface InvitationListProps {
  orgId: string
}

export function InvitationList({ orgId }: InvitationListProps) {
  const [invitations, setInvitations] = useState<Invitation[]>([])
  const [stats, setStats] = useState<InvitationStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [total, setTotal] = useState(0)
  const { handleError } = useErrorHandler()
  const { toast } = useToast()

  const fetchInvitations = async () => {
    try {
      setLoading(true)
      setError(null)

      const params = new URLSearchParams({
        page: page.toString(),
        per_page: '10',
        ...(search && { search }),
        ...(statusFilter !== 'all' && { status_filter: statusFilter })
      })

      const [invitationsResponse, statsResponse] = await Promise.all([
        apiClient<InvitationListResponse>(`/api/v1/organizations/${orgId}/invitations?${params}`),
        apiClient<InvitationStats>(`/api/v1/organizations/${orgId}/invitations/stats`)
      ])

      setInvitations(invitationsResponse.invitations)
      setTotalPages(invitationsResponse.total_pages)
      setTotal(invitationsResponse.total)
      setStats(statsResponse)
      setError(null)
    } catch (err) {
      const handled = handleError(err, { title: "Failed to fetch invitations", showToast: false })
      setError(handled.userMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleResendInvitation = async (invitationId: string) => {
    try {
      await apiClient(`/api/v1/organizations/${orgId}/invitations/${invitationId}/resend`, {
        method: 'POST'
      })
      toast({
        variant: "success",
        title: "Invitation resent",
        description: "The invitation has been resent successfully.",
      })
      await fetchInvitations() // Refresh the list
    } catch (err) {
      handleError(err, { title: "Failed to resend invitation" })
    }
  }

  const handleCancelInvitation = async (invitationId: string) => {
    try {
      await apiClient(`/api/v1/organizations/${orgId}/invitations/${invitationId}`, {
        method: 'DELETE'
      })
      toast({
        variant: "success",
        title: "Invitation cancelled",
        description: "The invitation has been cancelled successfully.",
      })
      await fetchInvitations() // Refresh the list
    } catch (err) {
      handleError(err, { title: "Failed to cancel invitation" })
    }
  }

  useEffect(() => {
    fetchInvitations()
  }, [orgId, page, search, statusFilter])

  const getStatusBadge = (status: string) => {
    const variants = {
      pending: 'default',
      accepted: 'default',
      expired: 'secondary',
      cancelled: 'destructive'
    } as const

    const colors = {
      pending: 'bg-yellow-100 text-yellow-800',
      accepted: 'bg-green-100 text-green-800',
      expired: 'bg-gray-100 text-gray-800',
      cancelled: 'bg-red-100 text-red-800'
    }

    return (
      <Badge className={colors[status as keyof typeof colors]}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    )
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const isExpired = (expiresAt: string) => {
    return new Date(expiresAt) < new Date()
  }

  if (loading && invitations.length === 0) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <Loader size="md" text="Loading invitations..." />
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-yellow-600">{stats.pending}</div>
              <div className="text-sm text-gray-600">Pending</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-green-600">{stats.accepted}</div>
              <div className="text-sm text-gray-600">Accepted</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-gray-600">{stats.expired}</div>
              <div className="text-sm text-gray-600">Expired</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-red-600">{stats.cancelled}</div>
              <div className="text-sm text-gray-600">Cancelled</div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="text-2xl font-bold text-blue-600">{stats.total}</div>
              <div className="text-sm text-gray-600">Total</div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Invitations Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Invitations</CardTitle>
            <Button onClick={fetchInvitations} variant="outline" size="sm">
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-4 mb-6">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                placeholder="Search by email or inviter..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-full sm:w-48">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="accepted">Accepted</SelectItem>
                <SelectItem value="expired">Expired</SelectItem>
                <SelectItem value="cancelled">Cancelled</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Error Alert */}
          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Table */}
          <div className="border rounded-lg">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Email</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Sent By</TableHead>
                  <TableHead>Sent At</TableHead>
                  <TableHead>Expires At</TableHead>
                  <TableHead className="w-12"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {invitations.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8 text-gray-500">
                      No invitations found
                    </TableCell>
                  </TableRow>
                ) : (
                  invitations.map((invitation) => (
                    <TableRow key={invitation.id}>
                      <TableCell className="font-medium">{invitation.email}</TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {invitation.role.charAt(0).toUpperCase() + invitation.role.slice(1)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getStatusBadge(invitation.status)}
                          {isExpired(invitation.expires_at) && invitation.status === 'pending' && (
                            <Badge variant="destructive" className="text-xs">
                              Expired
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>{invitation.inviter_name || 'Unknown'}</TableCell>
                      <TableCell>{formatDate(invitation.sent_at)}</TableCell>
                      <TableCell>
                        <span className={isExpired(invitation.expires_at) ? 'text-red-600' : ''}>
                          {formatDate(invitation.expires_at)}
                        </span>
                      </TableCell>
                      <TableCell>
                        {invitation.status === 'pending' && (
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="sm">
                                <MoreHorizontal className="w-4 h-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem onClick={() => handleResendInvitation(invitation.id)}>
                                <Mail className="w-4 h-4 mr-2" />
                                Resend
                              </DropdownMenuItem>
                              <DropdownMenuItem 
                                onClick={() => handleCancelInvitation(invitation.id)}
                                className="text-red-600"
                              >
                                <X className="w-4 h-4 mr-2" />
                                Cancel
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        )}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <div className="text-sm text-gray-600">
                Showing {((page - 1) * 10) + 1} to {Math.min(page * 10, total)} of {total} invitations
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(page - 1)}
                  disabled={page === 1}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(page + 1)}
                  disabled={page === totalPages}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}


