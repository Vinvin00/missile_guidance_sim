import { useCallback, useEffect, useRef } from 'react'

import { loadTrialSet } from '../data/trajectoryData'
import { useSimulationStore } from '../store/useSimulationStore'

function websocketUrl() {
  if (import.meta.env.VITE_WS_URL) return import.meta.env.VITE_WS_URL
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/ws/trajectory`
}

export function useTrajectoryStream() {
  const socketRef = useRef(null)
  const requestIdRef = useRef(0)
  const selectedScenarioId = useSimulationStore(
    (state) => state.selectedScenarioId,
  )
  const selectedGuidanceLaw = useSimulationStore(
    (state) => state.selectedGuidanceLaw,
  )
  const parameterValues = useSimulationStore(
    (state) => state.parameterValues,
  )
  const beginStream = useSimulationStore((state) => state.beginStream)
  const markStreamStarted = useSimulationStore(
    (state) => state.markStreamStarted,
  )
  const appendFrame = useSimulationStore((state) => state.appendFrame)
  const completeStream = useSimulationStore((state) => state.completeStream)
  const failStream = useSimulationStore((state) => state.failStream)
  const setTrialSet = useSimulationStore((state) => state.setTrialSet)

  const startStream = useCallback(() => {
    requestIdRef.current += 1
    const requestId = requestIdRef.current
    socketRef.current?.close(1000, 'superseded')
    beginStream()

    const socket = new WebSocket(websocketUrl())
    socketRef.current = socket
    let completed = false

    socket.onopen = () => {
      socket.send(
        JSON.stringify({
          type: 'stream.start',
          scenario_id: selectedScenarioId,
          guidance_law: selectedGuidanceLaw,
          frame_interval_ms: 6,
          parameter_overrides: parameterValues,
        }),
      )
    }

    socket.onmessage = (event) => {
      if (requestId !== requestIdRef.current) return
      const message = JSON.parse(event.data)
      switch (message.type) {
        case 'stream.started':
          markStreamStarted(message)
          break
        case 'trajectory.frame':
          appendFrame(message)
          break
        case 'stream.completed':
          completed = true
          completeStream(message)
          loadTrialSet({
            baseFrames: useSimulationStore.getState().frames,
            count: useSimulationStore.getState().trialCount,
          }).then((trialSet) => {
            if (requestId === requestIdRef.current) setTrialSet(trialSet)
          })
          break
        case 'stream.error':
          completed = true
          failStream(message.detail)
          break
        default:
          completed = true
          failStream(`Unsupported stream message: ${message.type}`)
      }
    }

    socket.onerror = () => {
      if (requestId === requestIdRef.current) {
        failStream('Unable to connect to the trajectory stream.')
      }
    }

    socket.onclose = (event) => {
      if (
        requestId === requestIdRef.current &&
        !completed &&
        event.code !== 1000
      ) {
        failStream(`Trajectory stream closed unexpectedly (${event.code}).`)
      }
    }
  }, [
    appendFrame,
    beginStream,
    completeStream,
    failStream,
    markStreamStarted,
    parameterValues,
    selectedGuidanceLaw,
    selectedScenarioId,
    setTrialSet,
  ])

  useEffect(
    () => () => {
      requestIdRef.current += 1
      socketRef.current?.close(1000, 'viewer unmounted')
    },
    [],
  )

  return startStream
}
