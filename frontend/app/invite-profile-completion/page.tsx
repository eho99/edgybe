'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import apiClient from '@/lib/apiClient'
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert'
import { Spinner } from '@/components/ui/spinner'

export default function InviteProfileCompletionPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [fullName, setFullName] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isProcessingInvite, setIsProcessingInvite] = useState(true)
  const [inviteData, setInviteData] = useState<any>(null)
  
  const supabase = createClient()

  useEffect(() => {
    const handleInvitationCallback = async () => {
      try {
        console.log('=== INVITATION CALLBACK HANDLER ===')
        console.log('Current URL:', window.location.href)
        console.log('Search params:', window.location.search)
        console.log('Hash:', window.location.hash)
        
        // Parse URL parameters
        const urlParams = new URLSearchParams(window.location.search)
        const hashParams = new URLSearchParams(window.location.hash.substring(1))
        
        // Check for auth tokens in hash (Supabase puts them there)
        const accessToken = hashParams.get('access_token')
        const refreshToken = hashParams.get('refresh_token')
        const error = hashParams.get('error') || urlParams.get('error')
        
        console.log('Auth tokens found:', { 
          hasAccessToken: !!accessToken, 
          hasRefreshToken: !!refreshToken,
          error 
        })
        
        if (error) {
          console.error('Auth error:', error)
          setError(`Authentication error: ${error}`)
          setIsProcessingInvite(false)
          return
        }
        
        // If we have tokens in hash, set the session
        if (accessToken && refreshToken) {
          console.log('Setting session from hash tokens...')
          const { data, error: setSessionError } = await supabase.auth.setSession({
            access_token: accessToken,
            refresh_token: refreshToken
          })
          
          if (setSessionError) {
            console.error('Error setting session:', setSessionError)
            setError('Failed to authenticate. Please try again.')
            setIsProcessingInvite(false)
            return
          }
          
          if (data.session && data.user) {
            console.log('✅ Session set successfully for user:', data.user.email)
            setInviteData(data.user)
            setIsProcessingInvite(false)
            return
          }
        }
        
        // If no tokens in hash, wait for session to be created by Supabase
        console.log('No tokens in hash, waiting for Supabase to create session...')
        
        let sessionFound = false
        let attempts = 0
        const maxAttempts = 10
        
        while (!sessionFound && attempts < maxAttempts) {
          console.log(`Checking for session (attempt ${attempts + 1}/${maxAttempts})...`)
          
          const { data: { session }, error: sessionError } = await supabase.auth.getSession()
          
          console.log('Session check result:', { 
            hasSession: !!session, 
            error: sessionError?.message,
            userEmail: session?.user?.email 
          })
          
          if (session && session.user) {
            console.log('✅ Session found for user:', session.user.email)
            setInviteData(session.user)
            setIsProcessingInvite(false)
            sessionFound = true
            return
          }
          
          // Wait before next attempt
          await new Promise(resolve => setTimeout(resolve, 500))
          attempts++
        }
        
        // Listen for auth state changes as a fallback
        console.log('Setting up auth state change listener...')
        const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
          console.log('Auth state change:', event, session?.user?.email)
          
          if (event === 'SIGNED_IN' && session && session.user) {
            console.log('✅ User signed in via auth state change:', session.user.email)
            setInviteData(session.user)
            setIsProcessingInvite(false)
            subscription?.unsubscribe()
          }
        })
        
        // If we still haven't found a session after waiting, show error
        setTimeout(() => {
          if (!sessionFound) {
            console.log('❌ No session found after waiting')
            setError('Unable to process invitation. Please try clicking the invitation link again.')
            setIsProcessingInvite(false)
            subscription?.unsubscribe()
          }
        }, 5000)
        
      } catch (err) {
        console.error('Error in invitation callback handler:', err)
        setError('Failed to process invitation. Please try again.')
        setIsProcessingInvite(false)
      }
    }

    handleInvitationCallback()
  }, [supabase, router])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)

    // Validation
    if (!fullName.trim()) {
      setError('Full name is required.')
      setIsSubmitting(false)
      return
    }

    if (!password.trim()) {
      setError('Password is required.')
      setIsSubmitting(false)
      return
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      setIsSubmitting(false)
      return
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters long.')
      setIsSubmitting(false)
      return
    }

    try {
      // Update the user's password in Supabase
      const { error: passwordError } = await supabase.auth.updateUser({
        password: password
      })

      if (passwordError) {
        throw new Error(`Failed to update password: ${passwordError.message}`)
      }

      // Update the user's profile using the API client
      await apiClient('/api/v1/users/me/profile', {
        method: 'PUT',
        body: {
          full_name: fullName,
        },
      })

      // Profile updated successfully, redirect to dashboard
      router.push('/dashboard')

    } catch (err: any) {
      console.error('Profile completion error:', err)
      setError(err.message || 'Failed to complete profile. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isProcessingInvite) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Card className="w-full max-w-md p-6">
          <CardContent className="flex flex-col items-center space-y-4">
            <Spinner className="w-8 h-8" />
            <p className="text-center">Processing your invitation...</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (error && !inviteData) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Card className="w-full max-w-md p-6">
          <CardContent>
            <Alert variant="destructive">
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
            <Button 
              onClick={() => router.push('/login')} 
              className="w-full mt-4"
            >
              Go to Login
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md p-0">
        <CardHeader>
          <CardTitle>Welcome! Let&apos;s complete your profile.</CardTitle>
          <CardDescription>
            You&apos;ve been invited to join. Please enter your full name and password to complete your profile.
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit} autoComplete="off">
          <CardContent>
            <div className="space-y-4">
              <div>
                <label htmlFor="fullName" className="block text-sm font-medium mb-1">
                  Full Name
                </label>
                <Input
                  id="fullName"
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g., Jane Doe"
                  required
                  autoComplete="off"
                  disabled={isSubmitting}
                />
              </div>
              
              <div>
                <label htmlFor="password" className="block text-sm font-medium mb-1">
                  Password
                </label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  required
                  autoComplete="new-password"
                  disabled={isSubmitting}
                />
              </div>
              
              <div>
                <label htmlFor="confirmPassword" className="block text-sm font-medium mb-1">
                  Confirm Password
                </label>
                <Input
                  id="confirmPassword"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirm your password"
                  required
                  autoComplete="new-password"
                  disabled={isSubmitting}
                />
              </div>
              
              {error && (
                <Alert variant="destructive">
                  <AlertTitle>Error</AlertTitle>
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
            </div>
          </CardContent>
          <CardFooter>
            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? (
                <span className="flex items-center gap-2">
                  <Spinner className="w-4 h-4" /> Saving...
                </span>
              ) : (
                'Complete Profile & Continue'
              )}
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  )
}
