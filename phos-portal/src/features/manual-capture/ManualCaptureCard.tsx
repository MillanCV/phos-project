import { useEffect, useMemo, useState } from 'react'
import { Camera, Download, X } from 'lucide-react'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/Card'
import { Toast } from '../../components/ui/Toast'
import { apiClient } from '../../shared/api-client'

type CaptureRecord = {
  id: string
  file_path: string
  captured_at: string
  source: string
  preview_url: string
  download_url: string
}

const API_PREFIX = '/api'

function resolveCaptureAssetUrl(rawUrl: string): string {
  if (rawUrl.startsWith('http')) return rawUrl
  const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? API_PREFIX).replace(/\/$/, '')
  const normalizedPath = rawUrl.startsWith('/') ? rawUrl : `/${rawUrl}`

  if (apiBaseUrl.endsWith(API_PREFIX) && normalizedPath.startsWith(`${API_PREFIX}/`)) {
    return `${apiBaseUrl}${normalizedPath.slice(API_PREFIX.length)}`
  }
  return `${apiBaseUrl}${normalizedPath}`
}

export function ManualCaptureCard() {
  const [latest, setLatest] = useState<CaptureRecord | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [imageNonce, setImageNonce] = useState(0)

  const imageUrl = useMemo(() => {
    if (!latest) return null
    const base = resolveCaptureAssetUrl(latest.preview_url)
    return `${base}?ts=${encodeURIComponent(latest.captured_at)}&n=${imageNonce}`
  }, [latest, imageNonce])
  const downloadUrl = useMemo(() => {
    if (!latest) return null
    return resolveCaptureAssetUrl(latest.download_url)
  }, [latest])
  const [isPreviewOpen, setPreviewOpen] = useState(false)

  const capture = async () => {
    setLoading(true)
    setError('')
    try {
      const result = await apiClient.post<CaptureRecord>('/capture/photo')
      setLatest(result)
      setImageNonce((value) => value + 1)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al disparar')
    } finally {
      setLoading(false)
    }
  }

  const loadLatest = async () => {
    setError('')
    try {
      const result = await apiClient.get<CaptureRecord | null>('/capture/latest')
      setLatest(result)
      setImageNonce((value) => value + 1)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al consultar ultima captura')
    }
  }

  useEffect(() => {
    const timer = setTimeout(() => {
      void loadLatest()
    }, 0)
    return () => clearTimeout(timer)
  }, [])

  return (
    <Card>
      <CardHeader>
        <div className="space-y-1">
          <CardTitle>Disparo manual</CardTitle>
          <CardDescription>Captura bajo demanda para validar encuadre y foco.</CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-2">
          <Button disabled={loading} onClick={() => void capture()}>
            <Camera className="h-4 w-4" />
            {loading ? 'Disparando...' : 'Disparar'}
          </Button>
          <Button variant="secondary" onClick={() => void loadLatest()}>
            <Download className="h-4 w-4" />
            Ver ultima captura
          </Button>
          <Button variant="ghost" disabled={!imageUrl} onClick={() => setPreviewOpen(true)}>
            Ver grande
          </Button>
          {downloadUrl ? (
            <a
              href={downloadUrl}
              className="inline-flex items-center justify-center gap-2 rounded-md border border-border bg-transparent px-3 py-2 text-sm font-medium text-mutedForeground transition-all duration-150 hover:bg-muted/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-background focus-visible:ring-primary/40"
              target="_blank"
              rel="noopener noreferrer"
              download
            >
              Descargar
            </a>
          ) : (
            <Button variant="ghost" disabled>
              Descargar
            </Button>
          )}
        </div>
        {loading && <p className="text-xs text-mutedForeground">Capturando foto, puede tardar unos segundos...</p>}
        {error && <Toast variant="danger">{error}</Toast>}
        {latest ? (
          <div className="grid gap-2 text-sm text-mutedForeground">
            {imageUrl && (
              <div className="overflow-hidden rounded-md border border-border/60 bg-background/70">
                <img src={imageUrl} alt="Ultima captura" className="max-h-80 w-full object-contain" loading="lazy" />
              </div>
            )}
            <div className="flex min-w-0 items-start justify-between gap-2">
              <span className="text-foreground">Archivo</span>
              <span className="min-w-0 max-w-[65%] break-all text-right text-xs">{latest.file_path}</span>
            </div>
            <div className="flex min-w-0 items-center justify-between gap-2">
              <span className="text-foreground">Fecha</span>
              <span className="min-w-0 text-right">{new Date(latest.captured_at).toLocaleString()}</span>
            </div>
            <div className="flex min-w-0 items-center justify-between gap-2">
              <span className="text-foreground">Fuente</span>
              <Badge variant="default">{latest.source}</Badge>
            </div>
          </div>
        ) : (
          <p className="text-sm text-mutedForeground">Sin capturas registradas todavia.</p>
        )}
        {isPreviewOpen && imageUrl && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-6"
            role="button"
            tabIndex={0}
            onClick={() => setPreviewOpen(false)}
            onKeyDown={(event) => {
              if (event.key === 'Escape') {
                setPreviewOpen(false)
              }
            }}
          >
            <div className="relative max-h-full max-w-full" onClick={(event) => event.stopPropagation()}>
              <button
                type="button"
                className="absolute right-2 top-2 inline-flex items-center justify-center rounded-md border border-border bg-black/70 p-1 text-white hover:bg-black/90"
                onClick={() => setPreviewOpen(false)}
                aria-label="Cerrar vista ampliada"
              >
                <X className="h-4 w-4" />
              </button>
              <img
                src={imageUrl}
                alt="Vista ampliada de captura"
                className="max-h-full max-w-full rounded-md border border-border/60 bg-black object-contain"
              />
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
