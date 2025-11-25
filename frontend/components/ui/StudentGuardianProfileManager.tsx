'use client'

import { Fragment, useEffect, useMemo, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import apiClient from '@/lib/apiClient'
import { Loader } from '@/components/ui/loader'
import { useErrorHandler } from '@/hooks/useErrorHandler'
import { useToast } from '@/hooks/useToast'

interface ProfileRecord {
  id: string
  full_name: string | null
  email: string | null
  phone: string | null
  street_number: string | null
  street_name: string | null
  city: string | null
  state: string | null
  zip_code: string | null
  country: string | null
  preferred_language: string | null
  grade_level?: string | null
  student_id?: string | null
}

interface ProfileListResponse {
  profiles: ProfileRecord[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

type ProfileRole = 'students' | 'guardians'

export function StudentGuardianProfileManager({ orgId }: { orgId: string }) {
  const [activeTab, setActiveTab] = useState<ProfileRole>('students')
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [profiles, setProfiles] = useState<ProfileRecord[]>([])
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [isLoading, setIsLoading] = useState(true)
  const [editingProfile, setEditingProfile] = useState<ProfileRecord | null>(null)
  const [formState, setFormState] = useState<Partial<ProfileRecord>>({})
  const [archivingProfileId, setArchivingProfileId] = useState<string | null>(null)
  const { handleError } = useErrorHandler()
  const { toast } = useToast()

  const isStudentTab = activeTab === 'students'

  useEffect(() => {
    if (!orgId) return
    fetchProfiles()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orgId, activeTab, page, search])

  const fetchProfiles = async () => {
    try {
      setIsLoading(true)
      const params = new URLSearchParams({
        page: page.toString(),
        per_page: '10',
      })
      if (search) {
        params.set('search', search)
      }
      const response = await apiClient<ProfileListResponse>(
        `/api/v1/organizations/${orgId}/${activeTab}?${params.toString()}`
      )
      setProfiles(response.profiles)
      setTotalPages(response.total_pages)
    } catch (err) {
      handleError(err, { title: 'Failed to load profiles' })
    } finally {
      setIsLoading(false)
    }
  }

  const handleSearch = () => {
    setPage(1)
    setSearch(searchInput.trim())
  }

  const startEditing = (profile: ProfileRecord) => {
    setEditingProfile(profile)
    setFormState({
      full_name: profile.full_name ?? '',
      email: profile.email ?? '',
      phone: profile.phone ?? '',
      street_number: profile.street_number ?? '',
      street_name: profile.street_name ?? '',
      city: profile.city ?? '',
      state: profile.state ?? '',
      zip_code: profile.zip_code ?? '',
      country: profile.country ?? '',
      preferred_language: profile.preferred_language ?? '',
      grade_level: profile.grade_level ?? '',
      student_id: profile.student_id ?? '',
    })
  }

  const cancelEditing = () => {
    setEditingProfile(null)
    setFormState({})
  }

  const handleSave = async () => {
    if (!editingProfile) return
    const payload: Record<string, string | null> = {}
    Object.entries(formState).forEach(([key, value]) => {
      if (value !== undefined) {
        payload[key] = value === '' ? null : value
      }
    })

    if (!isStudentTab) {
      delete payload.grade_level
      delete payload.student_id
    }

    try {
      await apiClient(
        `/api/v1/organizations/${orgId}/${isStudentTab ? 'students' : 'guardians'}/${editingProfile.id}`,
        {
          method: 'PATCH',
          body: payload,
        }
      )
      toast({
        variant: 'success',
        title: 'Profile updated',
        description: `${editingProfile.full_name ?? 'Profile'} updated successfully.`,
      })
      cancelEditing()
      fetchProfiles()
    } catch (err) {
      handleError(err, { title: 'Failed to update profile' })
    }
  }

  const handleArchiveProfile = async (profile: ProfileRecord) => {
    const entity = isStudentTab ? 'student' : 'guardian'
    const profileName = profile.full_name || profile.email || 'Profile'
    const confirmed = window.confirm(
      `Archive the ${entity} ${profileName}? This will hide the account from the active list.`
    )

    if (!confirmed) return

    try {
      setArchivingProfileId(profile.id)
      await apiClient(
        `/api/v1/organizations/${orgId}/${isStudentTab ? 'students' : 'guardians'}/${profile.id}`,
        {
          method: 'DELETE'
        }
      )
      toast({
        variant: 'success',
        title: `${entity.charAt(0).toUpperCase() + entity.slice(1)} archived`,
        description: `${profileName} has been archived.`
      })
      fetchProfiles()
    } catch (err) {
      handleError(err, { title: 'Failed to archive profile' })
    } finally {
      setArchivingProfileId(null)
    }
  }

  const columns = useMemo(() => {
    if (isStudentTab) {
      return ['Name', 'Grade / ID', 'Email', 'Phone', 'Location', 'Preferred Lang', '']
    }
    return ['Name', 'Email', 'Phone', 'Location', 'Preferred Lang', '']
  }, [isStudentTab])

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          {(['students', 'guardians'] as ProfileRole[]).map((tab) => (
            <Button
              key={tab}
              variant={activeTab === tab ? 'default' : 'outline'}
              size="sm"
              onClick={() => {
                setActiveTab(tab)
                setPage(1)
                setEditingProfile(null)
              }}
            >
              {tab === 'students' ? 'Students' : 'Guardians'}
            </Button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <Input
            placeholder="Search by name, phone, city..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                handleSearch()
              }
            }}
            className="w-64"
          />
          <Button variant="outline" size="sm" onClick={handleSearch}>
            Search
          </Button>
        </div>
      </div>

      <div className="border rounded-md">
        <Table>
          <TableHeader>
            <TableRow>
              {columns.map((col) => (
                <TableHead key={col}>{col}</TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={columns.length}>
                  <div className="flex justify-center py-6">
                    <Loader text="Loading profiles..." />
                  </div>
                </TableCell>
              </TableRow>
            ) : profiles.length === 0 ? (
              <TableRow>
                <TableCell colSpan={columns.length}>
                  <p className="py-6 text-center text-sm text-muted-foreground">
                    No {isStudentTab ? 'students' : 'guardians'} found.
                  </p>
                </TableCell>
              </TableRow>
            ) : (
              profiles.map((profile) => {
                const isEditing = editingProfile?.id === profile.id
                return (
                  <Fragment key={profile.id}>
                    <TableRow key={`${profile.id}-row`}>
                      <TableCell className="font-medium">{profile.full_name ?? '—'}</TableCell>
                      {isStudentTab ? (
                        <TableCell>
                          <div className="flex flex-col text-sm">
                            <span>{profile.grade_level ?? '—'}</span>
                            <span className="text-muted-foreground">{profile.student_id ?? '—'}</span>
                          </div>
                      </TableCell>
                      ) : null}
                    <TableCell>{profile.email ?? '—'}</TableCell>
                      <TableCell>{profile.phone ?? '—'}</TableCell>
                      <TableCell>
                        {[profile.city, profile.state]
                          .filter(Boolean)
                          .join(', ') || '—'}
                      </TableCell>
                      <TableCell>{profile.preferred_language ?? '—'}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-2">
                          <Button variant="ghost" size="sm" onClick={() => startEditing(profile)}>
                            Edit
                          </Button>
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => handleArchiveProfile(profile)}
                            disabled={archivingProfileId === profile.id}
                          >
                            {archivingProfileId === profile.id ? (
                              <Loader size="sm" />
                            ) : (
                              'Archive'
                            )}
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                    {isEditing && (
                      <TableRow key={`${profile.id}-edit`}>
                        <TableCell colSpan={columns.length}>
                          <ProfileEditForm
                            isStudent={isStudentTab}
                            formState={formState}
                            onFieldChange={(field, value) =>
                              setFormState((prev) => ({
                                ...prev,
                                [field]: value,
                              }))
                            }
                            onCancel={cancelEditing}
                            onSave={handleSave}
                          />
                        </TableCell>
                      </TableRow>
                    )}
                  </Fragment>
                )
              })
            )}
          </TableBody>
        </Table>
      </div>

      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <p>
          Page {page} of {Math.max(totalPages, 1)}
        </p>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page === 1}
            onClick={() => setPage((prev) => Math.max(prev - 1, 1))}
          >
            Previous
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= totalPages}
            onClick={() => setPage((prev) => prev + 1)}
          >
            Next
          </Button>
        </div>
      </div>
    </div>
  )
}

function ProfileEditForm({
  isStudent,
  formState,
  onFieldChange,
  onCancel,
  onSave,
}: {
  isStudent: boolean
  formState: Partial<ProfileRecord>
  onFieldChange: (field: keyof ProfileRecord, value: string) => void
  onCancel: () => void
  onSave: () => void
}) {
  const handleChange = (field: keyof ProfileRecord, value: string) => {
    onFieldChange(field, value)
  }

  return (
    <div className="space-y-4 rounded-md border bg-muted/30 p-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Full Name</Label>
          <Input
            value={formState.full_name ?? ''}
            onChange={(e) => handleChange('full_name', e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label>Email</Label>
          <Input
            type="email"
            value={formState.email ?? ''}
            onChange={(e) => handleChange('email', e.target.value)}
            placeholder="user@example.com"
          />
        </div>
        {isStudent && (
          <div className="space-y-2">
            <Label>Grade Level</Label>
            <Input
              value={formState.grade_level ?? ''}
              onChange={(e) => handleChange('grade_level', e.target.value)}
            />
          </div>
        )}
        {isStudent && (
          <div className="space-y-2">
            <Label>Student ID</Label>
            <Input
              value={formState.student_id ?? ''}
              onChange={(e) => handleChange('student_id', e.target.value)}
            />
          </div>
        )}
        <div className="space-y-2">
          <Label>Phone</Label>
          <Input
            value={formState.phone ?? ''}
            onChange={(e) => handleChange('phone', e.target.value)}
            placeholder="+14155551234"
          />
        </div>
        <div className="space-y-2">
          <Label>Preferred Language</Label>
          <Input
            value={formState.preferred_language ?? ''}
            onChange={(e) => handleChange('preferred_language', e.target.value)}
            placeholder="en"
          />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label>Street Number</Label>
          <Input
            value={formState.street_number ?? ''}
            onChange={(e) => handleChange('street_number', e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label>Street Name</Label>
          <Input
            value={formState.street_name ?? ''}
            onChange={(e) => handleChange('street_name', e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label>City</Label>
          <Input
            value={formState.city ?? ''}
            onChange={(e) => handleChange('city', e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label>State</Label>
          <Input
            value={formState.state ?? ''}
            onChange={(e) => handleChange('state', e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label>ZIP Code</Label>
          <Input
            value={formState.zip_code ?? ''}
            onChange={(e) => handleChange('zip_code', e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label>Country</Label>
          <Input
            value={formState.country ?? ''}
            onChange={(e) => handleChange('country', e.target.value)}
          />
        </div>
      </div>
      <div className="flex items-center justify-end gap-2">
        <Button variant="outline" size="sm" onClick={onCancel}>
          Cancel
        </Button>
        <Button size="sm" onClick={onSave}>
          Save changes
        </Button>
      </div>
    </div>
  )
}

