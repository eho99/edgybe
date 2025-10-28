import { createClient } from './supabaseClient'

const apiClient = async (
    url: string,
    options: RequestInit = {}
): Promise<Response> => {
    const supabase = createClient()

    // Get the current session
    const { data: { session } } = await supabase.auth.getSession()

    const token = session?.access_token

    if (!token) {
        // This should trigger a redirect to /login
        throw new Error('No authenticated session found. Please log in.')
    }

    // Add the Authorization header
    const headers = new Headers(options.headers || {})
    headers.set('Authorization', `Bearer ${token}`)

    const fullUrl = `${process.env.NEXT_PUBLIC_API_BASE_URL}${url}`

    const response = await fetch(fullUrl, {
        ...options,
        headers,
    })

    if (!response.ok) {
        // Handle API errors
        const errorData = await response.json()
        throw new Error(errorData.detail || 'API request failed')
    }

    return response
}

export default apiClient

