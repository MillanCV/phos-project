import { CameraConsoleCard } from './features/camera-console/CameraConsoleCard'
import { CameraStatusCard } from './features/camera-status/CameraStatusCard'
import { ManualCaptureCard } from './features/manual-capture/ManualCaptureCard'
import { SolarWindowCard } from './features/solar-window/SolarWindowCard'
import { SystemMetricsCard } from './features/system-metrics/SystemMetricsCard'
import { TimelapseSchedulerCard } from './features/timelapse-scheduler/TimelapseSchedulerCard'
import { AppShell } from './layout/AppShell'

function App() {
  return (
    <AppShell>
      <CameraStatusCard />
      <CameraConsoleCard />
      <ManualCaptureCard />
      <TimelapseSchedulerCard />
      <SolarWindowCard />
      <SystemMetricsCard />
    </AppShell>
  )
}

export default App
