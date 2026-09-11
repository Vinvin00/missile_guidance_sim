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
  it('shows mock intercept counts for the trial set', () => {
    useSimulationStore.setState({
      trialSet: {
        trials: [
          { episode: 1, success: true, frames: [{ range_m: 2 }] },
          { episode: 2, success: false, frames: [{ range_m: 40 }] },
        ],
      },
    })
    render(<TrialsOverlay />)

    expect(screen.getByText('/2')).toBeTruthy()
    expect(screen.getByText('MOCK EPISODES')).toBeTruthy()
  })

  it('notifies the parent when the mock trial count changes', () => {
    const onTrialCountChange = vi.fn()
    render(<TrialsOverlay onTrialCountChange={onTrialCountChange} />)

    fireEvent.change(screen.getByLabelText('Mock episodes'), {
      target: { value: '50' },
    })

    expect(onTrialCountChange).toHaveBeenCalledWith(50)
    expect(useSimulationStore.getState().trialCount).toBe(50)
  })
})
