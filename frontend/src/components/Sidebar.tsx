"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { LayoutGrid, Clock, ImagePlus, Settings, LogOut, Library, BookCopy, Users } from "lucide-react"
import { useAuth } from "@/contexts/AuthContext"

type SidebarLink = {
  href: string
  label: string
  icon: typeof LayoutGrid
  /** Times autorizados a ver. undefined = todos. */
  times?: Array<"scan" | "agregador">
  /** Se true, só admin / superuser veem. */
  managerOnly?: boolean
}

const allLinks: SidebarLink[] = [
  { href: "/", label: "Visão Geral", icon: LayoutGrid },
  { href: "/scan", label: "Scan (Obras)", icon: Library, times: ["scan"] },
  { href: "/agregador", label: "Agregador (Obras)", icon: BookCopy, times: ["agregador"] },
  { href: "/capitulos", label: "Capítulos", icon: Clock },
  { href: "/upload", label: "Upload", icon: ImagePlus },
  { href: "/usuarios", label: "Usuários", icon: Users, managerOnly: true },
]

export default function Sidebar() {
  const pathname = usePathname()
  const { user, logout } = useAuth()

  const initials = user?.username?.slice(0, 2).toUpperCase() || "US"
  const papelDisplay = user?.papel_display || "Administrador"

  // Filtra links pelo time e pelo papel do usuário.
  const mainLinks = allLinks.filter((link) => {
    if (!user) return true
    // Links de gestão (Usuários): só admin/superuser
    if (link.managerOnly && !user.can_manage_users) return false
    // Links por time: superuser vê todos; usuário com time só vê o seu
    if (link.times) {
      if (user.has_full_access) return true
      return user.time ? link.times.includes(user.time) : true
    }
    return true
  })

  return (
    <aside className="w-64 min-h-screen bg-[oklch(0.06_0_0)] border-r border-border flex flex-col">
      <div className="p-5 flex items-center gap-2">
        <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
          <span className="text-primary-foreground font-bold text-sm">M</span>
        </div>
        <span className="text-foreground font-semibold text-lg">MangáPanel</span>
      </div>

      <nav className="flex-1 px-3 flex flex-col gap-1">
        {mainLinks.map((link) => {
          const Icon = link.icon
          const isActive = pathname === link.href || (link.href !== "/" && pathname?.startsWith(link.href))
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive
                  ? "bg-[oklch(0.14_0_0)] text-foreground"
                  : "text-[oklch(0.75_0_0)] hover:text-foreground hover:bg-[oklch(0.14_0_0)]"
              }`}
            >
              <Icon className="w-4 h-4" />
              {link.label}
            </Link>
          )
        })}
      </nav>

      <div className="px-3 pb-4 flex flex-col gap-1 border-t border-border pt-3">
        <Link
          href="/settings"
          className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-[oklch(0.75_0_0)] hover:text-foreground hover:bg-[oklch(0.14_0_0)] transition-colors"
        >
          <Settings className="w-4 h-4" />
          Configurações
        </Link>

        <div className="flex items-center gap-3 px-3 py-2 mt-1">
          <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
            {user?.avatar_url ? (
              <img src={user.avatar_url} alt={user.username} className="w-8 h-8 rounded-full object-cover" />
            ) : (
              <span className="text-xs text-primary font-medium">{initials}</span>
            )}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-foreground text-sm font-medium truncate">{user?.username || "Carregando..."}</p>
            <p className="text-[oklch(0.55_0_0)] text-xs truncate">
              {papelDisplay}
              {user?.time_display ? ` · ${user.time_display}` : ""}
            </p>
          </div>
        </div>

        <button
          onClick={logout}
          className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-[oklch(0.55_0_0)] hover:text-destructive hover:bg-destructive/10 transition-colors w-full"
        >
          <LogOut className="w-4 h-4" />
          Sair
        </button>
      </div>
    </aside>
  )
}