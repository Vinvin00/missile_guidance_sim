/** @vitest-environment jsdom */
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { TrainingDashboard } from './TrainingDashboard'

vi.mock('../data/trainingData', () => ({
  loadTrainingLog: vi.fn(async () => [
    { episode: 1, reward: -20, success: false },
    { episode: 2, reward: 40, success: true },
    { episode: 3, reward: 70, success: true },
  ]),
}))

afterEach(() => {
  cleanup()
})

describe('TrainingDashboard', () => {
  it('renders mock episode stats from loadTrainingLog()', async () => {
    render(<TrainingDashboard />)

    await waitFor(() => {
      expect(screen.getByText('3')).toBeTruthy()
    })
    expect(screen.getByText('70')).toBeTruthy()
    expect(screen.getByText('67%')).toBeTruthy()
    expect(screen.getByText(/synthetic training history/i)).toBeTruthy()
  })
})
