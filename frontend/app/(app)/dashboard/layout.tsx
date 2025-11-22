"use client"

import { type ReactNode } from "react"
import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar"
import { AppSidebar } from "@/components/layout/Sidebar"
import { Header } from "@/components/layout/Header"
import { ErrorBoundary } from "@/components/error/ErrorBoundary"

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <SidebarProvider>
      <div className="flex min-h-screen w-full bg-muted/30">
        <AppSidebar />
        <SidebarInset className="flex flex-1 flex-col">
          <ErrorBoundary>
            <Header />
            <main className="flex-1 overflow-y-auto p-4 sm:p-6">{children}</main>
          </ErrorBoundary>
        </SidebarInset>
      </div>
    </SidebarProvider>
  )
}
