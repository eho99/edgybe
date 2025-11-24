"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  Sidebar as SidebarShell,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from "@/components/ui/sidebar"
import {
  LayoutDashboard,
  Users,
  UserPlus,
  FileText,
  Building2,
  Landmark,
} from "lucide-react"
import { useCurrentUserRole } from "@/hooks/useCurrentUserRole"
import { cn } from "@/lib/utils"

interface NavItem {
  label: string
  href: string
  icon: React.ComponentType<{ className?: string }>
}

const mainNavItems: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
]

const referralNavItems: NavItem[] = [
  { label: "Overview", href: "/dashboard/referrals", icon: FileText },
]

const adminNavItems: NavItem[] = [
  { label: "Invitations", href: "/dashboard/admin/invitations", icon: UserPlus },
  { label: "Accounts", href: "/dashboard/admin/accounts", icon: Users },
  { label: "Students & Guardians", href: "/dashboard/admin/students-guardians", icon: FileText },
  { label: "School Settings", href: "/dashboard/school-settings", icon: Landmark },
]

const devNavItems: NavItem[] = [
  { label: "Organizations", href: "/dashboard/organizations", icon: Building2 },
]

function NavSection({ title, items }: { title?: string; items: NavItem[] }) {
  const pathname = usePathname()
  return (
    <SidebarGroup>
      {title && <SidebarGroupLabel>{title}</SidebarGroupLabel>}
      <SidebarGroupContent>
        <SidebarMenu>
          {items.map((item) => {
            const Icon = item.icon
            const isActive =
              pathname === item.href ||
              (item.href !== "/dashboard" && pathname.startsWith(item.href))
            return (
              <SidebarMenuItem key={item.href}>
                <SidebarMenuButton asChild isActive={isActive} tooltip={item.label}>
                  <Link href={item.href} className="flex items-center gap-2">
                    <Icon className="h-4 w-4" />
                    <span>{item.label}</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            )
          })}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  )
}

export function AppSidebar() {
  const { isAdmin } = useCurrentUserRole()

  return (
    <>
      <SidebarShell collapsible="icon" className="border-border/60">
        <SidebarHeader className="border-b border-border/60">
          <Link href="/dashboard" className="flex items-center gap-3 px-2 py-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-2xl bg-primary text-primary-foreground">
              <LayoutDashboard className="h-4 w-4" />
            </div>
            <div className="flex flex-col text-sm font-semibold">
              <span>EdgyBe</span>
              <span className="text-xs font-normal text-muted-foreground">
                District Console
              </span>
            </div>
          </Link>
        </SidebarHeader>
        <SidebarContent>
          <NavSection items={mainNavItems} />
          <NavSection title="Referrals" items={referralNavItems} />
          {isAdmin && <NavSection title="Admin" items={adminNavItems} />}
          <NavSection title="Dev Tools" items={devNavItems} />
        </SidebarContent>
        <SidebarFooter className="border-t border-border/60 text-xs text-muted-foreground">
          &copy; {new Date().getFullYear()} EdgyBe
        </SidebarFooter>
      </SidebarShell>
      <SidebarRail />
    </>
  )
}

