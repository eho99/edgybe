import { useMemo } from 'react'
import useSWR from 'swr'
import apiClient from '@/lib/apiClient'

const ORGANIZATIONS_ENDPOINT = '/api/v1/organizations'
const MEMBERSHIPS_ENDPOINT = '/api/v1/organizations/my-memberships'

export interface Organization {
  id: string
  name: string
  district_name: string | null
  street_number: string | null
  street_name: string | null
  city: string | null
  state: string | null
  zip_code: string | null
  phone_number: string | null
  office_extension: string | null
  lower_grade: number | null
  upper_grade: number | null
  slug: string | null
  preset_config: Record<string, unknown> | null
  form_config: Record<string, unknown> | null
  aeries_school_code: string | null
  sis_source_id: string | null
  sis_client_id: string | null
  sis_client_secret: string | null
  disclaimers: Record<string, unknown> | null
  assignment_config: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface OrganizationMembership {
  org_id: string
  role: string
  organization_name: string
  joined_at: string
}

export interface Disclaimers {
  general?: string
  self_harm?: string
  child_abuse?: string
}

export type OrganizationWithRole = Organization & { role?: string }

interface OrganizationBasePayload {
  street_number?: string
  street_name?: string
  city?: string
  state?: string
  zip_code?: string
  phone_number?: string
  office_extension?: string
  lower_grade?: number
  upper_grade?: number
  slug?: string
  preset_config?: Record<string, unknown>
  form_config?: Record<string, unknown>
  aeries_school_code?: string
  sis_source_id?: string
  sis_client_id?: string
  sis_client_secret?: string
  disclaimers?: Record<string, unknown>
  assignment_config?: Record<string, unknown> | null
}

export type OrganizationCreatePayload = {
  name: string
} & OrganizationBasePayload

export type OrganizationUpdatePayload = Partial<OrganizationCreatePayload>

export const useOrganizations = () => {
  const {
    data,
    error,
    isLoading,
    mutate,
  } = useSWR<Organization[]>(ORGANIZATIONS_ENDPOINT, apiClient)

  const {
    data: memberships,
    error: membershipsError,
    isLoading: membershipsLoading,
  } = useSWR<OrganizationMembership[]>(MEMBERSHIPS_ENDPOINT, apiClient)

  const organizations = useMemo<OrganizationWithRole[] | undefined>(() => {
    if (!data) return undefined
    const roleMap = new Map(memberships?.map((membership) => [membership.org_id, membership.role]))
    return data.map((org) => ({
      ...org,
      role: roleMap.get(org.id),
    }))
  }, [data, memberships])

  return {
    organizations,
    memberships,
    isLoading: isLoading || membershipsLoading,
    error: error || membershipsError,
    mutate,
  }
}

export function useOrganization(orgId: string | null) {
  const { data, error, isLoading } = useSWR<Organization>(
    orgId ? `${ORGANIZATIONS_ENDPOINT}/${orgId}` : null,
    apiClient
  )

  return {
    organization: data,
    isLoading,
    error,
  }
}

export const createOrganization = async (payload: OrganizationCreatePayload) => {
  return apiClient<Organization>(ORGANIZATIONS_ENDPOINT, {
    method: 'POST',
    body: payload,
  })
}

export const updateOrganization = async (
  orgId: string,
  payload: OrganizationUpdatePayload
) => {
  return apiClient<Organization>(`${ORGANIZATIONS_ENDPOINT}/${orgId}`, {
    method: 'PATCH',
    body: payload,
  })
}



