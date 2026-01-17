import { useEffect, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'

export function useSecurityGate(redirectTo = '/login') {
  const [isAuthorized, setIsAuthorized] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()
  const pathname = usePathname()
  const supabase = createClient()

  useEffect(() => {
    const secureEntry = async () => {
      setIsLoading(true)

      // Provides extra security over getSession, for use in pathways needing stronger security checks
      const { data, error } = await supabase.auth.getClaims()

      const hasValidSession = !error && !!data?.claims

      // Manual expiration check (Double safety)
      const now = Math.floor(Date.now() / 1000)
      const isExpired = data?.claims?.exp && data.claims.exp < now

      if (!hasValidSession || isExpired) {
        setIsAuthorized(false)
        router.push(redirectTo)
      } else {
        setIsAuthorized(true)
      }
      setIsLoading(false)
    }

    secureEntry()

    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      if (event === 'SIGNED_OUT' || !session) {
        router.push(redirectTo)
        setIsAuthorized(false)
      }
    })

    return () => subscription.unsubscribe()
  }, [router, pathname, redirectTo, supabase])

  return { isAuthorized, isLoading }
}
