'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { createEmailTemplate, updateEmailTemplate, type EmailTemplate } from '@/hooks/useReferrals'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { Checkbox } from '@/components/ui/checkbox'
import { useToast } from '@/hooks/useToast'
import { useErrorHandler } from '@/hooks/useErrorHandler'
import { VariableInserter } from './VariableInserter'
import { Label } from '@/components/ui/label'
import { ChevronDown, ChevronUp } from 'lucide-react'

const templateSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  subject_template: z.string().min(1, 'Subject template is required'),
  body_template: z.string().min(1, 'Body template is required'),
  type: z.string().min(1, 'Type is required'),
  scope: z.string().default('organization'),
  is_active: z.boolean().default(true),
})

type TemplateFormValues = z.input<typeof templateSchema>

interface CreateEmailTemplateFormProps {
  orgId: string
  onSuccess?: () => void
  initialData?: EmailTemplate
}

export function CreateEmailTemplateForm({ orgId, onSuccess, initialData }: CreateEmailTemplateFormProps) {
  const { toast } = useToast()
  const { handleError } = useErrorHandler()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [activeField, setActiveField] = useState<'subject_template' | 'body_template'>('body_template')
  const [showVariables, setShowVariables] = useState(false)

  const form = useForm<TemplateFormValues>({
    resolver: zodResolver(templateSchema),
    defaultValues: {
      name: initialData?.name || '',
      subject_template: initialData?.subject_template || '',
      body_template: initialData?.body_template || '',
      type: initialData?.type || 'referral',
      scope: initialData?.scope || 'organization',
      is_active: initialData?.is_active ?? true,
    },
  })

  const onSubmit = async (values: TemplateFormValues) => {
    setIsSubmitting(true)
    try {
      if (initialData) {
        await updateEmailTemplate(orgId, initialData.id, values)
        toast({
          title: 'Template updated',
          description: 'The email template has been updated successfully.',
          variant: 'success',
        })
      } else {
        await createEmailTemplate(orgId, values)
        toast({
          title: 'Template created',
          description: 'The email template has been created successfully.',
          variant: 'success',
        })
      }
      onSuccess?.()
    } catch (err) {
      handleError(err, { title: initialData ? 'Failed to update template' : 'Failed to create template' })
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleInsertVariable = (value: string) => {
    const current = form.getValues(activeField) || ''
    form.setValue(activeField, current + value, { shouldDirty: true })
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <div className="grid gap-6 md:grid-cols-2">
          <FormField
            control={form.control}
            name="name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Template Name</FormLabel>
                <FormControl>
                  <Input placeholder="e.g. Parent Notification" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="type"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Type</FormLabel>
                <Select onValueChange={field.onChange} defaultValue={field.value}>
                  <FormControl>
                    <SelectTrigger>
                      <SelectValue placeholder="Select type" />
                    </SelectTrigger>
                  </FormControl>
                  <SelectContent>
                    <SelectItem value="referral">Referral</SelectItem>
                    <SelectItem value="intervention">Intervention</SelectItem>
                    <SelectItem value="general">General</SelectItem>
                  </SelectContent>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

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
                        Click to insert variable into <strong>{activeField === 'subject_template' ? 'Subject' : 'Body'}</strong>.
                    </p>
                    <VariableInserter orgId={orgId} onInsert={handleInsertVariable} />
                </div>
            )}
        </div>

        <FormField
          control={form.control}
          name="subject_template"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Subject Template</FormLabel>
              <FormControl>
                <Input 
                    placeholder="e.g. Referral for {{student_name}}" 
                    {...field} 
                    onFocus={() => setActiveField('subject_template')}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="body_template"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Body Template (HTML)</FormLabel>
              <FormControl>
                <Textarea 
                  placeholder="<p>Dear Parent/Guardian,</p>..." 
                  className="min-h-[300px] font-mono"
                  {...field} 
                  onFocus={() => setActiveField('body_template')}
                />
              </FormControl>
              <FormDescription>
                Supports basic HTML and Jinja2 variables.
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="is_active"
          render={({ field }) => (
            <FormItem className="flex flex-row items-start space-x-3 space-y-0 rounded-md border p-4">
              <FormControl>
                <Checkbox
                  checked={field.value}
                  onCheckedChange={field.onChange}
                />
              </FormControl>
              <div className="space-y-1 leading-none">
                <FormLabel>
                  Active
                </FormLabel>
                <FormDescription>
                  Make this template available for use
                </FormDescription>
              </div>
            </FormItem>
          )}
        />

        <div className="flex justify-end">
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Saving...' : (initialData ? 'Update Template' : 'Create Template')}
          </Button>
        </div>
      </form>
    </Form>
  )
}

