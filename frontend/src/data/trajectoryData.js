/**
 * Trial/session adapters live here so the viewer only consumes one shape:
 * { source, trials: [{ episode, reward, success, frames }] } for overlays,
 * or { source, frames } for single-session replay.
 */

function distance(a, b) {
  return Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z)
}

function velocityAt(samples, index, field) {
  const before = samples[Math.max(0, index - 1)]
  const after = samples[Math.min(samples.length - 1, index + 1)]
  const dt = after.time_s - before.time_s || 1
  return {
    x: (after[field].x - before[field].x) / dt,
    y: (after[field].y - before[field].y) / dt,
    z: (after[field].z - before[field].z) / dt,
  }
}

function zeroAccel() {
  return { x: 0, y: 0, z: 0 }
}

function lateralFromVelocityChange(samples, index) {
  if (samples.length < 2) return zeroAccel()
  const before = samples[Math.max(0, index - 1)]
  const after = samples[Math.min(samples.length - 1, index + 1)]
  const dt = after.time_s - before.time_s || 1
  const vBefore = velocityAt(samples, Math.max(0, index - 1), 'pursuer_position_m')
  const vAfter = velocityAt(samples, Math.min(samples.length - 1, index + 1), 'pursuer_position_m')
  const ax = (vAfter.x - vBefore.x) / dt
  const ay = (vAfter.y - vBefore.y) / dt
  const az = (vAfter.z - vBefore.z) / dt
  const vel = velocityAt(samples, index, 'pursuer_position_m')
  const speed = Math.hypot(vel.x, vel.y, vel.z) || 1
  const along = (ax * vel.x + ay * vel.y + az * vel.z) / (speed * speed)
  return {
    x: ax - along * vel.x,
    y: ay - along * vel.y,
    z: az - along * vel.z,
  }
}

async function readJson(source) {
  if (typeof source === 'string') {
    const response = await fetch(source)
    if (!response.ok) {
      throw new Error(`Trajectory log request failed (${response.status}).`)
    }
    return response.json()
  }
  if (source && typeof source.text === 'function') {
    return JSON.parse(await source.text())
  }
  return source
}

export async function loadTrajectoryLog(
  source = '/mock/last-session.json',
) {
  const log = await readJson(source)
  if (
    !log ||
    log.schema_version !== '1.0' ||
    !Array.isArray(log.samples) ||
    log.samples.length < 2
  ) {
    throw new Error('Unsupported trajectory log format.')
  }

  const streamId = `replay:${log.session_id}`
  const frames = log.samples.map((sample, index) => {
    const pursuerVelocity = velocityAt(
      log.samples,
      index,
      'pursuer_position_m',
    )
    const targetVelocity = velocityAt(
      log.samples,
      index,
      'target_position_m',
    )
    const isTerminal = index === log.samples.length - 1
    const achieved = isTerminal
      ? zeroAccel()
      : lateralFromVelocityChange(log.samples, index)
    const commanded = isTerminal
      ? zeroAccel()
      : {
          x: achieved.x * 1.15,
          y: achieved.y * 1.15,
          z: achieved.z * 1.15,
        }
    return {
      type: 'trajectory.frame',
      stream_id: streamId,
      sequence: index,
      time_s: sample.time_s,
      pursuer: {
        position_m: sample.pursuer_position_m,
        velocity_m_s: pursuerVelocity,
      },
      target: {
        position_m: sample.target_position_m,
        velocity_m_s: targetVelocity,
      },
      range_m: distance(
        sample.pursuer_position_m,
        sample.target_position_m,
      ),
      pursuer_accel_cmd_m_s2: commanded,
      pursuer_accel_achieved_m_s2: achieved,
    }
  })

  const closestApproach = Math.min(...frames.map((frame) => frame.range_m))
  return {
    schema_version: log.schema_version,
    session_id: log.session_id,
    source: log.source ?? 'mock-saved-session',
    scenario_id: log.scenario_id,
    guidance_law: log.guidance_law,
    dt_s: frames[1].time_s - frames[0].time_s,
    outcome: log.outcome,
    closest_approach_m: closestApproach,
    frames,
  }
}

export async function loadTrialSet({ scenarioId, parameterOverrides, count }) {
  const response = await fetch(
    `${import.meta.env.VITE_API_BASE_URL ?? ''}/api/trials`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        scenario_id: scenarioId,
        parameter_overrides: parameterOverrides,
        count,
      }),
    },
  )
  if (!response.ok) {
    throw new Error(`RL trials request failed (${response.status}).`)
  }
  return response.json()
}
