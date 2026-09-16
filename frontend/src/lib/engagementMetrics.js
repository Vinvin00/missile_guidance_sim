const G0 = 9.80665
const G_LIMIT = 25

function vec(vector) {
  if (!vector) return { x: 0, y: 0, z: 0 }
  return vector
}

function hypot3(v) {
  return Math.hypot(v.x, v.y, v.z)
}

function sub(a, b) {
  return { x: a.x - b.x, y: a.y - b.y, z: a.z - b.z }
}

function cross(a, b) {
  return {
    x: a.y * b.z - a.z * b.y,
    y: a.z * b.x - a.x * b.z,
    z: a.x * b.y - a.y * b.x,
  }
}

function num(value, digits = 0) {
  if (value == null || Number.isNaN(value)) return '—'
  return value.toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })
}

/** Derive HUD quantities from a trajectory frame (+ optional neighbors for accel). */
export function engagementMetrics(
  frame,
  previousFrame = null,
  streamResult = null,
  gLimit = G_LIMIT,
) {
  if (!frame) {
    return {
      clock: '+0.00s',
      rangeTxt: '—',
      closingTxt: '—',
      tgoTxt: '—',
      gLoad: 0,
      gTxt: '—',
      gFrac: 0,
      gPct: '0%',
      gColor: '#f4f5f7',
      altI: '—',
      spdI: '—',
      altT: '—',
      spdT: '—',
      pk: 0,
      pkTxt: '—',
      pkColor: '#f4f5f7',
      missTxt: '—',
      losTxt: '—',
      alert: null,
      interceptorSpeed: 0,
      targetSpeed: 0,
      rangeM: null,
    }
  }

  const pPos = vec(frame.pursuer.position_m)
  const tPos = vec(frame.target.position_m)
  const pVel = vec(frame.pursuer.velocity_m_s)
  const tVel = vec(frame.target.velocity_m_s)
  const los = sub(tPos, pPos)
  const relVel = sub(tVel, pVel)
  const range = Math.hypot(los.x, los.y, los.z) || 1
  const closing = -(los.x * relVel.x + los.y * relVel.y + los.z * relVel.z) / range
  const losCross = cross(los, relVel)
  const relMag = hypot3(relVel) || 1
  const miss = hypot3(losCross) / relMag
  const losRate = hypot3(losCross) / (range * range)
  const tgo = closing > 1 ? range / closing : 0

  let accelMag = 0
  if (frame.pursuer_accel_achieved_m_s2) {
    const a = vec(frame.pursuer_accel_achieved_m_s2)
    accelMag = Math.hypot(a.x, a.y, a.z)
  } else if (previousFrame) {
    const dt = frame.time_s - previousFrame.time_s || 0.05
    const prevVel = vec(previousFrame.pursuer.velocity_m_s)
    accelMag = Math.hypot(
      (pVel.x - prevVel.x) / dt,
      (pVel.y - prevVel.y) / dt,
      (pVel.z - prevVel.z) / dt,
    )
  }
  const gLoad = accelMag / G0
  const gFrac = Math.min(gLoad / gLimit, 1)
  const pk = Math.max(
    0,
    Math.min(
      99.4,
      100 * (1 - Math.min(miss / 40, 1)) * (0.55 + 0.45 * (1 - range / 6000)),
    ),
  )

  let alert = null
  if (range < 260) alert = { text: 'INTERCEPT LOCK · TERMINAL', color: '#ff5238' }
  else if (gFrac > 0.8)
    alert = { text: 'G-LIMIT 82% · COMMAND SATURATED', color: '#ff5238' }

  const interceptorSpeed = hypot3(pVel)
  const targetSpeed = hypot3(tVel)

  return {
    clock: `+${num(frame.time_s, 2)}s`,
    rangeTxt:
      range >= 1000 ? `${num(range / 1000, 3)} km` : `${num(range, 0)} m`,
    closingTxt: `${num(closing, 0)} m/s`,
    tgoTxt: `${num(tgo, 2)} s`,
    gLoad,
    gTxt: `${num(gLoad, 1)} G`,
    gFrac,
    gColor: gFrac > 0.8 ? '#ff5238' : '#f4f5f7',
    gPct: `${gFrac * 100}%`,
    altI: num(pPos.z, 0),
    spdI: num(interceptorSpeed, 0),
    altT: num(tPos.z, 0),
    spdT: num(targetSpeed, 0),
    pk,
    pkTxt: `${num(pk, 1)}%`,
    pkColor: pk > 90 ? '#62d3a4' : '#f4f5f7',
    missTxt:
      streamResult?.closest_approach_m != null
        ? `${num(streamResult.closest_approach_m, 1)} m`
        : `${num(miss, 1)} m`,
    losTxt: `${num(losRate * 1000, 2)} mrad/s`,
    alert,
    interceptorSpeed,
    targetSpeed,
    rangeM: range,
  }
}

export { G_LIMIT, num }
