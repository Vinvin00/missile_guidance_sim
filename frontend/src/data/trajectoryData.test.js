import { describe, expect, it } from 'vitest'

import { generateMockTrialSet, loadTrajectoryLog } from './trajectoryData'

const baseFrames = [
  {
    time_s: 0,
    pursuer: { position_m: { x: 0, y: 0, z: 3000 }, velocity_m_s: { x: 700, y: 0, z: 0 } },
    target: { position_m: { x: 5000, y: 0, z: 3200 }, velocity_m_s: { x: -240, y: 0, z: 0 } },
  },
  {
    time_s: 1,
    pursuer: { position_m: { x: 700, y: 10, z: 3010 }, velocity_m_s: { x: 700, y: 0, z: 0 } },
    target: { position_m: { x: 4760, y: 20, z: 3210 }, velocity_m_s: { x: -240, y: 0, z: 0 } },
  },
  {
    time_s: 2,
    pursuer: { position_m: { x: 1400, y: 20, z: 3020 }, velocity_m_s: { x: 700, y: 0, z: 0 } },
    target: { position_m: { x: 4520, y: 40, z: 3220 }, velocity_m_s: { x: -240, y: 0, z: 0 } },
  },
]

describe('trajectory data adapters', () => {
  it('maps a saved session log into viewer frames', async () => {
    const log = await loadTrajectoryLog({
      schema_version: '1.0',
      session_id: 'unit-session',
      source: 'mock-saved-session',
      scenario_id: 'crossing-intercept',
      guidance_law: 'pn',
      outcome: 'intercept',
      samples: [
        {
          time_s: 0,
          pursuer_position_m: { x: 0, y: 0, z: 3000 },
          target_position_m: { x: 1000, y: 0, z: 3000 },
        },
        {
          time_s: 1,
          pursuer_position_m: { x: 400, y: 0, z: 3000 },
          target_position_m: { x: 600, y: 0, z: 3000 },
        },
      ],
    })

    expect(log.frames).toHaveLength(2)
    expect(log.frames[1].range_m).toBe(200)
    expect(log.source).toBe('mock-saved-session')
  })

  it('builds a training-shaped mock trial overlay from a seed trajectory', () => {
    const trialSet = generateMockTrialSet(baseFrames, { count: 20, seed: 7 })
    const successes = trialSet.trials.filter((trial) => trial.success).length

    expect(trialSet.source).toBe('mock-training-trials')
    expect(trialSet.trials).toHaveLength(20)
    expect(trialSet.trials.at(-1)?.success).toBe(true)
    expect(successes).toBeGreaterThan(2)
    expect(successes).toBeLessThan(20)
  })
})
