'use client'

import { useEffect, useMemo, useState, type ReactNode } from 'react'
import {
  useOrganizations,
  createOrganization,
  updateOrganization,
  OrganizationWithRole,
  OrganizationCreatePayload,
  OrganizationUpdatePayload,
} from '@/hooks/useOrganizations'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Spinner } from '@/components/ui/spinner'
import { ApiError } from '@/lib/apiClient'
import { cn } from '@/lib/utils'

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
  preset_config: string
  form_config: string
  aeries_school_code: string
  sis_source_id: string
  sis_client_id: string
  sis_client_secret: string
  disclaimers: string
}

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
  preset_config: '',
  form_config: '',
  aeries_school_code: '',
  sis_source_id: '',
  sis_client_id: '',
  sis_client_secret: '',
  disclaimers: '',
}

const restrictedRoles = new Set(['staff', 'secretary'])

const textareaClass =
  'w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50'

const SummaryItem = ({ label, value }: { label: string; value: ReactNode }) => (
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
  preset_config: formatJsonField(organization.preset_config),
  form_config: formatJsonField(organization.form_config),
  aeries_school_code: organization.aeries_school_code ?? '',
  sis_source_id: organization.sis_source_id ?? '',
  sis_client_id: organization.sis_client_id ?? '',
  sis_client_secret: organization.sis_client_secret ?? '',
  disclaimers: formatJsonField(organization.disclaimers),
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

export default function OrganizationsDashboardPage() {
  const { organizations, memberships, isLoading, error, mutate } = useOrganizations()
  const [selectedOrgId, setSelectedOrgId] = useState<string | null>(null)
  const [formState, setFormState] = useState<OrganizationFormState>(emptyFormState)
  const [isCreating, setIsCreating] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  const hasAdminMembership = useMemo(
    () => (memberships ?? []).some((membership) => membership.role === 'admin'),
    [memberships]
  )

  useEffect(() => {
    if (!organizations || organizations.length === 0 || isCreating) {
      return
    }
    if (!selectedOrgId) {
      setSelectedOrgId(organizations[0].id)
    }
  }, [organizations, selectedOrgId, isCreating])

  useEffect(() => {
    if (!organizations || !selectedOrgId || isCreating) {
      return
    }
    const found = organizations.find((org) => org.id === selectedOrgId)
    if (found) {
      setFormState(convertOrgToFormState(found))
    }
  }, [organizations, selectedOrgId, isCreating])

  const selectedOrg = useMemo(
    () => organizations?.find((org) => org.id === selectedOrgId),
    [organizations, selectedOrgId]
  )

  const selectedRole = isCreating
    ? 'admin'
    : selectedOrg?.role ??
      memberships?.find((membership) => membership.org_id === selectedOrgId)?.role

  const canEdit = isCreating ? hasAdminMembership : selectedRole === 'admin'

  const handleInputChange = (field: keyof OrganizationFormState, value: string) => {
    setFormState((prev) => ({
      ...prev,
      [field]: value,
    }))
  }

  const resetToList = () => {
    setIsCreating(false)
    setFormState(emptyFormState)
    setFormError(null)
    setSuccessMessage(null)
    if (organizations && organizations.length > 0) {
      setSelectedOrgId(organizations[0].id)
    } else {
      setSelectedOrgId(null)
    }
  }

  const buildPayload = (
    mode: 'create' | 'update'
  ): OrganizationCreatePayload | OrganizationUpdatePayload => {
    const name = formState.name.trim()
    if (!name) {
      throw new Error('Organization name is required')
    }

    const payloadBase = {
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
      preset_config: parseJsonField(formState.preset_config, 'Preset config'),
      form_config: parseJsonField(formState.form_config, 'Form config'),
      aeries_school_code: toOptionalString(formState.aeries_school_code),
      sis_source_id: toOptionalString(formState.sis_source_id),
      sis_client_id: toOptionalString(formState.sis_client_id),
      sis_client_secret: toOptionalString(formState.sis_client_secret),
      disclaimers: parseJsonField(formState.disclaimers, 'Disclaimers'),
    }

    if (mode === 'create') {
      return payloadBase as OrganizationCreatePayload
    }
    return payloadBase as OrganizationUpdatePayload
  }

  const handleSubmit = async () => {
    setFormError(null)
    setSuccessMessage(null)
    if (!canEdit) {
      setFormError('You do not have permission to modify this organization.')
      return
    }

    try {
      setIsSaving(true)
      const payload = buildPayload(isCreating ? 'create' : 'update')
      if (isCreating) {
        const created = await createOrganization(payload as OrganizationCreatePayload)
        await mutate()
        setSelectedOrgId(created.id)
        setFormState(convertOrgToFormState(created))
        setIsCreating(false)
        setSuccessMessage('Organization created successfully')
      } else if (selectedOrgId) {
        const updated = await updateOrganization(selectedOrgId, payload as OrganizationUpdatePayload)
        await mutate()
        setFormState(convertOrgToFormState(updated))
        setSuccessMessage('Organization updated successfully')
      }
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : err instanceof Error ? err.message : 'Unknown error'
      setFormError(message)
    } finally {
      setIsSaving(false)
    }
  }

  const fieldGroups: {
    title: string
    fields: { name: keyof OrganizationFormState; label: string; type?: string; placeholder?: string; textarea?: boolean }[]
  }[] = [
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
    {
      title: 'Advanced Config',
      fields: [
        { name: 'preset_config', label: 'Preset Config (JSON)', textarea: true },
        { name: 'form_config', label: 'Form Config (JSON)', textarea: true },
        { name: 'disclaimers', label: 'Disclaimers (JSON)', textarea: true },
      ],
    },
  ]

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

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-bold">Organizations</h1>
          <p className="text-muted-foreground">
            View and manage organization metadata. Admins can create and edit records.
          </p>
        </div>
        {hasAdminMembership && (
          <div className="flex gap-3">
            {isCreating && (
              <Button variant="outline" onClick={resetToList}>
                Cancel
              </Button>
            )}
            <Button
              onClick={() => {
                setIsCreating(true)
                setSelectedOrgId(null)
                setFormState(emptyFormState)
                setFormError(null)
                setSuccessMessage(null)
              }}
            >
              New Organization
            </Button>
          </div>
        )}
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
            <CardTitle>Your Organizations</CardTitle>
            <CardDescription>Select an organization to view details.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {!organizations || organizations.length === 0 ? (
              <p className="text-sm text-muted-foreground">No organizations available.</p>
            ) : (
              <div className="space-y-2">
                {organizations.map((org) => (
                  <button
                    key={org.id}
                    onClick={() => {
                      setSelectedOrgId(org.id)
                      setIsCreating(false)
                      setFormError(null)
                      setSuccessMessage(null)
                    }}
                    className={cn(
                      'w-full rounded-md border px-3 py-2 text-left transition hover:border-ring',
                      selectedOrgId === org.id && !isCreating ? 'border-ring bg-primary/5' : 'border-border'
                    )}
                  >
                    <div className="flex items-center justify-between">
                      <p className="font-medium">{org.name}</p>
                      {org.role && (
                        <Badge variant={org.role === 'admin' ? 'default' : 'outline'} className="capitalize">
                          {org.role}
                        </Badge>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Updated {new Date(org.updated_at).toLocaleDateString()}
                    </p>
                  </button>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="border-muted">
          <CardHeader>
            <CardTitle>{isCreating ? 'Create Organization' : selectedOrg?.name ?? 'Select an organization'}</CardTitle>
            <CardDescription>
              {isCreating
                ? 'Provide details for the new organization.'
                : selectedRole
                ? `You are viewing this organization as ${selectedRole}.`
                : 'Choose an organization from the list.'}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {!isCreating && selectedOrg && restrictedRoles.has((selectedRole ?? '').toLowerCase()) && (
              <Alert>
                <AlertTitle>Limited access</AlertTitle>
                <AlertDescription>
                  Certain SIS fields are hidden for staff and secretary roles.
                </AlertDescription>
              </Alert>
            )}

            {!isCreating && selectedOrg && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Summary</h3>
                <div className="grid gap-4 md:grid-cols-2">
                  <SummaryItem label="District Name" value={selectedOrg.district_name ?? '—'} />
                  <SummaryItem label="Phone" value={selectedOrg.phone_number ?? '—'} />
                  <SummaryItem
                    label="Address"
                    value={[selectedOrg.street_number, selectedOrg.street_name].filter(Boolean).join(' ') || '—'}
                  />
                  <SummaryItem
                    label="Location"
                    value={
                      [selectedOrg.city, selectedOrg.state, selectedOrg.zip_code].filter(Boolean).join(', ') ||
                      '—'
                    }
                  />
                  <SummaryItem
                    label="Grades"
                    value={
                      selectedOrg.lower_grade !== null || selectedOrg.upper_grade !== null
                        ? `${selectedOrg.lower_grade ?? '—'} - ${selectedOrg.upper_grade ?? '—'}`
                        : '—'
                    }
                  />
                  <SummaryItem label="Aeries Code" value={selectedOrg.aeries_school_code ?? '—'} />
                </div>
              </div>
            )}

            {(isCreating || selectedOrg) && (
              <div className="space-y-6">
                {!canEdit && !isCreating && (
                  <Alert variant="default">
                    <AlertTitle>Read-only access</AlertTitle>
                    <AlertDescription>
                      You can view this organization but only admins can make changes.
                    </AlertDescription>
                  </Alert>
                )}

                {fieldGroups.map((group) => (
                  <div key={group.title} className="space-y-3">
                    <h4 className="text-base font-semibold">{group.title}</h4>
                    <div className="grid gap-4 md:grid-cols-2">
                      {group.fields.map((field) => (
                        <div key={field.name} className={field.textarea ? 'md:col-span-2' : undefined}>
                          <Label htmlFor={field.name}>{field.label}</Label>
                          {field.textarea ? (
                            <textarea
                              id={field.name}
                              name={field.name}
                              value={formState[field.name]}
                              placeholder={field.placeholder}
                              onChange={(event) => handleInputChange(field.name, event.target.value)}
                              className={textareaClass}
                              disabled={!canEdit}
                            />
                          ) : (
                            <Input
                              id={field.name}
                              name={field.name}
                              type={field.type ?? 'text'}
                              value={formState[field.name]}
                              placeholder={field.placeholder}
                              onChange={(event) => handleInputChange(field.name, event.target.value)}
                              disabled={!canEdit}
                            />
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}

                {canEdit && (
                  <div className="flex justify-end gap-3">
                    <Button
                      variant="outline"
                      type="button"
                      disabled={isSaving}
                      onClick={() => {
                        if (isCreating) {
                          resetToList()
                        } else if (selectedOrg) {
                          setFormState(convertOrgToFormState(selectedOrg))
                          setFormError(null)
                          setSuccessMessage(null)
                        }
                      }}
                    >
                      {isCreating ? 'Cancel' : 'Reset'}
                    </Button>
                    <Button onClick={handleSubmit} disabled={isSaving}>
                      {isSaving ? 'Saving...' : isCreating ? 'Create Organization' : 'Save Changes'}
                    </Button>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

