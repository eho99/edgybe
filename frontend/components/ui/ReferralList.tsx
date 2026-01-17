'use client'

import { useState, useMemo } from 'react'
import Link from 'next/link'
import { useReferrals, archiveReferral, unarchiveReferral, useReferralConfig } from '@/hooks/useReferrals'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { useToast } from '@/hooks/useToast'
import { useErrorHandler } from '@/hooks/useErrorHandler'
import { Archive, ArchiveRestore, X } from 'lucide-react'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import { useOrganizationAdmins } from '@/hooks/useOrganizationMembers'
import { useCurrentUserRole } from '@/hooks/useCurrentUserRole'

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
    grade: '',
    location: '',
    assigned_admin_id: '',
  })
  const [myReferralsOnly, setMyReferralsOnly] = useState(false)
  const [dateRange, setDateRange] = useState({
    start: '',
    end: '',
  })
  const { toast } = useToast()
  const { handleError } = useErrorHandler()
  const { config } = useReferralConfig(orgId)
  const { admins, isLoading: adminsLoading } = useOrganizationAdmins(orgId)
  const { orgData, isAdmin } = useCurrentUserRole()

  // Build API filters
  const apiFilters = useMemo(() => {
    const apiFilter: {
      page: number
      per_page: number
      status?: string
      type?: string
      include_archived: boolean
      grade_level?: string
      location?: string
      created_after?: string
      created_before?: string
      assigned_admin_id?: string
    } = {
      page,
      per_page: 20,
      include_archived: includeArchived,
    }

    if (filters.status) apiFilter.status = filters.status
    if (filters.type) apiFilter.type = filters.type
    if (filters.grade) apiFilter.grade_level = filters.grade
    if (filters.location) apiFilter.location = filters.location
    if (dateRange.start) {
      // Convert local date to ISO string (assumes start of day in local timezone)
      const date = new Date(dateRange.start)
      date.setHours(0, 0, 0, 0)
      apiFilter.created_after = date.toISOString()
    }
    if (dateRange.end) {
      // Convert local date to ISO string (assumes end of day in local timezone)
      const date = new Date(dateRange.end)
      date.setHours(23, 59, 59, 999)
      apiFilter.created_before = date.toISOString()
    }
    // Handle assigned admin filter - prioritize "My Referrals" if enabled
    if (myReferralsOnly && orgData?.user?.id) {
      apiFilter.assigned_admin_id = orgData.user.id
    } else if (filters.assigned_admin_id) {
      apiFilter.assigned_admin_id = filters.assigned_admin_id
    }

    return apiFilter
  }, [page, includeArchived, filters, dateRange, myReferralsOnly, orgData])

  const { referrals, total, per_page, total_pages, isLoading, mutate } = useReferrals(orgId, apiFilters)

  // Extract unique grade levels from referrals
  const uniqueGrades = useMemo(() => {
    const grades = new Set<string>()
    referrals.forEach((referral) => {
      if (referral.student_grade_level) {
        grades.add(referral.student_grade_level)
      }
    })
    return Array.from(grades).sort()
  }, [referrals])

  const handleFilterChange = (key: string, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }))
    setPage(1) // Reset to first page when filter changes
  }

  const handleDateRangeChange = (key: 'start' | 'end', value: string) => {
    setDateRange((prev) => ({ ...prev, [key]: value }))
    setPage(1) // Reset to first page when filter changes
  }

  const handleClearFilters = () => {
    setFilters({
      status: '',
      type: '',
      search: '',
      grade: '',
      location: '',
      assigned_admin_id: '',
    })
    setMyReferralsOnly(false)
    setDateRange({
      start: '',
      end: '',
    })
    setPage(1)
  }

  // Check if any filters are active
  const hasActiveFilters = useMemo(() => {
    return (
      filters.status !== '' ||
      filters.type !== '' ||
      filters.search !== '' ||
      filters.grade !== '' ||
      filters.location !== '' ||
      filters.assigned_admin_id !== '' ||
      myReferralsOnly ||
      dateRange.start !== '' ||
      dateRange.end !== ''
    )
  }, [filters, dateRange, myReferralsOnly])

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
        <CardHeader>
          <div className="flex items-center justify-between">
            <Skeleton className="h-6 w-24" />
            <Skeleton className="h-4 w-32" />
          </div>
        </CardHeader>
        <CardContent>
          {/* Filters Skeleton */}
          <div className="mb-6 rounded-lg border-2 border-border/80 bg-muted/30 p-4">
            <div className="mb-4 space-y-1">
              <Skeleton className="h-4 w-16" />
              <Skeleton className="h-3 w-48" />
            </div>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-5">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="space-y-2">
                  <Skeleton className="h-4 w-16" />
                  <Skeleton className="h-10 w-full" />
                </div>
              ))}
            </div>
          </div>

          {/* Table Skeleton */}
          <div className="rounded-lg border-2 border-border/80 bg-background">
            <div className="p-4">
              <div className="space-y-4">
                {/* Table Header */}
                <div className="grid grid-cols-9 gap-4 border-b border-border pb-2">
                  {Array.from({ length: 9 }).map((_, i) => (
                    <Skeleton key={i} className="h-4 w-full" />
                  ))}
                </div>

                {/* Table Rows */}
                {Array.from({ length: 5 }).map((_, i) => (
                  <div key={i} className="grid grid-cols-9 gap-4 py-3 border-b border-border/50">
                    {Array.from({ length: 9 }).map((_, j) => (
                      <Skeleton key={j} className="h-4 w-full" />
                    ))}
                  </div>
                ))}
              </div>

              {/* Pagination Skeleton */}
              <div className="mt-6 flex items-center justify-between">
                <Skeleton className="h-4 w-32" />
                <div className="flex gap-2">
                  <Skeleton className="h-9 w-9" />
                  <Skeleton className="h-9 w-9" />
                  <Skeleton className="h-9 w-9" />
                </div>
              </div>
            </div>
          </div>
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
        <div className="mb-6 rounded-lg border-2 border-border/80 bg-muted/30 p-4 shadow-sm">
          <div className="mb-4">
            <h3 className="text-sm font-semibold text-foreground">Filters</h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              Refine your search to find specific referrals
            </p>
          </div>
          <div className="space-y-4">
            {/* First row of filters */}
            <div className="grid grid-cols-1 gap-4 md:grid-cols-5">
              <div className="space-y-2">
                <Label htmlFor="search" className="text-sm font-medium text-foreground">
                  Search
                </Label>
                <Input
                  id="search"
                  placeholder="Student name..."
                  value={filters.search}
                  onChange={(e) => handleFilterChange('search', e.target.value)}
                  className="bg-background"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="status" className="text-sm font-medium text-foreground">
                  Status
                </Label>
                <Select
                  value={filters.status}
                  onValueChange={(value) => handleFilterChange('status', value)}
                >
                  <SelectTrigger id="status" className="bg-background">
                    <SelectValue placeholder="All" />
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
              <div className="space-y-2">
                <Label htmlFor="type" className="text-sm font-medium text-foreground">
                  Type
                </Label>
                <Select
                  value={filters.type}
                  onValueChange={(value) => handleFilterChange('type', value)}
                >
                  <SelectTrigger id="type" className="bg-background">
                    <SelectValue placeholder="All" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value=" ">All Types</SelectItem>
                    <SelectItem value="Behavior">Behavior</SelectItem>
                    <SelectItem value="Support">Support</SelectItem>
                    <SelectItem value="Academic">Academic</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {isAdmin && (
                <div className="space-y-2">
                  <Label htmlFor="assigned-admin" className="text-sm font-medium text-foreground">
                    Assigned Admin
                  </Label>
                  <Select
                    value={filters.assigned_admin_id}
                    onValueChange={(value) => {
                      setMyReferralsOnly(false)
                      handleFilterChange('assigned_admin_id', value)
                    }}
                    disabled={myReferralsOnly}
                  >
                    <SelectTrigger id="assigned-admin" className="bg-background">
                      <SelectValue placeholder="All" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value=" ">All Administrators</SelectItem>
                      {admins
                        .filter((admin) => admin.user_id)
                        .map((admin) => (
                          <SelectItem key={admin.user_id} value={admin.user_id!}>
                            {admin.full_name || admin.email || 'Unknown'}
                          </SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
              <div className="flex items-end">
                <div className="flex items-center space-x-2 rounded-md border-2 border-border/60 bg-background px-3 py-2 h-9 shadow-sm">
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
                    className="text-sm font-medium leading-none cursor-pointer peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                  >
                    Include archived
                  </label>
                </div>
              </div>
            </div>
            {/* Second row of filters */}
            <div className="grid grid-cols-1 gap-4 md:grid-cols-5">
              <div className="space-y-2">
                <Label htmlFor="grade" className="text-sm font-medium text-foreground">
                  Grade
                </Label>
                <Select
                  value={filters.grade}
                  onValueChange={(value) => handleFilterChange('grade', value)}
                >
                  <SelectTrigger id="grade" className="bg-background">
                    <SelectValue placeholder="All" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value=" ">All Grades</SelectItem>
                    {uniqueGrades.map((grade) => (
                      <SelectItem key={grade} value={grade}>
                        {grade}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="location" className="text-sm font-medium text-foreground">
                  Location
                </Label>
                <Select
                  value={filters.location}
                  onValueChange={(value) => handleFilterChange('location', value)}
                >
                  <SelectTrigger id="location" className="bg-background">
                    <SelectValue placeholder="All" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value=" ">All Locations</SelectItem>
                    {config?.locations?.options?.map((location) => (
                      <SelectItem key={location} value={location}>
                        {location}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="date-start" className="text-sm font-medium text-foreground">
                  Created after
                </Label>
                <Input
                  id="date-start"
                  type="date"
                  value={dateRange.start}
                  onChange={(e) => handleDateRangeChange('start', e.target.value)}
                  className="bg-background"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="date-end" className="text-sm font-medium text-foreground">
                  Created before
                </Label>
                <Input
                  id="date-end"
                  type="date"
                  value={dateRange.end}
                  onChange={(e) => handleDateRangeChange('end', e.target.value)}
                  className="bg-background"
                />
              </div>
              {isAdmin && (
                <div className="flex items-end">
                  <div className="flex items-center space-x-2 rounded-md border-2 border-border/60 bg-background px-3 py-2 h-9 shadow-sm">
                    <Checkbox
                      id="my-referrals"
                      checked={myReferralsOnly}
                      onCheckedChange={(checked) => {
                        setMyReferralsOnly(checked === true)
                        if (checked) {
                          handleFilterChange('assigned_admin_id', '')
                        }
                        setPage(1)
                      }}
                    />
                    <label
                      htmlFor="my-referrals"
                      className="text-sm font-medium leading-none cursor-pointer peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                    >
                      My Referrals
                    </label>
                  </div>
                </div>
              )}
            </div>
            {/* Clear filters button */}
            {hasActiveFilters && (
              <div className="flex justify-end pt-2 border-t border-border/60">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleClearFilters}
                  className="gap-2"
                >
                  <X className="h-4 w-4" />
                  Clear filters
                </Button>
              </div>
            )}
          </div>
        </div>

        {/* Table */}
        <div className="rounded-lg border-2 border-border/80 bg-background shadow-sm">
          {referrals.length === 0 ? (
            <div className="py-12 text-center text-muted-foreground">
              No referrals found
            </div>
          ) : (
            <>
              <div className="rounded-md">
                <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Student</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead>Author</TableHead>
                    {isAdmin && <TableHead>Assigned Admin</TableHead>}
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
                      {isAdmin && (
                        <TableCell className="text-sm">
                          {referral.assigned_admin_name || 'Unassigned'}
                        </TableCell>
                      )}
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
                <div className="mt-4 flex items-center justify-between border-t border-border/60 px-4 py-3">
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
        </div>
      </CardContent>
    </Card>
  )
}

