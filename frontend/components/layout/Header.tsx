"use client"

import Link from "next/link"
import {
  NavigationMenu,
  NavigationMenuList,
  NavigationMenuItem,
  NavigationMenuLink,
} from "@/components/ui/navigation-menu"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { ProfileDropdown } from "./ProfileDropdown"

const navItems = [
  { label: "Overview", href: "/dashboard" },
  { label: "Accounts", href: "/dashboard/admin/accounts" },
  { label: "Referrals", href: "/dashboard/referrals" },
]

interface HeaderProps {
  title?: string
  description?: string
}

export function Header({ title, description }: HeaderProps) {
  return (
    <header className="sticky top-0 z-40 border-b border-border/60 bg-background/80 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/60 sm:px-6">
      <div className="flex h-16 items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <SidebarTrigger className="rounded-full border border-border/60 text-muted-foreground hover:text-foreground" />
          <NavigationMenu className="hidden md:flex">
            <NavigationMenuList>
              {navItems.map((item) => (
                <NavigationMenuItem key={item.href}>
                  <NavigationMenuLink asChild>
                    <Link
                      href={item.href}
                      className="rounded-full px-3 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                    >
                      {item.label}
                    </Link>
                  </NavigationMenuLink>
                </NavigationMenuItem>
              ))}
            </NavigationMenuList>
          </NavigationMenu>
        </div>
        <div className="flex items-center gap-3">
          <ProfileDropdown />
        </div>
      </div>
      {(title || description) && (
        <div className="pb-4">
          {title && (
            <h1 className="text-base font-semibold text-foreground sm:text-lg">{title}</h1>
          )}
          {description && <p className="text-sm text-muted-foreground">{description}</p>}
        </div>
      )}
    </header>
  )
}

