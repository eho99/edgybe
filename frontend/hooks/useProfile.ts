import useSWR, { KeyedMutator } from 'swr'
import apiClient from '@/lib/apiClient' // My existing API client

// This is the shape of the data from backend/app/schemas.py -> ProfileSchema
export interface UserProfile {
    id: string;
    full_name: string | null;
    has_completed_profile: boolean;
    email: string | null;
    phone: string | null;
    street_number: string | null;
    street_name: string | null;
    city: string | null;
    state: string | null;
    zip_code: string | null;
    country: string | null;
    preferred_language: string | null;
    grade_level: string | null;
    student_id: string | null;
    is_active: boolean;
    updated_at: string;
}

interface UseProfileResult {
    profile: UserProfile | undefined;
    isLoading: boolean;
    isError: unknown;
    mutateProfile: KeyedMutator<UserProfile>;
}

export function useProfile(): UseProfileResult {
    const { data, error, isLoading, mutate } = useSWR<UserProfile>(
        '/api/v1/users/me/profile', // The backend endpoint
        apiClient, // Pass apiClient directly to SWR
        {
            shouldRetryOnError: false, // Don't retry on 404/403
            revalidateOnFocus: false, // Optional: disable re-fetching on window focus
        }
    );

    return {
        profile: data,
        isLoading,
        isError: error,
        mutateProfile: mutate, // Allows us to manually refetch data
    };
}
