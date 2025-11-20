'use client'

import { useState } from 'react'
import apiClient from '@/lib/apiClient'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'

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

function SingleCreateForm({ orgId, onSuccess }: { orgId: string; onSuccess?: () => void }) {
  const [studentName, setStudentName] = useState('')
  const [studentEmail, setStudentEmail] = useState('')
  const [guardianName, setGuardianName] = useState('')
  const [guardianEmail, setGuardianEmail] = useState('')
  const [linkImmediately, setLinkImmediately] = useState(true)
  const [relationshipType, setRelationshipType] = useState('primary')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setError(null)
    setSuccess(null)

    try {
      // Create student
      const studentResponse = await apiClient(
        `/api/v1/organizations/${orgId}/students`,
        {
          method: 'POST',
          body: {
            full_name: studentName,
            email: studentEmail || undefined,
          },
        }
      ) as any

      // Create guardian
      const guardianResponse = await apiClient(
        `/api/v1/organizations/${orgId}/guardians`,
        {
          method: 'POST',
          body: {
            full_name: guardianName,
            email: guardianEmail || undefined,
          },
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
        setSuccess(`Successfully created and linked student "${studentName}" with guardian "${guardianName}".`)
      } else {
        setSuccess(`Successfully created student "${studentName}" and guardian "${guardianName}".`)
      }

      // Reset form
      setStudentName('')
      setStudentEmail('')
      setGuardianName('')
      setGuardianEmail('')
      
      onSuccess?.()
    } catch (err: any) {
      setError(err.message || 'An unknown error occurred.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-4">
          <h3 className="font-semibold">Student</h3>
          <div className="space-y-2">
            <Label htmlFor="student-name">Full Name *</Label>
            <Input
              id="student-name"
              value={studentName}
              onChange={(e) => setStudentName(e.target.value)}
              placeholder="John Doe"
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="student-email">Email (optional)</Label>
            <Input
              id="student-email"
              type="email"
              value={studentEmail}
              onChange={(e) => setStudentEmail(e.target.value)}
              placeholder="john@example.com"
            />
          </div>
        </div>

        <div className="space-y-4">
          <h3 className="font-semibold">Guardian</h3>
          <div className="space-y-2">
            <Label htmlFor="guardian-name">Full Name *</Label>
            <Input
              id="guardian-name"
              value={guardianName}
              onChange={(e) => setGuardianName(e.target.value)}
              placeholder="Jane Doe"
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="guardian-email">Email (optional)</Label>
            <Input
              id="guardian-email"
              type="email"
              value={guardianEmail}
              onChange={(e) => setGuardianEmail(e.target.value)}
              placeholder="jane@example.com"
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

      {error && (
        <Alert variant="destructive">
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      {success && (
        <Alert variant="default">
          <AlertTitle>Success</AlertTitle>
          <AlertDescription>{success}</AlertDescription>
        </Alert>
      )}
    </form>
  )
}

function BulkCreateForm({ orgId, onSuccess }: { orgId: string; onSuccess?: () => void }) {
  const [pairs, setPairs] = useState([{ student: { full_name: '', email: '' }, guardian: { full_name: '', email: '' }, relationship_type: 'primary' }])
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const addPair = () => {
    setPairs([...pairs, { student: { full_name: '', email: '' }, guardian: { full_name: '', email: '' }, relationship_type: 'primary' }])
  }

  const removePair = (index: number) => {
    setPairs(pairs.filter((_, i) => i !== index))
  }

  const updatePair = (index: number, field: string, value: any) => {
    const newPairs = [...pairs]
    if (field.includes('.')) {
      const [parent, child] = field.split('.')
      ;(newPairs[index] as any)[parent][child] = value
    } else {
      ;(newPairs[index] as any)[field] = value
    }
    setPairs(newPairs)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setError(null)
    setSuccess(null)

    try {
      const pairsData = pairs
        .filter(p => p.student.full_name && p.guardian.full_name)
        .map(p => ({
          student: {
            full_name: p.student.full_name,
            email: p.student.email || undefined,
          },
          guardian: {
            full_name: p.guardian.full_name,
            email: p.guardian.email || undefined,
          },
          relationship_type: p.relationship_type,
        }))

      if (pairsData.length === 0) {
        setError('Please add at least one valid student-guardian pair.')
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

      setSuccess(`Successfully created and linked ${response.created} student-guardian pair(s).`)
      setPairs([{ student: { full_name: '', email: '' }, guardian: { full_name: '', email: '' }, relationship_type: 'primary' }])
      onSuccess?.()
    } catch (err: any) {
      setError(err.message || 'An unknown error occurred.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-4 max-h-96 overflow-y-auto">
        {pairs.map((pair, index) => (
          <Card key={index}>
            <CardHeader className="pb-3">
              <div className="flex justify-between items-center">
                <CardTitle className="text-sm">Pair {index + 1}</CardTitle>
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
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Student Name *</Label>
                  <Input
                    value={pair.student.full_name}
                    onChange={(e) => updatePair(index, 'student.full_name', e.target.value)}
                    placeholder="Student Name"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>Guardian Name *</Label>
                  <Input
                    value={pair.guardian.full_name}
                    onChange={(e) => updatePair(index, 'guardian.full_name', e.target.value)}
                    placeholder="Guardian Name"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>Student Email</Label>
                  <Input
                    type="email"
                    value={pair.student.email}
                    onChange={(e) => updatePair(index, 'student.email', e.target.value)}
                    placeholder="student@example.com"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Guardian Email</Label>
                  <Input
                    type="email"
                    value={pair.guardian.email}
                    onChange={(e) => updatePair(index, 'guardian.email', e.target.value)}
                    placeholder="guardian@example.com"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Relationship Type</Label>
                <select
                  value={pair.relationship_type}
                  onChange={(e) => updatePair(index, 'relationship_type', e.target.value)}
                  className="w-full p-2 border rounded"
                >
                  <option value="primary">Primary</option>
                  <option value="secondary">Secondary</option>
                  <option value="emergency">Emergency</option>
                </select>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Button type="button" variant="outline" onClick={addPair}>
        Add Another Pair
      </Button>

      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Creating...' : `Create ${pairs.length} Pair(s)`}
      </Button>

      {error && (
        <Alert variant="destructive">
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      {success && (
        <Alert variant="default">
          <AlertTitle>Success</AlertTitle>
          <AlertDescription>{success}</AlertDescription>
        </Alert>
      )}
    </form>
  )
}

function CSVUploadForm({ orgId, onSuccess }: { orgId: string; onSuccess?: () => void }) {
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [preview, setPreview] = useState<any[]>([])

  const downloadSampleCSV = () => {
    // Create sample CSV content
    const csvContent = `student_name,student_email,guardian_name,guardian_email,relationship_type
John Doe,john.doe@example.com,Jane Doe,jane.doe@example.com,primary
Alice Smith,alice.smith@example.com,Bob Smith,bob.smith@example.com,primary
Charlie Brown,,Lucy Brown,lucy.brown@example.com,secondary
David Wilson,david.wilson@example.com,Sarah Wilson,,emergency`

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
    setError(null)
    setSuccess(null)

    // Parse CSV and preview
    const reader = new FileReader()
    reader.onload = (event) => {
      const text = event.target?.result as string
      const lines = text.split('\n').filter(line => line.trim())
      
      if (lines.length < 2) {
        setError('CSV must have at least a header row and one data row.')
        return
      }

      const headers = lines[0].split(',').map(h => h.trim().toLowerCase())
      const requiredHeaders = ['student_name', 'guardian_name']
      const missingHeaders = requiredHeaders.filter(h => !headers.includes(h))
      
      if (missingHeaders.length > 0) {
        setError(`Missing required columns: ${missingHeaders.join(', ')}`)
        return
      }

      const previewData = lines.slice(1, 6).map(line => {
        const values = line.split(',').map(v => v.trim())
        const row: any = {}
        headers.forEach((header, index) => {
          row[header] = values[index] || ''
        })
        return row
      })

      setPreview(previewData)
    }
    reader.readAsText(selectedFile)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) {
      setError('Please select a CSV file.')
      return
    }

    setIsSubmitting(true)
    setError(null)
    setSuccess(null)

    try {
      const text = await file.text()
      const lines = text.split('\n').filter(line => line.trim())
      const headers = lines[0].split(',').map(h => h.trim().toLowerCase())
      
      const pairs = lines.slice(1).map(line => {
        const values = line.split(',').map(v => v.trim())
        const row: any = {}
        headers.forEach((header, index) => {
          row[header] = values[index] || ''
        })
        
        return {
          student: {
            full_name: row.student_name || '',
            email: row.student_email || undefined,
          },
          guardian: {
            full_name: row.guardian_name || '',
            email: row.guardian_email || undefined,
          },
          relationship_type: row.relationship_type || 'primary',
        }
      }).filter(p => p.student.full_name && p.guardian.full_name)

      if (pairs.length === 0) {
        setError('No valid pairs found in CSV file.')
        setIsSubmitting(false)
        return
      }

      const response = await apiClient(
        `/api/v1/organizations/${orgId}/pairs/bulk`,
        {
          method: 'POST',
          body: { pairs },
        }
      ) as any

      setSuccess(`Successfully created and linked ${response.created} student-guardian pair(s) from CSV.`)
      setFile(null)
      setPreview([])
      onSuccess?.()
    } catch (err: any) {
      setError(err.message || 'An unknown error occurred.')
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
              <li><code className="bg-white px-1 rounded">student_name</code> - Full name of the student (required)</li>
              <li><code className="bg-white px-1 rounded">guardian_name</code> - Full name of the guardian (required)</li>
            </ul>
            <p className="font-semibold mb-2">Optional columns:</p>
            <ul className="list-disc list-inside space-y-1 mb-3">
              <li><code className="bg-white px-1 rounded">student_email</code> - Email address of the student</li>
              <li><code className="bg-white px-1 rounded">guardian_email</code> - Email address of the guardian</li>
              <li><code className="bg-white px-1 rounded">relationship_type</code> - primary, secondary, or emergency (defaults to primary)</li>
            </ul>
            <div className="mt-3 pt-3 border-t">
              <p className="font-semibold mb-2">Example:</p>
              <pre className="bg-white p-2 rounded text-xs overflow-x-auto">
{`student_name,student_email,guardian_name,guardian_email,relationship_type
John Doe,john.doe@example.com,Jane Doe,jane.doe@example.com,primary
Alice Smith,alice@example.com,Bob Smith,bob@example.com,primary
Charlie Brown,,Lucy Brown,lucy@example.com,secondary`}
              </pre>
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
                  <th className="text-left p-1">Guardian</th>
                </tr>
              </thead>
              <tbody>
                {preview.map((row, i) => (
                  <tr key={i}>
                    <td className="p-1">{row.student_name || ''}</td>
                    <td className="p-1">{row.guardian_name || ''}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <Button type="submit" disabled={isSubmitting || !file}>
        {isSubmitting ? 'Processing...' : 'Upload and Create'}
      </Button>

      {error && (
        <Alert variant="destructive">
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      {success && (
        <Alert variant="default">
          <AlertTitle>Success</AlertTitle>
          <AlertDescription>{success}</AlertDescription>
        </Alert>
      )}
    </form>
  )
}

