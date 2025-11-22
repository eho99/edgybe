'use client'

import { useState, useEffect } from 'react'
import { sendReferralEmail, useEmailTemplates } from '@/hooks/useReferrals'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { useToast } from '@/hooks/useToast'
import { useErrorHandler } from '@/hooks/useErrorHandler'
import apiClient from '@/lib/apiClient'
import { X, ChevronDown, ChevronUp } from 'lucide-react'
import { VariableInserter } from './VariableInserter'

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
  const { templates } = useEmailTemplates(orgId, { type: 'referral' })

  const [guardians, setGuardians] = useState<GuardianInfo[]>([])
  const [loadingGuardians, setLoadingGuardians] = useState(true)
  const [selectedEmails, setSelectedEmails] = useState<string[]>([])
  const [customEmail, setCustomEmail] = useState('')
  const [subject, setSubject] = useState('')
  const [message, setMessage] = useState('')
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>('none')
  const [isSending, setIsSending] = useState(false)
  const [activeField, setActiveField] = useState<'subject' | 'message'>('message')
  const [showVariables, setShowVariables] = useState(false)

  // Fetch guardians for the student
  useEffect(() => {
    async function fetchGuardians() {
      try {
        const response = await apiClient<{ guardians: { guardian: GuardianInfo, guardian_email?: string }[] }>(
          `/api/v1/organizations/${orgId}/students/${studentId}/guardians`
        )
        
        const guardiansList = response.guardians
          .map((g) => ({
            ...g.guardian,
            email: g.guardian_email || undefined
          }))
          .filter((g): g is GuardianInfo => !!g.email) // Only include guardians with email

        setGuardians(guardiansList)
        // Pre-select all guardians by default? Maybe better to let user choose.
      } catch (err) {
        handleError(err, { title: 'Failed to load guardians' })
      } finally {
        setLoadingGuardians(false)
      }
    }
    fetchGuardians()
  }, [orgId, studentId])

  // Load template when selected
  useEffect(() => {
    if (selectedTemplateId && selectedTemplateId !== 'none') {
      const template = templates.find(t => t.id === selectedTemplateId)
      if (template) {
        setSubject(template.subject_template)
        setMessage(template.body_template)
      }
    }
  }, [selectedTemplateId, templates])

  const toggleEmail = (email: string) => {
    setSelectedEmails((prev) =>
      prev.includes(email) ? prev.filter((e) => e !== email) : [...prev, email]
    )
  }

  const handleAddCustomEmail = () => {
    if (customEmail && !selectedEmails.includes(customEmail)) {
      // Basic email validation
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(customEmail)) {
        toast({ title: 'Invalid email address', variant: 'destructive' })
        return
      }
      setSelectedEmails((prev) => [...prev, customEmail])
      setCustomEmail('')
    }
  }

  const handleInsertVariable = (value: string) => {
    if (activeField === 'subject') {
      setSubject(prev => prev + value)
    } else {
      setMessage(prev => prev + value)
    }
  }

  const handleSubmit = async () => {
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
        template_id: selectedTemplateId !== 'none' ? selectedTemplateId : undefined
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
    <Dialog open={true} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Email Referral Report</DialogTitle>
          <DialogDescription>
            Send the referral report PDF via email. You can use a template or write a custom message.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-6 py-4 md:grid-cols-2">
          {/* Left Column: Recipients & Template Selection */}
          <div className="space-y-6">
            <div className="space-y-3">
              <Label>Recipients</Label>
              {loadingGuardians ? (
                <div className="py-4 text-center text-muted-foreground text-sm">
                  Loading guardians...
                </div>
              ) : (
                <div className="space-y-2 rounded-md border p-3 max-h-[150px] overflow-y-auto">
                  {guardians.length === 0 ? (
                    <p className="text-sm text-muted-foreground">
                      No guardians with email addresses found for this student.
                    </p>
                  ) : (
                    guardians.map((guardian) => (
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
                    ))
                  )}
                </div>
              )}
            </div>

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

            <div className="space-y-2">
              <Label>Template (Optional)</Label>
              <Select value={selectedTemplateId} onValueChange={setSelectedTemplateId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a template" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No Template (Custom)</SelectItem>
                  {templates.map((template) => (
                    <SelectItem key={template.id} value={template.id}>
                      {template.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Right Column: Email Content */}
          <div className="space-y-4">
            <div className="space-y-2 rounded-md border p-4 bg-muted/10">
                <div className="flex items-center justify-between">
                    <Label>Variable Inserter</Label>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={() => setShowVariables(!showVariables)}
                      type="button"
                    >
                      {showVariables ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </Button>
                </div>
                
                {showVariables && (
                    <div className="pt-2">
                        <p className="text-xs text-muted-foreground mb-2">
                            Click to insert variable into <strong>{activeField === 'subject' ? 'Subject' : 'Message'}</strong>.
                        </p>
                        <VariableInserter orgId={orgId} onInsert={handleInsertVariable} />
                    </div>
                )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="subject">Subject</Label>
              <Input
                id="subject"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                onFocus={() => setActiveField('subject')}
                placeholder="Referral Report"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="message">Message</Label>
              <Textarea
                id="message"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onFocus={() => setActiveField('message')}
                className="min-h-[200px] font-mono"
                placeholder="Please find attached..."
              />
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={onClose} disabled={isSending}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={isSending || selectedEmails.length === 0}>
            {isSending ? 'Sending...' : 'Send Email'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
