'use client'

import { useState, useEffect } from 'react'
import { useReferralConfig, createIntervention, updateIntervention, type InterventionCreatePayload } from '@/hooks/useReferrals'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useToast } from '@/hooks/useToast'
import { useErrorHandler } from '@/hooks/useErrorHandler'
import { Loader } from '@/components/ui/loader'

interface InterventionFormProps {
  orgId: string
  referralId: string
  intervention?: {
    id: string
    title: string
    description: string | null
    status: string
    completed_at: string | null
  }
  onSuccess?: () => void
  onCancel?: () => void
}

export function InterventionForm({
  orgId,
  referralId,
  intervention,
  onSuccess,
  onCancel,
}: InterventionFormProps) {
  const { config, isLoading: configLoading } = useReferralConfig(orgId)
  const { toast } = useToast()
  const { handleError } = useErrorHandler()

  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isCustomTitle, setIsCustomTitle] = useState(false)

  // Form state
  const [formData, setFormData] = useState({
    title: intervention?.title || '',
    description: intervention?.description || '',
    status: intervention?.status || 'PLANNED',
    completed_at: intervention?.completed_at || '',
  })

  // Check if title is custom on mount
  useEffect(() => {
    if (intervention && config) {
      const isInList = config.common_interventions.includes(intervention.title)
      setIsCustomTitle(!isInList)
    }
  }, [intervention, config])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      // Validate required fields
      if (!formData.title) {
        toast({
          variant: 'destructive',
          title: 'Validation error',
          description: 'Please enter an intervention title',
        })
        setIsSubmitting(false)
        return
      }

      // Prepare payload
      const payload: InterventionCreatePayload = {
        title: formData.title,
        description: formData.description || undefined,
        status: formData.status,
        completed_at: formData.completed_at || undefined,
      }

      if (intervention) {
        // Update existing intervention
        await updateIntervention(orgId, referralId, intervention.id, payload)
        toast({
          variant: 'success',
          title: 'Intervention updated',
          description: 'The intervention has been updated successfully',
        })
      } else {
        // Create new intervention
        await createIntervention(orgId, referralId, payload)
        toast({
          variant: 'success',
          title: 'Intervention created',
          description: 'The intervention has been added successfully',
        })
      }

      onSuccess?.()
    } catch (err) {
      handleError(err, {
        title: intervention ? 'Failed to update intervention' : 'Failed to create intervention',
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  if (configLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader />
      </div>
    )
  }

  if (!config) {
    return (
      <div className="py-8 text-center text-muted-foreground">
        Configuration not found
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Title Selection/Input */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="title">Intervention Type *</Label>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => {
              setIsCustomTitle(!isCustomTitle)
              if (!isCustomTitle) {
                setFormData((prev) => ({ ...prev, title: '' }))
              }
            }}
          >
            {isCustomTitle ? 'Select from list' : 'Create custom'}
          </Button>
        </div>

        {isCustomTitle ? (
          <Input
            id="title"
            value={formData.title}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, title: e.target.value }))
            }
            placeholder="Enter custom intervention name"
            required
          />
        ) : (
          <Select
            value={formData.title}
            onValueChange={(value) =>
              setFormData((prev) => ({ ...prev, title: value }))
            }
          >
            <SelectTrigger id="title">
              <SelectValue placeholder="Select intervention type" />
            </SelectTrigger>
            <SelectContent>
              {config.common_interventions.map((intervention) => (
                <SelectItem key={intervention} value={intervention}>
                  {intervention}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
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
          className="flex min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
          placeholder="Provide additional details about the intervention..."
        />
      </div>

      {/* Status */}
      <div className="space-y-2">
        <Label htmlFor="status">Status *</Label>
        <Select
          value={formData.status}
          onValueChange={(value) =>
            setFormData((prev) => ({ ...prev, status: value }))
          }
        >
          <SelectTrigger id="status">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="PLANNED">Planned</SelectItem>
            <SelectItem value="IN_PROGRESS">In Progress</SelectItem>
            <SelectItem value="COMPLETED">Completed</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Completed Date (only show if status is COMPLETED) */}
      {formData.status === 'COMPLETED' && (
        <div className="space-y-2">
          <Label htmlFor="completed_at">Completion Date</Label>
          <Input
            type="datetime-local"
            id="completed_at"
            value={formData.completed_at}
            onChange={(e) =>
              setFormData((prev) => ({ ...prev, completed_at: e.target.value }))
            }
          />
        </div>
      )}

      {/* Submit Buttons */}
      <div className="flex justify-end gap-3 pt-4">
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          disabled={isSubmitting}
        >
          Cancel
        </Button>
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting
            ? intervention
              ? 'Updating...'
              : 'Creating...'
            : intervention
            ? 'Update Intervention'
            : 'Add Intervention'}
        </Button>
      </div>
    </form>
  )
}

