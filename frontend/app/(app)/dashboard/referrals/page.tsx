'use client'

import Link from 'next/link'
import { ReferralList } from '@/components/ui/ReferralList'
import { Button } from '@/components/ui/button'
import { useCurrentUserRole } from '@/hooks/useCurrentUserRole'
import { PageSkeletonLoader } from '@/components/ui/page-skeleton-loader'
import { ErrorDisplay } from '@/components/error/ErrorDisplay'
import { Plus, Settings } from 'lucide-react'

export default function ReferralsPage() {
  const { orgId, isAdmin, isLoading, error } = useCurrentUserRole()

  if (isLoading) {
    return <PageSkeletonLoader contentType="list" />
  }

  if (error) {
    return (
      <ErrorDisplay
        error={error instanceof Error ? error : new Error('Failed to load referrals')}
        title="Failed to load referrals"
      />
    )
  }

  if (!orgId) {
    return (
      <ErrorDisplay
        error={new Error('No organization found')}
        title="Organization Required"
      />
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Referrals</h1>
          <p className="text-muted-foreground">
            Manage student behavioral and supportive referrals
          </p>
        </div>
        <div className="flex gap-2">
          {isAdmin && (
            <Link href="/dashboard/referrals/templates">
              <Button variant="outline">
                <Settings className="mr-2 h-4 w-4" />
                Email Templates
              </Button>
            </Link>
          )}
          <Link href="/dashboard/referrals/create">
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Create Referral
            </Button>
          </Link>
        </div>
      </div>

      {/* Referrals List */}
      <ReferralList orgId={orgId} basePath="/dashboard/referrals" />
    </div>
  )
}

