'use client'

import { useState } from 'react'
import apiClient from '@/lib/apiClient'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'

interface InviteMemberFormProps {
  orgId: string
  onSuccess?: () => void
}

export function InviteMemberForm({ orgId, onSuccess }: InviteMemberFormProps) {
  const [activeTab, setActiveTab] = useState<'single' | 'bulk' | 'csv'>('single')

  return (
    <Card>
      <CardHeader>
        <CardTitle>Invite New Members</CardTitle>
        <CardDescription>
          Invite internal users (staff, secretary, admin) to your organization.
          They will receive an email invitation to join.
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
          <SingleInviteForm orgId={orgId} onSuccess={onSuccess} />
        )}
        {activeTab === 'bulk' && (
          <BulkInviteForm orgId={orgId} onSuccess={onSuccess} />
        )}
        {activeTab === 'csv' && (
          <CSVInviteForm orgId={orgId} onSuccess={onSuccess} />
        )}
      </CardContent>
    </Card>
  )
}

function SingleInviteForm({ orgId, onSuccess }: { orgId: string; onSuccess?: () => void }) {
  const [email, setEmail] = useState('')
  const [fullName, setFullName] = useState('')
  const [role, setRole] = useState('staff')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setError(null)
    setSuccess(null)

    try {
      const response = await apiClient(
        `/api/v1/organizations/${orgId}/members/invite`,
        {
          method: 'POST',
          body: { email, role, full_name: fullName || undefined } as any,
        }
      )
      setSuccess(`Successfully invited ${email} as a ${role}.`)
      setEmail('')
      setFullName('')
      onSuccess?.()
    } catch (err: any) {
      setError(err.message || 'An unknown error occurred.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="email">Email *</Label>
        <Input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="member@example.com"
          required
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="full-name">Full Name (optional)</Label>
        <Input
          id="full-name"
          type="text"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          placeholder="John Doe"
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="role">Role *</Label>
        <select
          id="role"
          value={role}
          onChange={(e) => setRole(e.target.value)}
          className="w-full p-2 border rounded"
        >
          <option value="staff">Staff</option>
          <option value="secretary">Secretary</option>
          <option value="admin">Admin</option>
        </select>
      </div>
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Sending Invite...' : 'Send Invite'}
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

function BulkInviteForm({ orgId, onSuccess }: { orgId: string; onSuccess?: () => void }) {
  const [users, setUsers] = useState([{ email: '', full_name: '', role: 'staff' }])
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const addUser = () => {
    setUsers([...users, { email: '', full_name: '', role: 'staff' }])
  }

  const removeUser = (index: number) => {
    setUsers(users.filter((_, i) => i !== index))
  }

  const updateUser = (index: number, field: string, value: string) => {
    const newUsers = [...users]
    ;(newUsers[index] as any)[field] = value
    setUsers(newUsers)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setError(null)
    setSuccess(null)

    try {
      const usersData = users
        .filter(u => u.email)
        .map(u => ({
          email: u.email,
          role: u.role,
          full_name: u.full_name || undefined,
        }))

      if (usersData.length === 0) {
        setError('Please add at least one user with an email address.')
        setIsSubmitting(false)
        return
      }

      const response = await apiClient(
        `/api/v1/organizations/${orgId}/members/invite/bulk`,
        {
          method: 'POST',
          body: { users: usersData },
        }
      ) as any

      const successMsg = `Successfully invited ${response.succeeded} user(s).`
      const failedMsg = response.failed_count > 0 ? ` ${response.failed_count} invitation(s) failed.` : ''
      setSuccess(successMsg + failedMsg)
      setUsers([{ email: '', full_name: '', role: 'staff' }])
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
        {users.map((user, index) => (
          <Card key={index}>
            <CardHeader className="pb-3">
              <div className="flex justify-between items-center">
                <CardTitle className="text-sm">User {index + 1}</CardTitle>
                {users.length > 1 && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => removeUser(index)}
                  >
                    Remove
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Email *</Label>
                  <Input
                    type="email"
                    value={user.email}
                    onChange={(e) => updateUser(index, 'email', e.target.value)}
                    placeholder="user@example.com"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>Full Name</Label>
                  <Input
                    type="text"
                    value={user.full_name}
                    onChange={(e) => updateUser(index, 'full_name', e.target.value)}
                    placeholder="John Doe"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Role *</Label>
                  <select
                    value={user.role}
                    onChange={(e) => updateUser(index, 'role', e.target.value)}
                    className="w-full p-2 border rounded"
                  >
                    <option value="staff">Staff</option>
                    <option value="secretary">Secretary</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Button type="button" variant="outline" onClick={addUser}>
        Add Another User
      </Button>

      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Sending Invites...' : `Invite ${users.length} User(s)`}
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

function CSVInviteForm({ orgId, onSuccess }: { orgId: string; onSuccess?: () => void }) {
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [preview, setPreview] = useState<any[]>([])

  const downloadSampleCSV = () => {
    const csvContent = `email,full_name,role
staff1@example.com,John Doe,staff
staff2@example.com,Jane Smith,staff
secretary1@example.com,Bob Johnson,secretary
admin1@example.com,Alice Williams,admin`

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', 'member_invite_template.csv')
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

    const reader = new FileReader()
    reader.onload = (event) => {
      const text = event.target?.result as string
      const lines = text.split('\n').filter(line => line.trim())
      
      if (lines.length < 2) {
        setError('CSV must have at least a header row and one data row.')
        return
      }

      const headers = lines[0].split(',').map(h => h.trim().toLowerCase())
      const requiredHeaders = ['email']
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
      
      const users = lines.slice(1).map(line => {
        const values = line.split(',').map(v => v.trim())
        const row: any = {}
        headers.forEach((header, index) => {
          row[header] = values[index] || ''
        })
        
        return {
          email: row.email || '',
          full_name: row.full_name || undefined,
          role: row.role || 'staff',
        }
      }).filter(u => u.email)

      if (users.length === 0) {
        setError('No valid users found in CSV file.')
        setIsSubmitting(false)
        return
      }

      const response = await apiClient(
        `/api/v1/organizations/${orgId}/members/invite/bulk`,
        {
          method: 'POST',
          body: { users },
        }
      ) as any

      const successMsg = `Successfully invited ${response.succeeded} user(s) from CSV.`
      const failedMsg = response.failed_count > 0 ? ` ${response.failed_count} invitation(s) failed.` : ''
      setSuccess(successMsg + failedMsg)
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
              <li><code className="bg-white px-1 rounded">email</code> - Email address of the user (required)</li>
            </ul>
            <p className="font-semibold mb-2">Optional columns:</p>
            <ul className="list-disc list-inside space-y-1 mb-3">
              <li><code className="bg-white px-1 rounded">full_name</code> - Full name of the user</li>
              <li><code className="bg-white px-1 rounded">role</code> - staff, secretary, or admin (defaults to staff)</li>
            </ul>
            <div className="mt-3 pt-3 border-t">
              <p className="font-semibold mb-2">Example:</p>
              <pre className="bg-white p-2 rounded text-xs overflow-x-auto">
{`email,full_name,role
staff1@example.com,John Doe,staff
secretary1@example.com,Jane Smith,secretary
admin1@example.com,Bob Johnson,admin`}
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
                  <th className="text-left p-1">Email</th>
                  <th className="text-left p-1">Name</th>
                  <th className="text-left p-1">Role</th>
                </tr>
              </thead>
              <tbody>
                {preview.map((row, i) => (
                  <tr key={i}>
                    <td className="p-1">{row.email || ''}</td>
                    <td className="p-1">{row.full_name || ''}</td>
                    <td className="p-1">{row.role || 'staff'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <Button type="submit" disabled={isSubmitting || !file}>
        {isSubmitting ? 'Processing...' : 'Upload and Invite'}
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
