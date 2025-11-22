'use client'

import { useState } from 'react'
import { useParams } from 'next/navigation'
import { ReferralList } from '@/components/ui/ReferralList'
import { CreateReferralForm } from '@/components/ui/CreateReferralForm'
import { Button } from '@/components/ui/button'
import { Plus, X } from 'lucide-react'

export default function ReferralsPage() {
  const params = useParams()
  const orgId = params?.orgId as string
  const [showCreateForm, setShowCreateForm] = useState(false)

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
        <Button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className={showCreateForm ? 'bg-destructive hover:bg-destructive/90' : ''}
        >
          {showCreateForm ? (
            <>
              <X className="mr-2 h-4 w-4" />
              Cancel
            </>
          ) : (
            <>
              <Plus className="mr-2 h-4 w-4" />
              Create Referral
            </>
          )}
        </Button>
      </div>

      {/* Create Form */}
      {showCreateForm && (
        <CreateReferralForm
          orgId={orgId}
          onSuccess={() => {
            setShowCreateForm(false)
            // List will auto-refresh via SWR
          }}
        />
      )}

      {/* Referrals List */}
      <ReferralList orgId={orgId} />
    </div>
  )
}

