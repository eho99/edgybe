'use client'

import { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert'
import { Spinner } from '@/components/ui/spinner'
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
import { Search, RefreshCw, Trash2 } from 'lucide-react'
import apiClient from '@/lib/apiClient'

interface Account {
  id: string
  organization_id: string
  user_id: string | null
  invite_email: string | null
  email: string | null
  full_name: string | null
  role: string
  status: 'active' | 'inactive'
  joined_at: string
}

interface AccountListResponse {
  accounts: Account[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

interface AccountListProps {
  orgId: string
}

export function AccountList({ orgId }: AccountListProps) {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [total, setTotal] = useState(0)
  const [accountToDelete, setAccountToDelete] = useState<Account | null>(null)
  const [deleting, setDeleting] = useState(false)

  const fetchAccounts = async () => {
    try {
      setLoading(true)
      setError(null)

      const params = new URLSearchParams({
        page: page.toString(),
        per_page: '10',
        ...(search && { search }),
        ...(statusFilter !== 'all' && { status_filter: statusFilter })
      })

      const response = await apiClient<AccountListResponse>(
        `/api/v1/organizations/${orgId}/members?${params}`
      )

      setAccounts(response.accounts)
      setTotalPages(response.total_pages)
      setTotal(response.total)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch accounts')
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteAccount = async (account: Account) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete the account for ${getDisplayEmail(account)}? This action cannot be undone.`
    )
    
    if (!confirmed) return

    try {
      setDeleting(true)
      setAccountToDelete(account)
      await apiClient(`/api/v1/organizations/${orgId}/members/${account.id}`, {
        method: 'DELETE'
      })
      setAccountToDelete(null)
      await fetchAccounts() // Refresh the list
    } catch (err: any) {
      setError(err.message || 'Failed to delete account')
    } finally {
      setDeleting(false)
    }
  }

  useEffect(() => {
    fetchAccounts()
  }, [orgId, page, search, statusFilter])

  const getDisplayEmail = (account: Account) => {
    return account.email || account.invite_email || 'N/A'
  }

  const getDisplayName = (account: Account) => {
    return account.full_name || 'N/A'
  }

  const getStatusBadge = (status: string) => {
    const colors = {
      active: 'bg-green-100 text-green-800',
      inactive: 'bg-gray-100 text-gray-800'
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
      day: 'numeric'
    })
  }

  if (loading && accounts.length === 0) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <Spinner className="w-6 h-6" />
          <span className="ml-2">Loading accounts...</span>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Main Accounts Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Accounts</CardTitle>
            <Button onClick={fetchAccounts} variant="outline" size="sm">
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
                placeholder="Search by email or name..."
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
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
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
                  <TableHead>Name</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Joined Date</TableHead>
                  <TableHead className="w-12">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {accounts.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-8 text-gray-500">
                      No accounts found
                    </TableCell>
                  </TableRow>
                ) : (
                  accounts.map((account) => (
                    <TableRow key={account.id}>
                      <TableCell className="font-medium">
                        {getDisplayEmail(account)}
                      </TableCell>
                      <TableCell>{getDisplayName(account)}</TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {account.role.charAt(0).toUpperCase() + account.role.slice(1)}
                        </Badge>
                      </TableCell>
                      <TableCell>{getStatusBadge(account.status)}</TableCell>
                      <TableCell>{formatDate(account.joined_at)}</TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteAccount(account)}
                          disabled={deleting && accountToDelete?.id === account.id}
                          className="text-red-600 hover:text-red-700"
                        >
                          {deleting && accountToDelete?.id === account.id ? (
                            <Spinner className="w-4 h-4" />
                          ) : (
                            <Trash2 className="w-4 h-4" />
                          )}
                        </Button>
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
                Showing {((page - 1) * 10) + 1} to {Math.min(page * 10, total)} of {total} accounts
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

