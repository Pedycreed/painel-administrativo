"use client"

import { useState, useCallback } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Eye, GripVertical, Save, Loader2 } from "lucide-react"
import { apiGet, apiPost } from "@/lib/api"
import {
  DndContext,
  closestCenter,
  PointerSensor,
  TouchSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from "@dnd-kit/core"
import {
  arrayMove,
  SortableContext,
  useSortable,
  rectSortingStrategy,
} from "@dnd-kit/sortable"
import { CSS } from "@dnd-kit/utilities"

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

function SortablePage({ pagina, index }: { pagina: Pagina; index: number }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: pagina.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    zIndex: isDragging ? 50 : undefined,
    opacity: isDragging ? 0.7 : 1,
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`relative group ${isDragging ? "ring-2 ring-primary rounded-lg" : ""}`}
    >
      <div className="aspect-[2/3] bg-[oklch(0.16_0_0)] rounded-lg overflow-hidden border border-border">
        <img
          src={pagina.thumbnail_url || pagina.imagem_url}
          alt={`Página ${index + 1}`}
          className="w-full h-full object-cover"
          loading="lazy"
        />
      </div>
      <div className="absolute top-1 right-1 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity">
        <button
          {...attributes}
          {...listeners}
          className="bg-black/70 text-white p-2 sm:p-1.5 rounded cursor-grab active:cursor-grabbing touch-none"
          title="Arrastar para reordenar"
        >
          <GripVertical className="w-4 h-4 sm:w-3.5 sm:h-3.5" />
        </button>
      </div>
      <div className="absolute bottom-2 left-2 bg-black/70 text-white text-xs px-2 py-1 rounded">
        #{index + 1}
      </div>
    </div>
  )
}

export default function PreviewCapituloDialog({ capituloId, obraSlug, numero }: PreviewCapituloDialogProps) {
  const [open, setOpen] = useState(false)
  const [paginas, setPaginas] = useState<Pagina[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [saving, setSaving] = useState(false)
  const [dirty, setDirty] = useState(false)

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(TouchSensor, { activationConstraint: { delay: 200, tolerance: 5 } }),
  )

  async function loadPaginas() {
    if (paginas.length > 0) return
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

  const handleDragEnd = useCallback((event: DragEndEvent) => {
    const { active, over } = event
    if (!over || active.id === over.id) return

    setPaginas((prev) => {
      const oldIndex = prev.findIndex((p) => p.id === active.id)
      const newIndex = prev.findIndex((p) => p.id === over.id)
      if (oldIndex === -1 || newIndex === -1) return prev
      setDirty(true)
      return arrayMove(prev, oldIndex, newIndex)
    })
  }, [])

  async function handleSave() {
    setSaving(true)
    try {
      await apiPost("/paginas/reorder/", {
        pages: paginas.map((p, i) => ({ id: p.id, ordem: i + 1 })),
      })
      setDirty(false)
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro ao salvar ordem")
    } finally {
      setSaving(false)
    }
  }

  function handleOpenChange(o: boolean) {
    setOpen(o)
    if (o) loadPaginas()
    if (!o && dirty) {
      setPaginas([])
      setDirty(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogTrigger>
        <Button variant="ghost" size="sm" className="text-[oklch(0.55_0_0)] hover:text-foreground">
          <Eye className="w-4 h-4" />
        </Button>
      </DialogTrigger>
      <DialogContent className="bg-card border-border text-foreground max-w-[95vw] sm:max-w-4xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center justify-between pr-8">
            <DialogTitle className="text-foreground">
              Preview: {obraSlug} - Capítulo {numero}
            </DialogTitle>
            {dirty && (
              <Button
                size="sm"
                onClick={handleSave}
                disabled={saving}
                className="bg-primary hover:bg-primary/80 text-primary-foreground"
              >
                {saving ? (
                  <Loader2 className="w-4 h-4 mr-1.5 animate-spin" />
                ) : (
                  <Save className="w-4 h-4 mr-1.5" />
                )}
                {saving ? "Salvando..." : "Salvar ordem"}
              </Button>
            )}
          </div>
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
          <>
            <p className="text-[oklch(0.55_0_0)] text-xs mb-2">
              Toque e segure o ícone ⋮⋮ para arrastar e reordenar as páginas.
            </p>
            <DndContext
              sensors={sensors}
              collisionDetection={closestCenter}
              onDragEnd={handleDragEnd}
            >
              <SortableContext items={paginas.map((p) => p.id)} strategy={rectSortingStrategy}>
                <div className="grid grid-cols-3 sm:grid-cols-4 gap-3 py-2">
                  {paginas.map((pagina, index) => (
                    <SortablePage key={pagina.id} pagina={pagina} index={index} />
                  ))}
                </div>
              </SortableContext>
            </DndContext>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
