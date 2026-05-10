import { useState } from 'react'
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

  const capture = async () => {
    setLoading(true)
    setError('')
    try {
      const result = await apiClient.post<CaptureRecord>('/capture/photo')
      setLatest(result)
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
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al consultar ultima captura')
    }
  }

  return (
    <section className="card">
      <header className="card-header">
        <h2>Disparo Manual</h2>
      </header>
      <div className="row">
        <button type="button" disabled={loading} onClick={() => void capture()}>
          {loading ? 'Disparando...' : 'Disparar'}
        </button>
        <button type="button" onClick={() => void loadLatest()}>
          Ver ultima captura
        </button>
      </div>
      {error && <p className="error">{error}</p>}
      {latest && (
        <div className="content-grid">
          <p>
            <strong>Archivo:</strong> {latest.file_path}
          </p>
          <p>
            <strong>Fecha:</strong> {new Date(latest.captured_at).toLocaleString()}
          </p>
          <p>
            <strong>Fuente:</strong> {latest.source}
          </p>
        </div>
      )}
    </section>
  )
}
