"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { AlertCircle } from "lucide-react"
import { getUserFriendlyMessage } from "@/lib/errorMessages"

interface ErrorDisplayProps {
  error: Error
  resetError?: () => void
  title?: string
  description?: string
}

export function ErrorDisplay({ 
  error, 
  resetError, 
  title = "Something went wrong",
  description 
}: ErrorDisplayProps) {
  const userMessage = description || getUserFriendlyMessage(error)

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <CardTitle>{title}</CardTitle>
          </div>
          <CardDescription>
            An unexpected error occurred. Please try again.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Alert variant="destructive">
            <AlertTitle>Error Details</AlertTitle>
            <AlertDescription>{userMessage}</AlertDescription>
          </Alert>
          {resetError && (
            <div className="flex gap-2">
              <Button onClick={resetError} className="flex-1">
                Try Again
              </Button>
              <Button
                variant="outline"
                onClick={() => window.location.reload()}
                className="flex-1"
              >
                Reload Page
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

