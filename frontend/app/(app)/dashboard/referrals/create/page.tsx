'use client'

import { useRouter } from 'next/navigation'
import { CreateReferralForm } from '@/components/ui/CreateReferralForm'
import { useCurrentUserRole } from '@/hooks/useCurrentUserRole'
import { PageLoader } from '@/components/ui/page-loader'
import { ErrorDisplay } from '@/components/error/ErrorDisplay'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { ArrowLeft } from 'lucide-react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'

export default function CreateReferralPage() {
  const router = useRouter()
  const { orgId, isLoading, error } = useCurrentUserRole()

  if (isLoading) {
    return <PageLoader text="Loading..." />
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

  const handleSuccess = (referralId: string) => {
    router.push(`/dashboard/referrals/${referralId}`)
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
          <h1 className="text-3xl font-bold tracking-tight">Create Referral</h1>
          <p className="text-muted-foreground">
            Fill out the referral intake form
          </p>
        </div>
      </div>

      {/* Form Card */}
      <Card>
        <CardHeader>
          <CardTitle>Referral Information</CardTitle>
          <CardDescription>
            Provide details about the incident or concern
          </CardDescription>
        </CardHeader>
        <CardContent>
          <CreateReferralForm
            orgId={orgId}
            onSuccess={handleSuccess}
            onCancel={() => router.push('/dashboard/referrals')}
          />
        </CardContent>
      </Card>
    </div>
  )
}

