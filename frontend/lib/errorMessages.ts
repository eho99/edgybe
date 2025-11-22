/**
 * Maps technical error messages to user-friendly messages
 */

export interface ErrorMessage {
  userMessage: string
  technicalMessage?: string
}

/**
 * Common error message mappings
 */
export const ERROR_MESSAGES: Record<string, string> = {
  // Network errors
  "Network request failed": "Unable to connect to the server. Please check your internet connection.",
  "Failed to fetch": "Unable to connect to the server. Please try again later.",
  "NetworkError": "Network error occurred. Please check your connection and try again.",
  
  // Authentication errors
  "Unauthorized": "You are not authorized to perform this action. Please log in again.",
  "Forbidden": "You don't have permission to access this resource.",
  "Invalid credentials": "Invalid email or password. Please try again.",
  "Session expired": "Your session has expired. Please log in again.",
  
  // API errors
  "Not Found": "The requested resource was not found.",
  "Internal Server Error": "An unexpected error occurred. Please try again later.",
  "Bad Request": "Invalid request. Please check your input and try again.",
  "Conflict": "This action conflicts with existing data. Please review and try again.",
  
  // Validation errors
  "Validation error": "Please check your input and try again.",
  "Invalid input": "The information you provided is invalid. Please review and try again.",
  
  // Generic
  "An error occurred": "Something went wrong. Please try again.",
}

/**
 * Get user-friendly error message from error
 */
export function getUserFriendlyMessage(error: unknown): string {
  if (error instanceof Error) {
    // Check if we have a specific mapping
    const message = error.message
    for (const [key, value] of Object.entries(ERROR_MESSAGES)) {
      if (message.includes(key) || message.toLowerCase().includes(key.toLowerCase())) {
        return value
      }
    }
    
    // Check for HTTP status codes in message
    if (message.includes("404")) {
      return ERROR_MESSAGES["Not Found"]
    }
    if (message.includes("401") || message.includes("403")) {
      return ERROR_MESSAGES["Unauthorized"]
    }
    if (message.includes("500")) {
      return ERROR_MESSAGES["Internal Server Error"]
    }
    if (message.includes("400")) {
      return ERROR_MESSAGES["Bad Request"]
    }
    
    // Return the error message if it's already user-friendly
    if (message.length < 100 && !message.includes("Error:") && !message.includes("at ")) {
      return message
    }
  }
  
  if (typeof error === "string") {
    return ERROR_MESSAGES[error] || error
  }
  
  return ERROR_MESSAGES["An error occurred"]
}

/**
 * Extract technical details for logging
 */
export function getTechnicalMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message
  }
  if (typeof error === "string") {
    return error
  }
  return String(error)
}

