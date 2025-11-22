import { useCallback } from "react"
import { handleError, isAuthError } from "@/lib/errorHandler"
import { useToast } from "./useToast"
import { useRouter } from "next/navigation"

/**
 * Hook for consistent error handling across components
 */
export function useErrorHandler() {
  const { toast } = useToast()
  const router = useRouter()

  const handleErrorWithToast = useCallback(
    (error: unknown, options?: { 
      title?: string
      showToast?: boolean
      redirectOnAuthError?: boolean
    }) => {
      const { title = "Error", showToast = true, redirectOnAuthError = true } = options || {}
      const handled = handleError(error)

      // Log error for debugging
      console.error(`[${title}]`, handled.technicalMessage, handled.originalError)

      // Handle authentication errors
      if (isAuthError(error) && redirectOnAuthError) {
        router.push("/login")
        return handled
      }

      // Show toast notification
      if (showToast) {
        toast({
          variant: "destructive",
          title,
          description: handled.userMessage,
        })
      }

      return handled
    },
    [toast, router]
  )

  return {
    handleError: handleErrorWithToast,
    handleErrorSync: handleError,
  }
}

