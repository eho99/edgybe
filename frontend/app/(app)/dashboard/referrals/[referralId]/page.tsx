'use client'

import { use } from 'react'
import Link from 'next/link'
import { ReferralDetail } from '@/components/ui/ReferralDetail'
import { useCurrentUserRole } from '@/hooks/useCurrentUserRole'
import { PageLoader } from '@/components/ui/page-loader'
import { ErrorDisplay } from '@/components/error/ErrorDisplay'
import { Button } from '@/components/ui/button'
import { ArrowLeft } from 'lucide-react'

interface ReferralDetailPageProps {
  params: Promise<{
    referralId: string
  }>
}

export default function ReferralDetailPage({ params }: ReferralDetailPageProps) {
  const resolvedParams = use(params)
  const { orgId, isLoading, error } = useCurrentUserRole()

  if (isLoading) {
    return <PageLoader text="Loading referral..." />
  }

  if (error) {
    return (
      <ErrorDisplay
        error={error instanceof Error ? error : new Error('Failed to load organization')}
        title="Failed to load organization"
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
      <div className="flex items-center gap-4">
        <Link href="/dashboard/referrals">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Referral Details</h1>
          <p className="text-muted-foreground">
            View and manage referral information
          </p>
        </div>
      </div>

      {/* Referral Detail Component */}
      <ReferralDetail orgId={orgId} referralId={resolvedParams.referralId} />
    </div>
  )
}

