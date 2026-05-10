import { CameraStatusCard } from './features/camera-status/CameraStatusCard'
import { ManualCaptureCard } from './features/manual-capture/ManualCaptureCard'
import { SystemMetricsCard } from './features/system-metrics/SystemMetricsCard'
import { TimelapseSchedulerCard } from './features/timelapse-scheduler/TimelapseSchedulerCard'
import { AppShell } from './layout/AppShell'

function App() {
  return (
    <AppShell>
      <CameraStatusCard />
      <ManualCaptureCard />
      <TimelapseSchedulerCard />
      <SystemMetricsCard />
    </AppShell>
  )
}

export default App
