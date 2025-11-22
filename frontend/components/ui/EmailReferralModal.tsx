'use client'

import { useState, useEffect } from 'react'
import { sendReferralEmail } from '@/hooks/useReferrals'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { useToast } from '@/hooks/useToast'
import { useErrorHandler } from '@/hooks/useErrorHandler'
import apiClient from '@/lib/apiClient'
import { X } from 'lucide-react'

interface EmailReferralModalProps {
  orgId: string
  referralId: string
  studentId: string
  onClose: () => void
}

interface GuardianInfo {
  id: string
  full_name: string
  email: string
}

export function EmailReferralModal({
  orgId,
  referralId,
  studentId,
  onClose,
}: EmailReferralModalProps) {
  const { toast } = useToast()
  const { handleError } = useErrorHandler()

  const [guardians, setGuardians] = useState<GuardianInfo[]>([])
  const [loadingGuardians, setLoadingGuardians] = useState(true)
  const [selectedEmails, setSelectedEmails] = useState<string[]>([])
  const [customEmail, setCustomEmail] = useState('')
  const [subject, setSubject] = useState('')
  const [message, setMessage] = useState('')
  const [isSending, setIsSending] = useState(false)

  // Fetch guardians for the student
  useEffect(() => {
    async function fetchGuardians() {
      try {
        const response = await apiClient<{ guardians: { guardian: GuardianInfo }[] }>(
          `/api/v1/organizations/${orgId}/students/${studentId}/guardians`
        )
        
        const guardiansList = response.guardians
          .map((g) => g.guardian)
          .filter((g) => g.email) // Only include guardians with email

        setGuardians(guardiansList)
      } catch (err) {
        handleError(err, { title: 'Failed to load guardians' })
      } finally {
        setLoadingGuardians(false)
      }
    }
    fetchGuardians()
  }, [orgId, studentId])

  const toggleEmail = (email: string) => {
    setSelectedEmails((prev) =>
      prev.includes(email) ? prev.filter((e) => e !== email) : [...prev, email]
    )
  }

  const handleAddCustomEmail = () => {
    if (customEmail && !selectedEmails.includes(customEmail)) {
      setSelectedEmails((prev) => [...prev, customEmail])
      setCustomEmail('')
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (selectedEmails.length === 0) {
      toast({
        variant: 'destructive',
        title: 'Validation error',
        description: 'Please select at least one recipient',
      })
      return
    }

    setIsSending(true)

    try {
      const result = await sendReferralEmail(orgId, referralId, {
        recipient_emails: selectedEmails,
        subject: subject || undefined,
        message: message || undefined,
      })

      if (result.success) {
        toast({
          variant: 'success',
          title: 'Email sent',
          description: result.message,
        })
        onClose()
      } else {
        toast({
          variant: 'destructive',
          title: 'Email failed',
          description: result.message,
        })
      }
    } catch (err) {
      handleError(err, { title: 'Failed to send email' })
    } finally {
      setIsSending(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="mx-4 w-full max-w-2xl rounded-lg bg-white shadow-lg">
        {/* Header */}
        <div className="flex items-center justify-between border-b p-6">
          <h2 className="text-xl font-semibold">Email Referral</h2>
          <button
            onClick={onClose}
            className="rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} className="p-6">
          <div className="space-y-6">
            {/* Guardian Emails */}
            {loadingGuardians ? (
              <div className="py-4 text-center text-muted-foreground">
                Loading guardians...
              </div>
            ) : (
              <div className="space-y-3">
                <Label>Recipients</Label>
                {guardians.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No guardians with email addresses found for this student.
                  </p>
                ) : (
                  <div className="space-y-2 rounded-md border p-3">
                    {guardians.map((guardian) => (
                      <div key={guardian.id} className="flex items-center space-x-2">
                        <Checkbox
                          id={`guardian-${guardian.id}`}
                          checked={selectedEmails.includes(guardian.email)}
                          onCheckedChange={() => toggleEmail(guardian.email)}
                        />
                        <label
                          htmlFor={`guardian-${guardian.id}`}
                          className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                        >
                          {guardian.full_name} ({guardian.email})
                        </label>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Add Custom Email */}
            <div className="space-y-2">
              <Label htmlFor="custom-email">Add Custom Email</Label>
              <div className="flex gap-2">
                <Input
                  id="custom-email"
                  type="email"
                  placeholder="email@example.com"
                  value={customEmail}
                  onChange={(e) => setCustomEmail(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault()
                      handleAddCustomEmail()
                    }
                  }}
                />
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleAddCustomEmail}
                >
                  Add
                </Button>
              </div>
              {selectedEmails.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {selectedEmails.map((email) => (
                    <div
                      key={email}
                      className="flex items-center gap-1 rounded-md bg-secondary px-2 py-1 text-sm"
                    >
                      {email}
                      <button
                        type="button"
                        onClick={() => toggleEmail(email)}
                        className="ml-1 hover:text-destructive"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Subject */}
            <div className="space-y-2">
              <Label htmlFor="subject">Subject (Optional)</Label>
              <Input
                id="subject"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="Leave blank for default subject"
              />
            </div>

            {/* Message */}
            <div className="space-y-2">
              <Label htmlFor="message">Message (Optional)</Label>
              <textarea
                id="message"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                className="flex min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                placeholder="Leave blank for default message. The referral PDF will be attached."
              />
            </div>
          </div>

          {/* Footer */}
          <div className="mt-6 flex justify-end gap-3">
            <Button type="button" variant="outline" onClick={onClose} disabled={isSending}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSending || selectedEmails.length === 0}>
              {isSending ? 'Sending...' : 'Send Email'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

