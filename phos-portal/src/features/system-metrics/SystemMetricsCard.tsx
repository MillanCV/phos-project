import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { Activity, HardDrive, Thermometer, Timer } from 'lucide-react'
import { Button } from '../../components/ui/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/Card'
import { Skeleton } from '../../components/ui/Skeleton'
import { Toast } from '../../components/ui/Toast'
import { apiClient } from '../../shared/api-client'

type SystemMetrics = {
  disk_free_bytes: number
  disk_total_bytes: number
  cpu_load_1m: number
  temperature_c: number | null
  uptime_seconds: number
  collected_at: string
}

function toGb(bytes: number) {
  return (bytes / 1024 / 1024 / 1024).toFixed(2)
}

export function SystemMetricsCard() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  const fetchMetrics = async () => {
    try {
      const result = await apiClient.get<SystemMetrics>('/system/metrics')
      setMetrics(result)
      setError('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error cargando metricas')
    } finally {
      setLoading(false)
    }
  }

  const refresh = async () => {
    setLoading(true)
    void fetchMetrics()
  }

  useEffect(() => {
    const initialTimer = setTimeout(() => {
      void fetchMetrics()
    }, 0)
    const timer = setInterval(() => {
      void fetchMetrics()
    }, 15000)
    return () => {
      clearTimeout(initialTimer)
      clearInterval(timer)
    }
  }, [])

  return (
    <Card>
      <CardHeader>
        <div className="space-y-1">
          <CardTitle>Salud del sistema</CardTitle>
          <CardDescription>Metricas operativas de la Raspberry para observacion remota.</CardDescription>
        </div>
        <Button variant="secondary" onClick={() => void refresh()}>
          Refrescar
        </Button>
      </CardHeader>
      <CardContent>
        {loading && (
          <div className="grid gap-2 sm:grid-cols-2">
            <Skeleton className="h-20" />
            <Skeleton className="h-20" />
            <Skeleton className="h-20" />
            <Skeleton className="h-20" />
          </div>
        )}
        {error && <Toast variant="danger">{error}</Toast>}
        {!loading && metrics && (
          <div className="grid gap-2 sm:grid-cols-2">
            <MetricTile
              icon={<HardDrive className="h-4 w-4 text-primary" />}
              label="Disco libre"
              value={`${toGb(metrics.disk_free_bytes)} GB`}
              helper={`de ${toGb(metrics.disk_total_bytes)} GB`}
            />
            <MetricTile
              icon={<Activity className="h-4 w-4 text-primary" />}
              label="CPU load 1m"
              value={metrics.cpu_load_1m.toFixed(2)}
              helper="carga promedio"
            />
            <MetricTile
              icon={<Thermometer className="h-4 w-4 text-primary" />}
              label="Temperatura"
              value={metrics.temperature_c !== null ? `${metrics.temperature_c} C` : 'N/D'}
              helper="sensor termico"
            />
            <MetricTile
              icon={<Timer className="h-4 w-4 text-primary" />}
              label="Uptime"
              value={`${(metrics.uptime_seconds / 3600).toFixed(1)} h`}
              helper="desde ultimo reinicio"
            />
          </div>
        )}
      </CardContent>
    </Card>
  )
}

type MetricTileProps = {
  icon: ReactNode
  label: string
  value: string
  helper: string
}

function MetricTile({ icon, label, value, helper }: MetricTileProps) {
  return (
    <div className="rounded-md border border-border bg-background/70 p-3">
      <div className="mb-2 flex items-center justify-between text-xs uppercase tracking-wide text-mutedForeground">
        <span>{label}</span>
        {icon}
      </div>
      <p className="text-lg font-semibold text-foreground">{value}</p>
      <p className="text-xs text-mutedForeground">{helper}</p>
    </div>
  )
}
