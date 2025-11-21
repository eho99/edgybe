import { getUserFriendlyMessage, getTechnicalMessage } from "./errorMessages"

/**
 * Error handler utility functions
 */

export interface HandledError {
  userMessage: string
  technicalMessage: string
  originalError: unknown
}

/**
 * Handle and format an error for display
 */
export function handleError(error: unknown): HandledError {
  const userMessage = getUserFriendlyMessage(error)
  const technicalMessage = getTechnicalMessage(error)
  
  // Log technical details for debugging
  console.error("Error occurred:", {
    technical: technicalMessage,
    user: userMessage,
    error,
  })
  
  return {
    userMessage,
    technicalMessage,
    originalError: error,
  }
}

/**
 * Check if error is a network error
 */
export function isNetworkError(error: unknown): boolean {
  if (error instanceof Error) {
    return (
      error.message.includes("Network") ||
      error.message.includes("fetch") ||
      error.message.includes("Failed to fetch")
    )
  }
  return false
}

/**
 * Check if error is an authentication error
 */
export function isAuthError(error: unknown): boolean {
  if (error instanceof Error) {
    return (
      error.message.includes("401") ||
      error.message.includes("403") ||
      error.message.includes("Unauthorized") ||
      error.message.includes("Forbidden") ||
      error.message.includes("Session expired")
    )
  }
  return false
}

/**
 * Check if error is a validation error
 */
export function isValidationError(error: unknown): boolean {
  if (error instanceof Error) {
    return (
      error.message.includes("Validation") ||
      error.message.includes("Invalid") ||
      error.message.includes("400")
    )
  }
  return false
}

