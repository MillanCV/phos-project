import { useState } from 'react'
import { Clock3, Play, Square } from 'lucide-react'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/Card'
import { Input } from '../../components/ui/Input'
import { Separator } from '../../components/ui/Separator'
import { Toast } from '../../components/ui/Toast'
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
    <Card>
      <CardHeader>
        <div className="space-y-1">
          <CardTitle>Timelapse programado</CardTitle>
          <CardDescription>Intervalo fijo con ventana horaria de operacion automatica.</CardDescription>
        </div>
        {plan && <Badge variant={plan.active ? 'success' : 'warning'}>{plan.active ? 'activo' : 'inactivo'}</Badge>}
      </CardHeader>
      <CardContent>
        <div className="grid gap-3 sm:grid-cols-3">
          <label className="grid gap-1 text-sm text-mutedForeground">
            Intervalo (s)
            <Input
              type="number"
              min={10}
              value={intervalSeconds}
              onChange={(event) => setIntervalSeconds(Number(event.target.value))}
            />
          </label>
          <label className="grid gap-1 text-sm text-mutedForeground">
            Inicio ventana
            <Input
              type="number"
              min={0}
              max={23}
              value={windowStartHour}
              onChange={(event) => setWindowStartHour(Number(event.target.value))}
            />
          </label>
          <label className="grid gap-1 text-sm text-mutedForeground">
            Fin ventana
            <Input
              type="number"
              min={0}
              max={23}
              value={windowEndHour}
              onChange={(event) => setWindowEndHour(Number(event.target.value))}
            />
          </label>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" onClick={() => void createPlan()}>
            <Clock3 className="h-4 w-4" />
            Crear plan
          </Button>
          <Button disabled={!plan} onClick={() => void startPlan()}>
            <Play className="h-4 w-4" />
            Iniciar
          </Button>
          <Button variant="danger" disabled={!plan} onClick={() => void stopPlan()}>
            <Square className="h-4 w-4" />
            Detener
          </Button>
        </div>
        {error && <Toast variant="danger">{error}</Toast>}
        {plan ? (
          <>
            <Separator />
            <div className="grid gap-2 text-sm text-mutedForeground">
              <div className="flex items-center justify-between gap-2">
                <span className="text-foreground">ID del plan</span>
                <span className="truncate text-right">{plan.id}</span>
              </div>
              <div className="flex items-center justify-between gap-2">
                <span className="text-foreground">Ultima captura</span>
                <span>{plan.last_capture_at ? new Date(plan.last_capture_at).toLocaleString() : 'sin datos'}</span>
              </div>
            </div>
          </>
        ) : (
          <p className="text-sm text-mutedForeground">Crea un plan para habilitar el control automatico.</p>
        )}
      </CardContent>
    </Card>
  )
}
