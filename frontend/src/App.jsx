import { useEffect } from 'react'

import { ControlPanel } from './components/ControlPanel'
import { PlaybackControls } from './components/PlaybackControls'
import { SimulationScene } from './components/SimulationScene'
import { Telemetry } from './components/Telemetry'
import { usePlaybackClock } from './hooks/usePlaybackClock'
import { useTrajectoryStream } from './hooks/useTrajectoryStream'
import { useSimulationStore } from './store/useSimulationStore'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

export default function App() {
  const setCatalog = useSimulationStore((state) => state.setCatalog)
  const failStream = useSimulationStore((state) => state.failStream)
  const startStream = useTrajectoryStream()
  usePlaybackClock()

  useEffect(() => {
    const controller = new AbortController()
    fetch(`${API_BASE_URL}/api/catalog`, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Catalog request failed (${response.status}).`)
        }
        return response.json()
      })
      .then(setCatalog)
      .catch((error) => {
        if (error.name !== 'AbortError') failStream(error.message)
      })
    return () => controller.abort()
  }, [failStream, setCatalog])

  return (
    <main className="app-shell">
      <header className="app-header">
        <div>
          <span className="eyebrow">3-DOF point-mass study</span>
          <h1>Guidance trajectory viewer</h1>
        </div>
        <div className="legend">
          <span>
            <i className="legend-swatch interceptor" />
            Interceptor A
          </span>
          <span>
            <i className="legend-swatch target" />
            Target B
          </span>
        </div>
      </header>

      <div className="workspace">
        <ControlPanel onRun={startStream} />
        <section className="viewer-column" aria-label="3D trajectory viewer">
          <SimulationScene />
          <PlaybackControls />
        </section>
        <Telemetry />
      </div>
    </main>
  )
}
