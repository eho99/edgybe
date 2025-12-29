'use client'

import { useState } from 'react'
import { useReferral, downloadReferralPDF, archiveReferral, unarchiveReferral, updateReferral } from '@/hooks/useReferrals'
import { useOrganizationAdmins } from '@/hooks/useOrganizationMembers'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Loader } from '@/components/ui/loader'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { InterventionForm } from './InterventionForm'
import { EmailReferralModal } from './EmailReferralModal'
import { useToast } from '@/hooks/useToast'
import { useErrorHandler } from '@/hooks/useErrorHandler'
import { Download, Mail, Plus, Edit, Archive, ArchiveRestore, UserCheck } from 'lucide-react'

interface ReferralDetailProps {
  orgId: string
  referralId: string
}

const STATUS_COLORS: Record<string, 'default' | 'warning' | 'success' | 'destructive'> = {
  DRAFT: 'default',
  SUBMITTED: 'warning',
  REVIEW: 'warning',
  CLOSED: 'success',
}

const INTERVENTION_STATUS_COLORS: Record<string, 'default' | 'warning' | 'success'> = {
  PLANNED: 'default',
  IN_PROGRESS: 'warning',
  COMPLETED: 'success',
}

export function ReferralDetail({ orgId, referralId }: ReferralDetailProps) {
  const { referral, isLoading, mutate } = useReferral(orgId, referralId)
  const { toast } = useToast()
  const { handleError } = useErrorHandler()

  const [showAddIntervention, setShowAddIntervention] = useState(false)
  const [editingIntervention, setEditingIntervention] = useState<string | null>(null)
  const [showEmailModal, setShowEmailModal] = useState(false)
  const [downloadingPDF, setDownloadingPDF] = useState(false)
  const [updatingAssignment, setUpdatingAssignment] = useState(false)
  
  const { admins } = useOrganizationAdmins(orgId)

  const handleDownloadPDF = async () => {
    setDownloadingPDF(true)
    try {
      const blob = await downloadReferralPDF(orgId, referralId)
      
      // Create download link
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `referral-${referralId}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      toast({
        variant: 'success',
        title: 'PDF Downloaded',
        description: 'The referral PDF has been downloaded',
      })
    } catch (err) {
      handleError(err, { title: 'Failed to download PDF' })
    } finally {
      setDownloadingPDF(false)
    }
  }

  const handleArchive = async () => {
    try {
      await archiveReferral(orgId, referralId)
      toast({
        variant: 'success',
        title: 'Referral Archived',
        description: 'The referral has been archived successfully',
      })
      mutate() // Refresh the referral data
    } catch (err) {
      handleError(err, { title: 'Failed to archive referral' })
    }
  }

  const handleUnarchive = async () => {
    try {
      await unarchiveReferral(orgId, referralId)
      toast({
        variant: 'success',
        title: 'Referral Unarchived',
        description: 'The referral has been restored successfully',
      })
      mutate() // Refresh the referral data
    } catch (err) {
      handleError(err, { title: 'Failed to unarchive referral' })
    }
  }

  const handleAssignmentChange = async (adminId: string | null) => {
    setUpdatingAssignment(true)
    try {
      await updateReferral(orgId, referralId, {
        assigned_admin_id: adminId,
      })
      toast({
        variant: 'success',
        title: 'Assignment Updated',
        description: adminId 
          ? 'Admin assignment has been updated successfully'
          : 'Admin assignment has been removed',
      })
      mutate() // Refresh the referral data
    } catch (err) {
      handleError(err, { title: 'Failed to update assignment' })
    } finally {
      setUpdatingAssignment(false)
    }
  }

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader />
      </div>
    )
  }

  if (!referral) {
    return (
      <Card>
        <CardContent className="py-12 text-center text-muted-foreground">
          Referral not found
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header with Actions */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2">
                <CardTitle className="text-2xl">
                  Referral for {referral.student_name}
                </CardTitle>
                {referral.archived && (
                  <Badge variant="outline">Archived</Badge>
                )}
              </div>
              <CardDescription>
                Created {formatDate(referral.created_at)} by {referral.author_name}
                {referral.archived_at && (
                  <> • Archived {formatDate(referral.archived_at)}</>
                )}
              </CardDescription>
            </div>
            <div className="flex gap-2">
              {/* Admin Assignment */}
              <div className="flex items-center gap-2">
                <Select
                  value={referral.assigned_admin_id || 'none'}
                  onValueChange={(value) => 
                    handleAssignmentChange(value === 'none' ? null : value)
                  }
                  disabled={updatingAssignment}
                >
                  <SelectTrigger className="w-[200px]">
                    <SelectValue placeholder="Assign admin">
                      {referral.assigned_admin_name 
                        ? `Assigned: ${referral.assigned_admin_name}`
                        : 'Assign Admin'}
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Not assigned</SelectItem>
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
              {referral.archived ? (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleUnarchive}
                >
                  <ArchiveRestore className="mr-2 h-4 w-4" />
                  Unarchive
                </Button>
              ) : (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleArchive}
                >
                  <Archive className="mr-2 h-4 w-4" />
                  Archive
                </Button>
              )}
              <Button
                variant="outline"
                size="sm"
                onClick={handleDownloadPDF}
                disabled={downloadingPDF}
              >
                <Download className="mr-2 h-4 w-4" />
                {downloadingPDF ? 'Downloading...' : 'PDF'}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowEmailModal(true)}
              >
                <Mail className="mr-2 h-4 w-4" />
                Email
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Student Information */}
      <Card>
        <CardHeader>
          <CardTitle>Student Information</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-2 gap-4">
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Name</dt>
              <dd className="mt-1 text-sm">{referral.student_name}</dd>
            </div>
            {referral.student_student_id && (
              <div>
                <dt className="text-sm font-medium text-muted-foreground">Student ID</dt>
                <dd className="mt-1 text-sm">{referral.student_student_id}</dd>
              </div>
            )}
            {referral.student_grade_level && (
              <div>
                <dt className="text-sm font-medium text-muted-foreground">Grade Level</dt>
                <dd className="mt-1 text-sm">{referral.student_grade_level}</dd>
              </div>
            )}
          </dl>
        </CardContent>
      </Card>

      {/* Incident Details */}
      <Card>
        <CardHeader>
          <CardTitle>Incident Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Status</dt>
              <dd className="mt-1">
                <Badge variant={STATUS_COLORS[referral.status] || 'default'}>
                  {referral.status}
                </Badge>
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Type</dt>
              <dd className="mt-1 text-sm">{referral.type}</dd>
            </div>
            {referral.location && (
              <div>
                <dt className="text-sm font-medium text-muted-foreground">Location</dt>
                <dd className="mt-1 text-sm">{referral.location}</dd>
              </div>
            )}
            {referral.time_of_day && (
              <div>
                <dt className="text-sm font-medium text-muted-foreground">Time of Day</dt>
                <dd className="mt-1 text-sm">{referral.time_of_day}</dd>
              </div>
            )}
          </div>

          {referral.behaviors && referral.behaviors.length > 0 && (
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Behaviors</dt>
              <dd className="mt-2 flex flex-wrap gap-2">
                {referral.behaviors.map((behavior) => (
                  <Badge key={behavior} variant="outline">
                    {behavior}
                  </Badge>
                ))}
              </dd>
            </div>
          )}

          {referral.description && (
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Description</dt>
              <dd className="mt-2 rounded-md border bg-muted/50 p-4 text-sm">
                {referral.description}
              </dd>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Interventions */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Interventions</CardTitle>
            <Button
              size="sm"
              onClick={() => setShowAddIntervention(true)}
              disabled={showAddIntervention}
            >
              <Plus className="mr-2 h-4 w-4" />
              Add Intervention
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {showAddIntervention && (
            <div className="rounded-lg border bg-muted/50 p-4">
              <InterventionForm
                orgId={orgId}
                referralId={referralId}
                onSuccess={() => {
                  setShowAddIntervention(false)
                  mutate()
                }}
                onCancel={() => setShowAddIntervention(false)}
              />
            </div>
          )}

          {referral.interventions.length === 0 && !showAddIntervention ? (
            <div className="py-8 text-center text-muted-foreground">
              No interventions yet
            </div>
          ) : (
            <div className="space-y-3">
              {referral.interventions.map((intervention) => (
                <div
                  key={intervention.id}
                  className="rounded-lg border p-4"
                >
                  {editingIntervention === intervention.id ? (
                    <InterventionForm
                      orgId={orgId}
                      referralId={referralId}
                      intervention={intervention}
                      onSuccess={() => {
                        setEditingIntervention(null)
                        mutate()
                      }}
                      onCancel={() => setEditingIntervention(null)}
                    />
                  ) : (
                    <>
                      <div className="flex items-start justify-between">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <h4 className="font-medium">{intervention.title}</h4>
                            <Badge
                              variant={
                                INTERVENTION_STATUS_COLORS[intervention.status] ||
                                'default'
                              }
                              className="text-xs"
                            >
                              {intervention.status}
                            </Badge>
                          </div>
                          {intervention.description && (
                            <p className="text-sm text-muted-foreground">
                              {intervention.description}
                            </p>
                          )}
                          <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            <span>
                              Created by {intervention.creator_name || 'Unknown'}
                            </span>
                            <span>{formatDate(intervention.created_at)}</span>
                            {intervention.completed_at && (
                              <span>Completed {formatDate(intervention.completed_at)}</span>
                            )}
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setEditingIntervention(intervention.id)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                      </div>
                    </>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Email Modal */}
      {showEmailModal && (
        <EmailReferralModal
          orgId={orgId}
          referralId={referralId}
          studentId={referral.student_id}
          onClose={() => setShowEmailModal(false)}
        />
      )}
    </div>
  )
}

