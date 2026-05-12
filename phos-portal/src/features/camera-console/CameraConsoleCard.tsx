import { useEffect, useState } from 'react'
import { Play } from 'lucide-react'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/Card'
import { Skeleton } from '../../components/ui/Skeleton'
import { Toast } from '../../components/ui/Toast'
import { apiClient } from '../../shared/api-client'

type CameraPreset = {
  name: string
  description: string
  timeout_seconds: number
}

type ScriptRunResult = {
  run_id: string
  profile_name: string
  state: 'running' | 'completed' | 'failed' | 'stopped'
  started_at: string
  finished_at: string | null
  stdout: string
  stderr: string
  exit_code: number | null
  artifacts: string[]
}

export function CameraConsoleCard() {
  const [presets, setPresets] = useState<CameraPreset[]>([])
  const [loading, setLoading] = useState(true)
  const [runningPreset, setRunningPreset] = useState<string | null>(null)
  const [lastRun, setLastRun] = useState<ScriptRunResult | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const load = async () => {
      try {
        const result = await apiClient.get<CameraPreset[]>('/camera/presets')
        setPresets(result)
        setError('')
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error cargando presets de camara')
      } finally {
        setLoading(false)
      }
    }
    void load()
  }, [])

  const runPreset = async (presetName: string) => {
    setRunningPreset(presetName)
    setError('')
    try {
      const result = await apiClient.post<ScriptRunResult>(`/camera/presets/${presetName}/run`)
      setLastRun(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error ejecutando preset')
    } finally {
      setRunningPreset(null)
    }
  }

  const runBadgeVariant = lastRun?.state === 'completed' ? 'success' : lastRun?.state === 'failed' ? 'danger' : 'warning'

  return (
    <Card>
      <CardHeader>
        <div className="space-y-1">
          <CardTitle>Camera Console</CardTitle>
          <CardDescription>Ejecuta presets seguros para validar y operar la camara.</CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        {loading && (
          <div className="grid gap-2">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-2/3" />
          </div>
        )}
        {!loading && presets.length > 0 && (
          <div className="grid gap-2">
            {presets.map((preset) => (
              <div key={preset.name} className="rounded-md border border-border/60 p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <p className="text-sm font-medium text-foreground">{preset.name}</p>
                    <p className="text-xs text-mutedForeground">{preset.description}</p>
                  </div>
                  <Button
                    className="px-2 py-1 text-xs"
                    disabled={runningPreset !== null}
                    onClick={() => void runPreset(preset.name)}
                  >
                    <Play className="h-4 w-4" />
                    {runningPreset === preset.name ? 'Ejecutando...' : 'Ejecutar'}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
        {!loading && presets.length === 0 && (
          <p className="text-sm text-mutedForeground">No hay presets configurados.</p>
        )}
        {error && <Toast variant="danger">{error}</Toast>}
        {lastRun && (
          <div className="mt-3 grid gap-2 rounded-md border border-border/60 p-3 text-sm text-mutedForeground">
            <div className="flex items-center justify-between gap-2">
              <span className="text-foreground">Ultima ejecucion</span>
              <Badge variant={runBadgeVariant}>{lastRun.state}</Badge>
            </div>
            <div className="flex items-center justify-between gap-2">
              <span className="text-foreground">Preset</span>
              <span>{lastRun.profile_name}</span>
            </div>
            <div className="flex items-center justify-between gap-2">
              <span className="text-foreground">Inicio</span>
              <span>{new Date(lastRun.started_at).toLocaleString()}</span>
            </div>
            {lastRun.finished_at && (
              <div className="flex items-center justify-between gap-2">
                <span className="text-foreground">Fin</span>
                <span>{new Date(lastRun.finished_at).toLocaleString()}</span>
              </div>
            )}
            {lastRun.stderr && (
              <p className="rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-warning">{lastRun.stderr}</p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
