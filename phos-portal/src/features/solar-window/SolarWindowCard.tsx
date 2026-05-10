import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { Sunrise, Sunset, SunMedium, Moon } from 'lucide-react'
import { Button } from '../../components/ui/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/Card'
import { Input } from '../../components/ui/Input'
import { Skeleton } from '../../components/ui/Skeleton'
import { Toast } from '../../components/ui/Toast'
import { apiClient } from '../../shared/api-client'

type SolarWindow = {
  day: string
  astronomical_dawn: string | null
  nautical_dawn: string | null
  civil_dawn: string | null
  blue_hour_morning_start: string | null
  blue_hour_morning_end: string | null
  golden_hour_morning_start: string | null
  sunrise: string
  golden_hour_morning_end: string | null
  sunset: string
  golden_hour_evening_start: string | null
  golden_hour_evening_end: string | null
  blue_hour_evening_start: string | null
  blue_hour_evening_end: string | null
  civil_dusk: string | null
  nautical_dusk: string | null
  astronomical_dusk: string | null
  solar_noon: string
  daylight_hours: number
  night_hours: number
  calculated_at: string
}

type SolarSummary = {
  start_date: string
  end_date: string
  days: number
  sunrise_min: string
  sunrise_max: string
  sunset_min: string
  sunset_max: string
  daylight_min_hours: number
  daylight_max_hours: number
  daylight_avg_hours: number
  night_min_hours: number
  night_max_hours: number
  night_avg_hours: number
}

function toTime(value: string) {
  return new Date(value).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function toTimeOrNA(value: string | null) {
  return value ? toTime(value) : 'N/A'
}

export function SolarWindowCard() {
  const [today, setToday] = useState<SolarWindow | null>(null)
  const [summary, setSummary] = useState<SolarSummary | null>(null)
  const [days, setDays] = useState(30)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const fetchSolarData = async (rangeDays: number) => {
    try {
      const [todayData, summaryData] = await Promise.all([
        apiClient.get<SolarWindow>('/solar/today'),
        apiClient.get<SolarSummary>(`/solar/range/summary?days=${rangeDays}`),
      ])
      setToday(todayData)
      setSummary(summaryData)
      setError('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error cargando ventana solar')
    } finally {
      setLoading(false)
    }
  }

  const refresh = async () => {
    setLoading(true)
    void fetchSolarData(days)
  }

  useEffect(() => {
    const initialTimer = setTimeout(() => {
      void fetchSolarData(30)
    }, 0)
    return () => clearTimeout(initialTimer)
  }, [])

  return (
    <Card>
      <CardHeader>
        <div className="space-y-1">
          <CardTitle>Ventana solar</CardTitle>
          <CardDescription>Amanecer/atardecer diario y rango estadistico por periodo.</CardDescription>
        </div>
        <Button variant="secondary" onClick={() => void refresh()}>
          Refrescar
        </Button>
      </CardHeader>
      <CardContent>
        <div className="flex items-end gap-2">
          <label className="grid flex-1 gap-1 text-sm text-mutedForeground">
            Dias de analisis
            <Input
              type="number"
              min={1}
              max={366}
              value={days}
              onChange={(event) => setDays(Number(event.target.value))}
            />
          </label>
          <Button onClick={() => void refresh()}>Aplicar</Button>
        </div>

        {loading && (
          <div className="grid gap-2">
            <Skeleton className="h-10" />
            <Skeleton className="h-20" />
            <Skeleton className="h-20" />
          </div>
        )}

        {!loading && error && <Toast variant="danger">{error}</Toast>}

        {!loading && today && (
          <div className="grid gap-2 rounded-md border border-border bg-background/70 p-3">
            <p className="text-xs uppercase tracking-wide text-mutedForeground">{today.day}</p>
            <div className="grid gap-2 sm:grid-cols-2">
              <MiniMetric
                icon={<Sunrise className="h-4 w-4 text-primary" />}
                label="Astronomical dawn"
                value={toTimeOrNA(today.astronomical_dawn)}
              />
              <MiniMetric
                icon={<Sunrise className="h-4 w-4 text-primary" />}
                label="Nautical dawn"
                value={toTimeOrNA(today.nautical_dawn)}
              />
              <MiniMetric icon={<Sunrise className="h-4 w-4 text-primary" />} label="Civil dawn" value={toTimeOrNA(today.civil_dawn)} />
              <MiniMetric
                icon={<Sunrise className="h-4 w-4 text-warning" />}
                label="Blue hour AM"
                value={`${toTimeOrNA(today.blue_hour_morning_start)} - ${toTimeOrNA(today.blue_hour_morning_end)}`}
              />
              <MiniMetric
                icon={<Sunrise className="h-4 w-4 text-warning" />}
                label="Golden hour AM"
                value={`${toTimeOrNA(today.golden_hour_morning_start)} - ${toTimeOrNA(today.golden_hour_morning_end)}`}
              />
              <MiniMetric icon={<Sunrise className="h-4 w-4 text-warning" />} label="Sunrise" value={toTime(today.sunrise)} />
              <MiniMetric icon={<Sunset className="h-4 w-4 text-warning" />} label="Sunset" value={toTime(today.sunset)} />
              <MiniMetric
                icon={<Sunset className="h-4 w-4 text-warning" />}
                label="Golden hour PM"
                value={`${toTimeOrNA(today.golden_hour_evening_start)} - ${toTimeOrNA(today.golden_hour_evening_end)}`}
              />
              <MiniMetric
                icon={<Sunset className="h-4 w-4 text-primary" />}
                label="Blue hour PM"
                value={`${toTimeOrNA(today.blue_hour_evening_start)} - ${toTimeOrNA(today.blue_hour_evening_end)}`}
              />
              <MiniMetric icon={<Sunset className="h-4 w-4 text-primary" />} label="Civil dusk" value={toTimeOrNA(today.civil_dusk)} />
              <MiniMetric icon={<Sunset className="h-4 w-4 text-primary" />} label="Nautical dusk" value={toTimeOrNA(today.nautical_dusk)} />
              <MiniMetric
                icon={<Sunset className="h-4 w-4 text-primary" />}
                label="Astronomical dusk"
                value={toTimeOrNA(today.astronomical_dusk)}
              />
              <MiniMetric
                icon={<SunMedium className="h-4 w-4 text-primary" />}
                label="Daytime"
                value={`${today.daylight_hours.toFixed(2)} h`}
              />
              <MiniMetric icon={<Moon className="h-4 w-4 text-primary" />} label="Nighttime" value={`${today.night_hours.toFixed(2)} h`} />
            </div>
          </div>
        )}

        {!loading && summary && (
          <div className="grid gap-2 rounded-md border border-border bg-background/70 p-3 text-sm text-mutedForeground">
            <p className="text-xs uppercase tracking-wide">
              Rango {summary.start_date} - {summary.end_date} ({summary.days} dias)
            </p>
            <div className="grid gap-1 sm:grid-cols-2">
              <p>
                <strong className="text-foreground">Sunrise min/max:</strong> {toTime(summary.sunrise_min)} /{' '}
                {toTime(summary.sunrise_max)}
              </p>
              <p>
                <strong className="text-foreground">Sunset min/max:</strong> {toTime(summary.sunset_min)} /{' '}
                {toTime(summary.sunset_max)}
              </p>
              <p>
                <strong className="text-foreground">Daylight avg:</strong> {summary.daylight_avg_hours.toFixed(2)} h
              </p>
              <p>
                <strong className="text-foreground">Night avg:</strong> {summary.night_avg_hours.toFixed(2)} h
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

type MiniMetricProps = {
  icon: ReactNode
  label: string
  value: string
}

function MiniMetric({ icon, label, value }: MiniMetricProps) {
  return (
    <div className="rounded-md border border-border bg-card p-2">
      <div className="mb-1 flex items-center justify-between text-xs uppercase tracking-wide text-mutedForeground">
        <span>{label}</span>
        {icon}
      </div>
      <p className="text-base font-semibold text-foreground">{value}</p>
    </div>
  )
}
