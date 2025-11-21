'use client'

import { useState } from 'react'
import apiClient from '@/lib/apiClient'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { useErrorHandler } from '@/hooks/useErrorHandler'
import { useToast } from '@/hooks/useToast'
import { Loader } from '@/components/ui/loader'
import PhoneInput from 'react-phone-number-input'
import { ChevronDown, ChevronUp } from 'lucide-react'

interface CreateStudentGuardianFormProps {
  orgId: string
  onSuccess?: () => void
}

export function CreateStudentGuardianForm({ orgId, onSuccess }: CreateStudentGuardianFormProps) {
  const [activeTab, setActiveTab] = useState<'single' | 'bulk' | 'csv'>('single')
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Create Student & Guardian Profiles</CardTitle>
        <CardDescription>
          Create student and guardian profiles without requiring login accounts.
          These are data records that can be linked together.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Tab Navigation */}
        <div className="border-b border-gray-200 mb-4">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('single')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'single'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Single
            </button>
            <button
              onClick={() => setActiveTab('bulk')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'bulk'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Bulk
            </button>
            <button
              onClick={() => setActiveTab('csv')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'csv'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              CSV Upload
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === 'single' && (
          <SingleCreateForm orgId={orgId} onSuccess={onSuccess} />
        )}
        {activeTab === 'bulk' && (
          <BulkCreateForm orgId={orgId} onSuccess={onSuccess} />
        )}
        {activeTab === 'csv' && (
          <CSVUploadForm orgId={orgId} onSuccess={onSuccess} />
        )}
      </CardContent>
    </Card>
  )
}

interface StudentFormData {
  full_name: string
  grade_level: string
  student_id: string
  email?: string
  phone?: string
  street_number?: string
  street_name?: string
  city?: string
  state?: string
  zip_code?: string
  country?: string
  preferred_language?: string
}

interface GuardianFormData {
  full_name: string
  email: string
  phone?: string
  street_number?: string
  street_name?: string
  city?: string
  state?: string
  zip_code?: string
  country?: string
  preferred_language?: string
}

function SingleCreateForm({ orgId, onSuccess }: { orgId: string; onSuccess?: () => void }) {
  const [studentData, setStudentData] = useState<StudentFormData>({
    full_name: '',
    grade_level: '',
    student_id: '',
    email: '',
    phone: '',
    street_number: '',
    street_name: '',
    city: '',
    state: '',
    zip_code: '',
    country: '',
    preferred_language: '',
  })
  const [guardianData, setGuardianData] = useState<GuardianFormData>({
    full_name: '',
    email: '',
    phone: '',
    street_number: '',
    street_name: '',
    city: '',
    state: '',
    zip_code: '',
    country: '',
    preferred_language: '',
  })
  const [linkImmediately, setLinkImmediately] = useState(true)
  const [relationshipType, setRelationshipType] = useState('primary')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { handleError } = useErrorHandler()
  const { toast } = useToast()

  const updateStudentField = (field: keyof StudentFormData, value: string) => {
    setStudentData(prev => ({ ...prev, [field]: value }))
  }

  const updateGuardianField = (field: keyof GuardianFormData, value: string) => {
    setGuardianData(prev => ({ ...prev, [field]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      // Prepare student payload
      const studentPayload: any = {
        full_name: studentData.full_name,
        grade_level: studentData.grade_level,
        student_id: studentData.student_id,
      }
      if (studentData.email) studentPayload.email = studentData.email
      if (studentData.phone) studentPayload.phone = studentData.phone
      if (studentData.street_number) studentPayload.street_number = studentData.street_number
      if (studentData.street_name) studentPayload.street_name = studentData.street_name
      if (studentData.city) studentPayload.city = studentData.city
      if (studentData.state) studentPayload.state = studentData.state
      if (studentData.zip_code) studentPayload.zip_code = studentData.zip_code
      if (studentData.country) studentPayload.country = studentData.country
      if (studentData.preferred_language) studentPayload.preferred_language = studentData.preferred_language

      // Prepare guardian payload
      const guardianPayload: any = {
        full_name: guardianData.full_name,
        email: guardianData.email,
      }
      if (guardianData.phone) guardianPayload.phone = guardianData.phone
      if (guardianData.street_number) guardianPayload.street_number = guardianData.street_number
      if (guardianData.street_name) guardianPayload.street_name = guardianData.street_name
      if (guardianData.city) guardianPayload.city = guardianData.city
      if (guardianData.state) guardianPayload.state = guardianData.state
      if (guardianData.zip_code) guardianPayload.zip_code = guardianData.zip_code
      if (guardianData.country) guardianPayload.country = guardianData.country
      if (guardianData.preferred_language) guardianPayload.preferred_language = guardianData.preferred_language

      // Create student
      const studentResponse = await apiClient(
        `/api/v1/organizations/${orgId}/students`,
        {
          method: 'POST',
          body: studentPayload,
        }
      ) as any

      // Create guardian
      const guardianResponse = await apiClient(
        `/api/v1/organizations/${orgId}/guardians`,
        {
          method: 'POST',
          body: guardianPayload,
        }
      ) as any

      // Link them if requested
      if (linkImmediately) {
        await apiClient(
          `/api/v1/organizations/${orgId}/guardians/link`,
          {
            method: 'POST',
            body: {
              student_id: studentResponse.id,
              guardian_id: guardianResponse.id,
              relationship_type: relationshipType,
            },
          }
        )
        toast({
          variant: "success",
          title: "Student and guardian created",
          description: `Successfully created and linked student "${studentData.full_name}" with guardian "${guardianData.full_name}".`,
        })
      } else {
        toast({
          variant: "success",
          title: "Student and guardian created",
          description: `Successfully created student "${studentData.full_name}" and guardian "${guardianData.full_name}".`,
        })
      }

      // Reset form
      setStudentData({
        full_name: '',
        grade_level: '',
        student_id: '',
        email: '',
        phone: '',
        street_number: '',
        street_name: '',
        city: '',
        state: '',
        zip_code: '',
        country: '',
        preferred_language: '',
      })
      setGuardianData({
        full_name: '',
        email: '',
        phone: '',
        street_number: '',
        street_name: '',
        city: '',
        state: '',
        zip_code: '',
        country: '',
        preferred_language: '',
      })
      
      onSuccess?.()
    } catch (err) {
      handleError(err, { title: "Failed to create student and guardian" })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-2 gap-6">
        {/* Student Section */}
        <div className="space-y-4">
          <h3 className="font-semibold text-lg">Student</h3>
          
          <div className="space-y-2">
            <Label htmlFor="student-name">Full Name *</Label>
            <Input
              id="student-name"
              value={studentData.full_name}
              onChange={(e) => updateStudentField('full_name', e.target.value)}
              placeholder="John Doe"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="student-grade">Grade Level *</Label>
            <Input
              id="student-grade"
              value={studentData.grade_level}
              onChange={(e) => updateStudentField('grade_level', e.target.value)}
              placeholder="9"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="student-id">Student ID *</Label>
            <Input
              id="student-id"
              value={studentData.student_id}
              onChange={(e) => updateStudentField('student_id', e.target.value)}
              placeholder="STU001"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="student-email">Email</Label>
            <Input
              id="student-email"
              type="email"
              value={studentData.email}
              onChange={(e) => updateStudentField('email', e.target.value)}
              placeholder="john@example.com"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="student-phone">Phone</Label>
            <div className="[&_.PhoneInput]:flex [&_.PhoneInput]:items-center [&_.PhoneInput]:gap-2 [&_.PhoneInput]:w-full [&_.PhoneInputInput]:flex-1 [&_.PhoneInputInput]:h-10 [&_.PhoneInputInput]:w-full [&_.PhoneInputInput]:rounded-md [&_.PhoneInputInput]:border [&_.PhoneInputInput]:border-input [&_.PhoneInputInput]:bg-background [&_.PhoneInputInput]:px-3 [&_.PhoneInputInput]:py-2 [&_.PhoneInputInput]:text-sm [&_.PhoneInputInput]:ring-offset-background [&_.PhoneInputInput]:placeholder:text-muted-foreground [&_.PhoneInputInput]:focus-visible:outline-none [&_.PhoneInputInput]:focus-visible:ring-2 [&_.PhoneInputInput]:focus-visible:ring-ring [&_.PhoneInputInput]:focus-visible:ring-offset-2 [&_.PhoneInputCountry]:mr-2 [&_.PhoneInputCountryIcon]:w-6 [&_.PhoneInputCountryIcon]:h-6 [&_.PhoneInputCountryIcon]:rounded [&_.PhoneInputCountrySelect]:px-2 [&_.PhoneInputCountrySelect]:py-1 [&_.PhoneInputCountrySelect]:text-sm [&_.PhoneInputCountrySelect]:rounded-md [&_.PhoneInputCountrySelect]:border [&_.PhoneInputCountrySelect]:border-input [&_.PhoneInputCountrySelect]:bg-background">
              <PhoneInput
                international
                defaultCountry="US"
                value={studentData.phone || undefined}
                onChange={(value) => updateStudentField('phone', value || '')}
                placeholder="Enter phone number"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div className="space-y-2">
              <Label htmlFor="student-street-number">Street Number</Label>
              <Input
                id="student-street-number"
                value={studentData.street_number}
                onChange={(e) => updateStudentField('street_number', e.target.value)}
                placeholder="123"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="student-street-name">Street Name</Label>
              <Input
                id="student-street-name"
                value={studentData.street_name}
                onChange={(e) => updateStudentField('street_name', e.target.value)}
                placeholder="Main St"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div className="space-y-2">
              <Label htmlFor="student-city">City</Label>
              <Input
                id="student-city"
                value={studentData.city}
                onChange={(e) => updateStudentField('city', e.target.value)}
                placeholder="Springfield"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="student-state">State</Label>
              <Input
                id="student-state"
                value={studentData.state}
                onChange={(e) => updateStudentField('state', e.target.value)}
                placeholder="IL"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div className="space-y-2">
              <Label htmlFor="student-zip">ZIP Code</Label>
              <Input
                id="student-zip"
                value={studentData.zip_code}
                onChange={(e) => updateStudentField('zip_code', e.target.value)}
                placeholder="62701"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="student-country">Country</Label>
              <Input
                id="student-country"
                value={studentData.country}
                onChange={(e) => updateStudentField('country', e.target.value)}
                placeholder="USA"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="student-language">Preferred Language</Label>
            <Input
              id="student-language"
              value={studentData.preferred_language}
              onChange={(e) => updateStudentField('preferred_language', e.target.value)}
              placeholder="en"
            />
          </div>
        </div>

        {/* Guardian Section */}
        <div className="space-y-4">
          <h3 className="font-semibold text-lg">Guardian</h3>
          
          <div className="space-y-2">
            <Label htmlFor="guardian-name">Full Name *</Label>
            <Input
              id="guardian-name"
              value={guardianData.full_name}
              onChange={(e) => updateGuardianField('full_name', e.target.value)}
              placeholder="Jane Doe"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="guardian-email">Email *</Label>
            <Input
              id="guardian-email"
              type="email"
              value={guardianData.email}
              onChange={(e) => updateGuardianField('email', e.target.value)}
              placeholder="jane@example.com"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="guardian-phone">Phone</Label>
            <div className="[&_.PhoneInput]:flex [&_.PhoneInput]:items-center [&_.PhoneInput]:gap-2 [&_.PhoneInput]:w-full [&_.PhoneInputInput]:flex-1 [&_.PhoneInputInput]:h-10 [&_.PhoneInputInput]:w-full [&_.PhoneInputInput]:rounded-md [&_.PhoneInputInput]:border [&_.PhoneInputInput]:border-input [&_.PhoneInputInput]:bg-background [&_.PhoneInputInput]:px-3 [&_.PhoneInputInput]:py-2 [&_.PhoneInputInput]:text-sm [&_.PhoneInputInput]:ring-offset-background [&_.PhoneInputInput]:placeholder:text-muted-foreground [&_.PhoneInputInput]:focus-visible:outline-none [&_.PhoneInputInput]:focus-visible:ring-2 [&_.PhoneInputInput]:focus-visible:ring-ring [&_.PhoneInputInput]:focus-visible:ring-offset-2 [&_.PhoneInputCountry]:mr-2 [&_.PhoneInputCountryIcon]:w-6 [&_.PhoneInputCountryIcon]:h-6 [&_.PhoneInputCountryIcon]:rounded [&_.PhoneInputCountrySelect]:px-2 [&_.PhoneInputCountrySelect]:py-1 [&_.PhoneInputCountrySelect]:text-sm [&_.PhoneInputCountrySelect]:rounded-md [&_.PhoneInputCountrySelect]:border [&_.PhoneInputCountrySelect]:border-input [&_.PhoneInputCountrySelect]:bg-background">
              <PhoneInput
                international
                defaultCountry="US"
                value={guardianData.phone || undefined}
                onChange={(value) => updateGuardianField('phone', value || '')}
                placeholder="Enter phone number"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div className="space-y-2">
              <Label htmlFor="guardian-street-number">Street Number</Label>
              <Input
                id="guardian-street-number"
                value={guardianData.street_number}
                onChange={(e) => updateGuardianField('street_number', e.target.value)}
                placeholder="123"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="guardian-street-name">Street Name</Label>
              <Input
                id="guardian-street-name"
                value={guardianData.street_name}
                onChange={(e) => updateGuardianField('street_name', e.target.value)}
                placeholder="Main St"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div className="space-y-2">
              <Label htmlFor="guardian-city">City</Label>
              <Input
                id="guardian-city"
                value={guardianData.city}
                onChange={(e) => updateGuardianField('city', e.target.value)}
                placeholder="Springfield"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="guardian-state">State</Label>
              <Input
                id="guardian-state"
                value={guardianData.state}
                onChange={(e) => updateGuardianField('state', e.target.value)}
                placeholder="IL"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div className="space-y-2">
              <Label htmlFor="guardian-zip">ZIP Code</Label>
              <Input
                id="guardian-zip"
                value={guardianData.zip_code}
                onChange={(e) => updateGuardianField('zip_code', e.target.value)}
                placeholder="62701"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="guardian-country">Country</Label>
              <Input
                id="guardian-country"
                value={guardianData.country}
                onChange={(e) => updateGuardianField('country', e.target.value)}
                placeholder="USA"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="guardian-language">Preferred Language</Label>
            <Input
              id="guardian-language"
              value={guardianData.preferred_language}
              onChange={(e) => updateGuardianField('preferred_language', e.target.value)}
              placeholder="en"
            />
          </div>
        </div>
      </div>

      {linkImmediately && (
        <div className="space-y-2">
          <Label htmlFor="relationship-type">Relationship Type</Label>
          <select
            id="relationship-type"
            value={relationshipType}
            onChange={(e) => setRelationshipType(e.target.value)}
            className="w-full p-2 border rounded"
          >
            <option value="primary">Primary</option>
            <option value="secondary">Secondary</option>
            <option value="emergency">Emergency</option>
          </select>
        </div>
      )}

      <div className="flex items-center space-x-2">
        <input
          type="checkbox"
          id="link-immediately"
          checked={linkImmediately}
          onChange={(e) => setLinkImmediately(e.target.checked)}
          className="rounded"
        />
        <Label htmlFor="link-immediately">Link student and guardian immediately</Label>
      </div>

      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Creating...' : 'Create Profiles'}
      </Button>
    </form>
  )
}

function BulkCreateForm({ orgId, onSuccess }: { orgId: string; onSuccess?: () => void }) {
  const [pairs, setPairs] = useState<Array<{
    student: StudentFormData
    guardian: GuardianFormData
    relationship_type: string
  }>>([{
    student: {
      full_name: '',
      grade_level: '',
      student_id: '',
      email: '',
      phone: '',
      street_number: '',
      street_name: '',
      city: '',
      state: '',
      zip_code: '',
      country: '',
      preferred_language: '',
    },
    guardian: {
      full_name: '',
      email: '',
      phone: '',
      street_number: '',
      street_name: '',
      city: '',
      state: '',
      zip_code: '',
      country: '',
      preferred_language: '',
    },
    relationship_type: 'primary'
  }])
  const [expandedPairs, setExpandedPairs] = useState<boolean[]>([true])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { handleError } = useErrorHandler()
  const { toast } = useToast()

  const addPair = () => {
    setPairs(prev => [
      ...prev,
      {
        student: {
          full_name: '',
          grade_level: '',
          student_id: '',
          email: '',
          phone: '',
          street_number: '',
          street_name: '',
          city: '',
          state: '',
          zip_code: '',
          country: '',
          preferred_language: '',
        },
        guardian: {
          full_name: '',
          email: '',
          phone: '',
          street_number: '',
          street_name: '',
          city: '',
          state: '',
          zip_code: '',
          country: '',
          preferred_language: '',
        },
        relationship_type: 'primary',
      },
    ])
    setExpandedPairs((prev) => [...prev, true])
  }

  const removePair = (index: number) => {
    setPairs(pairs.filter((_, i) => i !== index))
    setExpandedPairs(expandedPairs.filter((_, i) => i !== index))
  }

  const updatePair = (index: number, type: 'student' | 'guardian', field: string, value: string) => {
    const newPairs = [...pairs]
    ;(newPairs[index][type] as any)[field] = value
    setPairs(newPairs)
  }

  const togglePairVisibility = (index: number) => {
    setExpandedPairs((prev) =>
      prev.map((isOpen, i) => (i === index ? !isOpen : isOpen))
    )
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      const pairsData = pairs
        .filter(p => p.student.full_name && p.student.grade_level && p.student.student_id && p.guardian.full_name && p.guardian.email)
        .map(p => {
          const studentPayload: any = {
            full_name: p.student.full_name,
            grade_level: p.student.grade_level,
            student_id: p.student.student_id,
          }
          if (p.student.email) studentPayload.email = p.student.email
          if (p.student.phone) studentPayload.phone = p.student.phone
          if (p.student.street_number) studentPayload.street_number = p.student.street_number
          if (p.student.street_name) studentPayload.street_name = p.student.street_name
          if (p.student.city) studentPayload.city = p.student.city
          if (p.student.state) studentPayload.state = p.student.state
          if (p.student.zip_code) studentPayload.zip_code = p.student.zip_code
          if (p.student.country) studentPayload.country = p.student.country
          if (p.student.preferred_language) studentPayload.preferred_language = p.student.preferred_language

          const guardianPayload: any = {
            full_name: p.guardian.full_name,
            email: p.guardian.email,
          }
          if (p.guardian.phone) guardianPayload.phone = p.guardian.phone
          if (p.guardian.street_number) guardianPayload.street_number = p.guardian.street_number
          if (p.guardian.street_name) guardianPayload.street_name = p.guardian.street_name
          if (p.guardian.city) guardianPayload.city = p.guardian.city
          if (p.guardian.state) guardianPayload.state = p.guardian.state
          if (p.guardian.zip_code) guardianPayload.zip_code = p.guardian.zip_code
          if (p.guardian.country) guardianPayload.country = p.guardian.country
          if (p.guardian.preferred_language) guardianPayload.preferred_language = p.guardian.preferred_language

          return {
            student: studentPayload,
            guardian: guardianPayload,
            relationship_type: p.relationship_type,
          }
        })

      if (pairsData.length === 0) {
        toast({
          variant: "destructive",
          title: "Validation error",
          description: "Please add at least one valid student-guardian pair with all required fields.",
        })
        setIsSubmitting(false)
        return
      }

      const response = await apiClient(
        `/api/v1/organizations/${orgId}/pairs/bulk`,
        {
          method: 'POST',
          body: { pairs: pairsData },
        }
      ) as any

      toast({
        variant: "success",
        title: "Bulk creation successful",
        description: `Successfully created and linked ${response.created} student-guardian pair(s).`,
      })
      setPairs([{
        student: {
          full_name: '',
          grade_level: '',
          student_id: '',
          email: '',
        },
        guardian: {
          full_name: '',
          email: '',
        },
        relationship_type: 'primary'
      }])
      onSuccess?.()
    } catch (err) {
      handleError(err, { title: "Failed to create student-guardian pairs" })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-4 max-h-96 overflow-y-auto">
        {pairs.map((pair, index) => {
          const isExpanded = expandedPairs[index] ?? true
          return (
            <Card key={index}>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm">Pair {index + 1}</CardTitle>
                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => togglePairVisibility(index)}
                    aria-label={expandedPairs[index] ? "Collapse pair" : "Expand pair"}
                  >
                    {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  </Button>
                  {pairs.length > 1 && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => removePair(index)}
                    >
                      Remove
                    </Button>
                  )}
                </div>
              </div>
            </CardHeader>
            {isExpanded && (
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-semibold text-muted-foreground">Student</h4>
                    <span className="text-xs text-muted-foreground">Contact & details</span>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Full Name *</Label>
                      <Input
                        value={pair.student.full_name}
                        onChange={(e) => updatePair(index, 'student', 'full_name', e.target.value)}
                        placeholder="Student Name"
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Grade Level *</Label>
                      <Input
                        value={pair.student.grade_level}
                        onChange={(e) => updatePair(index, 'student', 'grade_level', e.target.value)}
                        placeholder="9"
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Student ID *</Label>
                      <Input
                        value={pair.student.student_id}
                        onChange={(e) => updatePair(index, 'student', 'student_id', e.target.value)}
                        placeholder="STU001"
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Email</Label>
                      <Input
                        type="email"
                        value={pair.student.email}
                        onChange={(e) => updatePair(index, 'student', 'email', e.target.value)}
                        placeholder="student@example.com"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Preferred Language</Label>
                      <Input
                        value={pair.student.preferred_language}
                        onChange={(e) => updatePair(index, 'student', 'preferred_language', e.target.value)}
                        placeholder="en"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Phone</Label>
                      <div className="[&_.PhoneInput]:flex [&_.PhoneInput]:items-center [&_.PhoneInput]:gap-2 [&_.PhoneInput]:w-full [&_.PhoneInputInput]:flex-1 [&_.PhoneInputInput]:h-10 [&_.PhoneInputInput]:w-full [&_.PhoneInputInput]:rounded-md [&_.PhoneInputInput]:border [&_.PhoneInputInput]:border-input [&_.PhoneInputInput]:bg-background [&_.PhoneInputInput]:px-3 [&_.PhoneInputInput]:py-2 [&_.PhoneInputInput]:text-sm [&_.PhoneInputInput]:ring-offset-background [&_.PhoneInputInput]:placeholder:text-muted-foreground [&_.PhoneInputInput]:focus-visible:outline-none [&_.PhoneInputInput]:focus-visible:ring-2 [&_.PhoneInputInput]:focus-visible:ring-ring [&_.PhoneInputInput]:focus-visible:ring-offset-2 [&_.PhoneInputCountry]:mr-2 [&_.PhoneInputCountryIcon]:w-6 [&_.PhoneInputCountryIcon]:h-6 [&_.PhoneInputCountryIcon]:rounded [&_.PhoneInputCountrySelect]:px-2 [&_.PhoneInputCountrySelect]:py-1 [&_.PhoneInputCountrySelect]:text-sm [&_.PhoneInputCountrySelect]:rounded-md [&_.PhoneInputCountrySelect]:border [&_.PhoneInputCountrySelect]:border-input [&_.PhoneInputCountrySelect]:bg-background">
                        <PhoneInput
                          international
                          defaultCountry="US"
                          value={pair.student.phone || undefined}
                          onChange={(value) => updatePair(index, 'student', 'phone', value || '')}
                          placeholder="Enter phone number"
                        />
                      </div>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Street Number</Label>
                      <Input
                        value={pair.student.street_number}
                        onChange={(e) => updatePair(index, 'student', 'street_number', e.target.value)}
                        placeholder="123"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Street Name</Label>
                      <Input
                        value={pair.student.street_name}
                        onChange={(e) => updatePair(index, 'student', 'street_name', e.target.value)}
                        placeholder="Main St"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>City</Label>
                      <Input
                        value={pair.student.city}
                        onChange={(e) => updatePair(index, 'student', 'city', e.target.value)}
                        placeholder="Springfield"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>State</Label>
                      <Input
                        value={pair.student.state}
                        onChange={(e) => updatePair(index, 'student', 'state', e.target.value)}
                        placeholder="IL"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>ZIP Code</Label>
                      <Input
                        value={pair.student.zip_code}
                        onChange={(e) => updatePair(index, 'student', 'zip_code', e.target.value)}
                        placeholder="62701"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Country</Label>
                      <Input
                        value={pair.student.country}
                        onChange={(e) => updatePair(index, 'student', 'country', e.target.value)}
                        placeholder="USA"
                      />
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-semibold text-muted-foreground">Guardian</h4>
                    <span className="text-xs text-muted-foreground">Contact & details</span>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Full Name *</Label>
                      <Input
                        value={pair.guardian.full_name}
                        onChange={(e) => updatePair(index, 'guardian', 'full_name', e.target.value)}
                        placeholder="Guardian Name"
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Email *</Label>
                      <Input
                        type="email"
                        value={pair.guardian.email}
                        onChange={(e) => updatePair(index, 'guardian', 'email', e.target.value)}
                        placeholder="guardian@example.com"
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Preferred Language</Label>
                      <Input
                        value={pair.guardian.preferred_language}
                        onChange={(e) => updatePair(index, 'guardian', 'preferred_language', e.target.value)}
                        placeholder="en"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Phone</Label>
                      <div className="[&_.PhoneInput]:flex [&_.PhoneInput]:items-center [&_.PhoneInput]:gap-2 [&_.PhoneInput]:w-full [&_.PhoneInputInput]:flex-1 [&_.PhoneInputInput]:h-10 [&_.PhoneInputInput]:w-full [&_.PhoneInputInput]:rounded-md [&_.PhoneInputInput]:border [&_.PhoneInputInput]:border-input [&_.PhoneInputInput]:bg-background [&_.PhoneInputInput]:px-3 [&_.PhoneInputInput]:py-2 [&_.PhoneInputInput]:text-sm [&_.PhoneInputInput]:ring-offset-background [&_.PhoneInputInput]:placeholder:text-muted-foreground [&_.PhoneInputInput]:focus-visible:outline-none [&_.PhoneInputInput]:focus-visible:ring-2 [&_.PhoneInputInput]:focus-visible:ring-ring [&_.PhoneInputInput]:focus-visible:ring-offset-2 [&_.PhoneInputCountry]:mr-2 [&_.PhoneInputCountryIcon]:w-6 [&_.PhoneInputCountryIcon]:h-6 [&_.PhoneInputCountryIcon]:rounded [&_.PhoneInputCountrySelect]:px-2 [&_.PhoneInputCountrySelect]:py-1 [&_.PhoneInputCountrySelect]:text-sm [&_.PhoneInputCountrySelect]:rounded-md [&_.PhoneInputCountrySelect]:border [&_.PhoneInputCountrySelect]:border-input [&_.PhoneInputCountrySelect]:bg-background">
                        <PhoneInput
                          international
                          defaultCountry="US"
                          value={pair.guardian.phone || undefined}
                          onChange={(value) => updatePair(index, 'guardian', 'phone', value || '')}
                          placeholder="Enter phone number"
                        />
                      </div>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Street Number</Label>
                      <Input
                        value={pair.guardian.street_number}
                        onChange={(e) => updatePair(index, 'guardian', 'street_number', e.target.value)}
                        placeholder="456"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Street Name</Label>
                      <Input
                        value={pair.guardian.street_name}
                        onChange={(e) => updatePair(index, 'guardian', 'street_name', e.target.value)}
                        placeholder="Oak Ave"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>City</Label>
                      <Input
                        value={pair.guardian.city}
                        onChange={(e) => updatePair(index, 'guardian', 'city', e.target.value)}
                        placeholder="Springfield"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>State</Label>
                      <Input
                        value={pair.guardian.state}
                        onChange={(e) => updatePair(index, 'guardian', 'state', e.target.value)}
                        placeholder="IL"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>ZIP Code</Label>
                      <Input
                        value={pair.guardian.zip_code}
                        onChange={(e) => updatePair(index, 'guardian', 'zip_code', e.target.value)}
                        placeholder="62702"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Country</Label>
                      <Input
                        value={pair.guardian.country}
                        onChange={(e) => updatePair(index, 'guardian', 'country', e.target.value)}
                        placeholder="USA"
                      />
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Relationship Type</Label>
                  <select
                    value={pair.relationship_type}
                    onChange={(e) => {
                      const newPairs = [...pairs]
                      newPairs[index].relationship_type = e.target.value
                      setPairs(newPairs)
                    }}
                    className="w-full p-2 border rounded"
                  >
                    <option value="primary">Primary</option>
                    <option value="secondary">Secondary</option>
                    <option value="emergency">Emergency</option>
                  </select>
                </div>
              </CardContent>
            )}
            </Card>
          )
        })}
      </div>

      <Button type="button" variant="outline" onClick={addPair}>
        Add Another Pair
      </Button>

      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Creating...' : `Create ${pairs.length} Pair(s)`}
      </Button>
    </form>
  )
}

function CSVUploadForm({ orgId, onSuccess }: { orgId: string; onSuccess?: () => void }) {
  const [file, setFile] = useState<File | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { handleError } = useErrorHandler()
  const { toast } = useToast()
  const [preview, setPreview] = useState<any[]>([])
  const [parseErrors, setParseErrors] = useState<Array<{ row: number; error: string }>>([])

  // Helper function to normalize phone numbers to E.164 format
  const normalizePhone = (phone: string | undefined): string | undefined => {
    if (!phone || phone.trim() === '') return undefined
    const cleaned = phone.trim().replace(/\s+/g, '').replace(/[()-]/g, '')
    // If it already starts with +, return as is
    if (cleaned.startsWith('+')) return cleaned
    // If it's a US number starting with 1 and 10 digits, add +
    if (/^1\d{10}$/.test(cleaned)) return `+${cleaned}`
    // If it's 10 digits (US number without country code), add +1
    if (/^\d{10}$/.test(cleaned)) return `+1${cleaned}`
    // Otherwise, try adding + and see if it's valid
    return `+${cleaned}`
  }

  // Helper function to parse CSV line handling quoted values
  const parseCSVLine = (line: string): string[] => {
    const result: string[] = []
    let current = ''
    let inQuotes = false
    
    for (let i = 0; i < line.length; i++) {
      const char = line[i]
      const nextChar = line[i + 1]
      
      if (char === '"') {
        if (inQuotes && nextChar === '"') {
          // Escaped quote
          current += '"'
          i++ // Skip next quote
        } else {
          // Toggle quote state
          inQuotes = !inQuotes
        }
      } else if (char === ',' && !inQuotes) {
        // End of field
        result.push(current.trim())
        current = ''
      } else {
        current += char
      }
    }
    
    // Add last field
    result.push(current.trim())
    return result
  }

  const downloadSampleCSV = () => {
    // Create sample CSV content with all fields
    const csvContent = `student_name,student_grade_level,student_id,student_email,student_phone,student_street_number,student_street_name,student_city,student_state,student_zip_code,student_country,student_preferred_language,guardian_name,guardian_email,guardian_phone,guardian_street_number,guardian_street_name,guardian_city,guardian_state,guardian_zip_code,guardian_country,guardian_preferred_language,relationship_type
John Doe,9,STU001,john.doe@example.com,+14155551234,123,Main St,Springfield,IL,62701,USA,en,Jane Doe,jane.doe@example.com,+14155555678,123,Main St,Springfield,IL,62701,USA,en,primary
Alice Smith,10,STU002,alice.smith@example.com,,456,Oak Ave,Chicago,IL,60601,USA,en,Bob Smith,bob.smith@example.com,+14155555679,456,Oak Ave,Chicago,IL,60601,USA,en,primary
Charlie Brown,11,STU003,,+14155551235,789,Elm St,Peoria,IL,61601,USA,es,Lucy Brown,lucy.brown@example.com,,789,Elm St,Peoria,IL,61601,USA,es,secondary`

    // Create a blob and download it
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', 'student_guardian_template.csv')
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (!selectedFile) return

    setFile(selectedFile)
    setParseErrors([])

    // Parse CSV and preview
    const reader = new FileReader()
    reader.onload = (event) => {
      try {
        const text = event.target?.result as string
        const lines = text.split('\n').filter(line => line.trim())
        
        if (lines.length < 2) {
          toast({
            variant: "destructive",
            title: "Invalid CSV",
            description: "CSV must have at least a header row and one data row.",
          })
          return
        }

        const headers = parseCSVLine(lines[0]).map(h => h.trim().toLowerCase().replace(/^"|"$/g, ''))
        const requiredHeaders = ['student_name', 'student_grade_level', 'student_id', 'guardian_name', 'guardian_email']
        const missingHeaders = requiredHeaders.filter(h => !headers.includes(h))
        
        if (missingHeaders.length > 0) {
          toast({
            variant: "destructive",
            title: "Missing columns",
            description: `Missing required columns: ${missingHeaders.join(', ')}`,
          })
          return
        }

        const previewData: any[] = []
        const errors: Array<{ row: number; error: string }> = []

        lines.slice(1, 6).forEach((line, idx) => {
          try {
            const values = parseCSVLine(line).map(v => v.trim().replace(/^"|"$/g, ''))
            const row: any = {}
            headers.forEach((header, index) => {
              row[header] = values[index] || ''
            })
            
            // Validate required fields
            if (!row.student_name || !row.student_grade_level || !row.student_id || !row.guardian_name || !row.guardian_email) {
              errors.push({ row: idx + 2, error: 'Missing required fields' })
            }
            
            previewData.push(row)
          } catch (err) {
            errors.push({ row: idx + 2, error: `Parse error: ${err instanceof Error ? err.message : 'Unknown error'}` })
          }
        })

        setPreview(previewData)
        if (errors.length > 0) {
          setParseErrors(errors)
        }
      } catch (err) {
        handleError(err, { title: "Error parsing CSV" })
      }
    }
    reader.readAsText(selectedFile)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) {
      toast({
        variant: "destructive",
        title: "No file selected",
        description: "Please select a CSV file.",
      })
      return
    }

    setIsSubmitting(true)
    setParseErrors([])

    try {
      const text = await file.text()
      const lines = text.split('\n').filter(line => line.trim())
      const headers = parseCSVLine(lines[0]).map(h => h.trim().toLowerCase().replace(/^"|"$/g, ''))
      
      const pairs: any[] = []
      const errors: Array<{ row: number; error: string }> = []

      // Process each row, collecting errors but continuing
      lines.slice(1).forEach((line, idx) => {
        try {
          const values = parseCSVLine(line).map(v => v.trim().replace(/^"|"$/g, ''))
          const row: any = {}
          headers.forEach((header, index) => {
            row[header] = values[index] || ''
          })
          
          // Validate required fields
          if (!row.student_name || row.student_name.trim() === '') {
            errors.push({ row: idx + 2, error: 'Missing student_name' })
            return
          }
          if (!row.student_grade_level || row.student_grade_level.trim() === '') {
            errors.push({ row: idx + 2, error: 'Missing student_grade_level' })
            return
          }
          if (!row.student_id || row.student_id.trim() === '') {
            errors.push({ row: idx + 2, error: 'Missing student_id' })
            return
          }
          if (!row.guardian_name || row.guardian_name.trim() === '') {
            errors.push({ row: idx + 2, error: 'Missing guardian_name' })
            return
          }
          if (!row.guardian_email || row.guardian_email.trim() === '') {
            errors.push({ row: idx + 2, error: 'Missing guardian_email' })
            return
          }

          // Build student payload
          const studentPayload: any = {
            full_name: row.student_name.trim(),
            grade_level: row.student_grade_level.trim(),
            student_id: row.student_id.trim(),
          }
          if (row.student_email && row.student_email.trim() !== '') {
            studentPayload.email = row.student_email.trim()
          }
          const normalizedStudentPhone = normalizePhone(row.student_phone)
          if (normalizedStudentPhone) {
            studentPayload.phone = normalizedStudentPhone
          }
          if (row.student_street_number && row.student_street_number.trim() !== '') {
            studentPayload.street_number = row.student_street_number.trim()
          }
          if (row.student_street_name && row.student_street_name.trim() !== '') {
            studentPayload.street_name = row.student_street_name.trim()
          }
          if (row.student_city && row.student_city.trim() !== '') {
            studentPayload.city = row.student_city.trim()
          }
          if (row.student_state && row.student_state.trim() !== '') {
            studentPayload.state = row.student_state.trim()
          }
          if (row.student_zip_code && row.student_zip_code.trim() !== '') {
            studentPayload.zip_code = row.student_zip_code.trim()
          }
          if (row.student_country && row.student_country.trim() !== '') {
            studentPayload.country = row.student_country.trim()
          }
          if (row.student_preferred_language && row.student_preferred_language.trim() !== '') {
            studentPayload.preferred_language = row.student_preferred_language.trim()
          }

          // Build guardian payload
          const guardianPayload: any = {
            full_name: row.guardian_name.trim(),
            email: row.guardian_email.trim(),
          }
          const normalizedGuardianPhone = normalizePhone(row.guardian_phone)
          if (normalizedGuardianPhone) {
            guardianPayload.phone = normalizedGuardianPhone
          }
          if (row.guardian_street_number && row.guardian_street_number.trim() !== '') {
            guardianPayload.street_number = row.guardian_street_number.trim()
          }
          if (row.guardian_street_name && row.guardian_street_name.trim() !== '') {
            guardianPayload.street_name = row.guardian_street_name.trim()
          }
          if (row.guardian_city && row.guardian_city.trim() !== '') {
            guardianPayload.city = row.guardian_city.trim()
          }
          if (row.guardian_state && row.guardian_state.trim() !== '') {
            guardianPayload.state = row.guardian_state.trim()
          }
          if (row.guardian_zip_code && row.guardian_zip_code.trim() !== '') {
            guardianPayload.zip_code = row.guardian_zip_code.trim()
          }
          if (row.guardian_country && row.guardian_country.trim() !== '') {
            guardianPayload.country = row.guardian_country.trim()
          }
          if (row.guardian_preferred_language && row.guardian_preferred_language.trim() !== '') {
            guardianPayload.preferred_language = row.guardian_preferred_language.trim()
          }

          pairs.push({
            student: studentPayload,
            guardian: guardianPayload,
            relationship_type: row.relationship_type || 'primary',
          })
        } catch (err) {
          errors.push({ 
            row: idx + 2, 
            error: `Parse error: ${err instanceof Error ? err.message : 'Unknown error'}` 
          })
        }
      })

      if (pairs.length === 0) {
        toast({
          variant: "destructive",
          title: "No valid pairs",
          description: "No valid pairs found in CSV file. Please check the format and required fields.",
        })
        setParseErrors(errors)
        setIsSubmitting(false)
        return
      }

      // Send to backend - backend will handle individual failures gracefully
      const response = await apiClient(
        `/api/v1/organizations/${orgId}/pairs/bulk`,
        {
          method: 'POST',
          body: { pairs },
        }
      ) as any

      let successMessage = `Successfully created and linked ${response.created} student-guardian pair(s) from CSV.`
      if (errors.length > 0) {
        successMessage += ` ${errors.length} row(s) had parsing errors and were skipped.`
      }
      if (pairs.length > response.created) {
        successMessage += ` ${pairs.length - response.created} pair(s) failed to create (check backend logs for details).`
      }

      toast({
        variant: "success",
        title: "CSV upload successful",
        description: successMessage,
      })
      if (errors.length > 0) {
        setParseErrors(errors)
      }
      setFile(null)
      setPreview([])
      onSuccess?.()
    } catch (err) {
      handleError(err, { title: "Failed to create student-guardian pairs" })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-4">
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="csv-file">CSV File</Label>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={downloadSampleCSV}
            >
              Download Sample CSV
            </Button>
          </div>
          <Input
            id="csv-file"
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            required
          />
        </div>

        <div className="space-y-2">
          <Label>CSV Format</Label>
          <div className="bg-gray-50 border rounded p-3 text-sm">
            <p className="font-semibold mb-2">Required columns:</p>
            <ul className="list-disc list-inside space-y-1 mb-3">
              <li><code className="bg-white px-1 rounded">student_name</code> - Full name of the student</li>
              <li><code className="bg-white px-1 rounded">student_grade_level</code> - Grade level of the student</li>
              <li><code className="bg-white px-1 rounded">student_id</code> - Unique student ID</li>
              <li><code className="bg-white px-1 rounded">guardian_name</code> - Full name of the guardian</li>
              <li><code className="bg-white px-1 rounded">guardian_email</code> - Email address of the guardian</li>
            </ul>
            <p className="font-semibold mb-2">Optional columns:</p>
            <ul className="list-disc list-inside space-y-1 mb-3">
              <li><code className="bg-white px-1 rounded">student_email</code> - Email address of the student</li>
              <li><code className="bg-white px-1 rounded">student_phone</code> - Phone number (E.164 format recommended, e.g., +14155551234). Will auto-add + prefix for US numbers.</li>
              <li><code className="bg-white px-1 rounded">student_street_number</code>, <code className="bg-white px-1 rounded">student_street_name</code>, <code className="bg-white px-1 rounded">student_city</code>, <code className="bg-white px-1 rounded">student_state</code>, <code className="bg-white px-1 rounded">student_zip_code</code>, <code className="bg-white px-1 rounded">student_country</code> - Address fields</li>
              <li><code className="bg-white px-1 rounded">student_preferred_language</code> - Preferred language code</li>
              <li><code className="bg-white px-1 rounded">guardian_phone</code> - Phone number (E.164 format recommended). Will auto-add + prefix for US numbers.</li>
              <li><code className="bg-white px-1 rounded">guardian_street_number</code>, <code className="bg-white px-1 rounded">guardian_street_name</code>, <code className="bg-white px-1 rounded">guardian_city</code>, <code className="bg-white px-1 rounded">guardian_state</code>, <code className="bg-white px-1 rounded">guardian_zip_code</code>, <code className="bg-white px-1 rounded">guardian_country</code> - Address fields</li>
              <li><code className="bg-white px-1 rounded">guardian_preferred_language</code> - Preferred language code</li>
              <li><code className="bg-white px-1 rounded">relationship_type</code> - primary, secondary, or emergency (defaults to primary)</li>
            </ul>
            <div className="mt-3 pt-3 border-t">
              <p className="font-semibold mb-2">Note:</p>
              <p className="text-xs text-gray-600 mb-2">
                Rows with parsing errors will be skipped, but processing will continue for valid rows.
              </p>
            </div>
          </div>
        </div>
      </div>

      {preview.length > 0 && (
        <div className="space-y-2">
          <Label>Preview (first 5 rows)</Label>
          <div className="border rounded p-2 max-h-48 overflow-y-auto">
            <table className="w-full text-sm">
              <thead>
                <tr>
                  <th className="text-left p-1">Student</th>
                  <th className="text-left p-1">Grade</th>
                  <th className="text-left p-1">Student ID</th>
                  <th className="text-left p-1">Guardian</th>
                  <th className="text-left p-1">Guardian Email</th>
                </tr>
              </thead>
              <tbody>
                {preview.map((row, i) => (
                  <tr key={i}>
                    <td className="p-1">{row.student_name || ''}</td>
                    <td className="p-1">{row.student_grade_level || ''}</td>
                    <td className="p-1">{row.student_id || ''}</td>
                    <td className="p-1">{row.guardian_name || ''}</td>
                    <td className="p-1">{row.guardian_email || ''}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {parseErrors.length > 0 && (
        <div className="space-y-2">
          <Label>Parsing Errors (non-blocking)</Label>
          <div className="border rounded p-2 max-h-32 overflow-y-auto bg-yellow-50">
            <ul className="text-sm space-y-1">
              {parseErrors.map((err, i) => (
                <li key={i} className="text-yellow-800">
                  Row {err.row}: {err.error}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      <Button type="submit" disabled={isSubmitting || !file}>
        {isSubmitting ? 'Processing...' : 'Upload and Create'}
      </Button>
    </form>
  )
}
