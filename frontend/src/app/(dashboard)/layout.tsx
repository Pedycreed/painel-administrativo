"use client"

import { useAuth } from "@/contexts/AuthContext"
import Sidebar from "@/components/Sidebar"
import { ReactNode } from "react"

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const { user, isLoading, isAuthenticated } = useAuth()

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[oklch(0.06_0_0)] flex items-center justify-center">
        <p className="text-[oklch(0.55_0_0)]">Carregando...</p>
      </div>
    )
  }

  // O AuthContext já redireciona automaticamente
  if (!isAuthenticated || !user) {
    return (
      <div className="min-h-screen bg-[oklch(0.06_0_0)] flex items-center justify-center">
        <p className="text-[oklch(0.55_0_0)]">Redirecionando...</p>
      </div>
    )
  }

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1">{children}</main>
    </div>
  )
}