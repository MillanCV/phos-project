import { useEffect, useState } from 'react'
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

  const refresh = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await apiClient.get<CameraStatus>('/camera/status')
      setStatus(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al cargar estado de camara')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void refresh()
  }, [])

  return (
    <section className="card">
      <header className="card-header">
        <h2>Camara</h2>
        <button type="button" onClick={() => void refresh()}>
          Refrescar
        </button>
      </header>
      {loading && <p>Cargando estado...</p>}
      {!loading && error && <p className="error">{error}</p>}
      {!loading && status && (
        <div className="content-grid">
          <p>
            <strong>Conexion:</strong> {status.connection}
          </p>
          <p>
            <strong>Modelo:</strong> {status.model ?? 'desconocido'}
          </p>
          <p>
            <strong>Bateria:</strong>{' '}
            {status.battery_percent !== null ? `${status.battery_percent}%` : 'no disponible'}
          </p>
          <p>
            <strong>Ultima comprobacion:</strong> {new Date(status.checked_at).toLocaleString()}
          </p>
          {status.last_error && (
            <p>
              <strong>Error:</strong> {status.last_error}
            </p>
          )}
        </div>
      )}
    </section>
  )
}
