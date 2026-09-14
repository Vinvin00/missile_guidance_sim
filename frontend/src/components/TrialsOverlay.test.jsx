/** @vitest-environment jsdom */
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { TrialsOverlay } from './TrialsOverlay'
import { useSimulationStore } from '../store/useSimulationStore'

afterEach(() => {
  cleanup()
})

beforeEach(() => {
  useSimulationStore.setState(useSimulationStore.getInitialState(), true)
})

describe('TrialsOverlay', () => {
  it('shows RL intercept counts for the trial set', () => {
    useSimulationStore.setState({
      trialSet: {
        trials: [
          { episode: 1, success: true, closest_approach_m: 2, frames: [] },
          { episode: 2, success: false, closest_approach_m: 40, frames: [] },
        ],
      },
    })
    render(<TrialsOverlay />)

    expect(screen.getByText('/2')).toBeTruthy()
    expect(screen.getByText('RL EPISODES')).toBeTruthy()
    expect(screen.getByText('21.0 m')).toBeTruthy()
  })

  it('notifies the parent when the trial count changes', () => {
    const onTrialCountChange = vi.fn()
    render(<TrialsOverlay onTrialCountChange={onTrialCountChange} />)

    fireEvent.change(screen.getByLabelText('RL episodes'), {
      target: { value: '50' },
    })

    expect(onTrialCountChange).toHaveBeenCalledWith(50)
    expect(useSimulationStore.getState().trialCount).toBe(50)
  })
})
