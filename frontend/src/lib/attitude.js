import { Matrix4, Quaternion, Vector3 } from 'three'

import { toSceneVector } from './coordinates'

const G = 9.80665
// Point-mass vehicles have no roll state, so the model is banked the way a pilot
// would: its "up" follows the lift vector (what you feel pushing you into the seat).
// Real turns at 9-25 g would roll the jet past 80 degrees, so the pull is scaled
// down and capped, which keeps the bank to about 55 degrees at most.
const BANK_GAIN = 0.45
const MAX_PULL = 1.4 * G

/**
 * Body "up" (scene axes, y-up) for a point-mass vehicle from two consecutive
 * velocities (m/s, scene axes). Continuous through vertical flight and loops, so
 * the model never snaps upside down the way a "world-up" or shortest-arc basis does.
 */
export function liftUp(velocity, previousVelocity, dt) {
  const v = new Vector3(...velocity)
  const dir = v.clone()
  if (dir.lengthSq() < 1e-6) return [0, 1, 0]
  dir.normalize()
  const pull = new Vector3(...velocity).sub(new Vector3(...previousVelocity))
  if (dt > 1e-6) pull.multiplyScalar(BANK_GAIN / dt)
  else pull.set(0, 0, 0)
  if (pull.length() > MAX_PULL) pull.setLength(MAX_PULL)
  const lift = pull.add(new Vector3(0, G, 0))
  lift.addScaledVector(dir, -lift.dot(dir))
  // Free fall straight down the velocity: nothing to bank into, so stay level.
  if (lift.lengthSq() < 1e-6) lift.set(0, 1, 0).addScaledVector(dir, -dir.y)
  if (lift.lengthSq() < 1e-6) return [0, 1, 0]
  return lift.normalize().toArray()
}

/** liftUp for one vehicle ('pursuer' | 'target') at a frame index of a recorded run. */
export function liftFromFrames(frames, index, who) {
  const now = frames[Math.min(index, frames.length - 1)]
  const before = frames[Math.max(0, Math.min(index, frames.length - 1) - 1)]
  return liftUp(
    toSceneVector(now[who].velocity_m_s),
    toSceneVector(before[who].velocity_m_s),
    now.time_s - before.time_s,
  )
}

/**
 * Rotation that puts a model's (forward, up) axes on the streamed (nose, up) axes.
 * Without an `up` it is the shortest arc from forward to the heading, which is
 * only safe for things that look the same at any roll.
 */
export function attitudeQuaternion(forward, modelUp, heading, up) {
  const dir = new Vector3(...heading)
  if (dir.lengthSq() < 1e-6) return new Quaternion()
  dir.normalize()
  if (!up || !modelUp) return new Quaternion().setFromUnitVectors(forward, dir)
  const worldUp = new Vector3(...up).normalize()
  const model = new Matrix4().makeBasis(
    forward, modelUp, new Vector3().crossVectors(forward, modelUp),
  )
  const world = new Matrix4().makeBasis(
    dir, worldUp, new Vector3().crossVectors(dir, worldUp),
  )
  return new Quaternion().setFromRotationMatrix(world.multiply(model.transpose()))
}
