'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  useReferralConfig,
  createReferral,
  type ReferralCreatePayload,
  type ReferralFieldConfig,
  type ReferralFieldSelection,
} from '@/hooks/useReferrals'
import { useOrganization, type Disclaimers } from '@/hooks/useOrganizations'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { useToast } from '@/hooks/useToast'
import { useErrorHandler } from '@/hooks/useErrorHandler'
import { Loader } from '@/components/ui/loader'
import { StudentSearchSelect } from '@/components/ui/StudentSearchSelect'
import { DisclaimerModal } from '@/components/ui/DisclaimerModal'

interface CreateReferralFormProps {
  orgId: string
  onSuccess?: (referralId: string) => void
  onCancel?: () => void
}

type ReferralFormState = {
  student_id: string
  type: string
  location: string
  location_custom: string
  time_of_day: string
  time_of_day_custom: string
  behaviors: string[]
  description: string
}

const createEmptyFormState = (): ReferralFormState => ({
  student_id: '',
  type: '',
  location: '',
  location_custom: '',
  time_of_day: '',
  time_of_day_custom: '',
  behaviors: [],
  description: '',
})

type NormalizedFieldConfig = {
  label: string
  helpText?: string
  required: boolean
  selection: ReferralFieldSelection
  options: string[]
}

const normalizeFieldConfig = (
  field: ReferralFieldConfig | undefined,
  fallback: { label: string; selection?: ReferralFieldSelection }
): NormalizedFieldConfig => {
  const rawOptions = Array.isArray(field?.options) ? field?.options ?? [] : []
  const options = rawOptions.filter((option): option is string => typeof option === 'string')
  return {
    label: field?.label ?? fallback.label,
    helpText: typeof field?.helpText === 'string' ? field.helpText : undefined,
    required: Boolean(field?.required),
    selection: field?.selection === 'multi' ? 'multi' : fallback.selection ?? 'single',
    options,
  }
}

type DisclaimerKey = 'general' | 'self_harm' | 'child_abuse'

const DISCLAIMER_TITLES: Record<DisclaimerKey, string> = {
  general: 'Important Notice',
  self_harm: 'Self-Harm Disclaimer',
  child_abuse: 'Child Abuse Disclaimer',
}

// Normalize behavior name to match disclaimer keys
// "Self-Harm" -> "self_harm", "Child Abuse" -> "child_abuse"
const normalizeToDisclaimerKey = (behavior: string): DisclaimerKey | null => {
  const normalized = behavior.toLowerCase().replace(/[\s-]+/g, '_')
  if (normalized.includes('self_harm')) return 'self_harm'
  if (normalized.includes('child_abuse')) return 'child_abuse'
  return null
}

export function CreateReferralForm({ orgId, onSuccess, onCancel }: CreateReferralFormProps) {
  const { config, isLoading: configLoading } = useReferralConfig(orgId)
  const { organization, isLoading: orgLoading } = useOrganization(orgId)
  const { toast } = useToast()
  const { handleError } = useErrorHandler()

  const [isSubmitting, setIsSubmitting] = useState(false)

  // Form state
  const [formData, setFormData] = useState<ReferralFormState>(createEmptyFormState)

  // Disclaimer state
  const [acknowledgedDisclaimers, setAcknowledgedDisclaimers] = useState<Set<DisclaimerKey>>(new Set())
  const [pendingDisclaimer, setPendingDisclaimer] = useState<DisclaimerKey | null>(null)
  const [pendingBehavior, setPendingBehavior] = useState<string | null>(null)

  // Get typed disclaimers from organization
  const disclaimers: Disclaimers = (organization?.disclaimers as Disclaimers) ?? {}

  // Show general disclaimer on mount if it exists and hasn't been acknowledged
  useEffect(() => {
    if (!orgLoading && disclaimers.general && !acknowledgedDisclaimers.has('general')) {
      setPendingDisclaimer('general')
    }
  }, [orgLoading, disclaimers.general, acknowledgedDisclaimers])

  const handleDisclaimerAcknowledge = useCallback(() => {
    if (pendingDisclaimer) {
      setAcknowledgedDisclaimers((prev) => new Set(prev).add(pendingDisclaimer))
      
      // If acknowledging a behavior-specific disclaimer, add the behavior to form
      if (pendingBehavior && pendingDisclaimer !== 'general') {
        setFormData((prev) => ({
          ...prev,
          behaviors: [...prev.behaviors, pendingBehavior],
        }))
      }
      
      setPendingDisclaimer(null)
      setPendingBehavior(null)
    }
  }, [pendingDisclaimer, pendingBehavior])

  const resetForm = () => {
    setFormData(createEmptyFormState())
    // Keep general disclaimer acknowledged, but reset behavior-specific ones
    setAcknowledgedDisclaimers((prev) => {
      const newSet = new Set<DisclaimerKey>()
      if (prev.has('general')) newSet.add('general')
      return newSet
    })
  }

  const handleBehaviorToggle = (behavior: string) => {
    const isAdding = !formData.behaviors.includes(behavior)
    
    if (isAdding) {
      // Check if this behavior requires a disclaimer
      const disclaimerKey = normalizeToDisclaimerKey(behavior)
      
      if (disclaimerKey && disclaimers[disclaimerKey] && !acknowledgedDisclaimers.has(disclaimerKey)) {
        // Show disclaimer modal before adding the behavior
        setPendingDisclaimer(disclaimerKey)
        setPendingBehavior(behavior)
        return
      }
    }
    
    // No disclaimer needed or removing behavior
    setFormData((prev) => ({
      ...prev,
      behaviors: isAdding
        ? [...prev.behaviors, behavior]
        : prev.behaviors.filter((b) => b !== behavior),
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      // Validate required fields
      if (!formData.student_id) {
        toast({
          variant: 'destructive',
          title: 'Validation error',
          description: 'Please select a student',
        })
        setIsSubmitting(false)
        return
      }

      if (!formData.type) {
        toast({
          variant: 'destructive',
          title: 'Validation error',
          description: 'Please select a referral type',
        })
        setIsSubmitting(false)
        return
      }

      // Prepare payload
      const payload: ReferralCreatePayload = {
        student_id: formData.student_id,
        type: formData.type,
        description: formData.description || undefined,
      }

      // Handle location (use custom if "Other" selected)
      if (formData.location === 'Other') {
        payload.location = formData.location_custom
      } else if (formData.location) {
        payload.location = formData.location
      }

      // Handle time_of_day (use custom if "Other" selected)
      if (formData.time_of_day === 'Other') {
        payload.time_of_day = formData.time_of_day_custom
      } else if (formData.time_of_day) {
        payload.time_of_day = formData.time_of_day
      }

      // Add behaviors if any selected
      if (formData.behaviors.length > 0) {
        payload.behaviors = formData.behaviors
      }

      // Create referral
      const result = await createReferral(orgId, payload)

      toast({
        variant: 'success',
        title: 'Referral created',
        description: 'The referral has been created successfully',
      })

      // Reset form
      resetForm()

      onSuccess?.(result.id)
    } catch (err) {
      handleError(err, { title: 'Failed to create referral' })
    } finally {
      setIsSubmitting(false)
    }
  }

  if (configLoading || orgLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <Loader />
        </CardContent>
      </Card>
    )
  }

  if (!config) {
    return (
      <Card>
        <CardContent className="py-12">
          <p className="text-center text-muted-foreground">
            Referral configuration not found for this organization
          </p>
        </CardContent>
      </Card>
    )
  }

  // Check if config has empty arrays (config loaded but no data)
  const locationField = normalizeFieldConfig(config.locations, { label: 'Location' })
  const timeOfDayField = normalizeFieldConfig(config.time_of_day, { label: 'Time of Day' })
  const behaviorsField = normalizeFieldConfig(config.behaviors, { label: 'Behaviors Observed', selection: 'multi' })

  const hasEmptyConfig =
    (!config.types || config.types.length === 0) &&
    (locationField.options.length === 0) &&
    (timeOfDayField.options.length === 0) &&
    (behaviorsField.options.length === 0)

  if (hasEmptyConfig) {
    return (
      <Card>
        <CardContent className="py-12">
          <p className="text-center text-muted-foreground">
            Referral configuration is empty. Please configure referral types, locations, time of day, and behaviors in organization settings.
          </p>
        </CardContent>
      </Card>
    )
  }

  // Check if general disclaimer is required but not yet acknowledged (blocks form access)
  const isBlocked = disclaimers.general && !acknowledgedDisclaimers.has('general')

  return (
    <>
      {/* Disclaimer Modal */}
      {pendingDisclaimer && disclaimers[pendingDisclaimer] && (
        <DisclaimerModal
          open={true}
          title={DISCLAIMER_TITLES[pendingDisclaimer]}
          content={disclaimers[pendingDisclaimer]!}
          onAcknowledge={handleDisclaimerAcknowledge}
        />
      )}

      <Card className={isBlocked ? 'pointer-events-none opacity-50' : ''}>
      <CardHeader>
        <CardTitle>Create Student Referral</CardTitle>
        <CardDescription>
          Document a behavioral or supportive incident for a student
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Student Selection */}
          <StudentSearchSelect
            orgId={orgId}
            value={formData.student_id}
            onValueChange={(value) =>
              setFormData((prev) => ({ ...prev, student_id: value }))
            }
            label="Student"
            required
          />

          {/* Referral Type */}
          <div className="space-y-2">
            <Label htmlFor="type">Referral Type *</Label>
            <Select
              value={formData.type}
              onValueChange={(value) =>
                setFormData((prev) => ({ ...prev, type: value }))
              }
            >
              <SelectTrigger id="type">
                <SelectValue placeholder="Select referral type" />
              </SelectTrigger>
              <SelectContent>
                {config.types.map((type) => (
                  <SelectItem key={type} value={type}>
                    {type}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Location */}
          <div className="space-y-2">
            <div>
              <Label htmlFor="location">
                {locationField.label}
                {locationField.required ? ' *' : ''}
              </Label>
              {locationField.helpText && (
                <p className="text-sm text-muted-foreground">{locationField.helpText}</p>
              )}
            </div>
            <Select
              value={formData.location}
              onValueChange={(value) =>
                setFormData((prev) => ({
                  ...prev,
                  location: value,
                  location_custom: value === 'Other' ? prev.location_custom : '',
                }))
              }
            >
              <SelectTrigger id="location">
                <SelectValue placeholder="Select location" />
              </SelectTrigger>
              <SelectContent>
                {locationField.options.length > 0 ? (
                  locationField.options.map((location) => (
                    <SelectItem key={location} value={location}>
                      {location}
                    </SelectItem>
                  ))
                ) : (
                  <div className="px-2 py-1 text-sm text-muted-foreground">
                    No locations available
                  </div>
                )}
              </SelectContent>
            </Select>
              {formData.location === 'Other' && (
              <Input
                placeholder="Specify location"
                value={formData.location_custom}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, location_custom: e.target.value }))
                }
                className="mt-2"
              />
            )}
          </div>

          {/* Time of Day */}
          <div className="space-y-2">
            <div>
              <Label htmlFor="time_of_day">
                {timeOfDayField.label}
                {timeOfDayField.required ? ' *' : ''}
              </Label>
              {timeOfDayField.helpText && (
                <p className="text-sm text-muted-foreground">{timeOfDayField.helpText}</p>
              )}
            </div>
            <Select
              value={formData.time_of_day}
              onValueChange={(value) =>
                setFormData((prev) => ({
                  ...prev,
                  time_of_day: value,
                  time_of_day_custom: value === 'Other' ? prev.time_of_day_custom : '',
                }))
              }
            >
              <SelectTrigger id="time_of_day">
                <SelectValue placeholder="Select time of day" />
              </SelectTrigger>
              <SelectContent>
                {timeOfDayField.options.length > 0 ? (
                  timeOfDayField.options.map((time) => (
                    <SelectItem key={time} value={time}>
                      {time}
                    </SelectItem>
                  ))
                ) : (
                  <div className="px-2 py-1 text-sm text-muted-foreground">
                    No time of day options available
                  </div>
                )}
              </SelectContent>
            </Select>
            {formData.time_of_day === 'Other' && (
              <Input
                placeholder="Specify time"
                value={formData.time_of_day_custom}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, time_of_day_custom: e.target.value }))
                }
                className="mt-2"
              />
            )}
          </div>

          {/* Behaviors */}
          <div className="space-y-3">
            <div>
              <Label>
                {behaviorsField.label}
                {behaviorsField.required ? ' *' : ''}
              </Label>
              {behaviorsField.helpText && (
                <p className="text-sm text-muted-foreground">{behaviorsField.helpText}</p>
              )}
            </div>
            <div className="grid grid-cols-2 gap-3">
              {behaviorsField.options.length > 0 ? (
                behaviorsField.options.map((behavior) => (
                <div key={behavior} className="flex items-center space-x-2">
                  <Checkbox
                    id={`behavior-${behavior}`}
                    checked={formData.behaviors.includes(behavior)}
                    onCheckedChange={() => handleBehaviorToggle(behavior)}
                  />
                  <label
                    htmlFor={`behavior-${behavior}`}
                    className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                  >
                    {behavior}
                  </label>
                </div>
              ))
              ) : (
                <div className="col-span-2 text-sm text-muted-foreground">
                  No behaviors available
                </div>
              )}
            </div>
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <textarea
              id="description"
              value={formData.description}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, description: e.target.value }))
              }
              className="flex min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              placeholder="Provide detailed description of the incident..."
            />
          </div>

          {/* Submit Button */}
          <div className="flex justify-end gap-3">
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                if (onCancel) {
                  onCancel()
                } else {
                  resetForm()
                }
              }}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Creating...' : 'Create Referral'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
    </>
  )
}

