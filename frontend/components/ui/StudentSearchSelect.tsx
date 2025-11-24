'use client'

import { useState, useEffect, useRef } from 'react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Loader } from '@/components/ui/loader'
import apiClient from '@/lib/apiClient'
import { useErrorHandler } from '@/hooks/useErrorHandler'
import { Search, X, Check } from 'lucide-react'
import { cn } from '@/lib/utils'

interface StudentOption {
  id: string
  full_name: string | null
  student_id: string | null
  grade_level: string | null
}

interface StudentSearchSelectProps {
  orgId: string
  value: string
  onValueChange: (value: string) => void
  label?: string
  required?: boolean
  error?: string
}

export function StudentSearchSelect({
  orgId,
  value,
  onValueChange,
  label = 'Student',
  required = false,
  error,
}: StudentSearchSelectProps) {
  const { handleError } = useErrorHandler()
  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [students, setStudents] = useState<StudentOption[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isOpen, setIsOpen] = useState(false)
  const [selectedStudent, setSelectedStudent] = useState<StudentOption | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const studentsRef = useRef<StudentOption[]>([])
  const isUserTypingRef = useRef(false)

  // Debounce search query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery)
    }, 300)

    return () => clearTimeout(timer)
  }, [searchQuery])

  // Fetch students when search query changes
  useEffect(() => {
    async function fetchStudents() {
      if (!orgId) return

      setIsLoading(true)
      try {
        const params = new URLSearchParams({
          page: '1',
          per_page: '20', // Limit results for dropdown
        })
        
        if (debouncedSearch.trim()) {
          params.set('search', debouncedSearch.trim())
        }

        const response = await apiClient<{
          profiles: StudentOption[]
          total: number
          total_pages: number
        }>(`/api/v1/organizations/${orgId}/students?${params.toString()}`)

        const newStudents = response.profiles || []
        setStudents(newStudents)
        studentsRef.current = newStudents
      } catch (err) {
        handleError(err, { title: 'Failed to search students' })
        setStudents([])
      } finally {
        setIsLoading(false)
      }
    }

    fetchStudents()
  }, [orgId, debouncedSearch, handleError])

  // Load selected student details when value changes (only when value or orgId changes)
  useEffect(() => {
    // Don't interfere if user is actively typing
    if (isUserTypingRef.current) {
      return
    }

    async function loadSelectedStudent() {
      if (!value || !orgId) {
        setSelectedStudent(null)
        // Only clear search query if value is explicitly cleared from parent
        // Don't clear if user is actively typing
        if (!value && selectedStudent) {
          setSearchQuery('')
        }
        return
      }

      // If we already have the student in our current list (from ref to avoid stale closure), use it
      const found = studentsRef.current.find(s => s.id === value)
      if (found) {
        setSelectedStudent(found)
        setSearchQuery(formatStudentDisplay(found))
        return
      }

      // Otherwise, fetch the specific student by fetching a page and finding by ID
      // Note: We can't search by UUID directly, so we fetch a page and look for it
      // In practice, this should rarely be needed since selection happens from search results
      try {
        const response = await apiClient<{
          profiles: StudentOption[]
          total: number
        }>(`/api/v1/organizations/${orgId}/students?page=1&per_page=100`)
        
        const student = response.profiles?.find(s => s.id === value)
        if (student) {
          setSelectedStudent(student)
          setSearchQuery(formatStudentDisplay(student))
        } else {
          // If not found, clear the selection
          setSelectedStudent(null)
          setSearchQuery('')
        }
      } catch (err) {
        // If we can't find it, just clear
        setSelectedStudent(null)
        setSearchQuery('')
      }
    }

    // Only load if value actually changed and we don't already have it selected
    if (value && (!selectedStudent || selectedStudent.id !== value)) {
      loadSelectedStudent()
    } else if (!value && selectedStudent) {
      // Clear selection if value is cleared from parent
      setSelectedStudent(null)
      setSearchQuery('')
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value, orgId]) // Only depend on value and orgId - studentsRef is used to avoid stale closures

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const formatStudentDisplay = (student: StudentOption): string => {
    const parts: string[] = []
    if (student.full_name) parts.push(student.full_name)
    if (student.student_id) parts.push(`(${student.student_id})`)
    if (student.grade_level) parts.push(`Grade ${student.grade_level}`)
    return parts.join(' ')
  }

  const handleSelect = (student: StudentOption) => {
    isUserTypingRef.current = false // User is done typing, they selected
    setSelectedStudent(student)
    setSearchQuery(formatStudentDisplay(student))
    onValueChange(student.id)
    setIsOpen(false)
  }

  const handleClear = () => {
    setSelectedStudent(null)
    setSearchQuery('')
    onValueChange('')
    setIsOpen(false)
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newQuery = e.target.value
    isUserTypingRef.current = true
    setSearchQuery(newQuery)
    
    // If user clears the input, clear selection
    if (!newQuery.trim()) {
      setSelectedStudent(null)
      onValueChange('')
    }
    
    // Open dropdown when typing
    if (newQuery.trim() && !isOpen) {
      setIsOpen(true)
    }

    // Reset typing flag after debounce delay
    setTimeout(() => {
      isUserTypingRef.current = false
    }, 400) // Slightly longer than debounce delay
  }

  const handleInputFocus = () => {
    if (searchQuery.trim() || students.length > 0) {
      setIsOpen(true)
    }
  }

  return (
    <div className="space-y-2" ref={containerRef}>
      {label && (
        <Label htmlFor="student-search">
          {label} {required && <span className="text-destructive">*</span>}
        </Label>
      )}
      <div className="relative">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
          <Input
            ref={inputRef}
            id="student-search"
            type="text"
            placeholder="Search by name or student ID..."
            value={searchQuery}
            onChange={handleInputChange}
            onFocus={handleInputFocus}
            className={cn(
              "pl-10 pr-10",
              error && "border-destructive"
            )}
            autoComplete="off"
          />
          {selectedStudent && (
            <button
              type="button"
              onClick={handleClear}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground hover:text-foreground"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        {/* Dropdown */}
        {isOpen && (
          <div className="absolute z-50 w-full mt-1 bg-popover border rounded-md shadow-lg max-h-60 overflow-auto">
            {isLoading ? (
              <div className="flex items-center justify-center py-4">
                <Loader />
              </div>
            ) : students.length === 0 ? (
              <div className="px-3 py-2 text-sm text-muted-foreground">
                {debouncedSearch.trim() ? 'No students found' : 'Start typing to search...'}
              </div>
            ) : (
              <div className="py-1">
                {students.map((student) => (
                  <button
                    key={student.id}
                    type="button"
                    onClick={() => handleSelect(student)}
                    className={cn(
                      "w-full text-left px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground flex items-center justify-between",
                      selectedStudent?.id === student.id && "bg-accent"
                    )}
                  >
                    <div>
                      <div className="font-medium">
                        {student.full_name || 'Unknown'}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {student.student_id && `ID: ${student.student_id}`}
                        {student.student_id && student.grade_level && ' • '}
                        {student.grade_level && `Grade ${student.grade_level}`}
                      </div>
                    </div>
                    {selectedStudent?.id === student.id && (
                      <Check className="h-4 w-4 text-primary" />
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
      {error && (
        <p className="text-sm text-destructive">{error}</p>
      )}
    </div>
  )
}

