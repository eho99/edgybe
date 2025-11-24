'use client'

import { useEffect, useMemo, useState } from 'react'
import {
  useOrganizations,
  updateOrganization,
  type OrganizationWithRole,
  type OrganizationUpdatePayload,
} from '@/hooks/useOrganizations'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Spinner } from '@/components/ui/spinner'
import { Textarea } from '@/components/ui/textarea'
import { ApiError } from '@/lib/apiClient'
import { cn } from '@/lib/utils'
import {
  PresetConfigEditor,
  type PresetConfigEntry,
  createEntry,
  validatePresetConfigEntries,
} from '@/components/school-settings/PresetConfigEditor'

type OrganizationFormState = {
  name: string
  street_number: string
  street_name: string
  city: string
  state: string
  zip_code: string
  phone_number: string
  office_extension: string
  lower_grade: string
  upper_grade: string
  slug: string
  form_config: string
  aeries_school_code: string
  sis_source_id: string
  sis_client_id: string
  sis_client_secret: string
}

type DisclaimerKey = 'general' | 'self_harm' | 'child_abuse'

type DisclaimerState = Record<DisclaimerKey, string>

const emptyFormState: OrganizationFormState = {
  name: '',
  street_number: '',
  street_name: '',
  city: '',
  state: '',
  zip_code: '',
  phone_number: '',
  office_extension: '',
  lower_grade: '',
  upper_grade: '',
  slug: '',
  form_config: '',
  aeries_school_code: '',
  sis_source_id: '',
  sis_client_id: '',
  sis_client_secret: '',
}

const disclaimerLabels: Record<DisclaimerKey, string> = {
  general: 'General Disclaimer',
  self_harm: 'Self-Harm Disclaimer',
  child_abuse: 'Child Abuse Disclaimer',
}

const textareaClass =
  'w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50'

const SummaryItem = ({ label, value }: { label: string; value: string }) => (
  <div>
    <p className="text-sm text-muted-foreground">{label}</p>
    <p className="font-medium break-words">{value ?? '—'}</p>
  </div>
)

const normalizePhoneInput = (value: string | null) => {
  if (!value) return ''
  if (value.startsWith('tel:')) {
    return value.replace('tel:', '').replace(/-/g, '')
  }
  return value
}

const formatJsonField = (value: Record<string, unknown> | null) =>
  value ? JSON.stringify(value, null, 2) : ''

const convertOrgToFormState = (organization: OrganizationWithRole): OrganizationFormState => ({
  name: organization.name ?? '',
  street_number: organization.street_number ?? '',
  street_name: organization.street_name ?? '',
  city: organization.city ?? '',
  state: organization.state ?? '',
  zip_code: organization.zip_code ?? '',
  phone_number: normalizePhoneInput(organization.phone_number),
  office_extension: organization.office_extension ?? '',
  lower_grade: organization.lower_grade?.toString() ?? '',
  upper_grade: organization.upper_grade?.toString() ?? '',
  slug: organization.slug ?? '',
  form_config: formatJsonField(organization.form_config),
  aeries_school_code: organization.aeries_school_code ?? '',
  sis_source_id: organization.sis_source_id ?? '',
  sis_client_id: organization.sis_client_id ?? '',
  sis_client_secret: organization.sis_client_secret ?? '',
})

const toOptionalString = (value: string) => {
  const trimmed = value.trim()
  return trimmed === '' ? undefined : trimmed
}

const toOptionalNumber = (value: string, label: string) => {
  if (value.trim() === '') return undefined
  const parsed = Number(value)
  if (Number.isNaN(parsed)) {
    throw new Error(`${label} must be a valid number`)
  }
  return parsed
}

const parseJsonField = (value: string, label: string) => {
  if (value.trim() === '') return undefined
  try {
    return JSON.parse(value)
  } catch {
    throw new Error(`${label} must be valid JSON`)
  }
}

const convertPresetConfigToEntries = (presetConfig: Record<string, unknown> | null): PresetConfigEntry[] => {
  if (!presetConfig) return []
  const entries = Object.entries(presetConfig).map(([key, value]) =>
    createEntry(key, JSON.stringify(value, null, 2))
  )
  return validatePresetConfigEntries(entries)
}

const convertDisclaimers = (value: Record<string, unknown> | null): DisclaimerState => ({
  general: typeof value?.general === 'string' ? value.general : '',
  self_harm: typeof value?.self_harm === 'string' ? value.self_harm : '',
  child_abuse: typeof value?.child_abuse === 'string' ? value.child_abuse : '',
})

const buildPresetConfigPayload = (entries: PresetConfigEntry[]) => {
  const meaningfulEntries = entries.filter((entry) => entry.key.trim() || entry.value.trim())
  if (meaningfulEntries.length === 0) {
    return undefined
  }

  const withErrors = meaningfulEntries.find((entry) => entry.error)
  if (withErrors) {
    throw new Error('Resolve preset config validation errors before saving.')
  }

  const payload: Record<string, unknown> = {}
  for (const entry of meaningfulEntries) {
    if (!entry.key.trim()) {
      throw new Error('Preset config key is required.')
    }
    try {
      payload[entry.key.trim()] = JSON.parse(entry.value)
    } catch {
      throw new Error(`Preset field "${entry.key}" contains invalid JSON.`)
    }
  }
  return payload
}

const buildDisclaimerPayload = (state: DisclaimerState) => {
  const payload: Record<DisclaimerKey, string> = {
    general: state.general.trim(),
    self_harm: state.self_harm.trim(),
    child_abuse: state.child_abuse.trim(),
  }

  (Object.keys(payload) as DisclaimerKey[]).forEach((key) => {
    if (!payload[key]) {
      throw new Error(`${disclaimerLabels[key]} cannot be empty.`)
    }
  })

  return payload
}

export default function SchoolSettingsPage() {
  const { organizations, isLoading, error, mutate } = useOrganizations()
  const [selectedOrgId, setSelectedOrgId] = useState<string | null>(null)
  const [formState, setFormState] = useState<OrganizationFormState>(emptyFormState)
  const [presetEntries, setPresetEntries] = useState<PresetConfigEntry[]>([])
  const [disclaimers, setDisclaimers] = useState<DisclaimerState>({
    general: '',
    self_harm: '',
    child_abuse: '',
  })
  const [isSaving, setIsSaving] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  const adminOrganizations = useMemo(
    () => (organizations ?? []).filter((org) => org.role === 'admin'),
    [organizations]
  )

  useEffect(() => {
    if (!adminOrganizations.length) {
      setSelectedOrgId(null)
      return
    }
    if (!selectedOrgId || !adminOrganizations.find((org) => org.id === selectedOrgId)) {
      setSelectedOrgId(adminOrganizations[0].id)
    }
  }, [adminOrganizations, selectedOrgId])

  const selectedOrg = useMemo(
    () => adminOrganizations.find((org) => org.id === selectedOrgId) ?? null,
    [adminOrganizations, selectedOrgId]
  )

  useEffect(() => {
    if (!selectedOrg) {
      setFormState(emptyFormState)
      setPresetEntries([])
      setDisclaimers({
        general: '',
        self_harm: '',
        child_abuse: '',
      })
      return
    }
    setFormState(convertOrgToFormState(selectedOrg))
    setPresetEntries(convertPresetConfigToEntries(selectedOrg.preset_config))
    setDisclaimers(convertDisclaimers(selectedOrg.disclaimers))
  }, [selectedOrg])

  const handleInputChange = (field: keyof OrganizationFormState, value: string) => {
    setFormState((prev) => ({
      ...prev,
      [field]: value,
    }))
  }

  const buildPayload = (): OrganizationUpdatePayload => {
    const name = formState.name.trim()
    if (!name) {
      throw new Error('Organization name is required')
    }

    return {
      name,
      street_number: toOptionalString(formState.street_number),
      street_name: toOptionalString(formState.street_name),
      city: toOptionalString(formState.city),
      state: toOptionalString(formState.state),
      zip_code: toOptionalString(formState.zip_code),
      phone_number: toOptionalString(formState.phone_number),
      office_extension: toOptionalString(formState.office_extension),
      lower_grade: toOptionalNumber(formState.lower_grade, 'Lower grade'),
      upper_grade: toOptionalNumber(formState.upper_grade, 'Upper grade'),
      slug: toOptionalString(formState.slug),
      preset_config: buildPresetConfigPayload(presetEntries),
      form_config: parseJsonField(formState.form_config, 'Form config'),
      aeries_school_code: toOptionalString(formState.aeries_school_code),
      sis_source_id: toOptionalString(formState.sis_source_id),
      sis_client_id: toOptionalString(formState.sis_client_id),
      sis_client_secret: toOptionalString(formState.sis_client_secret),
      disclaimers: buildDisclaimerPayload(disclaimers),
    }
  }

  const handleSave = async () => {
    if (!selectedOrg) return
    setFormError(null)
    setSuccessMessage(null)
    try {
      setIsSaving(true)
      const payload = buildPayload()
      const updated = await updateOrganization(selectedOrg.id, payload)
      await mutate()
      setFormState(convertOrgToFormState(updated))
      setPresetEntries(convertPresetConfigToEntries(updated.preset_config))
      setDisclaimers(convertDisclaimers(updated.disclaimers))
      setSuccessMessage('Settings saved successfully.')
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : err instanceof Error ? err.message : 'Unknown error'
      setFormError(message)
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex min-h-[300px] items-center justify-center rounded-lg border bg-white">
        <Spinner />
      </div>
    )
  }

  if (error) {
    const message =
      error instanceof ApiError ? error.message : error instanceof Error ? error.message : 'Failed to load organizations'
    return (
      <div className="flex min-h-[300px] items-center justify-center rounded-lg border bg-white p-6">
        <Alert variant="destructive" className="max-w-lg">
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{message}</AlertDescription>
        </Alert>
      </div>
    )
  }

  if (!adminOrganizations.length) {
    return (
      <div className="rounded-lg border bg-white p-6">
        <Alert>
          <AlertTitle>Admin access required</AlertTitle>
          <AlertDescription>You must be an organization admin to manage school settings.</AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">School Settings</h1>
        <p className="text-muted-foreground">
          Review and edit organization metadata, preset form options, and compliance disclaimers.
        </p>
      </div>

      {(formError || successMessage) && (
        <Alert variant={formError ? 'destructive' : 'default'}>
          <AlertTitle>{formError ? 'Action required' : 'Success'}</AlertTitle>
          <AlertDescription>{formError ?? successMessage}</AlertDescription>
        </Alert>
      )}

      <div className="grid gap-6 lg:grid-cols-[320px,1fr]">
        <Card className="border-muted">
          <CardHeader>
            <CardTitle>Your Admin Organizations</CardTitle>
            <CardDescription>Select a school to update settings.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {adminOrganizations.map((org) => (
              <button
                key={org.id}
                onClick={() => {
                  setSelectedOrgId(org.id)
                  setFormError(null)
                  setSuccessMessage(null)
                }}
                className={cn(
                  'w-full rounded-md border px-3 py-2 text-left transition hover:border-ring',
                  selectedOrgId === org.id ? 'border-ring bg-primary/5' : 'border-border'
                )}
              >
                <div className="flex items-center justify-between">
                  <p className="font-medium">{org.name}</p>
                  <Badge variant="default" className="capitalize">
                    {org.role}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground">
                  Updated {new Date(org.updated_at).toLocaleDateString()}
                </p>
              </button>
            ))}
          </CardContent>
        </Card>

        <Card className="border-muted">
          <CardHeader>
            <CardTitle>{selectedOrg?.name ?? 'Select an organization'}</CardTitle>
            <CardDescription>
              {selectedOrg ? 'Changes sync across the referral experience immediately.' : 'Choose an organization first.'}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {selectedOrg && (
              <>
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold">Summary</h3>
                  <div className="grid gap-4 md:grid-cols-2">
                    <SummaryItem label='District Name' value={selectedOrg.district_name ?? '—'} />
                    <SummaryItem label='Phone' value={selectedOrg.phone_number ?? '—'} />
                    <SummaryItem
                      label='Address'
                      value={[selectedOrg.street_number, selectedOrg.street_name].filter(Boolean).join(' ') || '—'}
                    />
                    <SummaryItem
                      label='Location'
                      value={[selectedOrg.city, selectedOrg.state, selectedOrg.zip_code].filter(Boolean).join(', ') || '—'}
                    />
                    <SummaryItem
                      label='Grades'
                      value={
                        selectedOrg.lower_grade !== null || selectedOrg.upper_grade !== null
                          ? `${selectedOrg.lower_grade ?? '—'} - ${selectedOrg.upper_grade ?? '—'}`
                          : '—'
                      }
                    />
                    <SummaryItem label='Aeries Code' value={selectedOrg.aeries_school_code ?? '—'} />
                  </div>
                </div>

                <div className="space-y-6">
                  {[
                    {
                      title: 'Basic Information',
                      fields: [
                        { name: 'name', label: 'Name' },
                        { name: 'slug', label: 'Slug', placeholder: 'url-friendly-name' },
                      ],
                    },
                    {
                      title: 'Address',
                      fields: [
                        { name: 'street_number', label: 'Street Number' },
                        { name: 'street_name', label: 'Street Name' },
                        { name: 'city', label: 'City' },
                        { name: 'state', label: 'State' },
                        { name: 'zip_code', label: 'ZIP Code' },
                      ],
                    },
                    {
                      title: 'Contact',
                      fields: [
                        { name: 'phone_number', label: 'Phone Number', placeholder: '+14155550123' },
                        { name: 'office_extension', label: 'Office Extension' },
                      ],
                    },
                    {
                      title: 'Grades',
                      fields: [
                        { name: 'lower_grade', label: 'Lower Grade', type: 'number' },
                        { name: 'upper_grade', label: 'Upper Grade', type: 'number' },
                      ],
                    },
                    {
                      title: 'SIS Integrations',
                      fields: [
                        { name: 'aeries_school_code', label: 'Aeries School Code' },
                        { name: 'sis_source_id', label: 'SIS Source ID' },
                        { name: 'sis_client_id', label: 'SIS Client ID' },
                        { name: 'sis_client_secret', label: 'SIS Client Secret' },
                      ],
                    },
                  ].map((group) => (
                    <div key={group.title} className="space-y-3">
                      <h4 className="text-base font-semibold">{group.title}</h4>
                      <div className="grid gap-4 md:grid-cols-2">
                        {group.fields.map((field) => (
                          <div key={field.name}>
                            <Label htmlFor={field.name}>{field.label}</Label>
                            <Input
                              id={field.name}
                              name={field.name}
                              type={field.type ?? 'text'}
                              value={formState[field.name as keyof OrganizationFormState]}
                              placeholder={field.placeholder}
                              onChange={(event) =>
                                handleInputChange(field.name as keyof OrganizationFormState, event.target.value)
                              }
                              disabled={isSaving}
                            />
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}

                  <div className="space-y-3">
                    <h4 className="text-base font-semibold">Form Config (JSON)</h4>
                    <Textarea
                      value={formState.form_config}
                      onChange={(event) => handleInputChange('form_config', event.target.value)}
                      className={`${textareaClass} font-mono text-xs`}
                      rows={10}
                      disabled={isSaving}
                    />
                  </div>

                  <div className="space-y-3">
                    <div>
                      <h4 className="text-base font-semibold">Preset Config</h4>
                      <p className="text-sm text-muted-foreground">
                        Manage the key/value schema that powers referral dropdowns.
                      </p>
                    </div>
                    <PresetConfigEditor entries={presetEntries} onChange={setPresetEntries} disabled={isSaving} />
                  </div>

                  <div className="space-y-3">
                    <div>
                      <h4 className="text-base font-semibold">Disclaimers</h4>
                      <p className="text-sm text-muted-foreground">
                        Customize the text admins, staff, and guardians will read before submitting referrals.
                      </p>
                    </div>
                    <div className="space-y-4">
                      {(Object.keys(disclaimerLabels) as DisclaimerKey[]).map((key) => (
                        <div key={key} className="space-y-2">
                          <Label htmlFor={`disclaimer-${key}`}>{disclaimerLabels[key]}</Label>
                          <Textarea
                            id={`disclaimer-${key}`}
                            value={disclaimers[key]}
                            onChange={(event) =>
                              setDisclaimers((prev) => ({
                                ...prev,
                                [key]: event.target.value,
                              }))
                            }
                            className={textareaClass}
                            rows={6}
                            disabled={isSaving}
                          />
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="flex justify-end gap-3">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => {
                        if (!selectedOrg) return
                        setFormState(convertOrgToFormState(selectedOrg))
                        setPresetEntries(convertPresetConfigToEntries(selectedOrg.preset_config))
                        setDisclaimers(convertDisclaimers(selectedOrg.disclaimers))
                        setFormError(null)
                        setSuccessMessage(null)
                      }}
                      disabled={isSaving}
                    >
                      Reset
                    </Button>
                    <Button onClick={handleSave} disabled={isSaving || !selectedOrg}>
                      {isSaving ? 'Saving...' : 'Save Settings'}
                    </Button>
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}


