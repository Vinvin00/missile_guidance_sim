import { useEffect, useRef } from 'react'

import { useSimulationStore } from '../store/useSimulationStore'

export function useDebouncedParameterRestream(startStream, delayMs = 300) {
  const parameterValues = useSimulationStore(
    (state) => state.parameterValues,
  )
  const hasTrajectory = useSimulationStore(
    (state) => state.frames.length > 0,
  )
  const activeDataSource = useSimulationStore(
    (state) => state.activeDataSource,
  )
  const previousSignature = useRef(null)
  const signature = JSON.stringify(parameterValues)

  useEffect(() => {
    if (previousSignature.current === null) {
      previousSignature.current = signature
      return undefined
    }
    if (previousSignature.current === signature) return undefined

    previousSignature.current = signature
    if (!hasTrajectory || activeDataSource !== 'synthetic-stream') {
      return undefined
    }

    const timeout = window.setTimeout(startStream, delayMs)
    return () => window.clearTimeout(timeout)
  }, [
    activeDataSource,
    delayMs,
    hasTrajectory,
    signature,
    startStream,
  ])
}
