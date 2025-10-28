'use client'

import { useEffect } from 'react'
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

  console.log('[AppLayout] State:', {
    pathname,
    isLoading,
    isError,
    profile,
  });
  if (isError) {
    console.error('[AppLayout] Profile fetch error:', isError);
  }

  useEffect(() => {
    const checkSession = async () => {
      const {
        data: { session },
      } = await supabase.auth.getSession()
      if (!session) {
        router.push('/login')
        return
      }

      // Wait for profile loading to settle
      if (!isLoading) {
        // If profile loading resulted in an error, or if the profile is incomplete,
        // redirect to the completion page.
        if (
          (isError || !profile?.has_completed_profile) &&
          pathname !== '/complete-profile'
        ) {
          router.push('/complete-profile')
        }
        // If profile is complete and we are on the completion page, go to dashboard.
        else if (
          profile?.has_completed_profile &&
          pathname === '/complete-profile'
        ) {
          router.push('/dashboard')
        }
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
  }, [router, supabase, profile, isLoading, isError, pathname])

  // While profile is loading, show a spinner.
  if (isLoading) {
    return <div>Loading user data...</div>
  }

  // If we are on the complete-profile page, just render it.
  // The useEffect handles redirecting away if the profile is already complete.
  if (pathname === '/complete-profile') {
    return <>{children}</>
  }

  // If profile is loaded AND completed, show the main app.
  if (profile?.has_completed_profile) {
    return (
      <main>
        {/* My main app nav/sidebar would go here */}
        {children}
      </main>
    )
  }

  // Fallback for loading or error states
  return <div>Loading...</div>
}

