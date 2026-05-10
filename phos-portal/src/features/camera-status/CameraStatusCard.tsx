import { useEffect, useState } from 'react'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/Card'
import { Skeleton } from '../../components/ui/Skeleton'
import { Toast } from '../../components/ui/Toast'
import { apiClient } from '../../shared/api-client'

type CameraStatus = {
  connection: 'connected' | 'disconnected' | 'error'
  model: string | null
  battery_percent: number | null
  last_error: string | null
  checked_at: string
}

export function CameraStatusCard() {
  const [status, setStatus] = useState<CameraStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchStatus = async () => {
    try {
      const data = await apiClient.get<CameraStatus>('/camera/status')
      setStatus(data)
      setError('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al cargar estado de camara')
    } finally {
      setLoading(false)
    }
  }

  const refresh = async () => {
    setLoading(true)
    void fetchStatus()
  }

  useEffect(() => {
    const timer = setTimeout(() => {
      void fetchStatus()
    }, 0)
    return () => clearTimeout(timer)
  }, [])

  const connectionVariant =
    status?.connection === 'connected'
      ? 'success'
      : status?.connection === 'error'
        ? 'danger'
        : 'warning'

  return (
    <Card>
      <CardHeader>
        <div className="space-y-1">
          <CardTitle>Estado de camara</CardTitle>
          <CardDescription>Comprobacion de enlace CHDKPTP con la Canon IXUS 105.</CardDescription>
        </div>
        <Button variant="secondary" onClick={() => void refresh()}>
          Refrescar
        </Button>
      </CardHeader>
      <CardContent>
        {loading && (
          <div className="grid gap-2">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-2/3" />
            <Skeleton className="h-4 w-1/2" />
          </div>
        )}
        {!loading && error && <Toast variant="danger">{error}</Toast>}
        {!loading && status && (
          <div className="grid gap-2 text-sm text-mutedForeground">
            <div className="flex items-center justify-between gap-2">
              <span className="text-foreground">Conexion</span>
              <Badge variant={connectionVariant}>{status.connection}</Badge>
            </div>
            <div className="flex items-center justify-between gap-2">
              <span className="text-foreground">Modelo</span>
              <span>{status.model ?? 'desconocido'}</span>
            </div>
            <div className="flex items-center justify-between gap-2">
              <span className="text-foreground">Bateria</span>
              <span>{status.battery_percent !== null ? `${status.battery_percent}%` : 'no disponible'}</span>
            </div>
            <div className="flex items-center justify-between gap-2">
              <span className="text-foreground">Ultima comprobacion</span>
              <span>{new Date(status.checked_at).toLocaleString()}</span>
            </div>
            {status.last_error && (
              <p className="rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-warning">
                {status.last_error}
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
