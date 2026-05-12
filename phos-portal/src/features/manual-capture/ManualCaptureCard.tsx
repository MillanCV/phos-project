import { useEffect, useMemo, useState } from 'react'
import { Camera, Download } from 'lucide-react'
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
}

export function ManualCaptureCard() {
  const [latest, setLatest] = useState<CaptureRecord | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [imageNonce, setImageNonce] = useState(0)

  const imageUrl = useMemo(() => {
    if (!latest) return null
    const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? '/api').replace(/\/$/, '')
    return `${apiBaseUrl}/capture/latest/file?ts=${encodeURIComponent(latest.captured_at)}&n=${imageNonce}`
  }, [latest, imageNonce])

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
        </div>
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
      </CardContent>
    </Card>
  )
}
