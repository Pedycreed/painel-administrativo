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
  capa_url: string | null
  capitulos: Capitulo[]
}

interface Capitulo {
  id: number
  numero: number
  titulo: string
  paginas: any[]
}

export default function ScanPage() {
  const allowed = useRequireTime("scan")
  const [obras, setObras] = useState<Obra[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    if (!allowed) return
    loadObras()
  }, [allowed])

  async function loadObras() {
    try {
      // Fetch apenas obras da scan
      const data = await apiGet<Obra[]>("/scan/obras/")
      setObras(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao carregar obras da scan")
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
      <div className="border-b border-border px-6 py-3">
        <div className="flex items-center gap-4 max-w-6xl mx-auto">
          <SearchBar />
          <NovaObraDialog />
        </div>
      </div>

      <div className="px-6 py-6 max-w-6xl mx-auto">
        {/* Welcome */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-semibold text-foreground">Scan</h1>
            <p className="text-[oklch(0.55_0_0)] text-sm mt-1">Obras originais traduzidas pela equipe</p>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          <Card className="bg-[oklch(0.12_0_0)] border-border">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <p className="text-[oklch(0.55_0_0)] text-sm">Obras (Scan)</p>
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
                <p className="text-[oklch(0.55_0_0)] text-sm">Capítulos (Scan)</p>
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
                <p className="text-[oklch(0.55_0_0)] text-sm">Páginas (Scan)</p>
                <ArrowUpRight className="w-4 h-4 text-[oklch(0.55_0_0)]" />
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-foreground">{totalPaginas}</p>
            </CardContent>
          </Card>
        </div>

        {/* Obras da Scan */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-base font-semibold text-foreground">Catálogo da Scan</h2>
          </div>

          {obras.length === 0 ? (
            <p className="text-[oklch(0.55_0_0)] text-center py-10">Nenhuma obra da Scan cadastrada.</p>
          ) : (
            <div className="grid grid-cols-6 gap-3">
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
