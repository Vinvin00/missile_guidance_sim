import { beforeEach, describe, expect, it } from 'vitest'

import { useSimulationStore } from './useSimulationStore'

const frames = [
  { sequence: 0, time_s: 0 },
  { sequence: 1, time_s: 0.1 },
  { sequence: 2, time_s: 0.2 },
]

beforeEach(() => {
  useSimulationStore.setState(useSimulationStore.getInitialState(), true)
})

describe('simulation playback store', () => {
  it('loads a stream and advances according to elapsed time', () => {
    const state = useSimulationStore.getState()
    state.beginStream()
    frames.forEach((frame) =>
      useSimulationStore.getState().appendFrame(frame),
    )
    useSimulationStore.getState().completeStream({ outcome: 'intercept' })

    useSimulationStore.getState().advancePlayback(0.15)
    expect(useSimulationStore.getState().cursor).toBe(1)

    useSimulationStore.getState().advancePlayback(1)
    expect(useSimulationStore.getState()).toMatchObject({
      cursor: 2,
      playheadS: 0.2,
      isPlaying: false,
    })
  })

  it('restarts when play is pressed at the final frame', () => {
    useSimulationStore.setState({
      frames,
      cursor: 2,
      playheadS: 0.2,
      isPlaying: false,
    })

    useSimulationStore.getState().togglePlayback()

    expect(useSimulationStore.getState()).toMatchObject({
      cursor: 0,
      playheadS: 0,
      isPlaying: true,
    })
  })
})
