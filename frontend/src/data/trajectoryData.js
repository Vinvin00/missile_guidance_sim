/**
 * Trial/session adapters live here so the viewer only consumes one shape:
 * { source, trials: [{ episode, reward, success, frames }] } for overlays,
 * or { source, frames } for single-session replay.
 */

function mulberry32(seed) {
  return () => {
    let value = (seed += 0x6d2b79f5)
    value = Math.imul(value ^ (value >>> 15), value | 1)
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61)
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296
  }
}

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

export function generateMockTrialSet(
  baseFrames,
  { count = 30, seed = 20260909 } = {},
) {
  if (!Array.isArray(baseFrames) || baseFrames.length < 2) {
    return {
      schema_version: '1.0',
      source: 'mock-training-trials',
      trials: [],
    }
  }

  const random = mulberry32(seed)
  const trials = Array.from({ length: count }, (_, trialIndex) => {
    const progress = count === 1 ? 1 : trialIndex / (count - 1)
    const successProbability = 0.12 + 0.84 * progress
    const success =
      trialIndex >= count - 3 ||
      (trialIndex > 1 && random() < successProbability)
    const phaseY = random() * Math.PI * 2
    const phaseZ = random() * Math.PI * 2
    const spreadM = 520 * (1 - progress) + 24
    const terminalMissM = success ? 0 : 70 + random() * 260

    const frames = baseFrames.map((frame, frameIndex) => {
      const u = frameIndex / (baseFrames.length - 1)
      const midcourseWindow = Math.sin(Math.PI * u)
      const yNoise =
        spreadM *
        midcourseWindow *
        (0.62 * Math.sin(2 * Math.PI * u + phaseY) +
          0.38 * Math.sin(5 * Math.PI * u + phaseY * 0.5))
      const zNoise =
        spreadM *
        0.35 *
        midcourseWindow *
        Math.sin(3 * Math.PI * u + phaseZ)
      const terminalOffset = terminalMissM * u ** 3
      const pursuerPosition = {
        x: frame.pursuer.position_m.x,
        y: frame.pursuer.position_m.y + yNoise + terminalOffset,
        z: frame.pursuer.position_m.z + zNoise,
      }

      return {
        ...frame,
        stream_id: `mock-trial-${trialIndex + 1}`,
        pursuer: {
          ...frame.pursuer,
          position_m: pursuerPosition,
        },
        range_m: distance(pursuerPosition, frame.target.position_m),
      }
    })

    return {
      episode: trialIndex + 1,
      reward: -95 + progress * 205 + (random() - 0.5) * 35,
      success,
      outcome: success ? 'intercept' : 'miss',
      frames,
    }
  })

  return {
    schema_version: '1.0',
    source: 'mock-training-trials',
    trials,
  }
}

export async function loadTrialSet(options) {
  // Swap this body for a fetch/parser when the RL episode format is frozen.
  return generateMockTrialSet(options.baseFrames, options)
}
