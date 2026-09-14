import { describe, expect, it } from 'vitest'

import { loadTrajectoryLog } from './trajectoryData'

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
    expect(log.frames[0].pursuer_accel_cmd_m_s2).toBeTruthy()
    expect(log.frames[1].pursuer_accel_achieved_m_s2).toEqual({
      x: 0,
      y: 0,
      z: 0,
    })
  })
})
