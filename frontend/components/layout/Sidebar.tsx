"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import {
  LayoutDashboard,
  Users,
  UserPlus,
  FileText,
  Settings,
  ChevronLeft,
  ChevronRight,
  Bug,
  Building2,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { NavSection } from "./NavSection"
import { useCurrentUserRole } from "@/hooks/useCurrentUserRole"

const SIDEBAR_COLLAPSED_KEY = "sidebar-collapsed"

export function Sidebar() {
  const pathname = usePathname()
  const { isAdmin, isLoading: roleLoading } = useCurrentUserRole()
  const [isCollapsed, setIsCollapsed] = useState(false)

  useEffect(() => {
    const saved = localStorage.getItem(SIDEBAR_COLLAPSED_KEY)
    if (saved !== null) {
      setIsCollapsed(JSON.parse(saved))
    }
  }, [])

  const toggleCollapse = () => {
    const newState = !isCollapsed
    setIsCollapsed(newState)
    localStorage.setItem(SIDEBAR_COLLAPSED_KEY, JSON.stringify(newState))
  }

  const mainNavItems = [
    {
      label: "Dashboard",
      href: "/dashboard",
      icon: LayoutDashboard,
    },
  ]

  const referralsNavItems = [
    {
      label: "Overview",
      href: "/dashboard/referrals",
      icon: FileText,
    },
  ]

  const adminNavItems = [
    {
      label: "Invitations",
      href: "/dashboard/admin/invitations",
      icon: UserPlus,
    },
    {
      label: "Accounts",
      href: "/dashboard/admin/accounts",
      icon: Users,
    },
    {
      label: "Students & Guardians",
      href: "/dashboard/admin/students-guardians",
      icon: FileText,
    },
  ]

  const devNavItems = [
    {
      label: "Organizations",
      href: "/dashboard/organizations",
      icon: Building2,
    },
  ]

  return (
    <aside
      className={cn(
        "relative flex h-screen flex-col border-r bg-background transition-all duration-300",
        isCollapsed ? "w-16" : "w-64"
      )}
    >
      {/* Logo/Brand */}
      <div className="flex h-16 items-center border-b px-4">
        {!isCollapsed && (
          <Link href="/dashboard" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <LayoutDashboard className="h-4 w-4" />
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-semibold">EdgyBe</span>
              <span className="text-xs text-muted-foreground">Console</span>
            </div>
          </Link>
        )}
        {isCollapsed && (
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground mx-auto">
            <LayoutDashboard className="h-4 w-4" />
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-4 overflow-y-auto p-4">
        <NavSection items={mainNavItems} />

        <NavSection
          title="Referrals"
          items={referralsNavItems}
          collapsible={true}
          defaultOpen={true}
        />

        {!roleLoading && isAdmin && (
          <NavSection
            title="Admin"
            items={adminNavItems}
            collapsible={true}
            defaultOpen={true}
          />
        )}

        <NavSection
          title="Dev Tools"
          items={devNavItems}
          collapsible={true}
          defaultOpen={false}
        />
      </nav>

      {/* Footer */}
      <div className="border-t p-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleCollapse}
          className="w-full"
          title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {isCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </Button>
        {!isCollapsed && (
          <p className="mt-2 text-xs text-center text-muted-foreground">
            &copy; {new Date().getFullYear()} EdgyBe
          </p>
        )}
      </div>
    </aside>
  )
}

