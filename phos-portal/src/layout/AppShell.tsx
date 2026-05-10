import type { ReactNode } from 'react'
import { Clock3, HardDrive, MoonStar, Radar, Wifi } from 'lucide-react'
import { Badge } from '../components/ui/Badge'

type AppShellProps = {
  children: ReactNode
}

export function AppShell({ children }: AppShellProps) {
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
            <Badge variant="success">camera online</Badge>
            <Badge variant="warning">ixus 105</Badge>
            <Badge variant="default">capture mode</Badge>
          </div>
          <div className="control-strip__right">
            <StatusPill icon={<Wifi className="h-3.5 w-3.5" />} label="Link" value="Stable" />
            <StatusPill icon={<Clock3 className="h-3.5 w-3.5" />} label="Cycle" value="15s" />
            <StatusPill icon={<HardDrive className="h-3.5 w-3.5" />} label="Storage" value="Nominal" />
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
}

function StatusPill({ icon, label, value }: StatusPillProps) {
  return (
    <div className="status-pill">
      {icon}
      <span className="status-pill__label">{label}</span>
      <span className="status-pill__value">{value}</span>
    </div>
  )
}
