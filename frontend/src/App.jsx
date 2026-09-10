import { useCallback, useEffect, useState } from 'react'

import { ControlPanel } from './components/ControlPanel'
import { PlaybackControls } from './components/PlaybackControls'
import { SimulationScene } from './components/SimulationScene'
import { Telemetry } from './components/Telemetry'
import { TrainingDashboard } from './components/TrainingDashboard'
import { loadTrajectoryLog, loadTrialSet } from './data/trajectoryData'
import { useDebouncedParameterRestream } from './hooks/useDebouncedParameterRestream'
import { usePlaybackClock } from './hooks/usePlaybackClock'
import { useTrajectoryStream } from './hooks/useTrajectoryStream'
import { useSimulationStore } from './store/useSimulationStore'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

function currentHashRoute() {
  return window.location.hash.replace(/^#/, '') || '/'
}

export default function App() {
  const [route, setRoute] = useState(currentHashRoute)
  const setCatalog = useSimulationStore((state) => state.setCatalog)
  const failStream = useSimulationStore((state) => state.failStream)
  const loadReplay = useSimulationStore((state) => state.loadReplay)
  const setTrialCount = useSimulationStore((state) => state.setTrialCount)
  const setTrialSet = useSimulationStore((state) => state.setTrialSet)
  const startStream = useTrajectoryStream()
  usePlaybackClock()
  useDebouncedParameterRestream(startStream)

  useEffect(() => {
    const onHashChange = () => setRoute(currentHashRoute())
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

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

  const handleReplay = useCallback(
    async (file) => {
      try {
        const trajectoryLog = await loadTrajectoryLog(file)
        loadReplay(trajectoryLog)
      } catch (error) {
        failStream(error.message)
      }
    },
    [failStream, loadReplay],
  )

  const handleTrialCountChange = useCallback(
    (count) => {
      setTrialCount(count)
      const frames = useSimulationStore.getState().frames
      if (frames.length < 2) return
      loadTrialSet({ baseFrames: frames, count }).then(setTrialSet)
    },
    [setTrialCount, setTrialSet],
  )

  return (
    <main className="app-shell">
      <header className="app-header">
        <div>
          <span className="eyebrow">3-DOF point-mass study</span>
          <h1>Guidance trajectory viewer</h1>
        </div>
        <nav className="app-nav" aria-label="Viewer sections">
          <a
            href="#/"
            aria-current={route !== '/training' ? 'page' : undefined}
          >
            Viewer
          </a>
          <a
            href="#/training"
            aria-current={route === '/training' ? 'page' : undefined}
          >
            Training
          </a>
        </nav>
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

      {route === '/training' ? (
        <section className="training-route" aria-label="Training dashboard">
          <TrainingDashboard />
        </section>
      ) : (
        <div className="workspace">
          <ControlPanel
            onRun={startStream}
            onReplay={handleReplay}
            onTrialCountChange={handleTrialCountChange}
          />
          <section className="viewer-column" aria-label="3D trajectory viewer">
            <SimulationScene />
            <PlaybackControls />
          </section>
          <div className="side-column">
            <Telemetry />
            <TrainingDashboard />
          </div>
        </div>
      )}
    </main>
  )
}
