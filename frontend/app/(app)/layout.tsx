'use client'

import { useEffect, useMemo } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useProfile } from '@/hooks/useProfile' // The hook we just created
import { createClient } from '@/lib/supabase/client' // My existing Supabase client

export default function AppLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const pathname = usePathname()
  const supabase = createClient()
  const { profile, isLoading, isError } = useProfile()

  const needsProfileCompletion = useMemo(() => {
    if (!profile) {
      return false
    }

    const missingFullName = !profile.full_name || !profile.full_name.trim()
    const missingEmail = !profile.email || !profile.email.trim()

    return missingFullName || missingEmail
  }, [profile])

  useEffect(() => {
    const checkSession = async () => {
      const {
        data: { session },
      } = await supabase.auth.getSession()
      if (!session) {
        router.push('/login')
        return
      }

      if (isLoading || isError) {
        return
      }

      if (!profile) {
        return
      }

      if (needsProfileCompletion && pathname !== '/invite-profile-completion') {
        console.log('[AppLayout] Missing required profile fields, redirecting to invite-profile-completion')
        router.push('/invite-profile-completion')
      } else if (!needsProfileCompletion && pathname === '/invite-profile-completion') {
        console.log('[AppLayout] Required profile fields present, redirecting to dashboard')
        router.push('/dashboard')
      }
    }

    checkSession()

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, session) => {
      if (event === 'SIGNED_OUT' || !session) {
        router.push('/login')
      }
    })

    return () => {
      subscription?.unsubscribe()
    }
  }, [router, supabase, profile, needsProfileCompletion, isLoading, isError, pathname])

  // While profile is loading, show a spinner.
  if (isLoading) {
    return <div>Loading user data...</div>
  }

  if (isError) {
    return <div>We couldn&apos;t load your profile. Please refresh.</div>
  }

  // If we are on the invite-profile-completion page, just render it.
  // The useEffect handles redirecting away if the profile is already complete.
  if (pathname === '/invite-profile-completion') {
    return <>{children}</>
  }

  if (profile && !needsProfileCompletion) {
    return (
      <main>
        {/* My main app nav/sidebar would go here */}
        {children}
      </main>
    )
  }

  if (profile && needsProfileCompletion) {
    return <>{children}</>
  }

  // Fallback for loading states
  return <div>Loading user data...</div>
}

