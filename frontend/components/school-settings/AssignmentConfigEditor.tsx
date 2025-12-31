'use client'

import { useMemo, useState, useCallback, useEffect } from 'react'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Plus, Trash2 } from 'lucide-react'
import { useOrganizationAdmins, type OrganizationMember } from '@/hooks/useOrganizationMembers'
import { cn } from '@/lib/utils'

export type AssignmentConfig = {
  type: 'manual' | 'grade' | 'alphabetical' | null
  grade_mappings?: Record<string, string>
  letter_ranges?: Record<string, string>
  name_field?: 'first_name' | 'last_name'
}

interface AssignmentConfigEditorProps {
  orgId: string | null
  config: AssignmentConfig | null
  onChange: (config: AssignmentConfig | null) => void
  disabled?: boolean
}

export function AssignmentConfigEditor({
  orgId,
  config,
  onChange,
  disabled = false,
}: AssignmentConfigEditorProps) {
  const { admins, isLoading: adminsLoading } = useOrganizationAdmins(orgId)
  const [assignmentType, setAssignmentType] = useState<AssignmentConfig['type']>(
    config?.type ?? null
  )

  // Sync assignmentType when config changes from parent
  useEffect(() => {
    const newType = config?.type ?? null
    if (newType !== assignmentType) {
      setAssignmentType(newType)
    }
  }, [config?.type, assignmentType])

  const gradeMappings = useMemo(
    () => config?.grade_mappings ?? {},
    [config?.grade_mappings]
  )

  const letterRanges = useMemo(
    () => config?.letter_ranges ?? {},
    [config?.letter_ranges]
  )

  const nameField = useMemo(
    () => config?.name_field ?? 'last_name',
    [config?.name_field]
  )

  const handleTypeChange = useCallback(
    (newType: AssignmentConfig['type']) => {
      setAssignmentType(newType)
      if (newType === 'manual' || newType === null) {
        onChange(null)
      } else {
        // Preserve existing mappings when switching types
        const newConfig: AssignmentConfig = {
          type: newType,
        }
        if (newType === 'grade') {
          // Use current gradeMappings if switching to grade, or preserve if already grade
          newConfig.grade_mappings = config?.type === 'grade' ? gradeMappings : (config?.grade_mappings ?? {})
        } else if (newType === 'alphabetical') {
          // Use current letterRanges if switching to alphabetical, or preserve if already alphabetical
          newConfig.letter_ranges = config?.type === 'alphabetical' ? letterRanges : (config?.letter_ranges ?? {})
          newConfig.name_field = config?.type === 'alphabetical' ? nameField : (config?.name_field || 'last_name')
        }
        onChange(newConfig)
      }
    },
    [onChange, gradeMappings, letterRanges, nameField, config]
  )

  const handleGradeMappingRemove = useCallback(
    (grade: string) => {
      const newMappings = { ...gradeMappings }
      delete newMappings[grade]
      const newConfig: AssignmentConfig = {
        type: 'grade',
        grade_mappings: newMappings,
      }
      onChange(newConfig)
    },
    [gradeMappings, onChange]
  )

  const [gradeInputValue, setGradeInputValue] = useState<string>('')
  const [selectedGradeAdmin, setSelectedGradeAdmin] = useState<string>('')
  const [letterRangeInputValue, setLetterRangeInputValue] = useState<string>('')
  const [selectedLetterRangeAdmin, setSelectedLetterRangeAdmin] = useState<string>('')

  const handleGradeInputChange = useCallback((value: string) => {
    setGradeInputValue(value)
  }, [])

  const handleApplyGradeMapping = useCallback(() => {
    // Parse comma-separated grades
    const grades = gradeInputValue
      .split(',')
      .map(g => g.trim())
      .filter(g => g.length > 0)
    
    if (grades.length === 0 || !selectedGradeAdmin) {
      return
    }

    // Merge new mappings with existing ones
    const newMappings = { ...gradeMappings }
    grades.forEach(grade => {
      newMappings[grade] = selectedGradeAdmin
    })

    const newConfig: AssignmentConfig = {
      type: 'grade',
      grade_mappings: newMappings,
    }
    onChange(newConfig)
    
    // Clear inputs
    setGradeInputValue('')
    setSelectedGradeAdmin('')
  }, [gradeInputValue, selectedGradeAdmin, gradeMappings, onChange])


  const handleLetterRangeRemove = useCallback(
    (range: string) => {
      const newRanges = { ...letterRanges }
      delete newRanges[range]
      const newConfig: AssignmentConfig = {
        type: 'alphabetical',
        letter_ranges: newRanges,
        name_field: nameField,
      }
      onChange(newConfig)
    },
    [letterRanges, nameField, onChange]
  )

  const handleLetterRangeInputChange = useCallback((value: string) => {
    setLetterRangeInputValue(value)
  }, [])

  const handleApplyLetterRange = useCallback(() => {
    // Parse comma-separated letter ranges
    const ranges = letterRangeInputValue
      .split(',')
      .map(r => r.trim())
      .filter(r => r.length > 0)
    
    if (ranges.length === 0 || !selectedLetterRangeAdmin) {
      return
    }

    // Create mappings for all ranges to the selected admin
    const newRanges: Record<string, string> = {}
    ranges.forEach(range => {
      newRanges[range] = selectedLetterRangeAdmin
    })

    const newConfig: AssignmentConfig = {
      type: 'alphabetical',
      letter_ranges: { ...letterRanges, ...newRanges },
      name_field: nameField,
    }
    onChange(newConfig)
    
    // Clear inputs
    setLetterRangeInputValue('')
    setSelectedLetterRangeAdmin('')
  }, [letterRangeInputValue, selectedLetterRangeAdmin, letterRanges, nameField, onChange])

  const handleNameFieldChange = useCallback(
    (field: 'first_name' | 'last_name') => {
      const newConfig: AssignmentConfig = {
        type: 'alphabetical',
        letter_ranges: letterRanges,
        name_field: field,
      }
      onChange(newConfig)
    },
    [letterRanges, onChange]
  )

  const adminOptions = useMemo(() => {
    return admins
      .filter((admin) => admin.user_id) // Only include admins with user_id
      .map((admin) => ({
        id: admin.user_id!,
        name: admin.full_name || admin.email || 'Unknown',
      }))
  }, [admins])

  if (adminsLoading) {
    return <div className="text-sm text-muted-foreground">Loading admins...</div>
  }

  if (adminOptions.length === 0) {
    return (
      <div className="text-sm text-muted-foreground">
        No active admins found. Add admins to configure assignment rules.
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Label htmlFor="assignment-type">Assignment Method</Label>
        <Select
          value={assignmentType ?? 'manual'}
          onValueChange={(value) =>
            handleTypeChange(value === 'manual' ? null : (value as AssignmentConfig['type']))
          }
          disabled={disabled}
        >
          <SelectTrigger id="assignment-type">
            <SelectValue placeholder="Select assignment method" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="manual">Manual (No automatic assignment)</SelectItem>
            <SelectItem value="grade">By Grade Level</SelectItem>
            <SelectItem value="alphabetical">By Alphabetical Order</SelectItem>
          </SelectContent>
        </Select>
        <p className="text-xs text-muted-foreground">
          Choose how referrals are automatically assigned to admins.
        </p>
      </div>

      {assignmentType === 'grade' && (
        <div className="space-y-4 rounded-lg border p-4">
          <div>
            <h4 className="text-sm font-semibold">Grade Level Mappings</h4>
            <p className="text-xs text-muted-foreground">
              Enter comma-separated grade levels and assign them to an admin. Students will be assigned based on their grade.
            </p>
          </div>
          
          {/* Add new grade mapping */}
          <div className="space-y-3 rounded-md border bg-muted/50 p-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label htmlFor="grade-input" className="text-xs">
                  Grade Levels (comma-separated)
                </Label>
                <Input
                  id="grade-input"
                  value={gradeInputValue}
                  onChange={(e) => handleGradeInputChange(e.target.value)}
                  placeholder="e.g. 9, 10, 11, 12"
                  disabled={disabled}
                />
              </div>
              <div>
                <Label htmlFor="grade-admin-select" className="text-xs">
                  Assign to Admin
                </Label>
                <Select
                  value={selectedGradeAdmin}
                  onValueChange={setSelectedGradeAdmin}
                  disabled={disabled}
                >
                  <SelectTrigger id="grade-admin-select">
                    <SelectValue placeholder="Select admin" />
                  </SelectTrigger>
                  <SelectContent>
                    {adminOptions.map((admin) => (
                      <SelectItem key={admin.id} value={admin.id}>
                        {admin.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <Button
              type="button"
              variant="default"
              size="sm"
              onClick={handleApplyGradeMapping}
              disabled={disabled || !gradeInputValue.trim() || !selectedGradeAdmin}
            >
              <Plus className="mr-1 h-4 w-4" />
              Add Mapping
            </Button>
          </div>

          {/* Display existing mappings */}
          {Object.keys(gradeMappings).length > 0 && (
            <div className="space-y-2">
              <h5 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                Current Mappings
              </h5>
              <div className="space-y-2">
                {Object.entries(gradeMappings)
                  .filter(([grade]) => !grade.startsWith('__temp_'))
                  .map(([grade, adminId]) => {
                    const admin = adminOptions.find(a => a.id === adminId)
                    return (
                      <div
                        key={grade}
                        className="flex items-center justify-between rounded-md border bg-background px-3 py-2"
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-sm font-medium">Grade {grade}</span>
                          <span className="text-sm text-muted-foreground">→</span>
                          <span className="text-sm">{admin?.name || 'Unknown'}</span>
                        </div>
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 text-destructive"
                          onClick={() => handleGradeMappingRemove(grade)}
                          disabled={disabled}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    )
                  })}
              </div>
            </div>
          )}
        </div>
      )}

      {assignmentType === 'alphabetical' && (
        <div className="space-y-4 rounded-lg border p-4">
          <div className="space-y-2">
            <Label htmlFor="name-field">Name Field</Label>
            <Select
              value={nameField}
              onValueChange={(value) =>
                handleNameFieldChange(value as 'first_name' | 'last_name')
              }
              disabled={disabled}
            >
              <SelectTrigger id="name-field">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="last_name">Last Name</SelectItem>
                <SelectItem value="first_name">First Name</SelectItem>
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              Choose whether to assign based on student's first or last name.
            </p>
          </div>
          <div>
            <h4 className="text-sm font-semibold">Letter Range Mappings</h4>
            <p className="text-xs text-muted-foreground">
              Enter comma-separated letter ranges and assign them to an admin. Use single letters (e.g., "A") or ranges (e.g., "A-M").
            </p>
          </div>
          
          {/* Add new letter range mapping */}
          <div className="space-y-3 rounded-md border bg-muted/50 p-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label htmlFor="range-input" className="text-xs">
                  Letter Ranges (comma-separated)
                </Label>
                <Input
                  id="range-input"
                  value={letterRangeInputValue}
                  onChange={(e) => handleLetterRangeInputChange(e.target.value)}
                  placeholder="e.g. A-M, N-Z, or A, B, C"
                  disabled={disabled}
                />
              </div>
              <div>
                <Label htmlFor="range-admin-select" className="text-xs">
                  Assign to Admin
                </Label>
                <Select
                  value={selectedLetterRangeAdmin}
                  onValueChange={setSelectedLetterRangeAdmin}
                  disabled={disabled}
                >
                  <SelectTrigger id="range-admin-select">
                    <SelectValue placeholder="Select admin" />
                  </SelectTrigger>
                  <SelectContent>
                    {adminOptions.map((admin) => (
                      <SelectItem key={admin.id} value={admin.id}>
                        {admin.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <Button
              type="button"
              variant="default"
              size="sm"
              onClick={handleApplyLetterRange}
              disabled={disabled || !letterRangeInputValue.trim() || !selectedLetterRangeAdmin}
            >
              <Plus className="mr-1 h-4 w-4" />
              Add Mapping
            </Button>
          </div>

          {/* Display existing mappings */}
          {Object.keys(letterRanges).length > 0 && (
            <div className="space-y-2">
              <h5 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                Current Mappings
              </h5>
              <div className="space-y-2">
                {Object.entries(letterRanges)
                  .filter(([range]) => !range.startsWith('__temp_'))
                  .map(([range, adminId]) => {
                    const admin = adminOptions.find(a => a.id === adminId)
                    return (
                      <div
                        key={range}
                        className="flex items-center justify-between rounded-md border bg-background px-3 py-2"
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-sm font-medium">{range}</span>
                          <span className="text-sm text-muted-foreground">→</span>
                          <span className="text-sm">{admin?.name || 'Unknown'}</span>
                        </div>
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 text-destructive"
                          onClick={() => handleLetterRangeRemove(range)}
                          disabled={disabled}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    )
                  })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

