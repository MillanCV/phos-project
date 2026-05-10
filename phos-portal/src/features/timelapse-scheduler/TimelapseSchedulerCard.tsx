import { useState } from 'react'
import { apiClient } from '../../shared/api-client'

type TimelapsePlan = {
  id: string
  interval_seconds: number
  window_start_hour: number
  window_end_hour: number
  active: boolean
  last_capture_at: string | null
}

export function TimelapseSchedulerCard() {
  const [intervalSeconds, setIntervalSeconds] = useState(60)
  const [windowStartHour, setWindowStartHour] = useState(6)
  const [windowEndHour, setWindowEndHour] = useState(18)
  const [plan, setPlan] = useState<TimelapsePlan | null>(null)
  const [error, setError] = useState('')

  const createPlan = async () => {
    setError('')
    try {
      const result = await apiClient.post<TimelapsePlan>('/timelapse/plans', {
        interval_seconds: intervalSeconds,
        window_start_hour: windowStartHour,
        window_end_hour: windowEndHour,
      })
      setPlan(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error creando plan')
    }
  }

  const startPlan = async () => {
    if (!plan) return
    setError('')
    try {
      const result = await apiClient.post<TimelapsePlan>(`/timelapse/plans/${plan.id}/start`)
      setPlan(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error iniciando plan')
    }
  }

  const stopPlan = async () => {
    if (!plan) return
    setError('')
    try {
      const result = await apiClient.post<TimelapsePlan>(`/timelapse/plans/${plan.id}/stop`)
      setPlan(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error deteniendo plan')
    }
  }

  return (
    <section className="card">
      <header className="card-header">
        <h2>Timelapse</h2>
      </header>
      <div className="content-grid">
        <label>
          Intervalo (s)
          <input
            type="number"
            min={10}
            value={intervalSeconds}
            onChange={(event) => setIntervalSeconds(Number(event.target.value))}
          />
        </label>
        <label>
          Inicio ventana (0-23)
          <input
            type="number"
            min={0}
            max={23}
            value={windowStartHour}
            onChange={(event) => setWindowStartHour(Number(event.target.value))}
          />
        </label>
        <label>
          Fin ventana (0-23)
          <input
            type="number"
            min={0}
            max={23}
            value={windowEndHour}
            onChange={(event) => setWindowEndHour(Number(event.target.value))}
          />
        </label>
      </div>
      <div className="row">
        <button type="button" onClick={() => void createPlan()}>
          Crear plan
        </button>
        <button type="button" disabled={!plan} onClick={() => void startPlan()}>
          Iniciar
        </button>
        <button type="button" disabled={!plan} onClick={() => void stopPlan()}>
          Detener
        </button>
      </div>
      {error && <p className="error">{error}</p>}
      {plan && (
        <div className="content-grid">
          <p>
            <strong>ID:</strong> {plan.id}
          </p>
          <p>
            <strong>Estado:</strong> {plan.active ? 'activo' : 'inactivo'}
          </p>
          <p>
            <strong>Ultima captura:</strong>{' '}
            {plan.last_capture_at ? new Date(plan.last_capture_at).toLocaleString() : 'sin datos'}
          </p>
        </div>
      )}
    </section>
  )
}
