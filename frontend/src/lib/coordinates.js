export const METRES_PER_SCENE_UNIT = 1000

/**
 * Convert simulation coordinates (z-up, metres) to Three coordinates
 * (y-up, kilometres) while centering the horizontal engagement.
 */
export function toScenePoint(position, horizontalOrigin = { x: 0, y: 0 }) {
  return [
    (position.x - horizontalOrigin.x) / METRES_PER_SCENE_UNIT,
    position.z / METRES_PER_SCENE_UNIT,
    -(position.y - horizontalOrigin.y) / METRES_PER_SCENE_UNIT,
  ]
}

export function engagementOrigin(firstFrame) {
  if (!firstFrame) return { x: 0, y: 0 }
  return {
    x:
      (firstFrame.pursuer.position_m.x + firstFrame.target.position_m.x) /
      2,
    y:
      (firstFrame.pursuer.position_m.y + firstFrame.target.position_m.y) /
      2,
  }
}
