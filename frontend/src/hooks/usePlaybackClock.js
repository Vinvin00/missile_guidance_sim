import { useEffect } from 'react'

import { useSimulationStore } from '../store/useSimulationStore'

export function usePlaybackClock() {
  const isPlaying = useSimulationStore((state) => state.isPlaying)
  const advancePlayback = useSimulationStore(
    (state) => state.advancePlayback,
  )

  useEffect(() => {
    if (!isPlaying) return undefined

    let animationFrame
    let previousTime = performance.now()
    const tick = (currentTime) => {
      const elapsedS = Math.min((currentTime - previousTime) / 1000, 0.1)
      previousTime = currentTime
      advancePlayback(elapsedS)
      animationFrame = requestAnimationFrame(tick)
    }
    animationFrame = requestAnimationFrame(tick)

    return () => cancelAnimationFrame(animationFrame)
  }, [advancePlayback, isPlaying])
}
