import { useEffect, useState } from 'react'
import './App.css'

type ApiStatus = {
  message: string
  hostname: string
  timestamp_utc: string
}

function App() {
  const [status, setStatus] = useState<ApiStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadStatus = async () => {
    setLoading(true)
    setError('')

    try {
      const response = await fetch('/api/status')
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data = (await response.json()) as ApiStatus
      setStatus(data)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Error desconocido'
      setError(`No se pudo contactar el backend: ${message}`)
      setStatus(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadStatus()
  }, [])

  return (
    <main className="app">
      <h1>Phos Portal</h1>
      <p>Frontend minimo conectado al backend del observatorio.</p>

      <section className="card">
        {loading && <p>Cargando estado del backend...</p>}
        {!loading && error && <p className="error">{error}</p>}
        {!loading && status && (
          <>
            <p>
              <strong>Mensaje:</strong> {status.message}
            </p>
            <p>
              <strong>Host:</strong> {status.hostname}
            </p>
            <p>
              <strong>UTC:</strong> {new Date(status.timestamp_utc).toLocaleString()}
            </p>
          </>
        )}
      </section>

      <button type="button" onClick={() => void loadStatus()}>
        Actualizar estado
      </button>
    </main>
  )
}

export default App
