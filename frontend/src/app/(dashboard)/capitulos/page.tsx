"use client"

import { useEffect, useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import Link from "next/link"
import { apiGet } from "@/lib/api"

interface Capitulo {
  id: number
  numero: number
  titulo: string | null
  obra_slug?: string
  obra_titulo?: string
  paginas?: unknown[]
  criado_em?: string
}

export default function CapitulosPage() {
  const [capitulos, setCapitulos] = useState<Capitulo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const data = await apiGet<Capitulo[] | { results: Capitulo[] }>("/capitulos/")
        const lista = Array.isArray(data) ? data : (data?.results ?? [])
        // Ordena por criado_em desc se existir, senão por id desc
        lista.sort((a, b) => {
          if (a.criado_em && b.criado_em) {
            return b.criado_em.localeCompare(a.criado_em)
          }
          return b.id - a.id
        })
        if (!cancelled) setCapitulos(lista)
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Erro ao carregar capítulos")
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [])

  return (
    <div className="px-4 sm:px-6 py-4 sm:py-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
        <div>
          <h1 className="text-xl sm:text-2xl font-semibold text-foreground">Capítulos Recentes</h1>
          <p className="text-[oklch(0.55_0_0)] text-sm mt-1">Todos os capítulos cadastrados</p>
        </div>
      </div>

      {loading ? (
        <p className="text-[oklch(0.55_0_0)] text-center py-10">Carregando...</p>
      ) : error ? (
        <p className="text-red-400 text-center py-10">{error}</p>
      ) : capitulos.length === 0 ? (
        <div className="bg-[oklch(0.12_0_0)] border border-border rounded-lg py-12 text-center">
          <p className="text-[oklch(0.55_0_0)]">Nenhum capítulo cadastrado.</p>
        </div>
      ) : (
        <div className="bg-[oklch(0.12_0_0)] border border-border rounded-lg overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="border-border">
                <TableHead className="text-[oklch(0.55_0_0)] font-medium">Obra</TableHead>
                <TableHead className="text-[oklch(0.55_0_0)] font-medium">Capítulo</TableHead>
                <TableHead className="text-[oklch(0.55_0_0)] font-medium">Título</TableHead>
                <TableHead className="text-[oklch(0.55_0_0)] font-medium text-right">Páginas</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {capitulos.map((cap) => (
                <TableRow key={cap.id} className="border-border">
                  <TableCell className="text-foreground">{cap.obra_titulo || cap.obra_slug || "—"}</TableCell>
                  <TableCell>
                    {cap.obra_slug ? (
                      <Link href={`/obras/${cap.obra_slug}`} className="text-primary hover:underline">
                        #{cap.numero}
                      </Link>
                    ) : (
                      <span className="text-primary">#{cap.numero}</span>
                    )}
                  </TableCell>
                  <TableCell className="text-[oklch(0.75_0_0)]">{cap.titulo || "Sem título"}</TableCell>
                  <TableCell className="text-[oklch(0.55_0_0)] text-right">
                    {cap.paginas?.length || 0}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  )
}
