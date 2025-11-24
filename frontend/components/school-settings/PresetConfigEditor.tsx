'use client'

import { useCallback } from 'react'
import { Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'

export type PresetConfigEntry = {
  id: string
  key: string
  value: string
  error?: string
}

export const generateEntryId = () => {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) {
    return crypto.randomUUID()
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`
}

export const createEntry = (key = '', value = ''): PresetConfigEntry => ({
  id: generateEntryId(),
  key,
  value,
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
    const trimmedKey = entry.key.trim()
    const trimmedValue = entry.value.trim()
    const shouldValidate = trimmedKey !== '' || trimmedValue !== ''
    if (!shouldValidate) {
      return { ...entry, error: undefined }
    }

    if (!trimmedKey) {
      return { ...entry, error: 'Key is required' }
    }

    if (keyCounts[trimmedKey] > 1) {
      return { ...entry, error: 'Duplicate key' }
    }

    if (!trimmedValue) {
      return { ...entry, error: 'Value is required' }
    }

    try {
      JSON.parse(trimmedValue)
      return { ...entry, error: undefined }
    } catch {
      return { ...entry, error: 'Value must be valid JSON' }
    }
  })
}

interface PresetConfigEditorProps {
  entries: PresetConfigEntry[]
  onChange: (entries: PresetConfigEntry[]) => void
  disabled?: boolean
}

export const PresetConfigEditor = ({ entries, onChange, disabled }: PresetConfigEditorProps) => {
  const updateEntries = useCallback(
    (updater: (draft: PresetConfigEntry[]) => PresetConfigEntry[]) => {
      const nextEntries = updater(entries)
      onChange(validatePresetConfigEntries(nextEntries))
    },
    [entries, onChange]
  )

  const handleKeyChange = (id: string, value: string) => {
    updateEntries((draft) => draft.map((entry) => (entry.id === id ? { ...entry, key: value } : entry)))
  }

  const handleValueChange = (id: string, value: string) => {
    updateEntries((draft) => draft.map((entry) => (entry.id === id ? { ...entry, value } : entry)))
  }

  const handleRemove = (id: string) => {
    updateEntries((draft) => draft.filter((entry) => entry.id !== id))
  }

  const handleAddEntry = () => {
    updateEntries((draft) => [
      ...draft,
      {
        id: generateEntryId(),
        key: '',
        value: '',
      },
    ])
  }

  return (
    <div className="space-y-4">
      {entries.length === 0 && (
        <p className="text-sm text-muted-foreground">No preset fields yet. Add your first field below.</p>
      )}

      <div className="space-y-4">
        {entries.map((entry) => (
          <div key={entry.id} className="rounded-lg border p-4 shadow-xs">
            <div className="flex flex-col gap-3 md:flex-row md:items-start">
              <div className="flex-1 space-y-2">
                <Label htmlFor={`preset-key-${entry.id}`}>Key</Label>
                <Input
                  id={`preset-key-${entry.id}`}
                  value={entry.key}
                  onChange={(event) => handleKeyChange(entry.id, event.target.value)}
                  placeholder="e.g. locations"
                  disabled={disabled}
                />
              </div>
              <Button
                type="button"
                variant="ghost"
                className="text-destructive md:mt-7"
                onClick={() => handleRemove(entry.id)}
                disabled={disabled}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>

            <div className="mt-4 space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor={`preset-value-${entry.id}`}>Value (JSON)</Label>
                <span className="text-xs text-muted-foreground">Objects should include label/options/etc.</span>
              </div>
              <Textarea
                id={`preset-value-${entry.id}`}
                value={entry.value}
                onChange={(event) => handleValueChange(entry.id, event.target.value)}
                placeholder='{"label": "Location(s)", "options": ["Classroom"]}'
                className="font-mono text-xs"
                rows={6}
                disabled={disabled}
              />
            </div>

            {entry.error && <p className="mt-2 text-sm text-destructive">{entry.error}</p>}
          </div>
        ))}
      </div>

      <Button type="button" variant="outline" onClick={handleAddEntry} disabled={disabled}>
        Add preset field
      </Button>
    </div>
  )
}


