'use client'

import { useEffect, useState } from 'react'
import apiClient from '@/lib/apiClient'

interface AuthenticatedMember {
  user: {
    id: string
    email: string
  }
  org_id: string
  role: string
}

export default function DashboardPage() {
  const [data, setData] = useState<AuthenticatedMember | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const orgId = "..." 
        
        const response = await apiClient(`/api/v1/organizations/${orgId}/protected-data`)
        const result = await response.json()
        setData(result)
      } catch (err: any) {
        setError(err.message)
      }
    }

    fetchData()
  }, [])

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md w-full bg-white shadow-md rounded-lg p-6">
          <div className="text-red-600 text-center">
            <h2 className="text-xl font-semibold mb-2">Error</h2>
            <p>{error}</p>
          </div>
        </div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-600">Loading...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="border-4 border-dashed border-gray-200 rounded-lg p-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-6">Dashboard</h1>
            
            <div className="bg-white shadow rounded-lg p-6 mb-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Welcome!</h2>
              <p className="text-gray-600 mb-2">
                <strong>Email:</strong> {data.user.email}
              </p>
              <p className="text-gray-600 mb-2">
                <strong>Role:</strong> {data.role}
              </p>
              <p className="text-gray-600 mb-2">
                <strong>Organization ID:</strong> {data.org_id}
              </p>
            </div>

            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Raw Data</h3>
              <pre className="bg-gray-100 p-4 rounded text-sm overflow-auto">
                {JSON.stringify(data, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

