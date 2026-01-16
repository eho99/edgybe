'use client'

import { useEffect, useMemo } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useProfile } from '@/hooks/useProfile'
import { useSecurityGate } from '@/hooks/useSecurityGate'

export default function AppLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const pathname = usePathname()
  const { isAuthorized, isLoading: isAuthLoading } = useSecurityGate('/login')
  const { profile, isLoading: isProfileLoading, isError } = useProfile()

  const needsProfileCompletion = useMemo(() => {
    if (!profile) {
      return false
    }

    const missingFullName = !profile.full_name || !profile.full_name.trim()
    const missingEmail = !profile.email || !profile.email.trim()

    return missingFullName || missingEmail
  }, [profile])

  useEffect(() => {
    // Only handle profile completion redirects if we're authorized and profile is loaded
    if (isAuthLoading || isProfileLoading || isError || !isAuthorized) {
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
  }, [router, profile, needsProfileCompletion, isAuthLoading, isProfileLoading, isError, isAuthorized, pathname])

  // While auth or profile is loading, show a spinner.
  if (isAuthLoading || isProfileLoading) {
    return <div>Loading user data...</div>
  }

  // If not authorized, don't render (useSecurityGate handles redirect)
  if (!isAuthorized) {
    return null
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

