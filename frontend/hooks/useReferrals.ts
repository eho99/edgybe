import useSWR from 'swr'
import apiClient from '@/lib/apiClient'
import { createClient } from '@/lib/supabase/client'

// Types
export type ReferralFieldSelection = 'single' | 'multi'

export interface ReferralFieldConfig {
    label?: string
    options?: string[]
    helpText?: string
    required?: boolean
    selection?: ReferralFieldSelection
    allowOther?: boolean
}

export interface ReferralConfig {
    types: string[]
    locations?: ReferralFieldConfig
    time_of_day?: ReferralFieldConfig
    behaviors?: ReferralFieldConfig
    common_interventions: string[]
}

export interface Intervention {
    id: string
    referral_id: string
    title: string
    description: string | null
    status: string
    completed_at: string | null
    created_by: string | null
    created_at: string
    updated_at: string
    creator_name: string | null
}

export interface Referral {
    id: string
    organization_id: string
    student_id: string
    author_id: string | null
    status: string
    type: string
    location: string | null
    time_of_day: string | null
    behaviors: string[] | null
    description: string | null
    archived: boolean
    archived_at: string | null
    created_at: string
    updated_at: string
    student_name: string | null
    student_student_id: string | null
    student_grade_level: string | null
    author_name: string | null
    interventions: Intervention[]
}

export interface ReferralListItem {
    id: string
    organization_id: string
    student_id: string
    author_id: string | null
    status: string
    type: string
    location: string | null
    time_of_day: string | null
    archived: boolean
    archived_at: string | null
    created_at: string
    updated_at: string
    student_name: string | null
    student_student_id: string | null
    author_name: string | null
    intervention_count: number
}

export interface ReferralCreatePayload {
    student_id: string
    type: string
    location?: string
    time_of_day?: string
    behaviors?: string[]
    description?: string
}

export interface ReferralUpdatePayload {
    status?: string
    type?: string
    location?: string
    time_of_day?: string
    behaviors?: string[]
    description?: string
}

export interface InterventionCreatePayload {
    title: string
    description?: string
    status?: string
    completed_at?: string
}

export interface InterventionUpdatePayload {
    title?: string
    description?: string
    status?: string
    completed_at?: string
}

export interface EmailRequestPayload {
    recipient_emails: string[]
    subject?: string
    message?: string
    template_id?: string
}

export interface EmailTemplate {
    id: string
    organization_id: string | null
    created_by_user_id: string | null
    name: string
    subject_template: string
    body_template: string
    type: string
    scope: string
    is_active: boolean
    created_at: string
    updated_at: string
    creator_name: string | null
}

export interface EmailTemplateCreatePayload {
    name: string
    subject_template: string
    body_template: string
    type: string
    scope?: string
    is_active?: boolean
}

export interface EmailTemplateUpdatePayload {
    name?: string
    subject_template?: string
    body_template?: string
    type?: string
    scope?: string
    is_active?: boolean
}

export interface ReferralStatsBreakdownItem {
    label: string
    count: number
}

export interface ReferralStatsRecentItem {
    id: string
    student_name: string | null
    student_student_id: string | null
    type: string
    status: string
    location: string | null
    time_of_day: string | null
    behaviors: string[] | null
    created_at: string
}

export interface ReferralStatsData {
    total_referrals: number
    breakdown_by_location: ReferralStatsBreakdownItem[]
    breakdown_by_time_of_day: ReferralStatsBreakdownItem[]
    breakdown_by_behavior: ReferralStatsBreakdownItem[]
    recent_referrals: ReferralStatsRecentItem[]
    start_date: string
    end_date: string
}

export interface ReferralStatsFilters {
    start_date?: string
    end_date?: string
    location?: string
    time_of_day?: string
    behaviors?: string[]
    recent_limit?: number
}

export function useReferralStats(orgId: string | null, filters?: ReferralStatsFilters) {
    const queryParams = new URLSearchParams()
    if (filters) {
        if (filters.start_date) {
            queryParams.append('start_date', filters.start_date)
        }
        if (filters.end_date) {
            queryParams.append('end_date', filters.end_date)
        }
        if (filters.location) {
            queryParams.append('location', filters.location)
        }
        if (filters.time_of_day) {
            queryParams.append('time_of_day', filters.time_of_day)
        }
        if (filters.behaviors && filters.behaviors.length > 0) {
            filters.behaviors.forEach((behavior) => {
                queryParams.append('behaviors', behavior)
            })
        }
        if (filters.recent_limit) {
            queryParams.append('recent_limit', filters.recent_limit.toString())
        }
    }

    const queryString = queryParams.toString()
    const endpoint = orgId
        ? `/api/v1/organizations/${orgId}/referrals/stats${queryString ? `?${queryString}` : ''}`
        : null

    const { data, error, isLoading, mutate } = useSWR<ReferralStatsData>(endpoint, apiClient)

    return {
        stats: data,
        isLoading,
        error,
        mutate,
    }
}

export interface EmailVariable {
    label: string
    value: string
    description: string
}

// Hook to fetch referral config
export function useReferralConfig(orgId: string | null) {
    const { data, error, isLoading, mutate } = useSWR<ReferralConfig>(
        orgId ? `/api/v1/organizations/${orgId}/config/referrals` : null,
        apiClient
    )

    return {
        config: data,
        isLoading,
        error,
        mutate,
    }
}

// Hook to fetch email variables
export function useEmailVariables(orgId: string | null) {
    const { data, error, isLoading } = useSWR<EmailVariable[]>(
        orgId ? `/api/v1/organizations/${orgId}/config/email-variables` : null,
        apiClient
    )

    return {
        variables: data || [],
        isLoading,
        error,
    }
}

// Hook to fetch referrals list
export function useReferrals(
    orgId: string | null,
    filters?: {
        page?: number
        per_page?: number
        student_id?: string
        status?: string
        type?: string
        author_id?: string
        include_archived?: boolean
    }
) {
    // Build query string
    const queryParams = new URLSearchParams()
    if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
            if (value !== undefined && value !== null) {
                queryParams.append(key, value.toString())
            }
        })
    }

    const queryString = queryParams.toString()
    const endpoint = orgId
        ? `/api/v1/organizations/${orgId}/referrals${queryString ? `?${queryString}` : ''}`
        : null

    const { data, error, isLoading, mutate } = useSWR<{
        referrals: ReferralListItem[]
        total: number
        page: number
        per_page: number
        total_pages: number
    }>(endpoint, apiClient)

    return {
        referrals: data?.referrals || [],
        total: data?.total || 0,
        page: data?.page || 1,
        per_page: data?.per_page || 20,
        total_pages: data?.total_pages || 0,
        isLoading,
        error,
        mutate,
    }
}

// Hook to fetch single referral
export function useReferral(orgId: string | null, referralId: string | null) {
    const { data, error, isLoading, mutate } = useSWR<Referral>(
        orgId && referralId
            ? `/api/v1/organizations/${orgId}/referrals/${referralId}`
            : null,
        apiClient
    )

    return {
        referral: data,
        isLoading,
        error,
        mutate,
    }
}

// Hook to fetch email templates
export function useEmailTemplates(
    orgId: string | null,
    filters?: {
        page?: number
        per_page?: number
        type?: string
    }
) {
    const queryParams = new URLSearchParams()
    if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
            if (value !== undefined && value !== null) {
                queryParams.append(key, value.toString())
            }
        })
    }

    const queryString = queryParams.toString()
    const endpoint = orgId
        ? `/api/v1/organizations/${orgId}/email-templates${queryString ? `?${queryString}` : ''}`
        : null

    const { data, error, isLoading, mutate } = useSWR<{
        templates: EmailTemplate[]
        total: number
        page: number
        per_page: number
        total_pages: number
    }>(endpoint, apiClient)

    return {
        templates: data?.templates || [],
        total: data?.total || 0,
        page: data?.page || 1,
        per_page: data?.per_page || 20,
        total_pages: data?.total_pages || 0,
        isLoading,
        error,
        mutate,
    }
}

// API functions
export async function createReferral(
    orgId: string,
    payload: ReferralCreatePayload
): Promise<Referral> {
    return await apiClient(`/api/v1/organizations/${orgId}/referrals`, {
        method: 'POST',
        body: payload,
    })
}

export async function updateReferral(
    orgId: string,
    referralId: string,
    payload: ReferralUpdatePayload
): Promise<Referral> {
    return await apiClient(
        `/api/v1/organizations/${orgId}/referrals/${referralId}`,
        {
            method: 'PATCH',
            body: payload,
        }
    )
}

export async function archiveReferral(
    orgId: string,
    referralId: string
): Promise<Referral> {
    return await apiClient(
        `/api/v1/organizations/${orgId}/referrals/${referralId}/archive`,
        {
            method: 'POST',
        }
    )
}

export async function unarchiveReferral(
    orgId: string,
    referralId: string
): Promise<Referral> {
    return await apiClient(
        `/api/v1/organizations/${orgId}/referrals/${referralId}/unarchive`,
        {
            method: 'POST',
        }
    )
}

export async function createIntervention(
    orgId: string,
    referralId: string,
    payload: InterventionCreatePayload
): Promise<Intervention> {
    return await apiClient(
        `/api/v1/organizations/${orgId}/referrals/${referralId}/interventions`,
        {
            method: 'POST',
            body: payload,
        }
    )
}

export async function updateIntervention(
    orgId: string,
    referralId: string,
    interventionId: string,
    payload: InterventionUpdatePayload
): Promise<Intervention> {
    return await apiClient(
        `/api/v1/organizations/${orgId}/referrals/${referralId}/interventions/${interventionId}`,
        {
            method: 'PATCH',
            body: payload,
        }
    )
}

export async function downloadReferralPDF(
    orgId: string,
    referralId: string
): Promise<Blob> {
    const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/organizations/${orgId}/referrals/${referralId}/pdf`,
        {
            method: 'GET',
            headers: {
                Authorization: `Bearer ${await getAccessToken()}`,
            },
        }
    )

    if (!response.ok) {
        throw new Error('Failed to download PDF')
    }

    return await response.blob()
}

export async function sendReferralEmail(
    orgId: string,
    referralId: string,
    payload: EmailRequestPayload
): Promise<{ success: boolean; message: string; log_id?: string }> {
    return await apiClient(
        `/api/v1/organizations/${orgId}/referrals/${referralId}/email`,
        {
            method: 'POST',
            body: payload,
        }
    )
}

export async function createEmailTemplate(
    orgId: string,
    payload: EmailTemplateCreatePayload
): Promise<EmailTemplate> {
    return await apiClient(`/api/v1/organizations/${orgId}/email-templates`, {
        method: 'POST',
        body: payload,
    })
}

export async function updateEmailTemplate(
    orgId: string,
    templateId: string,
    payload: EmailTemplateUpdatePayload
): Promise<EmailTemplate> {
    return await apiClient(
        `/api/v1/organizations/${orgId}/email-templates/${templateId}`,
        {
            method: 'PATCH',
            body: payload,
        }
    )
}

export async function deleteEmailTemplate(
    orgId: string,
    templateId: string
): Promise<void> {
    await apiClient(
        `/api/v1/organizations/${orgId}/email-templates/${templateId}`,
        {
            method: 'DELETE',
        }
    )
}

// Helper function to get access token
async function getAccessToken(): Promise<string> {
    const supabase = createClient()
    const {
        data: { session },
    } = await supabase.auth.getSession()
    return session?.access_token || ''
}

