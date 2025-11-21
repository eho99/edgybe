"use client"

import { type ReactNode } from "react"
import { Sidebar } from "@/components/layout/Sidebar"
import { Header } from "@/components/layout/Header"
import { ErrorBoundary } from "@/components/error/ErrorBoundary"

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <ErrorBoundary>
      <div className="flex min-h-screen bg-muted/30">
        <Sidebar />
        <div className="flex flex-1 flex-col overflow-hidden">
          <Header />
          <main className="flex-1 overflow-y-auto p-4 sm:p-6">{children}</main>
        </div>
      </div>
    </ErrorBoundary>
  )
}
