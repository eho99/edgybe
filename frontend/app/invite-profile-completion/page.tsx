'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import apiClient from '@/lib/apiClient'
import PhoneInput from 'react-phone-number-input'
import 'react-phone-number-input/style.css'
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
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

export default function InviteProfileCompletionPage() {
  const router = useRouter()
  const [fullName, setFullName] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [phone, setPhone] = useState<string | undefined>('')
  const [streetNumber, setStreetNumber] = useState('')
  const [streetName, setStreetName] = useState('')
  const [city, setCity] = useState('')
  const [state, setState] = useState('')
  const [zipCode, setZipCode] = useState('')
  const [country, setCountry] = useState('')
  const [preferredLanguage, setPreferredLanguage] = useState('')
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

      // Build profile update body, only including fields with values
      const profileData: Record<string, string> = {
        full_name: fullName,
      }
      
      // Only add optional fields if they have values
      if (phone?.trim()) {
        profileData.phone = phone.trim()
      }
      if (streetNumber?.trim()) {
        profileData.street_number = streetNumber.trim()
      }
      if (streetName?.trim()) {
        profileData.street_name = streetName.trim()
      }
      if (city?.trim()) {
        profileData.city = city.trim()
      }
      if (state?.trim()) {
        profileData.state = state.trim()
      }
      if (zipCode?.trim()) {
        profileData.zip_code = zipCode.trim()
      }
      if (country?.trim()) {
        profileData.country = country.trim()
      }
      if (preferredLanguage?.trim()) {
        profileData.preferred_language = preferredLanguage.trim()
      }

      // Update the user's profile using the API client
      await apiClient('/api/v1/users/me/profile', {
        method: 'PUT',
        body: profileData,
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
            You&apos;ve been invited to join. Please fill out your profile information below.
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit} autoComplete="off">
          <CardContent>
            <div className="space-y-6">
              {/* Account Information */}
            <div className="space-y-4">
                <h3 className="text-lg font-semibold">Account Information</h3>
                
              <div>
                  <Label htmlFor="fullName">Full Name *</Label>
                <Input
                  id="fullName"
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g., Jane Doe"
                  required
                    autoComplete="name"
                  disabled={isSubmitting}
                    className="mt-1"
                />
              </div>
              
              <div>
                  <Label htmlFor="phone">Phone Number</Label>
                  <div className="mt-1 [&_.PhoneInput]:flex [&_.PhoneInput]:items-center [&_.PhoneInput]:gap-2 [&_.PhoneInput]:w-full [&_.PhoneInputInput]:flex-1 [&_.PhoneInputInput]:h-10 [&_.PhoneInputInput]:w-full [&_.PhoneInputInput]:rounded-md [&_.PhoneInputInput]:border [&_.PhoneInputInput]:border-input [&_.PhoneInputInput]:bg-background [&_.PhoneInputInput]:px-3 [&_.PhoneInputInput]:py-2 [&_.PhoneInputInput]:text-sm [&_.PhoneInputInput]:ring-offset-background [&_.PhoneInputInput]:placeholder:text-muted-foreground [&_.PhoneInputInput]:focus-visible:outline-none [&_.PhoneInputInput]:focus-visible:ring-2 [&_.PhoneInputInput]:focus-visible:ring-ring [&_.PhoneInputInput]:focus-visible:ring-offset-2 [&_.PhoneInputInput]:disabled:cursor-not-allowed [&_.PhoneInputInput]:disabled:opacity-50 [&_.PhoneInputCountry]:mr-2 [&_.PhoneInputCountryIcon]:w-6 [&_.PhoneInputCountryIcon]:h-6 [&_.PhoneInputCountryIcon]:rounded [&_.PhoneInputCountrySelect]:px-2 [&_.PhoneInputCountrySelect]:py-1 [&_.PhoneInputCountrySelect]:text-sm [&_.PhoneInputCountrySelect]:rounded-md [&_.PhoneInputCountrySelect]:border [&_.PhoneInputCountrySelect]:border-input [&_.PhoneInputCountrySelect]:bg-background">
                    <PhoneInput
                      international
                      defaultCountry="US"
                      value={phone}
                      onChange={(value) => setPhone(value ?? '')}
                      disabled={isSubmitting}
                      id="phone"
                      placeholder="Enter phone number"
                    />
                  </div>
                </div>
                
                <div>
                  <Label htmlFor="password">Password *</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  required
                  autoComplete="new-password"
                  disabled={isSubmitting}
                    className="mt-1"
                />
              </div>
              
              <div>
                  <Label htmlFor="confirmPassword">Confirm Password *</Label>
                <Input
                  id="confirmPassword"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirm your password"
                  required
                  autoComplete="new-password"
                  disabled={isSubmitting}
                    className="mt-1"
                />
                </div>
              </div>

              {/* Address Information */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Address Information</h3>
                
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label htmlFor="streetNumber">Street Number</Label>
                    <Input
                      id="streetNumber"
                      type="text"
                      value={streetNumber}
                      onChange={(e) => setStreetNumber(e.target.value)}
                      placeholder="123"
                      autoComplete="address-line1"
                      disabled={isSubmitting}
                      className="mt-1"
                    />
                  </div>
                  
                  <div className="col-span-2">
                    <Label htmlFor="streetName">Street Name</Label>
                    <Input
                      id="streetName"
                      type="text"
                      value={streetName}
                      onChange={(e) => setStreetName(e.target.value)}
                      placeholder="Main Street"
                      autoComplete="address-line2"
                      disabled={isSubmitting}
                      className="mt-1"
                    />
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="city">City</Label>
                    <Input
                      id="city"
                      type="text"
                      value={city}
                      onChange={(e) => setCity(e.target.value)}
                      placeholder="Springfield"
                      autoComplete="address-level2"
                      disabled={isSubmitting}
                      className="mt-1"
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="state">State</Label>
                    <Input
                      id="state"
                      type="text"
                      value={state}
                      onChange={(e) => setState(e.target.value)}
                      placeholder="IL"
                      autoComplete="address-level1"
                      disabled={isSubmitting}
                      className="mt-1"
                    />
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="zipCode">ZIP Code</Label>
                    <Input
                      id="zipCode"
                      type="text"
                      value={zipCode}
                      onChange={(e) => setZipCode(e.target.value)}
                      placeholder="62701"
                      autoComplete="postal-code"
                      disabled={isSubmitting}
                      className="mt-1"
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="country">Country</Label>
                    <Input
                      id="country"
                      type="text"
                      value={country}
                      onChange={(e) => setCountry(e.target.value)}
                      placeholder="United States"
                      autoComplete="country-name"
                      disabled={isSubmitting}
                      className="mt-1"
                    />
                  </div>
                </div>
              </div>

              {/* Additional Information */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Additional Information</h3>
                
                <div>
                  <Label htmlFor="preferredLanguage">Preferred Language</Label>
                  <Select value={preferredLanguage} onValueChange={setPreferredLanguage} disabled={isSubmitting}>
                    <SelectTrigger className="mt-1">
                      <SelectValue placeholder="Select a language" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="en">English</SelectItem>
                      <SelectItem value="es">Spanish</SelectItem>
                      <SelectItem value="fr">French</SelectItem>
                      <SelectItem value="de">German</SelectItem>
                      <SelectItem value="zh">Chinese</SelectItem>
                      <SelectItem value="ja">Japanese</SelectItem>
                      <SelectItem value="ko">Korean</SelectItem>
                      <SelectItem value="ar">Arabic</SelectItem>
                      <SelectItem value="pt">Portuguese</SelectItem>
                      <SelectItem value="ru">Russian</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
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

