"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { ChevronRight, LucideIcon } from "lucide-react"
import { useState } from "react"
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"

interface NavItem {
  label: string
  href: string
  icon?: LucideIcon
}

interface NavSectionProps {
  title?: string
  items: NavItem[]
  collapsible?: boolean
  defaultOpen?: boolean
  isCollapsed?: boolean
}

export function NavSection({
  title,
  items,
  collapsible = false,
  defaultOpen = true,
  isCollapsed = false,
}: NavSectionProps) {
  const pathname = usePathname()

  if (isCollapsed) {
    return (
      <div className="space-y-2">
        {title && (
          <div className="text-[10px] font-semibold uppercase tracking-[0.3em] text-muted-foreground/70 text-center">
            {title}
          </div>
        )}
        <nav className="flex flex-col items-center gap-2">
          {items.map((item) => {
            const Icon = item.icon
            const isActive =
              pathname === item.href ||
              (item.href !== "/dashboard" && pathname.startsWith(item.href))
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "group flex h-11 w-11 items-center justify-center rounded-xl border border-transparent text-muted-foreground transition-colors",
                  isActive
                    ? "border-primary/30 bg-primary/10 text-primary"
                    : "hover:border-border/60 hover:text-foreground"
                )}
                aria-label={item.label}
              >
                {Icon && <Icon className="h-4 w-4" />}
                <span className="sr-only">{item.label}</span>
              </Link>
            )
          })}
        </nav>
      </div>
    )
  }

  if (collapsible && title) {
    return (
      <Accordion
        type="single"
        collapsible
        defaultValue={defaultOpen ? title : undefined}
        className="w-full"
      >
        <AccordionItem value={title} className="border-none">
          <AccordionTrigger className="py-2 text-sm font-medium text-muted-foreground hover:no-underline">
            {title}
          </AccordionTrigger>
          <AccordionContent>
            <nav className="space-y-1">
              {items.map((item) => {
                const Icon = item.icon
                const isActive =
                  pathname === item.href ||
                  (item.href !== "/dashboard" && pathname.startsWith(item.href))
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                      isActive
                        ? "bg-primary/10 text-primary"
                        : "text-muted-foreground hover:bg-muted hover:text-foreground"
                    )}
                  >
                    {Icon && <Icon className="h-4 w-4" />}
                    {item.label}
                  </Link>
                )
              })}
            </nav>
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    )
  }

  return (
    <div className="space-y-1">
      {title && (
        <div className="px-3 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
          {title}
        </div>
      )}
      <nav className="space-y-1">
        {items.map((item) => {
          const Icon = item.icon
          const isActive =
            pathname === item.href ||
            (item.href !== "/dashboard" && pathname.startsWith(item.href))
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              {Icon && <Icon className="h-4 w-4" />}
              {item.label}
            </Link>
          )
        })}
      </nav>
    </div>
  )
}

