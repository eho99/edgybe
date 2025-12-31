import useSWR from 'swr'
import apiClient from '@/lib/apiClient'

export interface OrganizationMember {
  id: string
  organization_id: string
  user_id: string | null
  invite_email: string | null
  email: string | null
  full_name: string | null
  role: string
  status: string
  joined_at: string
}

export function useOrganizationAdmins(orgId: string | null) {
  const { data, error, isLoading, mutate } = useSWR<OrganizationMember[]>(
    orgId ? `/api/v1/organizations/${orgId}/members/admins` : null,
    apiClient
  )

  return {
    admins: data ?? [],
    isLoading,
    error,
    mutate,
  }
}

