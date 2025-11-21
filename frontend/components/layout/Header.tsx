"use client"

import { ProfileDropdown } from "./ProfileDropdown"

interface HeaderProps {
  title?: string
  description?: string
}

export function Header({ title, description }: HeaderProps) {
  return (
    <header className="sticky top-0 z-40 flex h-16 shrink-0 items-center gap-4 border-b bg-background px-4 sm:px-6">
      <div className="flex flex-1 items-center gap-4">
        {title && (
          <div className="flex flex-col">
            <h1 className="text-lg font-semibold">{title}</h1>
            {description && (
              <p className="text-sm text-muted-foreground">{description}</p>
            )}
          </div>
        )}
      </div>
      <div className="flex items-center gap-4">
        <ProfileDropdown />
      </div>
    </header>
  )
}

