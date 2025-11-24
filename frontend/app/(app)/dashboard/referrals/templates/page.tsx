'use client'

import Link from 'next/link'
import { EmailTemplateList } from '@/components/ui/EmailTemplateList'
import { useCurrentUserRole } from '@/hooks/useCurrentUserRole'
import { PageLoader } from '@/components/ui/page-loader'
import { ErrorDisplay } from '@/components/error/ErrorDisplay'
import { Button } from '@/components/ui/button'
import { ArrowLeft } from 'lucide-react'

export default function EmailTemplatesPage() {
  const { orgId, isAdmin, isLoading, error } = useCurrentUserRole()

  if (isLoading) {
    return <PageLoader text="Loading templates..." />
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
          <h1 className="text-3xl font-bold tracking-tight">Email Templates</h1>
          <p className="text-muted-foreground">
            Configure email templates for notifications
          </p>
        </div>
      </div>

      {/* Template List */}
      <EmailTemplateList orgId={orgId} isAdmin={isAdmin} />
    </div>
  )
}




