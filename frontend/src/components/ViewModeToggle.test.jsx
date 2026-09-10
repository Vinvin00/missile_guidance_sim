/** @vitest-environment jsdom */
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ViewModeToggle } from './ViewModeToggle'
import { useSimulationStore } from '../store/useSimulationStore'

afterEach(() => {
  cleanup()
})

beforeEach(() => {
  useSimulationStore.setState(useSimulationStore.getInitialState(), true)
})

describe('ViewModeToggle', () => {
  it('switches between single-trajectory and all-trials modes', () => {
    render(<ViewModeToggle />)

    fireEvent.click(screen.getByRole('button', { name: 'All trials' }))

    expect(useSimulationStore.getState().viewMode).toBe('trials')
    expect(screen.getByText('Mock episodes')).toBeTruthy()
  })

  it('notifies the parent when the mock trial count changes', () => {
    const onTrialCountChange = vi.fn()
    useSimulationStore.setState({ viewMode: 'trials' })
    render(<ViewModeToggle onTrialCountChange={onTrialCountChange} />)

    fireEvent.change(screen.getByDisplayValue('30'), {
      target: { value: '50' },
    })

    expect(onTrialCountChange).toHaveBeenCalledWith(50)
    expect(useSimulationStore.getState().trialCount).toBe(50)
  })
})
