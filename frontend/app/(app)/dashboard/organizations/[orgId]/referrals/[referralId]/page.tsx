'use client'

import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { ReferralDetail } from '@/components/ui/ReferralDetail'
import { Button } from '@/components/ui/button'
import { ArrowLeft } from 'lucide-react'

export default function ReferralDetailPage() {
  const params = useParams()
  const router = useRouter()
  const orgId = params?.orgId as string
  const referralId = params?.referralId as string

  return (
    <div className="space-y-6">
      {/* Header with Back Button */}
      <div className="flex items-center gap-4">
        <Link href={`/dashboard/organizations/${orgId}/referrals`}>
          <Button variant="ghost" size="sm">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Referrals
          </Button>
        </Link>
      </div>

      {/* Referral Detail Component */}
      <ReferralDetail orgId={orgId} referralId={referralId} />
    </div>
  )
}

