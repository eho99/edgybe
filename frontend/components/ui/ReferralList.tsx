'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useReferrals, archiveReferral, unarchiveReferral } from '@/hooks/useReferrals'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Loader } from '@/components/ui/loader'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useToast } from '@/hooks/useToast'
import { useErrorHandler } from '@/hooks/useErrorHandler'
import { Archive, ArchiveRestore } from 'lucide-react'
import { Checkbox } from '@/components/ui/checkbox'

interface ReferralListProps {
  orgId: string
  basePath?: string
}

const STATUS_COLORS: Record<string, 'default' | 'warning' | 'success' | 'destructive'> = {
  DRAFT: 'default',
  SUBMITTED: 'warning',
  REVIEW: 'warning',
  CLOSED: 'success',
}

export function ReferralList({ orgId, basePath = `/dashboard/organizations/${orgId}/referrals` }: ReferralListProps) {
  const [page, setPage] = useState(1)
  const [includeArchived, setIncludeArchived] = useState(false)
  const [filters, setFilters] = useState({
    status: '',
    type: '',
    search: '',
  })
  const { toast } = useToast()
  const { handleError } = useErrorHandler()

  const { referrals, total, per_page, total_pages, isLoading, mutate } = useReferrals(orgId, {
    page,
    per_page: 20,
    status: filters.status || undefined,
    type: filters.type || undefined,
    include_archived: includeArchived,
  })

  const handleFilterChange = (key: string, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }))
    setPage(1) // Reset to first page when filter changes
  }

  const handleArchive = async (referralId: string) => {
    try {
      await archiveReferral(orgId, referralId)
      toast({
        variant: 'success',
        title: 'Referral Archived',
        description: 'The referral has been archived successfully',
      })
      mutate() // Refresh the list
    } catch (err) {
      handleError(err, { title: 'Failed to archive referral' })
    }
  }

  const handleUnarchive = async (referralId: string) => {
    try {
      await unarchiveReferral(orgId, referralId)
      toast({
        variant: 'success',
        title: 'Referral Unarchived',
        description: 'The referral has been restored successfully',
      })
      mutate() // Refresh the list
    } catch (err) {
      handleError(err, { title: 'Failed to unarchive referral' })
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  if (isLoading && page === 1) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <Loader />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Referrals</CardTitle>
          <div className="text-sm text-muted-foreground">
            {total} total referral{total !== 1 ? 's' : ''}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Filters */}
        <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-4">
          <div>
            <Input
              placeholder="Search by student name..."
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
            />
          </div>
          <div>
            <Select
              value={filters.status}
              onValueChange={(value) => handleFilterChange('status', value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value=" ">All Statuses</SelectItem>
                <SelectItem value="DRAFT">Draft</SelectItem>
                <SelectItem value="SUBMITTED">Submitted</SelectItem>
                <SelectItem value="REVIEW">Review</SelectItem>
                <SelectItem value="CLOSED">Closed</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Select
              value={filters.type}
              onValueChange={(value) => handleFilterChange('type', value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Filter by type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value=" ">All Types</SelectItem>
                <SelectItem value="Behavior">Behavior</SelectItem>
                <SelectItem value="Support">Support</SelectItem>
                <SelectItem value="Academic">Academic</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center space-x-2">
            <Checkbox
              id="include-archived"
              checked={includeArchived}
              onCheckedChange={(checked) => {
                setIncludeArchived(checked === true)
                setPage(1)
              }}
            />
            <label
              htmlFor="include-archived"
              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
            >
              Include archived
            </label>
          </div>
        </div>

        {/* Table */}
        {referrals.length === 0 ? (
          <div className="py-12 text-center text-muted-foreground">
            No referrals found
          </div>
        ) : (
          <>
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Student</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead>Author</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Interventions</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {referrals.map((referral) => (
                    <TableRow key={referral.id}>
                      <TableCell className="font-medium">
                        <div>{referral.student_name || 'Unknown'}</div>
                        {referral.student_student_id && (
                          <div className="text-xs text-muted-foreground">
                            {referral.student_student_id}
                          </div>
                        )}
                      </TableCell>
                      <TableCell>{referral.type}</TableCell>
                      <TableCell>
                        <div className="flex flex-col gap-1">
                          <Badge variant={STATUS_COLORS[referral.status] || 'default'}>
                            {referral.status}
                          </Badge>
                          {referral.archived && (
                            <Badge variant="outline" className="text-xs">
                              Archived
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>{referral.location || 'N/A'}</TableCell>
                      <TableCell className="text-sm">
                        {referral.author_name || 'Unknown'}
                      </TableCell>
                      <TableCell className="text-sm">
                        {formatDate(referral.created_at)}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{referral.intervention_count}</Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Link href={`${basePath}/${referral.id}`}>
                            <Button variant="ghost" size="sm">
                              View
                            </Button>
                          </Link>
                          {referral.archived ? (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleUnarchive(referral.id)}
                              title="Unarchive referral"
                            >
                              <ArchiveRestore className="h-4 w-4" />
                            </Button>
                          ) : (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleArchive(referral.id)}
                              title="Archive referral"
                            >
                              <Archive className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            {/* Pagination */}
            {total_pages > 1 && (
              <div className="mt-4 flex items-center justify-between">
                <div className="text-sm text-muted-foreground">
                  Page {page} of {total_pages}
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1 || isLoading}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage((p) => Math.min(total_pages, p + 1))}
                    disabled={page === total_pages || isLoading}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}

