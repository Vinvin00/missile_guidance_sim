/** @vitest-environment jsdom */
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { TrainingDashboard } from './TrainingDashboard'

vi.mock('../data/trainingData', () => ({
  loadTrainingLog: vi.fn(async () => ({
    branch_name: 'unit_branch',
    model_path: 'outputs/unit/rl_checkpoint_02.zip',
    episodes: [
      { episode: 1, reward: -20, success: false },
      { episode: 2, reward: 40, success: true },
      { episode: 3, reward: 70, success: true },
    ],
    checkpoints: [
      { checkpoint: 2, timesteps: 40960, hits: 4, cases: 9, median_miss_m: 6.5 },
    ],
  })),
}))

afterEach(() => {
  cleanup()
})

describe('TrainingDashboard', () => {
  it('renders real run stats and checkpoint evals', async () => {
    render(<TrainingDashboard />)

    await waitFor(() => {
      expect(screen.getByText('3')).toBeTruthy()
    })
    expect(screen.getByText('70')).toBeTruthy()
    expect(screen.getByText('67%')).toBeTruthy()
    expect(screen.getByText('4/9')).toBeTruthy()
    expect(screen.getByText('UNIT_BRANCH')).toBeTruthy()
    expect(screen.getByText('outputs/unit/rl_checkpoint_02.zip')).toBeTruthy()
  })
})
