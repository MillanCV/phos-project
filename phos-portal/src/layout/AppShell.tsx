import type { ReactNode } from 'react'
import { MoonStar, Radar } from 'lucide-react'

type AppShellProps = {
  children: ReactNode
}

export function AppShell({ children }: AppShellProps) {
  return (
    <main className="min-h-screen bg-background text-foreground">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-6 md:px-6 md:py-8">
        <header className="rounded-lg border border-border bg-card/80 p-5 shadow-panel">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="rounded-md border border-primary/40 bg-primary/10 p-2 text-primary">
                <Radar className="h-5 w-5" />
              </div>
              <div>
                <h1 className="text-2xl font-semibold tracking-tight md:text-3xl">Phos Observatory</h1>
                <p className="text-sm text-mutedForeground md:text-base">
                  Canon IXUS 105 + CHDKPTP · Panel operativo remoto
                </p>
              </div>
            </div>
            <div className="inline-flex items-center gap-2 rounded-full border border-border bg-background/60 px-3 py-1 text-xs text-mutedForeground">
              <MoonStar className="h-3.5 w-3.5" />
              dark observatory mode
            </div>
          </div>
        </header>
        <section className="grid gap-4 md:grid-cols-2">{children}</section>
      </div>
    </main>
  )
}
