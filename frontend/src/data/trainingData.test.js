import { describe, expect, it, vi } from 'vitest'

import { loadTrainingLog } from './trainingData'
import { summarizeTrainingLog } from '../lib/trainingStats'

describe('training log adapter', () => {
  it('validates the {episode, reward, success} shape', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => ({
        ok: true,
        json: async () => [
          { episode: 1, reward: 12, success: false },
          { episode: 2, reward: 40, success: true },
        ],
      })),
    )

    await expect(loadTrainingLog('/mock/training-log.json')).resolves.toEqual([
      { episode: 1, reward: 12, success: false },
      { episode: 2, reward: 40, success: true },
    ])
    vi.unstubAllGlobals()
  })

  it('summarizes rolling success from the last window', () => {
    const stats = summarizeTrainingLog([
      { episode: 1, reward: -10, success: false },
      { episode: 2, reward: 4, success: true },
      { episode: 3, reward: 8, success: true },
    ], 2)

    expect(stats.episodeCount).toBe(3)
    expect(stats.latestReward).toBe(8)
    expect(stats.rollingSuccessRate).toBe(1)
  })
})
