"use client"

import { useAuth } from "@/contexts/AuthContext"
import Sidebar, { MobileHeader } from "@/components/Sidebar"
import { ReactNode, useState, useCallback } from "react"

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const { user, isLoading, isAuthenticated } = useAuth()
  const [mobileOpen, setMobileOpen] = useState(false)

  const handleMenuClick = useCallback(() => setMobileOpen(true), [])
  const handleSidebarClose = useCallback(() => setMobileOpen(false), [])

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[oklch(0.06_0_0)] flex items-center justify-center">
        <p className="text-[oklch(0.55_0_0)]">Carregando...</p>
      </div>
    )
  }

  if (!isAuthenticated || !user) {
    return (
      <div className="min-h-screen bg-[oklch(0.06_0_0)] flex items-center justify-center">
        <p className="text-[oklch(0.55_0_0)]">Redirecionando...</p>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar mobileOpen={mobileOpen} onClose={handleSidebarClose} />
      <div className="flex-1 flex flex-col min-w-0">
        <MobileHeader onMenuClick={handleMenuClick} />
        <main className="flex-1">{children}</main>
      </div>
    </div>
  )
}
