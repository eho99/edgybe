import { useMemo } from 'react'
import useSWR from 'swr'
import apiClient from '@/lib/apiClient'

interface AuthenticatedMember {
  user: {
    id: string
    email: string
  }
  org_id: string
  role: string
}

interface OrganizationMembership {
  org_id: string
  role: string
  organization_name: string
  joined_at: string
}

/**
 * Hook to get the current user's role and organization information
 */
export function useCurrentUserRole() {
  const { data: memberships, error: membershipsError, isLoading: membershipsLoading } = useSWR<OrganizationMembership[]>(
    '/api/v1/organizations/my-memberships',
    apiClient
  )

  // Get the first organization's data (or we could add logic to select a specific one)
  const firstOrgId = memberships?.[0]?.org_id

  const { data: orgData, error: orgError, isLoading: orgLoading } = useSWR<AuthenticatedMember>(
    firstOrgId ? `/api/v1/organizations/${firstOrgId}/protected-data` : null,
    apiClient
  )

  const isAdmin = useMemo(() => {
    return Boolean(
      orgData?.role === 'admin' || memberships?.some(m => m.role === 'admin')
    )
  }, [orgData, memberships])

  const currentRole = useMemo(() => {
    return orgData?.role || memberships?.[0]?.role || null
  }, [orgData, memberships])

  const currentOrgId = useMemo(() => {
    return orgData?.org_id || memberships?.[0]?.org_id || null
  }, [orgData, memberships])

  return {
    role: currentRole,
    orgId: currentOrgId,
    isAdmin,
    memberships,
    orgData,
    isLoading: membershipsLoading || orgLoading,
    error: membershipsError || orgError,
  }
}

