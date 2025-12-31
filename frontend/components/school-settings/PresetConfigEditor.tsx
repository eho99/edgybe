"use client"

import { useCallback, useMemo, useState } from 'react'
import { ArrowDown, ArrowUp, Info, Plus, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import type { ReferralFieldSelection } from '@/hooks/useReferrals'

export type PresetOptionEntry = {
  id: string
  value: string
}

export type PresetConfigEntry = {
  id: string
  key: string
  label: string
  helpText: string
  required: boolean
  selection: ReferralFieldSelection
  options: PresetOptionEntry[]
  allowOther: boolean
  error?: string
}

const toTitleCase = (value: string) =>
  value
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/\w\S*/g, (word) => word.charAt(0).toUpperCase() + word.slice(1))

export const generateEntryId = () => {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID()
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`
}

export const createOptionEntry = (value = ''): PresetOptionEntry => ({
  id: generateEntryId(),
  value,
})

export const createEntry = (
  key: string,
  config?: Partial<Omit<PresetConfigEntry, 'id' | 'key' | 'options'>> & { options?: PresetOptionEntry[] }
): PresetConfigEntry => ({
  id: generateEntryId(),
  key,
  label: typeof config?.label === 'string' && config.label !== '' ? config.label : toTitleCase(key),
  helpText: typeof config?.helpText === 'string' ? config.helpText : '',
  required: Boolean(config?.required),
  selection: config?.selection === 'multi' ? 'multi' : 'single',
  allowOther: Boolean(config?.allowOther),
  options:
    Array.isArray(config?.options) && config.options.length > 0
      ? config.options
      : [createOptionEntry()],
})

export const validatePresetConfigEntries = (entries: PresetConfigEntry[]) => {
  const keyCounts = entries.reduce<Record<string, number>>((acc, entry) => {
    const trimmedKey = entry.key.trim()
    if (trimmedKey) {
      acc[trimmedKey] = (acc[trimmedKey] ?? 0) + 1
    }
    return acc
  }, {})

  return entries.map((entry) => {
    if (!entry.key.trim()) {
      return { ...entry, error: 'Key is required' }
    }
    if (keyCounts[entry.key.trim()] > 1) {
      return { ...entry, error: 'Duplicate key' }
    }
    if (!entry.label.trim()) {
      return { ...entry, error: 'Label is required' }
    }
    const optionValues = entry.options.map((option) => option.value.trim()).filter(Boolean)
    if (optionValues.length === 0) {
      return { ...entry, error: 'At least one option is required' }
    }
    return { ...entry, error: undefined }
  })
}

interface PresetConfigEditorProps {
  entries: PresetConfigEntry[]
  onChange: (entries: PresetConfigEntry[]) => void
  disabled?: boolean
}

export const PresetConfigEditor = ({ entries, onChange, disabled }: PresetConfigEditorProps) => {
  const [newFieldKey, setNewFieldKey] = useState('')
  const hasDuplicateKey = useMemo(
    () =>
      Boolean(
        newFieldKey &&
          entries.some((entry) => entry.key.trim() === newFieldKey.trim())
      ),
    [entries, newFieldKey]
  )

  const updateEntries = useCallback(
    (updater: (draft: PresetConfigEntry[]) => PresetConfigEntry[]) => {
      const nextEntries = updater(entries)
      onChange(validatePresetConfigEntries(nextEntries))
    },
    [entries, onChange]
  )

  const handleRemoveEntry = (id: string) => {
    updateEntries((draft) => draft.filter((entry) => entry.id !== id))
  }

  const handleFieldChange = (
    id: string,
    field: keyof Omit<PresetConfigEntry, 'id' | 'key' | 'options' | 'error'>,
    value: string | boolean
  ) => {
    updateEntries((draft) =>
      draft.map((entry) =>
        entry.id === id
          ? {
              ...entry,
              [field]: value,
            }
          : entry
      )
    )
  }

  const handleOptionChange = (entryId: string, optionId: string, value: string) => {
    updateEntries((draft) =>
      draft.map((entry) =>
        entry.id === entryId
          ? {
              ...entry,
              options: entry.options.map((option) => (option.id === optionId ? { ...option, value } : option)),
            }
          : entry
      )
    )
  }

  const handleAddOption = (entryId: string) => {
    updateEntries((draft) =>
      draft.map((entry) =>
        entry.id === entryId ? { ...entry, options: [...entry.options, createOptionEntry()] } : entry
      )
    )
  }

  const handleRemoveOption = (entryId: string, optionId: string) => {
    updateEntries((draft) =>
      draft.map((entry) =>
        entry.id === entryId
          ? { ...entry, options: entry.options.filter((option) => option.id !== optionId) || [createOptionEntry()] }
          : entry
      )
    )
  }

  const handleMoveOption = (entryId: string, optionId: string, direction: 'up' | 'down') => {
    updateEntries((draft) =>
      draft.map((entry) => {
        if (entry.id !== entryId) return entry

        const index = entry.options.findIndex((option) => option.id === optionId)
        if (index === -1) return entry

        const targetIndex = direction === 'up' ? index - 1 : index + 1
        if (targetIndex < 0 || targetIndex >= entry.options.length) return entry

        const nextOptions = [...entry.options]
        const [moved] = nextOptions.splice(index, 1)
        nextOptions.splice(targetIndex, 0, moved)

        return {
          ...entry,
          options: nextOptions,
        }
      })
    )
  }

  const handleAddEntry = () => {
    const trimmedKey = newFieldKey.trim()
    if (!trimmedKey || hasDuplicateKey) {
      return
    }
    updateEntries((draft) => [...draft, createEntry(trimmedKey)])
    setNewFieldKey('')
  }

  return (
    <div className="space-y-4">
      {entries.length === 0 && (
        <p className="text-sm text-muted-foreground">No preset fields yet. Add your first field below.</p>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {entries.map((entry) => (
          <div
            key={entry.id}
            className={`rounded-lg border p-4 shadow-xs ${entry.error ? 'border-destructive' : 'border-border'}`}
          >
            <div className="flex flex-col gap-3 border-b pb-3 md:flex-row md:items-center md:justify-between">
              <div>
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Field key</p>
                <p className="font-mono text-sm font-semibold">{entry.key}</p>
              </div>
              <Button
                type="button"
                variant="ghost"
                className="text-destructive"
                onClick={() => handleRemoveEntry(entry.id)}
                disabled={disabled}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Remove field
              </Button>
            </div>

            <div className="grid gap-4 py-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor={`label-${entry.id}`}>Label</Label>
                <Input
                  id={`label-${entry.id}`}
                  value={entry.label}
                  onChange={(event) => handleFieldChange(entry.id, 'label', event.target.value)}
                  disabled={disabled}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor={`selection-${entry.id}`}>Selection style</Label>
                <Select
                  value={entry.selection}
                  onValueChange={(value) => handleFieldChange(entry.id, 'selection', value as ReferralFieldSelection)}
                  disabled={disabled}
                >
                  <SelectTrigger id={`selection-${entry.id}`}>
                    <SelectValue placeholder="Select style" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="single">Single choice</SelectItem>
                    <SelectItem value="multi">Multiple choice</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2 md:col-span-2">
                <Label htmlFor={`help-${entry.id}`}>Help text</Label>
                <Input
                  id={`help-${entry.id}`}
                  value={entry.helpText}
                  onChange={(event) => handleFieldChange(entry.id, 'helpText', event.target.value)}
                  disabled={disabled}
                />
              </div>
              <div className="flex items-center gap-2 rounded-md border px-3 py-2">
                <Checkbox
                  id={`required-${entry.id}`}
                  checked={entry.required}
                  onCheckedChange={(checked) => handleFieldChange(entry.id, 'required', Boolean(checked))}
                  disabled={disabled}
                />
                <Label htmlFor={`required-${entry.id}`}>Required field</Label>
              </div>
              <div className="flex items-center gap-2 rounded-md border px-3 py-2">
                <Checkbox
                  id={`allowOther-${entry.id}`}
                  checked={entry.allowOther}
                  onCheckedChange={(checked) => handleFieldChange(entry.id, 'allowOther', Boolean(checked))}
                  disabled={disabled}
                />
                <Label htmlFor={`allowOther-${entry.id}`} className="flex items-center gap-1.5">
                  Allow 'Other' with text input
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <button
                          type="button"
                          className="inline-flex items-center justify-center rounded-full focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                          disabled={disabled}
                        >
                          <Info className="h-3.5 w-3.5 text-muted-foreground" />
                        </button>
                      </TooltipTrigger>
                      <TooltipContent side="right" className="max-w-xs">
                        <p>
                          When enabled, users will see an "Other" option in the dropdown or checkbox list. Selecting
                          "Other" reveals a text input field where they can enter a custom value not in the predefined
                          options.
                        </p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </Label>
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-semibold">Options</h4>
                  <p className="text-xs text-muted-foreground">List the options exactly as they should appear.</p>
                </div>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => handleAddOption(entry.id)}
                  disabled={disabled}
                >
                  <Plus className="mr-1 h-4 w-4" />
                  Add option
                </Button>
              </div>
              <div className="space-y-2">
                {entry.options.map((option, index) => (
                  <div key={option.id} className="flex items-center gap-2">
                    <span className="w-6 text-xs text-muted-foreground text-right">{index + 1}.</span>
                    <Input
                      value={option.value}
                      onChange={(event) => handleOptionChange(entry.id, option.id, event.target.value)}
                      placeholder={`Option ${index + 1}`}
                      disabled={disabled}
                    />
                    <div className="flex items-center gap-1">
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 text-muted-foreground"
                        onClick={() => handleMoveOption(entry.id, option.id, 'up')}
                        disabled={disabled || index === 0}
                        aria-label="Move option up"
                      >
                        <ArrowUp className="h-3 w-3" />
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="h-7 w-7 text-muted-foreground"
                        onClick={() => handleMoveOption(entry.id, option.id, 'down')}
                        disabled={disabled || index === entry.options.length - 1}
                        aria-label="Move option down"
                      >
                        <ArrowDown className="h-3 w-3" />
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        className="text-muted-foreground"
                        onClick={() => handleRemoveOption(entry.id, option.id)}
                        disabled={disabled || entry.options.length === 1}
                        aria-label="Remove option"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {entry.error && <p className="mt-4 text-sm text-destructive">{entry.error}</p>}
          </div>
        ))}
      </div>

      <div className="rounded-lg border p-4 space-y-2">
        <Label htmlFor="new-field-key">Add preset field</Label>
        <div className="flex flex-col gap-2 md:flex-row md:items-center">
          <Input
            id="new-field-key"
            placeholder="e.g. locations"
            value={newFieldKey}
            onChange={(event) => setNewFieldKey(event.target.value)}
            disabled={disabled}
          />
          <Button type="button" onClick={handleAddEntry} disabled={disabled || !newFieldKey.trim() || hasDuplicateKey}>
            Add field
          </Button>
        </div>
        {hasDuplicateKey && <p className="text-sm text-destructive">That key already exists.</p>}
        <p className="text-xs text-muted-foreground">
          Keys are referenced in referral forms (examples: locations, time_of_day, referral_type).
        </p>
      </div>
    </div>
  )
}


