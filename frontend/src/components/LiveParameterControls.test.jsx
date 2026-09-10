/** @vitest-environment jsdom */
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { LiveParameterControls } from './LiveParameterControls'
import { useSimulationStore } from '../store/useSimulationStore'

const catalog = {
  scenarios: [],
  guidance_laws: [],
  vehicle_profiles: [
    {
      name: 'Interceptor A',
      role: 'interceptor',
      parameters: {
        speed: {
          value: 700,
          unit: 'm/s',
          reference_min: 600,
          reference_max: 1000,
          live_control: true,
          control_step: 10,
        },
        mass: {
          value: 200,
          unit: 'kg',
          reference_min: 50,
          reference_max: 300,
          live_control: false,
        },
      },
    },
    {
      name: 'Target B',
      role: 'target',
      parameters: {
        speed: {
          value: 240,
          unit: 'm/s',
          reference_min: 200,
          reference_max: 300,
          live_control: true,
          control_step: 5,
        },
      },
    },
  ],
}

afterEach(() => {
  cleanup()
})

beforeEach(() => {
  useSimulationStore.setState(useSimulationStore.getInitialState(), true)
  useSimulationStore.getState().setCatalog(catalog)
})

describe('LiveParameterControls', () => {
  it('renders catalog-marked live sliders and ignores non-live fields', () => {
    render(<LiveParameterControls />)

    expect(screen.getByLabelText('Interceptor A speed')).toBeTruthy()
    expect(screen.getByLabelText('Target B speed')).toBeTruthy()
    expect(screen.queryByLabelText(/mass/i)).toBeNull()
  })

  it('writes slider bounds from catalog metadata into the store', () => {
    render(<LiveParameterControls />)
    fireEvent.change(screen.getByLabelText('Interceptor A speed'), {
      target: { value: '820' },
    })

    expect(useSimulationStore.getState().parameterValues['interceptor.speed']).toBe(
      820,
    )
  })
})
