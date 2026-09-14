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
  engagement_parameters: {
    initial_range: { value: 4000, unit: 'm', reference_min: 2000, reference_max: 15000, live_control: true, control_step: 250 },
    lateral_offset: { value: 3000, unit: 'm', reference_min: -4000, reference_max: 4000, live_control: true, control_step: 100 },
    altitude_delta: { value: 0, unit: 'm', reference_min: -1500, reference_max: 1500, live_control: true, control_step: 50 },
  },
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

  it('shows the 3-D initial separation and updates it with the range slider', () => {
    render(<LiveParameterControls />)
    expect(screen.getByText('5.00 KM')).toBeTruthy()

    fireEvent.change(screen.getByLabelText('Engagement initial range'), {
      target: { value: '0' },
    })
    // Clamped by the input to its 2 km min: hypot(2000, 3000) = 3.61 km.
    expect(screen.getByText('3.61 KM')).toBeTruthy()
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
