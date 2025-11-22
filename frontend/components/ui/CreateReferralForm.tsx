'use client'

import { useState, useEffect } from 'react'
import { useReferralConfig, createReferral, type ReferralCreatePayload } from '@/hooks/useReferrals'
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

interface CreateReferralFormProps {
  orgId: string
  onSuccess?: (referralId: string) => void
}

export function CreateReferralForm({ orgId, onSuccess }: CreateReferralFormProps) {
  const { config, isLoading: configLoading } = useReferralConfig(orgId)
  const { toast } = useToast()
  const { handleError } = useErrorHandler()

  const [isSubmitting, setIsSubmitting] = useState(false)

  // Form state
  const [formData, setFormData] = useState({
    student_id: '',
    type: '',
    location: '',
    location_custom: '',
    time_of_day: '',
    time_of_day_custom: '',
    behaviors: [] as string[],
    description: '',
  })


  const handleBehaviorToggle = (behavior: string) => {
    setFormData((prev) => ({
      ...prev,
      behaviors: prev.behaviors.includes(behavior)
        ? prev.behaviors.filter((b) => b !== behavior)
        : [...prev.behaviors, behavior],
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
      setFormData({
        student_id: '',
        type: '',
        location: '',
        location_custom: '',
        time_of_day: '',
        time_of_day_custom: '',
        behaviors: [],
        description: '',
      })

      onSuccess?.(result.id)
    } catch (err) {
      handleError(err, { title: 'Failed to create referral' })
    } finally {
      setIsSubmitting(false)
    }
  }

  if (configLoading) {
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
  const hasEmptyConfig = 
    (!config.types || config.types.length === 0) &&
    (!config.locations?.options || config.locations.options.length === 0) &&
    (!config.time_of_day?.options || config.time_of_day.options.length === 0) &&
    (!config.behaviors?.options || config.behaviors.options.length === 0)

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

  return (
    <Card>
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
            <Label htmlFor="location">Location</Label>
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
                {config.locations?.options && config.locations.options.length > 0 ? (
                  config.locations.options.map((location) => (
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
            <Label htmlFor="time_of_day">Time of Day</Label>
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
                {config.time_of_day?.options && config.time_of_day.options.length > 0 ? (
                  config.time_of_day.options.map((time) => (
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
            <Label>Behaviors Observed</Label>
            <div className="grid grid-cols-2 gap-3">
              {config.behaviors?.options && config.behaviors.options.length > 0 ? (
                config.behaviors.options.map((behavior) => (
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
              onClick={onSuccess}
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
  )
}

