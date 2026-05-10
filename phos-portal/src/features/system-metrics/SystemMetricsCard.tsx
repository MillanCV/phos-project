import { useEffect, useState } from 'react'
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

  const refresh = async () => {
    setError('')
    try {
      const result = await apiClient.get<SystemMetrics>('/system/metrics')
      setMetrics(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error cargando metricas')
    }
  }

  useEffect(() => {
    void refresh()
    const timer = setInterval(() => {
      void refresh()
    }, 15000)
    return () => clearInterval(timer)
  }, [])

  return (
    <section className="card">
      <header className="card-header">
        <h2>Sistema</h2>
        <button type="button" onClick={() => void refresh()}>
          Refrescar
        </button>
      </header>
      {error && <p className="error">{error}</p>}
      {metrics && (
        <div className="content-grid">
          <p>
            <strong>Disco libre:</strong> {toGb(metrics.disk_free_bytes)} GB
          </p>
          <p>
            <strong>Disco total:</strong> {toGb(metrics.disk_total_bytes)} GB
          </p>
          <p>
            <strong>CPU load (1m):</strong> {metrics.cpu_load_1m.toFixed(2)}
          </p>
          <p>
            <strong>Temperatura:</strong>{' '}
            {metrics.temperature_c !== null ? `${metrics.temperature_c} C` : 'no disponible'}
          </p>
          <p>
            <strong>Uptime:</strong> {(metrics.uptime_seconds / 3600).toFixed(1)} horas
          </p>
        </div>
      )}
    </section>
  )
}
