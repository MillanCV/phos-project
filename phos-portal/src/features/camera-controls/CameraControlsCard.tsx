import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Badge } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/Card'
import { Toast } from '../../components/ui/Toast'
import { apiClient } from '../../shared/api-client'

type CameraManualCapabilities = {
  supports_flash_control: boolean
  supports_focus_control: boolean
  supports_zoom_control: boolean
  supports_nd_filter: boolean
}

type CameraZoomPosition = {
  step: number
  focal_length_mm: number
  focal_length_35mm_equiv_mm: number
}

type CameraManualState = {
  power_state: 'active' | 'sleep' | 'deep_sleep' | 'waking' | 'error'
  mode: 'record' | 'playback' | 'unknown'
  shutter_seconds: number | null
  shutter_display: string
  iso: number | null
  aperture_display: string
  nd_enabled: boolean | null
  zoom_step: number | null
  focus_mm: number | null
  flash_mode: number | null
  last_interaction_at: string
  idle_seconds: number
  capabilities: CameraManualCapabilities
  exposure_control: 'auto' | 'manual' | 'unknown'
  metering_shutter_display: string
  metering_iso: number | null
  shutter_auto_active?: boolean
  iso_auto_active?: boolean
  focus_auto_active?: boolean
  zoom_focal_length_mm?: number | null
  zoom_steps_count?: number | null
  zoom_positions?: CameraZoomPosition[]
  focus_control?: 'af' | 'mf' | 'unknown'
}

type CameraOperation = {
  operation_id: string
  operation_type: string
  state: 'pending' | 'running' | 'completed' | 'failed'
  error: string | null
  manual_state: CameraManualState | null
}

const SHUTTER_PRESETS = ['auto', '1/1000', '1/500', '1/250', '1/125', '1/60', '1/30', '1/15', '1/8', '1/4', '1/2', '1"', '2"', '4"']
const ISO_BASE: (number | 'auto')[] = ['auto', 100, 200, 400, 800, 1600, 3200]
const FLASH_PRESETS = [
  { value: 0, label: 'Auto' },
  { value: 1, label: 'On' },
  { value: 2, label: 'Off' },
]

/** Subject distance presets (mm) sent to CHDK set_focus; labels are photographer-friendly. */
const FOCUS_PRESETS: { value: 'auto' | number; label: string }[] = [
  { value: 'auto', label: 'Auto (AF)' },
  { value: 200000, label: '∞ · landscape' },
  { value: 10000, label: '10 m' },
  { value: 5000, label: '5 m' },
  { value: 2000, label: '2 m' },
  { value: 1000, label: '1 m' },
  { value: 500, label: '50 cm' },
  { value: 300, label: '30 cm' },
  { value: 150, label: '15 cm · macro zone' },
]

const APPLY_DEBOUNCE_MS = 400

type CameraControlsCardProps = {
  /** Narrow column: shorter copy, tighter layout, single-column controls. */
  compact?: boolean
}

export function CameraControlsCard({ compact = false }: CameraControlsCardProps) {
  const [state, setState] = useState<CameraManualState | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true)
  /** Blocks passive server→form sync while the user is editing (polling refresh). */
  const formDirtyRef = useRef(false)
  const userTouchedRef = useRef(false)
  const debounceTimerRef = useRef<ReturnType<typeof window.setTimeout> | null>(null)
  const [shutterSpeed, setShutterSpeed] = useState('1/125')
  const [iso, setIso] = useState<number | 'auto'>(100)
  const [ndEnabled, setNdEnabled] = useState(false)
  const [zoomStep, setZoomStep] = useState(0)
  const [focusPreset, setFocusPreset] = useState<number | 'auto'>('auto')
  const [flashMode, setFlashMode] = useState(0)
  const [exposureMode, setExposureMode] = useState<'auto' | 'manual'>('manual')
  const exposureModeRef = useRef(exposureMode)
  exposureModeRef.current = exposureMode

  const markUserEdit = useCallback(() => {
    userTouchedRef.current = true
    formDirtyRef.current = true
  }, [])

  const clearDirty = useCallback(() => {
    formDirtyRef.current = false
  }, [])

  const syncForm = useCallback(
    (next: CameraManualState, force = false) => {
      if (formDirtyRef.current && !force) return
      if (next.exposure_control === 'auto' || next.exposure_control === 'manual') {
        setExposureMode(next.exposure_control === 'auto' ? 'auto' : 'manual')
      }
      if (next.exposure_control === 'auto') {
        setShutterSpeed('auto')
        setIso('auto')
        setFocusPreset('auto')
      } else if (next.shutter_auto_active) {
        setShutterSpeed('auto')
      } else {
        const rawSd = next.shutter_display || '1/125'
        const sd = rawSd === 'auto' || next.shutter_seconds == null ? '1/125' : rawSd
        setShutterSpeed(sd)
      }
      if (next.exposure_control !== 'auto') {
        setIso(next.iso_auto_active ? 'auto' : (next.iso ?? 100))
      }
      setNdEnabled(next.nd_enabled ?? false)
      setZoomStep(next.zoom_step ?? 0)
      if (next.exposure_control !== 'auto') {
        if (next.focus_auto_active) {
          setFocusPreset('auto')
        } else if (next.focus_control === 'mf' && next.focus_mm != null && next.focus_mm >= 0) {
          setFocusPreset(next.focus_mm)
        }
      }
      setFlashMode(next.flash_mode ?? 0)
      if (force) clearDirty()
    },
    [clearDirty],
  )

  const refreshState = useCallback(async () => {
    try {
      const next = await apiClient.get<CameraManualState>('/camera/manual/state')
      setState(next)
      syncForm(next)
      setError('')
      setAutoRefreshEnabled(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not read manual camera state')
      setAutoRefreshEnabled(false)
    }
  }, [syncForm])

  useEffect(() => {
    void refreshState()
  }, [refreshState])

  useEffect(() => {
    if (!autoRefreshEnabled) return
    const timer = setInterval(() => {
      void refreshState()
    }, 15000)
    return () => {
      clearInterval(timer)
    }
  }, [autoRefreshEnabled, refreshState])

  const pollOperation = useCallback(async (operationId: string) => {
    for (let attempt = 0; attempt < 60; attempt += 1) {
      const op = await apiClient.get<CameraOperation>(`/camera/operations/${operationId}`)
      if (op.state === 'pending' || op.state === 'running') {
        await new Promise((resolve) => setTimeout(resolve, 500))
        continue
      }
      if (op.state === 'failed') {
        throw new Error(op.error ?? 'camera operation failed')
      }
      if (op.manual_state) {
        setState(op.manual_state)
        syncForm(op.manual_state, true)
      } else {
        await refreshState()
      }
      return
    }
    throw new Error('camera operation timeout')
  }, [refreshState, syncForm])

  const cancelDebouncedApply = useCallback(() => {
    if (debounceTimerRef.current !== null) {
      window.clearTimeout(debounceTimerRef.current)
      debounceTimerRef.current = null
    }
  }, [])

  const applySettings = useCallback(
    async (mode: 'auto' | 'manual') => {
      if (!userTouchedRef.current || !state) return
      cancelDebouncedApply()
      setBusy(true)
      setError('')
      try {
        await apiClient.post('/camera/power/touch')
        const op = await apiClient.post<CameraOperation>('/camera/manual/apply', {
          exposure_mode: mode,
          ...(mode === 'manual'
            ? {
                shutter_speed: shutterSpeed === 'auto' ? 'auto' : shutterSpeed,
                ...(iso === 'auto' ? { iso: 'auto' } : { iso }),
              }
            : {}),
          nd_enabled: state.capabilities.supports_nd_filter ? ndEnabled : undefined,
          zoom_step: state.capabilities.supports_zoom_control ? zoomStep : undefined,
          focus_auto:
            mode === 'auto'
              ? state.capabilities.supports_focus_control
                ? true
                : undefined
              : state.capabilities.supports_focus_control
                ? focusPreset === 'auto'
                : undefined,
          focus_mm:
            mode === 'manual' && state.capabilities.supports_focus_control && focusPreset !== 'auto'
              ? focusPreset
              : undefined,
          flash_mode: state.capabilities.supports_flash_control ? flashMode : undefined,
        })
        await pollOperation(op.operation_id)
        userTouchedRef.current = false
        clearDirty()
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Could not apply settings')
      } finally {
        setBusy(false)
      }
    },
    [
      state,
      shutterSpeed,
      iso,
      ndEnabled,
      zoomStep,
      focusPreset,
      flashMode,
      pollOperation,
      clearDirty,
      cancelDebouncedApply,
    ],
  )

  const applyExposureModeNow = useCallback(
    (mode: 'auto' | 'manual') => {
      cancelDebouncedApply()
      markUserEdit()
      void applySettings(mode)
    },
    [applySettings, cancelDebouncedApply, markUserEdit],
  )

  useEffect(() => {
    if (!state || !userTouchedRef.current || busy) return
    cancelDebouncedApply()
    debounceTimerRef.current = window.setTimeout(() => {
      debounceTimerRef.current = null
      void applySettings(exposureModeRef.current)
    }, APPLY_DEBOUNCE_MS)
    return () => {
      cancelDebouncedApply()
    }
  }, [state, busy, exposureMode, shutterSpeed, iso, ndEnabled, zoomStep, focusPreset, flashMode, applySettings, cancelDebouncedApply])

  const submitPower = async (action: 'sleep' | 'deep_sleep' | 'wake') => {
    setBusy(true)
    setError('')
    try {
      const op =
        action === 'wake'
          ? await apiClient.post<CameraOperation>('/camera/power/wake')
          : await apiClient.post<CameraOperation>('/camera/power/sleep', { level: action })
      await pollOperation(op.operation_id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not change power state')
    } finally {
      setBusy(false)
    }
  }

  const powerVariant = useMemo(() => {
    if (!state) return 'warning'
    if (state.power_state === 'active') return 'success'
    if (state.power_state === 'error') return 'danger'
    return 'warning'
  }, [state])

  const shutterOptions = useMemo(() => {
    if (!shutterSpeed || SHUTTER_PRESETS.includes(shutterSpeed)) return SHUTTER_PRESETS
    return [shutterSpeed, ...SHUTTER_PRESETS]
  }, [shutterSpeed])

  const isoOptions = useMemo((): (number | 'auto')[] => {
    const raw = state?.iso
    if (raw != null && typeof raw === 'number' && !ISO_BASE.includes(raw)) {
      return [...ISO_BASE, raw].sort((a, b) => {
        if (a === 'auto') return -1
        if (b === 'auto') return 1
        return (a as number) - (b as number)
      })
    }
    return ISO_BASE
  }, [state?.iso])

  const zoomSelectOptions = useMemo(() => {
    if (state?.zoom_positions && state.zoom_positions.length > 0) {
      return state.zoom_positions.map((p) => ({
        step: p.step,
        label: `≈${p.focal_length_35mm_equiv_mm}mm equiv. (${p.focal_length_mm}mm lens)`,
      }))
    }
    const n = Math.max(1, state?.zoom_steps_count ?? 10)
    return Array.from({ length: n }, (_, i) => ({
      step: i,
      label: `Zoom ${i + 1} / ${n}`,
    }))
  }, [state?.zoom_positions, state?.zoom_steps_count])

  return (
    <Card>
      <CardHeader className={compact ? 'space-y-2 pb-3' : undefined}>
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div className="min-w-0 space-y-1">
            <CardTitle className={compact ? 'text-base' : undefined}>
              {compact ? 'Camera controls' : 'Manual Camera Controls'}
            </CardTitle>
            {!compact && (
              <CardDescription>
                Exposure Auto / Manual applies immediately. In Manual mode you can set shutter or ISO to Auto individually.
                Zoom shows approximate 35mm-equivalent focal length after a one-time USB scan. Equiv. uses sensor crop
                multiplier from the engine (override with PHOS_FOCAL_35MM_EQUIV_MULT on the Pi).
              </CardDescription>
            )}
            {compact && (
              <CardDescription className="text-xs leading-snug">
                Auto/manual exposure and per-control settings; changes apply after a short debounce.
              </CardDescription>
            )}
          </div>
          <Badge variant={powerVariant}>{state?.power_state ?? 'loading'}</Badge>
        </div>
      </CardHeader>
      <CardContent className={compact ? 'space-y-3' : undefined}>
        {state && !compact && (
          <div className="grid gap-2 text-sm text-mutedForeground">
            <div className="flex items-center justify-between">
              <span className="text-foreground">Current mode</span>
              <span>{state.mode}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-foreground">Idle</span>
              <span>{state.idle_seconds}s</span>
            </div>
            {state.mode === 'playback' && (
              <p className="text-xs text-warning">
                Playback: use Wake, then switch to Manual exposure in record/shooting mode for shutter/ISO to stick.
              </p>
            )}
          </div>
        )}
        {state && compact && (
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-mutedForeground">
            <span>
              <span className="text-foreground">Mode </span>
              {state.mode}
            </span>
            <span>
              <span className="text-foreground">Idle </span>
              {state.idle_seconds}s
            </span>
            {state.mode === 'playback' && (
              <span className="text-warning">Playback — wake camera for manual controls.</span>
            )}
          </div>
        )}
        <div
          className={
            compact
              ? 'flex flex-wrap gap-2 rounded-md border border-border/60 bg-muted/30 p-2 text-xs'
              : 'flex flex-wrap gap-3 rounded-md border border-border/60 bg-muted/30 p-3 text-sm'
          }
        >
          <span className="font-medium text-foreground">Exposure</span>
          <label className="flex cursor-pointer items-center gap-2">
            <input
              type="radio"
              name="exposure-mode"
              checked={exposureMode === 'auto'}
              onChange={() => {
                setExposureMode('auto')
                setShutterSpeed('auto')
                setIso('auto')
                setFocusPreset('auto')
                applyExposureModeNow('auto')
              }}
            />
            {compact ? 'Auto' : 'Auto (camera)'}
          </label>
          <label className="flex cursor-pointer items-center gap-2">
            <input
              type="radio"
              name="exposure-mode"
              checked={exposureMode === 'manual'}
              onChange={() => {
                setExposureMode('manual')
                applyExposureModeNow('manual')
              }}
            />
            {compact ? 'Manual' : 'Manual (per-control shutter / ISO)'}
          </label>
        </div>
        <div className={compact ? 'grid gap-2 grid-cols-1' : 'grid gap-3 md:grid-cols-2'}>
          <div className="grid gap-1 text-sm">
            <label htmlFor="shutter-control" className="text-inherit">
              {compact ? 'Shutter' : 'Shutter speed'}
            </label>
            <select
              id="shutter-control"
              className={
                compact
                  ? 'h-9 w-full rounded-md border border-border bg-input px-2 text-sm text-foreground disabled:opacity-50'
                  : 'h-10 w-full rounded-md border border-border bg-input px-3 text-sm text-foreground disabled:opacity-50'
              }
              value={shutterSpeed}
              disabled={exposureMode === 'auto'}
              onChange={(event) => {
                setShutterSpeed(event.target.value)
                markUserEdit()
              }}
            >
              {shutterOptions.map((item) => (
                <option key={item} value={item}>
                  {item === 'auto' ? 'Auto' : item}
                </option>
              ))}
            </select>
          </div>
          <label className="grid gap-1 text-sm">
            <span>ISO</span>
            <select
              className={
                compact
                  ? 'h-9 rounded-md border border-border bg-input px-2 text-sm text-foreground disabled:opacity-50'
                  : 'h-10 rounded-md border border-border bg-input px-3 text-sm text-foreground disabled:opacity-50'
              }
              value={iso === 'auto' ? 'auto' : String(iso)}
              disabled={exposureMode === 'auto'}
              onChange={(event) => {
                const v = event.target.value
                setIso(v === 'auto' ? 'auto' : Number(v))
                markUserEdit()
              }}
            >
              {isoOptions.map((item) => (
                <option key={String(item)} value={String(item)}>
                  {item === 'auto' ? 'Auto' : item}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm">
            <span>{compact ? 'Zoom' : 'Zoom (35mm-style label)'}</span>
            <select
              className={
                compact
                  ? 'h-9 rounded-md border border-border bg-input px-2 text-sm text-foreground disabled:opacity-50'
                  : 'h-10 rounded-md border border-border bg-input px-3 text-sm text-foreground disabled:opacity-50'
              }
              value={zoomStep}
              onChange={(event) => {
                setZoomStep(Number(event.target.value))
                markUserEdit()
              }}
              disabled={!state?.capabilities.supports_zoom_control}
            >
              {zoomSelectOptions.map((z) => (
                <option key={z.step} value={z.step}>
                  {z.label}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm">
            <span>{compact ? 'Focus' : 'Focus distance'}</span>
            <select
              className={
                compact
                  ? 'h-9 rounded-md border border-border bg-input px-2 text-sm text-foreground disabled:opacity-50'
                  : 'h-10 rounded-md border border-border bg-input px-3 text-sm text-foreground disabled:opacity-50'
              }
              value={focusPreset === 'auto' ? 'auto' : String(focusPreset)}
              onChange={(event) => {
                const v = event.target.value
                setFocusPreset(v === 'auto' ? 'auto' : Number(v))
                markUserEdit()
              }}
              disabled={!state?.capabilities.supports_focus_control || exposureMode === 'auto'}
            >
              {FOCUS_PRESETS.map((p) => (
                <option key={String(p.value)} value={String(p.value)}>
                  {p.label}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm">
            <span>Flash</span>
            <select
              className={
                compact
                  ? 'h-9 rounded-md border border-border bg-input px-2 text-sm text-foreground'
                  : 'h-10 rounded-md border border-border bg-input px-3 text-sm text-foreground'
              }
              value={flashMode}
              onChange={(event) => {
                setFlashMode(Number(event.target.value))
                markUserEdit()
              }}
              disabled={!state?.capabilities.supports_flash_control}
            >
              {FLASH_PRESETS.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={ndEnabled}
              onChange={(event) => {
                setNdEnabled(event.target.checked)
                markUserEdit()
              }}
              disabled={!state?.capabilities.supports_nd_filter}
            />
            {compact ? 'ND filter' : 'ND filter enabled'}
          </label>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {busy && <span className="text-xs text-mutedForeground">Syncing…</span>}
          <Button variant="secondary" disabled={busy} onClick={() => void submitPower('sleep')}>
            Sleep
          </Button>
          <Button variant="secondary" disabled={busy} onClick={() => void submitPower('deep_sleep')}>
            Deep sleep
          </Button>
          <Button variant="ghost" disabled={busy} onClick={() => void submitPower('wake')}>
            Wake
          </Button>
          <Button variant="ghost" disabled={busy} onClick={() => void refreshState()}>
            Refresh
          </Button>
        </div>
        {state && (
          <div className={compact ? 'space-y-1 text-[11px] leading-snug text-mutedForeground' : 'space-y-1 text-xs text-mutedForeground'}>
            <p>
              {state.exposure_control === 'auto' ? (
                <>
                  <span className="text-foreground">Live metering</span>: shutter {state.metering_shutter_display}, ISO{' '}
                  {state.metering_iso ?? 'auto'} — CHDK reading at this moment; the camera may choose differently when you shoot.
                </>
              ) : state.exposure_control === 'manual' ? (
                <>
                  <span className="text-foreground">Applied (USB)</span>: shutter{' '}
                  {state.shutter_auto_active ? 'auto (camera)' : state.shutter_display}, ISO{' '}
                  {state.iso_auto_active ? 'auto (camera)' : (state.iso ?? '—')}, aperture {state.aperture_display}
                  {state.zoom_focal_length_mm != null && (
                    <>
                      {' '}
                      · zoom {state.zoom_focal_length_mm}mm
                      {state.focus_auto_active
                        ? ' · focus auto (camera)'
                        : state.focus_control && state.focus_control !== 'unknown'
                          ? state.focus_control === 'mf' && state.focus_mm != null
                            ? ` · focus MF (${state.focus_mm}mm)`
                            : ` · focus ${state.focus_control.toUpperCase()}`
                          : ''}
                    </>
                  )}
                </>
              ) : (
                <>
                  <span className="text-foreground">CHDK view</span>: shutter {state.shutter_display}, ISO {state.iso ?? 'auto'},
                  aperture {state.aperture_display} — choose Auto or Manual above to set the camera mode.
                </>
              )}
            </p>
            {state.exposure_control === 'manual' &&
              (state.metering_shutter_display !== state.shutter_display ||
                state.metering_iso !== state.iso) && (
                <p>
                  <span className="text-foreground">Live metering</span> (reference): shutter {state.metering_shutter_display}, ISO{' '}
                  {state.metering_iso ?? '—'}
                </p>
              )}
          </div>
        )}
        {error && <Toast variant="danger">{error}</Toast>}
      </CardContent>
    </Card>
  )
}
