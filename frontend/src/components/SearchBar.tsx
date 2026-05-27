"use client"

import { useState, useEffect, useRef } from "react"
import { Search } from "lucide-react"
import Link from "next/link"
import { apiGet } from "@/lib/api"

export default function SearchBar() {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<any[]>([])
  const [showDropdown, setShowDropdown] = useState(false)
  const [loading, setLoading] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!query.trim()) {
      setResults([])
      setShowDropdown(false)
      return
    }

    setLoading(true)
    const timer = setTimeout(async () => {
      try {
        const data = await apiGet<any[] | { results: any[] }>(`/obras/?search=${encodeURIComponent(query.trim())}`)
        const arr = Array.isArray(data) ? data : (data?.results ?? [])
        const filtered = arr.filter((o: any) =>
          o.titulo.toLowerCase().includes(query.toLowerCase()) ||
          o.autor.toLowerCase().includes(query.toLowerCase()) ||
          o.slug.toLowerCase().includes(query.toLowerCase())
        )
        setResults(filtered)
        setShowDropdown(true)
      } catch (e) {
        console.error(e)
        setResults([])
      } finally {
        setLoading(false)
      }
    }, 200)

    return () => clearTimeout(timer)
  }, [query])

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  function handleSelect() {
    setShowDropdown(false)
    setQuery("")
  }

  return (
    <div className="flex-1 relative" ref={dropdownRef}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[oklch(0.55_0_0)]" />
        <input
          type="text"
          placeholder="Buscar obras, capítulos..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => query.trim() && setShowDropdown(true)}
          className="w-full bg-[oklch(0.12_0_0)] border border-border rounded-lg pl-10 pr-4 py-2 text-sm text-foreground placeholder:text-[oklch(0.55_0_0)] focus:outline-none focus:border-primary/50"
        />
      </div>

      {showDropdown && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-[oklch(0.12_0_0)] border border-border rounded-lg overflow-hidden shadow-xl z-50 max-h-80 overflow-y-auto">
          {loading ? (
            <div className="px-4 py-8 text-center">
              <p className="text-[oklch(0.55_0_0)] text-sm">Buscando...</p>
            </div>
          ) : results.length === 0 ? (
            <div className="px-4 py-8 text-center">
              <p className="text-[oklch(0.55_0_0)] text-sm">Nenhuma obra encontrada</p>
            </div>
          ) : (
            results.map((obra: any) => (
              <Link
                key={obra.id}
                href={`/obras/${obra.slug}`}
                onClick={handleSelect}
                className="flex items-center gap-3 px-4 py-3 hover:bg-[oklch(0.16_0_0)] transition-colors"
              >
                <div className="w-10 h-14 bg-[oklch(0.16_0_0)] rounded shrink-0 overflow-hidden">
                  {obra.capa_url ? (
                    <img src={obra.capa_url} alt={obra.titulo} className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <span className="text-xs font-bold text-[oklch(0.35_0_0)]">
                        {obra.titulo?.charAt(0).toUpperCase()}
                      </span>
                    </div>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-foreground text-sm font-medium truncate">{obra.titulo}</p>
                  <p className="text-[oklch(0.55_0_0)] text-xs truncate">{obra.autor}</p>
                </div>
                <span className="text-[oklch(0.55_0_0)] text-xs shrink-0">
                  {obra.capitulos?.length || 0} caps
                </span>
              </Link>
            ))
          )}
        </div>
      )}
    </div>
  )
}
