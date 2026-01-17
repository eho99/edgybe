"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { createClient } from "@/lib/supabase/client"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Button } from "@/components/ui/button"
import { User, LogOut, Settings } from "lucide-react"
import { useProfile } from "@/hooks/useProfile"
import { useErrorHandler } from "@/hooks/useErrorHandler"
import { useToast } from "@/hooks/useToast"
import { Loader } from "@/components/ui/loader"
import { useCurrentUserRole } from "@/hooks/useCurrentUserRole"

interface ProfileDropdownProps {
  className?: string
}

export function ProfileDropdown({ className }: ProfileDropdownProps) {
  const router = useRouter()
  const supabase = createClient()
  const { profile, isLoading } = useProfile()
  const { role } = useCurrentUserRole()
  const { handleError } = useErrorHandler()
  const { toast } = useToast()
  const [isLoggingOut, setIsLoggingOut] = useState(false)

  const handleLogout = async () => {
    setIsLoggingOut(true)
    try {
      const { error } = await supabase.auth.signOut()
      if (error) {
        handleError(error, { title: "Logout failed" })
      } else {
        toast({
          variant: "success",
          title: "Logged out",
          description: "You have been successfully logged out.",
        })
        router.push("/login")
      }
    } catch (err) {
      handleError(err, { title: "Logout failed" })
    } finally {
      setIsLoggingOut(false)
    }
  }

  const userInitials = profile?.full_name
    ? profile.full_name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : profile?.id
    ? profile.id.slice(0, 2).toUpperCase()
    : "U"

  const displayName = profile?.full_name || "Team member"
  const roleLabel = role ? role.replace(/_/g, " ") : "Member"

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          className={`flex items-center gap-2 rounded-full border border-border/60 px-2 py-1 hover:border-border ${className}`}
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-primary to-primary/70 text-sm font-semibold text-primary-foreground shrink-0">
            {userInitials}
          </div>
          <div className="hidden text-left leading-tight sm:flex sm:flex-col">
            <span className="text-sm font-semibold text-foreground">{displayName}</span>
            <span className="text-xs text-muted-foreground capitalize">{roleLabel}</span>
          </div>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-56" align="end" forceMount>
        <DropdownMenuLabel className="font-normal">
          <div className="flex flex-col space-y-1">
            <p className="text-sm font-medium leading-none">{displayName}</p>
            <p className="text-xs leading-none text-muted-foreground capitalize">
              {roleLabel}
            </p>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem disabled={isLoading}>
          <User className="mr-2 h-4 w-4" />
          <span>Profile</span>
        </DropdownMenuItem>
        <DropdownMenuItem disabled>
          <Settings className="mr-2 h-4 w-4" />
          <span>Settings</span>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          onClick={handleLogout}
          disabled={isLoggingOut}
          className="text-destructive focus:text-destructive"
        >
          {isLoggingOut ? (
            <Loader size="sm" className="mr-2" />
          ) : (
            <LogOut className="mr-2 h-4 w-4" />
          )}
          <span>{isLoggingOut ? "Logging out..." : "Log out"}</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

