'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { type ReactNode } from 'react'
import { LayoutDashboard, Building2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

const navItems = [
  { label: 'Overview', href: '/dashboard', icon: LayoutDashboard },
  { label: 'Organizations', href: '/dashboard/organizations', icon: Building2 },
]

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname()

  return (
    <div className="flex min-h-screen bg-muted/30">
      <aside className="hidden w-64 flex-col border-r bg-white lg:flex">
        <div className="border-b px-6 py-6">
          <p className="text-lg font-semibold">District Console</p>
          <p className="text-sm text-muted-foreground">Operations & insights</p>
        </div>
        <nav className="flex-1 space-y-1 px-3 py-4">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive =
              pathname === item.href || (item.href !== '/dashboard' && pathname.startsWith(item.href))
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary/10 text-primary focus-visible:ring-2'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                )}
              >
                <Icon className="h-4 w-4" aria-hidden />
                {item.label}
              </Link>
            )
          })}
        </nav>
        <div className="px-6 py-4 text-xs text-muted-foreground">
          &copy; {new Date().getFullYear()} EdgyBe
        </div>
      </aside>
      <div className="flex flex-1 flex-col">
        <header className="flex flex-col gap-2 border-b bg-white px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <div>
            <p className="text-sm text-muted-foreground">EdgyBe Dashboard</p>
            <h1 className="text-xl font-semibold text-foreground">District overview</h1>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" size="sm">
              Support
            </Button>
            <Button size="sm">New action</Button>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto px-4 py-6 sm:px-6">{children}</main>
      </div>
    </div>
  )
}

