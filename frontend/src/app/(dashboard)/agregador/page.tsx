"use client"

import { useEffect, useState } from "react"
import { Card, CardHeader, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import NovaObraDialog from "@/components/NovaObraDialog"
import SearchBar from "@/components/SearchBar"
import { Bookmark, BookOpen, Plus, ArrowUpRight } from "lucide-react"
import Link from "next/link"
import { apiGet } from "@/lib/api"
import { useRequireTime } from "@/lib/teamGuard"

interface Obra {
  id: number
  titulo: string
  autor: string
  slug: string
  status: string
  fonte: string
  idioma?: string
  capa_url: string | null
  capitulos: Capitulo[]
}

interface Capitulo {
  id: number
  numero: number
  titulo: string
  paginas: any[]
}

export default function AgregadorPage() {
  const allowed = useRequireTime("agregador")
  const [obras, setObras] = useState<Obra[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [idioma, setIdioma] = useState<"pt" | "en">(() => {
    if (typeof window !== "undefined") {
      return (localStorage.getItem("agregador_idioma") as "pt" | "en") || "pt"
    }
    return "pt"
  })

  useEffect(() => {
    if (!allowed) return
    loadObras()
  }, [allowed, idioma])

  useEffect(() => {
    localStorage.setItem("agregador_idioma", idioma)
  }, [idioma])

  async function loadObras() {
    try {
      setLoading(true)
      const data = await apiGet<Obra[]>(`/agregador/obras/?idioma=${idioma}`)
      setObras(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao carregar obras do agregador")
    } finally {
      setLoading(false)
    }
  }

  if (!allowed) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-[oklch(0.55_0_0)]">Verificando acesso...</p>
      </div>
    )
  }

  const totalCapitulos = obras.reduce((acc, o) => acc + (o.capitulos?.length || 0), 0)
  const totalPaginas = obras.reduce((acc, o) =>
    acc + (o.capitulos?.reduce((s, c) => s + (c.paginas?.length || 0), 0) || 0), 0)

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-[oklch(0.55_0_0)]">Carregando...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-red-400">{error}</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen">
      {/* Top bar */}
      <div className="border-b border-border px-4 sm:px-6 py-3">
        <div className="flex items-center gap-3 sm:gap-4 max-w-6xl mx-auto">
          <SearchBar />
          <NovaObraDialog />
        </div>
      </div>

      <div className="px-4 sm:px-6 py-4 sm:py-6 max-w-6xl mx-auto">
        {/* Welcome + Language Filter */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
          <div>
            <h1 className="text-xl sm:text-2xl font-semibold text-foreground">Agregador</h1>
            <p className="text-[oklch(0.55_0_0)] text-sm mt-1">Obras externas agregadas automaticamente</p>
          </div>
          <div className="flex items-center gap-1 bg-[oklch(0.10_0_0)] rounded-lg p-1 border border-border">
            <button
              onClick={() => setIdioma("pt")}
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
                idioma === "pt"
                  ? "bg-primary text-primary-foreground"
                  : "text-[oklch(0.65_0_0)] hover:text-foreground"
              }`}
            >
              🇧🇷 PT
            </button>
            <button
              onClick={() => setIdioma("en")}
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
                idioma === "en"
                  ? "bg-primary text-primary-foreground"
                  : "text-[oklch(0.65_0_0)] hover:text-foreground"
              }`}
            >
              🇺🇸 EN
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4 mb-6 sm:mb-8">
          <Card className="bg-[oklch(0.12_0_0)] border-border">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <p className="text-[oklch(0.55_0_0)] text-sm">Obras ({idioma.toUpperCase()})</p>
                <Bookmark className="w-4 h-4 text-[oklch(0.55_0_0)]" />
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-foreground">{obras.length}</p>
            </CardContent>
          </Card>

          <Card className="bg-[oklch(0.12_0_0)] border-border">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <p className="text-[oklch(0.55_0_0)] text-sm">Capítulos ({idioma.toUpperCase()})</p>
                <BookOpen className="w-4 h-4 text-[oklch(0.55_0_0)]" />
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-foreground">{totalCapitulos}</p>
            </CardContent>
          </Card>

          <Card className="bg-[oklch(0.12_0_0)] border-border">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <p className="text-[oklch(0.55_0_0)] text-sm">Páginas ({idioma.toUpperCase()})</p>
                <ArrowUpRight className="w-4 h-4 text-[oklch(0.55_0_0)]" />
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-foreground">{totalPaginas}</p>
            </CardContent>
          </Card>
        </div>

        {/* Obras do Agregador */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-base font-semibold text-foreground">Catálogo do Agregador ({idioma.toUpperCase()})</h2>
          </div>

          {obras.length === 0 ? (
            <p className="text-[oklch(0.55_0_0)] text-center py-10">Nenhuma obra {idioma.toUpperCase()} do Agregador cadastrada.</p>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
              {obras.map((obra) => (
                <Link key={obra.id} href={`/obras/${obra.slug}`} className="block group">
                  <div className="bg-[oklch(0.12_0_0)] border border-border rounded-lg overflow-hidden transition-colors hover:border-primary/30">
                    <div className="aspect-[3/4] bg-[oklch(0.16_0_0)] relative overflow-hidden">
                      {obra.capa_url ? (
                        <img
                          src={obra.capa_url}
                          alt={obra.titulo}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <span className="text-2xl font-bold text-[oklch(0.3_0_0)]">
                            {obra.titulo?.charAt(0).toUpperCase()}
                          </span>
                        </div>
                      )}
                    </div>
                    <div className="p-2">
                      <p className="text-foreground text-xs font-medium truncate group-hover:text-primary transition-colors">
                        {obra.titulo}
                      </p>
                      <div className="flex items-center justify-between mt-1">
                        <span className="text-[oklch(0.55_0_0)] text-[10px]">
                          {obra.capitulos?.length || 0} caps
                        </span>
                        <span className={`text-[9px] font-bold uppercase px-1 py-0.5 rounded ${
                          obra.idioma === "en" ? "bg-blue-500/20 text-blue-400" : "bg-green-500/20 text-green-400"
                        }`}>
                          {obra.idioma?.toUpperCase() || "?"}
                        </span>
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
