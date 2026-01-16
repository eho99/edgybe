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
  const [showPassword, setShowPassword] = useState(false)
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
  const passwordInputType = showPassword ? 'text' : 'password'
  const supabase = createClient()

  useEffect(() => {
    let subscription: { unsubscribe: () => void } | null = null

    const handleInvitation = async () => {
      try {        
        // Parse URL parameters
        const urlParams = new URLSearchParams(window.location.search)
        const hashParams = new URLSearchParams(window.location.hash.substring(1))
        
        // Check for auth tokens in hash (Supabase puts them there)
        const accessToken = hashParams.get('access_token')
        const refreshToken = hashParams.get('refresh_token')
        const error = hashParams.get('error') || urlParams.get('error')
        
        if (error) {
          setError(`Authentication error: ${error}`)
          setIsProcessingInvite(false)
          return
        }
        
        // If we have tokens in hash, set the session
        if (accessToken && refreshToken) {
          const { error: setSessionError } = await supabase.auth.setSession({
            access_token: accessToken,
            refresh_token: refreshToken
          })
          
          if (setSessionError) {
            setError('Failed to authenticate. Please try again.')
            setIsProcessingInvite(false)
            return
          }
        }

        // WAITING LOGIC: Check once, then listen
        const { data: { session } } = await supabase.auth.getSession()
        
        if (session?.user) {
          setInviteData(session.user)
          setIsProcessingInvite(false)
        } else {
          // If session isn't ready yet, listen for the event
          const { data: { subscription: sub } } = supabase.auth.onAuthStateChange((event, session) => {
            if (event === 'SIGNED_IN' && session?.user) {
              setInviteData(session.user)
              setIsProcessingInvite(false)
              if (sub) {
                sub.unsubscribe() // Clean up immediately
              }
            }
          })
          subscription = sub
        }
        
      } catch (err) {
        setError('Failed to process invitation. Please try again.')
        setIsProcessingInvite(false)
      }
    }

    handleInvitation()

    return () => {
      if (subscription) {
        subscription.unsubscribe()
      }
    }
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
          const message = (passwordError.message ?? '').toLowerCase()
          const isPasswordReuseError =
            message.includes('different') ||
            message.includes('same password') ||
            message.includes('previous password')

          if (!isPasswordReuseError) {
            throw new Error(`Failed to update password: ${passwordError.message}`)
          }
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
      setError(err.message || 'Failed to complete profile. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isProcessingInvite) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 py-10">
        <Card className="w-full max-w-xl p-6">
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
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 py-10">
        <Card className="w-full max-w-xl p-6">
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
    <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 py-10">
      <Card className="w-full max-w-4xl p-0">
        <CardHeader className="px-6 pt-6">
          <CardTitle>Welcome! Let&apos;s complete your profile.</CardTitle>
          <CardDescription>
            You&apos;ve been invited to join. Please fill out your profile information below.
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit} autoComplete="off">
          <CardContent className="space-y-6 px-6 py-6">
            <div className="grid gap-8 lg:grid-cols-[1fr_1fr]">
              <div className="space-y-6">
                <h3 className="text-lg font-semibold">Account Information</h3>

                <div className="space-y-4">
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
                      type={passwordInputType}
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
                      type={passwordInputType}
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

                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <input
                    id="showPassword"
                    type="checkbox"
                    className="h-4 w-4 rounded border-input bg-background text-primary focus-visible:ring-ring"
                    checked={showPassword}
                    onChange={(e) => setShowPassword(e.target.checked)}
                    disabled={isSubmitting}
                  />
                  <label htmlFor="showPassword" className="font-medium">
                    Show password
                  </label>
                </div>
              </div>

              <div className="space-y-6">
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
              </div>
            </div>

            {error && (
              <Alert variant="destructive">
                <AlertTitle>Error</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
          </CardContent>
          <CardFooter className="px-6 pb-6">
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

