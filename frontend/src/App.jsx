import { useCallback, useEffect, useState } from 'react'

import { AppHeader } from './components/AppHeader'
import { AppNav } from './components/AppNav'
import { HudOverlay } from './components/HudOverlay'
import { PlaybackControls } from './components/PlaybackControls'
import { SessionReplayPanel } from './components/SessionReplayPanel'
import { SetupScreen } from './components/SetupScreen'
import { SimulationScene } from './components/SimulationScene'
import { TrainingDashboard } from './components/TrainingDashboard'
import { TrialsOverlay } from './components/TrialsOverlay'
import { loadTrajectoryLog, loadTrialSet } from './data/trajectoryData'
import { useDebouncedParameterRestream } from './hooks/useDebouncedParameterRestream'
import { usePlaybackClock } from './hooks/usePlaybackClock'
import { useTrajectoryStream } from './hooks/useTrajectoryStream'
import { useSimulationStore } from './store/useSimulationStore'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

export default function App() {
  const [screen, setScreen] = useState('hud')
  const [projection, setProjection] = useState('3d')
  const setCatalog = useSimulationStore((state) => state.setCatalog)
  const failStream = useSimulationStore((state) => state.failStream)
  const loadReplay = useSimulationStore((state) => state.loadReplay)
  const setTrialCount = useSimulationStore((state) => state.setTrialCount)
  const setTrialSet = useSimulationStore((state) => state.setTrialSet)
  const setViewMode = useSimulationStore((state) => state.setViewMode)
  const startStream = useTrajectoryStream()
  usePlaybackClock()
  useDebouncedParameterRestream(startStream)

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

  const selectScreen = useCallback(
    (next) => {
      setScreen(next)
      if (next === 'trials') setViewMode('trials')
      else if (useSimulationStore.getState().viewMode === 'trials') {
        setViewMode('single')
      }
    },
    [setViewMode],
  )

  const handleRun = useCallback(() => {
    startStream()
    selectScreen('hud')
  }, [selectScreen, startStream])

  const handleReplay = useCallback(
    async (file) => {
      try {
        const trajectoryLog = await loadTrajectoryLog(file)
        loadReplay(trajectoryLog)
        selectScreen('hud')
      } catch (error) {
        failStream(error.message)
      }
    },
    [failStream, loadReplay, selectScreen],
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
    <div className="hud-shell">
      <AppNav screen={screen} onSelect={selectScreen} />
      <div className="hud-stage">
        <AppHeader
          screen={screen}
          projection={projection}
          onProjection={setProjection}
        />
        <div className="scene-layer">
          <SimulationScene projection={projection} />
        </div>
        {screen === 'hud' && <HudOverlay />}
        {screen === 'setup' && <SetupScreen onRun={handleRun} />}
        {screen === 'trials' && (
          <TrialsOverlay onTrialCountChange={handleTrialCountChange} />
        )}
        {screen === 'train' && <TrainingDashboard />}
        {screen === 'replay' && (
          <SessionReplayPanel onReplay={handleReplay} />
        )}
        <PlaybackControls />
      </div>
    </div>
  )
}
