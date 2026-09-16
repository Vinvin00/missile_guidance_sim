/** @vitest-environment jsdom */
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { PerspectiveCamera, Vector3 } from 'three'

vi.mock('@react-three/fiber', () => ({ Canvas: () => null, useFrame: vi.fn(), useThree: vi.fn() }))
vi.mock('@react-three/drei', () => ({
  Grid: () => null, Html: () => null, Line: () => null,
  OrbitControls: () => null, PerspectiveCamera: () => null,
  useGLTF: Object.assign(vi.fn(), { preload: vi.fn() }),
}))
const { startStream } = vi.hoisted(() => ({ startStream: vi.fn() }))
vi.mock('../hooks/useTrajectoryStream', () => ({ useTrajectoryStream: () => startStream }))

import { fitDistance, SimulationScene, terrainHeight } from './SimulationScene'
import { useSimulationStore } from '../store/useSimulationStore'

afterEach(cleanup)
beforeEach(() => {
  vi.clearAllMocks()
  useSimulationStore.setState(useSimulationStore.getInitialState(), true)
})

describe('overview framing', () => {
  it.each([0.45, 0.75, 1, 1.8, 2.4])('keeps the entire engagement sphere inside a %s aspect viewport', (aspect) => {
    const radius = 6
    const center = new Vector3(2, 3, -1)
    const camera = new PerspectiveCamera(42, aspect, 0.01, 20000)
    camera.position.copy(center).addScaledVector(new Vector3(1.1, 1.25, 4.8).normalize(), fitDistance(radius, aspect))
    camera.lookAt(center)
    camera.updateMatrixWorld()
    for (let lat = 0; lat <= Math.PI; lat += 0.15) {
      for (let lon = 0; lon < 2 * Math.PI; lon += 0.15) {
        const projected = new Vector3(
          radius * Math.sin(lat) * Math.cos(lon),
          radius * Math.cos(lat),
          radius * Math.sin(lat) * Math.sin(lon),
        ).add(center).project(camera)
        expect(Math.abs(projected.x)).toBeLessThan(0.85)
        expect(Math.abs(projected.y)).toBeLessThan(0.85)
        expect(projected.z).toBeGreaterThan(-1)
        expect(projected.z).toBeLessThan(1)
      }
    }
  })
})

describe('alpine terrain', () => {
  it('keeps the central flight valley low and has mountain relief behind it', () => {
    for (let x = -4; x <= 4; x += 0.5) {
      for (let z = -2; z <= 2; z += 0.5) {
        expect(terrainHeight(x, z)).toBeLessThan(0.5)
      }
    }
    expect(terrainHeight(-4, -21)).toBeGreaterThan(7)
    expect(terrainHeight(20, -12)).toBeGreaterThan(7)
  })
})

describe('scene controls', () => {
  it('starts a real run from the empty scene and prevents duplicate starts while connecting', () => {
    useSimulationStore.setState({ catalog: { scenarios: [{ id: 'evasive-climb', label: 'Valley run' }] } })
    const { rerender } = render(<SimulationScene />)
    fireEvent.click(screen.getByRole('button', { name: /Run simulation/ }))
    expect(startStream).toHaveBeenCalledOnce()
    useSimulationStore.setState({ streamStatus: 'connecting' })
    rerender(<SimulationScene />)
    expect(screen.getByRole('button', { name: /Preparing simulation/ }).disabled).toBe(true)
  })

  it('restores overview from a chase camera and lets users hide and restore telemetry', () => {
    useSimulationStore.setState({ cameraMode: 'target' })
    const { container } = render(<SimulationScene />)
    fireEvent.click(screen.getByRole('button', { name: 'Fit both objects' }))
    expect(useSimulationStore.getState().cameraMode).toBe('overview')
    fireEvent.click(screen.getByRole('button', { name: 'Hide telemetry' }))
    expect(container.firstChild.dataset.telemetry).toBe('false')
    fireEvent.click(screen.getByRole('button', { name: 'Show telemetry' }))
    expect(container.firstChild.dataset.telemetry).toBe('true')
  })

  it('shows map scale and object legend in 2D after frames arrive', () => {
    useSimulationStore.setState({ frames: [{}] })
    render(<SimulationScene projection="2d" />)
    expect(screen.getByText('TOPOGRAPHIC VIEW')).toBeTruthy()
    expect(screen.getByText('Top view · Grid 500 m')).toBeTruthy()
    expect(screen.queryByRole('button', { name: /Run simulation/ })).toBeNull()
  })
})
