'use client'

import { useMemo } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import type { PresetConfigEntry } from './PresetConfigEditor'

interface FormPreviewProps {
  entries: PresetConfigEntry[]
}

export function FormPreview({ entries }: FormPreviewProps) {
  const meaningfulEntries = useMemo(
    () => entries.filter((entry) => entry.key.trim() && entry.options.some((opt) => opt.value.trim())),
    [entries]
  )

  if (meaningfulEntries.length === 0) {
    return (
      <Card className="border-muted">
        <CardHeader>
          <CardTitle>Form Preview</CardTitle>
          <CardDescription>Configure preset fields above to see a preview of your referral form.</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No fields configured yet.</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="border-muted">
      <CardHeader>
        <CardTitle>Form Preview</CardTitle>
        <CardDescription>
          This is how your referral form will appear to staff. Fields marked with * are required.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {meaningfulEntries.map((entry) => {
          const options = entry.options.map((opt) => opt.value.trim()).filter(Boolean)
          const hasOther = entry.allowOther

          return (
            <div key={entry.id} className="space-y-2">
              <div className="flex items-center gap-2">
                <Label htmlFor={`preview-${entry.id}`}>
                  {entry.label || entry.key}
                  {entry.required && <span className="text-destructive ml-1">*</span>}
                </Label>
                {entry.required && (
                  <Badge variant="outline" className="text-xs">
                    Required
                  </Badge>
                )}
                {hasOther && (
                  <Badge variant="outline" className="text-xs">
                    Allows Other
                  </Badge>
                )}
              </div>
              {entry.helpText && (
                <p className="text-sm text-muted-foreground">{entry.helpText}</p>
              )}

              {entry.selection === 'multi' ? (
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    {options.map((option) => (
                      <div key={option} className="flex items-center space-x-2">
                        <Checkbox id={`preview-${entry.id}-${option}`} disabled />
                        <label
                          htmlFor={`preview-${entry.id}-${option}`}
                          className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                        >
                          {option}
                        </label>
                      </div>
                    ))}
                    {hasOther && (
                      <div className="flex items-center space-x-2">
                        <Checkbox id={`preview-${entry.id}-other`} disabled />
                        <label
                          htmlFor={`preview-${entry.id}-other`}
                          className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                        >
                          Other
                        </label>
                      </div>
                    )}
                  </div>
                  {hasOther && (
                    <Input
                      placeholder="Specify other option"
                      disabled
                      className="mt-2 opacity-50"
                    />
                  )}
                </div>
              ) : (
                <div className="space-y-2">
                  <Select disabled>
                    <SelectTrigger id={`preview-${entry.id}`}>
                      <SelectValue placeholder="Select an option" />
                    </SelectTrigger>
                    <SelectContent>
                      {options.map((option) => (
                        <SelectItem key={option} value={option}>
                          {option}
                        </SelectItem>
                      ))}
                      {hasOther && <SelectItem value="Other">Other</SelectItem>}
                    </SelectContent>
                  </Select>
                  {hasOther && (
                    <Input
                      placeholder="Specify other option"
                      disabled
                      className="opacity-50"
                    />
                  )}
                </div>
              )}
            </div>
          )
        })}
      </CardContent>
    </Card>
  )
}

