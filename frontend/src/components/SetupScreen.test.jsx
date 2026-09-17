/** @vitest-environment jsdom */
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { SetupScreen } from './SetupScreen'
import { useSimulationStore } from '../store/useSimulationStore'

const catalog = {
  scenarios: [{ id: 'valley', label: 'Valley', description: 'Mountain run.', parameter_defaults: {} }],
  guidance_laws: [{ id: 'pn', label: 'PN', description: 'Guidance law.' }],
  vehicle_profiles: [{
    name: 'Interceptor', role: 'interceptor', parameters: {
      mass: { value: 200, unit: 'kg' },
    },
  }],
  engagement_parameters: {},
}

afterEach(cleanup)

beforeEach(() => {
  useSimulationStore.setState(useSimulationStore.getInitialState(), true)
  useSimulationStore.getState().setCatalog(catalog)
})

describe('SetupScreen', () => {
  it('keeps the primary run action available with all setup sections', () => {
    const onRun = vi.fn()
    render(<SetupScreen onRun={onRun} />)

    expect(screen.getByText('SCENARIO')).toBeTruthy()
    expect(screen.getByText('GUIDANCE LAW')).toBeTruthy()
    expect(screen.getByText('VEHICLE PROFILES')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'RUN LIVE ENGAGEMENT' }))
    expect(onRun).toHaveBeenCalledOnce()
  })

  it('shows stream errors beside the persistent action', () => {
    useSimulationStore.setState({ error: 'Stream unavailable.' })
    render(<SetupScreen onRun={() => {}} />)
    const action = screen.getByRole('button', { name: 'RUN LIVE ENGAGEMENT' }).parentElement
    expect(action.className).toBe('setup-actions')
    expect(action.textContent).toContain('Stream unavailable.')
  })

  it('shows a connecting message instead of a blank screen while the catalog loads', () => {
    useSimulationStore.setState({ catalog: null })
    render(<SetupScreen onRun={() => {}} />)
    expect(screen.getByText(/Connecting to the simulation backend/)).toBeTruthy()
  })
})
