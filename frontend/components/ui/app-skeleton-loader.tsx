"use client"

import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar"
import { Skeleton } from "@/components/ui/skeleton"

export function AppSkeletonLoader() {
  return (
    <SidebarProvider>
      <div className="flex min-h-screen w-full bg-muted/30">
        {/* Sidebar Skeleton */}
        <aside className="hidden md:flex flex-col w-64 border-r border-border/60 bg-sidebar">
          {/* Sidebar Header */}
          <div className="flex items-center gap-3 px-2 py-3 border-b border-border/60">
            <Skeleton className="h-9 w-9 rounded-2xl" />
            <div className="flex flex-col gap-2 flex-1">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-3 w-24" />
            </div>
          </div>

          {/* Sidebar Content */}
          <div className="flex-1 px-2 py-4 space-y-6">
            {/* Main Nav Section */}
            <div className="space-y-2">
              <Skeleton className="h-4 w-16 mb-2" />
              <div className="space-y-1">
                <Skeleton className="h-9 w-full rounded-md" />
              </div>
            </div>

            {/* Referrals Nav Section */}
            <div className="space-y-2">
              <Skeleton className="h-4 w-20 mb-2" />
              <div className="space-y-1">
                <Skeleton className="h-9 w-full rounded-md" />
              </div>
            </div>

            {/* Admin Nav Section */}
            <div className="space-y-2">
              <Skeleton className="h-4 w-16 mb-2" />
              <div className="space-y-1">
                <Skeleton className="h-9 w-full rounded-md" />
                <Skeleton className="h-9 w-full rounded-md" />
                <Skeleton className="h-9 w-full rounded-md" />
                <Skeleton className="h-9 w-full rounded-md" />
              </div>
            </div>
          </div>

          {/* Sidebar Footer */}
          <div className="border-t border-border/60 px-2 py-3">
            <Skeleton className="h-3 w-32" />
          </div>
        </aside>

        {/* Main Content Area */}
        <SidebarInset className="flex flex-1 flex-col">
          {/* Header Skeleton */}
          <header className="sticky top-0 z-40 border-b border-border/60 bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-4 sm:px-6">
            <div className="flex h-16 items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <Skeleton className="h-9 w-9 rounded-full" />
                <div className="hidden md:flex gap-2">
                  <Skeleton className="h-8 w-20 rounded-full" />
                  <Skeleton className="h-8 w-24 rounded-full" />
                  <Skeleton className="h-8 w-20 rounded-full" />
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Skeleton className="h-9 w-9 rounded-full" />
                <Skeleton className="h-9 w-9 rounded-full" />
              </div>
            </div>
          </header>

          {/* Main Content Skeleton */}
          <main className="flex-1 overflow-y-auto p-4 sm:p-6">
            <div className="space-y-6">
              {/* Title Section */}
              <div className="space-y-2">
                <Skeleton className="h-9 w-64" />
                <Skeleton className="h-5 w-96 max-w-full" />
              </div>

              {/* Stats Cards */}
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <div className="rounded-lg border border-border bg-card p-6 space-y-3">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-8 w-20" />
                  <Skeleton className="h-3 w-32" />
                </div>
                <div className="rounded-lg border border-border bg-card p-6 space-y-3">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-8 w-20" />
                  <Skeleton className="h-3 w-32" />
                </div>
                <div className="rounded-lg border border-border bg-card p-6 space-y-3">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-8 w-20" />
                  <Skeleton className="h-3 w-32" />
                </div>
                <div className="rounded-lg border border-border bg-card p-6 space-y-3">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-8 w-20" />
                  <Skeleton className="h-3 w-32" />
                </div>
              </div>

              {/* Content Cards */}
              <div className="rounded-lg border border-border bg-card p-6 space-y-4">
                <Skeleton className="h-6 w-48" />
                <div className="space-y-3">
                  <Skeleton className="h-16 w-full" />
                  <Skeleton className="h-16 w-full" />
                  <Skeleton className="h-16 w-full" />
                </div>
              </div>
            </div>
          </main>
        </SidebarInset>
      </div>
    </SidebarProvider>
  )
}
