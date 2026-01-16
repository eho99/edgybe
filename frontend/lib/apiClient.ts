import { createClient } from '@/lib/supabase/client'

// A custom error class to hold more context
export class ApiError extends Error {
    constructor(message: string, public status: number, public data: any) {
        super(message)
        this.name = 'ApiError'
    }
}


/**
 * A type-safe, client-side API client that automatically handles
 * Supabase auth and JSON request/response bodies.
 */
type ApiClientOptions = Omit<RequestInit, 'body'> & { body?: BodyInit | Record<string, unknown> | object }

const apiClient = async <T>(
    url: string,
    options: ApiClientOptions = {}
): Promise<T> => {
    const supabase = createClient()

    // OPTIMIZATION: Use getSession() here. It's faster.
    // We trust the backend to reject the token if it's forged or expired.
    const { data } = await supabase.auth.getSession()
    const accessToken = data.session?.access_token

    if (!accessToken) {
        // If no session exists locally, redirect immediately
        window.location.href = '/login'
        throw new Error('No session')
    }

    const headers = new Headers(options.headers || {})
    headers.set('Authorization', `Bearer ${accessToken}`)

    const { body: originalBody, ...restOptions } = options

    const shouldStringify =
        originalBody &&
        typeof originalBody === 'object' &&
        !(originalBody instanceof FormData) &&
        !(originalBody instanceof URLSearchParams)

    let requestBody: BodyInit | null | undefined = originalBody as BodyInit | null | undefined

    if (shouldStringify) {
        requestBody = JSON.stringify(originalBody)
        if (!headers.has('Content-Type')) {
            headers.set('Content-Type', 'application/json')
        }
    }

    const fullUrl = `${process.env.NEXT_PUBLIC_API_BASE_URL!}${url}`
    let response: Response

    try {
        response = await fetch(fullUrl, {
            ...restOptions,
            headers,
            body: requestBody,
        })
    } catch (error) {
        // Handle network errors (e.g., failed to fetch)
        throw new Error('Network request failed. Please check your connection.')
    }

    // Global Error Boundary for Auth
    if (response.status === 401) {
        // The backend rejected the token (expired/invalid).
        // Now we sign out on the frontend.
        await supabase.auth.signOut()
        window.location.href = '/login'
        throw new Error('Session expired')
    }

    // Handle API errors
    if (!response.ok) {
        let errorData: any = { detail: 'API request failed' }
        try {
            // Try to parse the error response from FastAPI
            errorData = await response.json()
        } catch (e) {
            // If response isn't JSON, use status text
            errorData = { detail: response.statusText }
        }

        throw new ApiError(
            errorData.detail || 'An unknown API error occurred',
            response.status,
            errorData
        )
    }

    // Handle 204 No Content
    if (response.status === 204) {
        return null as T
    }

    // Automatically parse and return JSON response data
    try {
        const data: T = await response.json()
        return data
    } catch (e) {
        throw new ApiError(
            'Failed to parse JSON response from API',
            response.status,
            null
        )
    }
}

export default apiClient

