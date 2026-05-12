import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { Clock3, HardDrive, MoonStar, Radar, Wifi } from 'lucide-react'
import { Badge } from '../components/ui/Badge'
import { apiClient } from '../shared/api-client'

type AppShellProps = {
  children: ReactNode
}

export function AppShell({ children }: AppShellProps) {
  const [cameraStatus, setCameraStatus] = useState<CameraStatus | null>(null)
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null)

  useEffect(() => {
    const fetchStripStatus = async () => {
      try {
        const [camera, system] = await Promise.all([
          apiClient.get<CameraStatus>('/camera/status'),
          apiClient.get<SystemMetrics>('/system/metrics'),
        ])
        setCameraStatus(camera)
        setMetrics(system)
      } catch {
        // Keep last known values; individual cards already expose detailed errors.
      }
    }

    void fetchStripStatus()
    const timer = setInterval(() => {
      void fetchStripStatus()
    }, 15000)
    return () => clearInterval(timer)
  }, [])

  const cameraOnline = cameraStatus?.connection === 'connected'
  const runtimeAvailable = cameraStatus?.chdkptp_available === true
  const cameraBadgeVariant = cameraOnline ? 'success' : 'danger'
  const runtimeBadgeVariant = runtimeAvailable ? 'success' : 'warning'
  const modeBadgeVariant = cameraStatus?.mode === 'record' ? 'default' : 'warning'

  const linkValue = !cameraStatus
    ? 'Checking'
    : !cameraStatus.chdkptp_available
      ? 'No runtime'
      : cameraStatus.connection === 'connected'
        ? 'Connected'
        : cameraStatus.connection === 'disconnected'
          ? 'No camera'
          : 'Error'

  const pollCycle = cameraStatus?.checked_at ? `${secondsSince(cameraStatus.checked_at)}s` : 'n/a'

  const storageStatus = !metrics
    ? 'Unknown'
    : getStorageHealth(metrics.disk_free_bytes / Math.max(metrics.disk_total_bytes, 1))

  const storageVariant = storageStatus === 'Nominal' ? 'success' : storageStatus === 'Low' ? 'warning' : 'danger'

  return (
    <main className="min-h-screen bg-background text-foreground">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-4 px-4 py-5 md:px-6 md:py-7">
        <header className="rounded-lg border border-border bg-card/80 p-5 shadow-panel">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="rounded-md border border-border bg-background p-2 text-warning">
                <Radar className="h-5 w-5" />
              </div>
              <div>
                <h1 className="text-xl font-semibold tracking-tight md:text-2xl">Phos Control Room</h1>
                <p className="text-sm text-mutedForeground">
                  Canon IXUS 105 · CHDKPTP · Operacion remota
                </p>
              </div>
            </div>
            <div className="inline-flex items-center gap-2 rounded-md border border-border bg-background/60 px-3 py-1 text-xs text-mutedForeground">
              <MoonStar className="h-3.5 w-3.5" />
              control room classic
            </div>
          </div>
        </header>

        <section className="control-strip">
          <div className="control-strip__left">
            <Badge variant={cameraBadgeVariant}>{cameraOnline ? 'camera online' : 'camera offline'}</Badge>
            <Badge variant={runtimeBadgeVariant}>{runtimeAvailable ? 'chdkptp ready' : 'chdkptp unavailable'}</Badge>
            <Badge variant={modeBadgeVariant}>{cameraStatus?.mode ?? 'unknown mode'}</Badge>
          </div>
          <div className="control-strip__right">
            <StatusPill icon={<Wifi className="h-3.5 w-3.5" />} label="Link" value={linkValue} />
            <StatusPill icon={<Clock3 className="h-3.5 w-3.5" />} label="Cycle" value={pollCycle} />
            <StatusPill icon={<HardDrive className="h-3.5 w-3.5" />} label="Storage" value={storageStatus} variant={storageVariant} />
          </div>
        </section>

        <section className="grid gap-4 md:grid-cols-2">{children}</section>
      </div>
    </main>
  )
}

type StatusPillProps = {
  icon: ReactNode
  label: string
  value: string
  variant?: 'default' | 'success' | 'warning' | 'danger'
}

function StatusPill({ icon, label, value, variant = 'default' }: StatusPillProps) {
  return (
    <div className="status-pill">
      {icon}
      <span className="status-pill__label">{label}</span>
      <span className={`status-pill__value ${statusValueClassname(variant)}`}>{value}</span>
    </div>
  )
}

type CameraStatus = {
  connection: 'connected' | 'disconnected' | 'error'
  mode: 'record' | 'playback' | 'unknown'
  chdkptp_available: boolean
  checked_at: string
}

type SystemMetrics = {
  disk_free_bytes: number
  disk_total_bytes: number
}

function secondsSince(isoDate: string) {
  const parsed = Date.parse(isoDate)
  if (Number.isNaN(parsed)) return 0
  return Math.max(0, Math.round((Date.now() - parsed) / 1000))
}

function getStorageHealth(freeRatio: number): 'Nominal' | 'Low' | 'Critical' {
  if (freeRatio <= 0.1) return 'Critical'
  if (freeRatio <= 0.2) return 'Low'
  return 'Nominal'
}

function statusValueClassname(variant: 'default' | 'success' | 'warning' | 'danger') {
  if (variant === 'success') return 'text-success'
  if (variant === 'warning') return 'text-warning'
  if (variant === 'danger') return 'text-danger'
  return ''
}
