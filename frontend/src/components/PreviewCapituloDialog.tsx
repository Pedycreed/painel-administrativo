"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Eye } from "lucide-react"
import { apiGet } from "@/lib/api"

interface Pagina {
  id: number
  imagem_url: string
  thumbnail_url: string
  ordem: number
}

interface PreviewCapituloDialogProps {
  capituloId: number
  obraSlug: string
  numero: string
}

export default function PreviewCapituloDialog({ capituloId, obraSlug, numero }: PreviewCapituloDialogProps) {
  const [open, setOpen] = useState(false)
  const [paginas, setPaginas] = useState<Pagina[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  async function loadPaginas() {
    if (paginas.length > 0) return // já carregou

    setLoading(true)
    setError("")
    try {
      const data = await apiGet<{ paginas: Pagina[] }>(`/capitulos/${capituloId}/`)
      setPaginas(data.paginas || [])
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao carregar páginas")
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(o) => {
      setOpen(o)
      if (o) loadPaginas()
    }}>
      <DialogTrigger>
        <Button variant="ghost" size="sm" className="text-[oklch(0.55_0_0)] hover:text-foreground">
          <Eye className="w-4 h-4" />
        </Button>
      </DialogTrigger>
      <DialogContent className="bg-card border-border text-foreground max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-foreground">
            Preview: {obraSlug} - Capítulo {numero}
          </DialogTitle>
        </DialogHeader>

        {loading && (
          <div className="py-12 text-center">
            <p className="text-[oklch(0.55_0_0)]">Carregando...</p>
          </div>
        )}

        {error && (
          <div className="py-12 text-center">
            <p className="text-red-400">{error}</p>
          </div>
        )}

        {!loading && !error && paginas.length === 0 && (
          <div className="py-12 text-center">
            <p className="text-[oklch(0.55_0_0)]">Nenhuma página cadastrada ainda.</p>
          </div>
        )}

        {!loading && !error && paginas.length > 0 && (
          <div className="grid grid-cols-4 gap-3 py-4">
            {paginas.map((pagina) => (
              <div key={pagina.id} className="relative group">
                <div className="aspect-[2/3] bg-[oklch(0.16_0_0)] rounded-lg overflow-hidden border border-border">
                  <img
                    src={pagina.thumbnail_url || pagina.imagem_url}
                    alt={`Página ${pagina.ordem + 1}`}
                    className="w-full h-full object-cover"
                    loading="lazy"
                  />
                </div>
                <div className="absolute bottom-2 left-2 bg-black/70 text-white text-xs px-2 py-1 rounded">
                  #{pagina.ordem + 1}
                </div>
              </div>
            ))}
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
