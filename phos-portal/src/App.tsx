import './App.css'
import { CameraStatusCard } from './features/camera-status/CameraStatusCard'
import { ManualCaptureCard } from './features/manual-capture/ManualCaptureCard'
import { SystemMetricsCard } from './features/system-metrics/SystemMetricsCard'
import { TimelapseSchedulerCard } from './features/timelapse-scheduler/TimelapseSchedulerCard'

function App() {
  return (
    <main className="app">
      <h1>Phos Portal</h1>
      <p>Panel minimo de observatorio para Canon IXUS 105 + CHDKPTP.</p>
      <CameraStatusCard />
      <ManualCaptureCard />
      <TimelapseSchedulerCard />
      <SystemMetricsCard />
    </main>
  )
}

export default App
