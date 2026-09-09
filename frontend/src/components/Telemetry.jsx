import { useSimulationStore } from '../store/useSimulationStore'

function speed(vector) {
  if (!vector) return 0
  return Math.hypot(vector.x, vector.y, vector.z)
}

function metric(value, unit, digits = 0) {
  if (value == null) return '—'
  return `${value.toLocaleString(undefined, {
    maximumFractionDigits: digits,
  })} ${unit}`
}

export function Telemetry() {
  const frames = useSimulationStore((state) => state.frames)
  const cursor = useSimulationStore((state) => state.cursor)
  const streamResult = useSimulationStore((state) => state.streamResult)
  const frame = frames[cursor]

  const items = [
    ['Range', metric(frame?.range_m, 'm', 1)],
    ['Interceptor speed', metric(speed(frame?.pursuer.velocity_m_s), 'm/s')],
    ['Target speed', metric(speed(frame?.target.velocity_m_s), 'm/s')],
    ['Interceptor altitude', metric(frame?.pursuer.position_m.z, 'm')],
    ['Target altitude', metric(frame?.target.position_m.z, 'm')],
    [
      'Closest approach',
      metric(streamResult?.closest_approach_m, 'm', 1),
    ],
  ]

  return (
    <section className="telemetry" aria-label="Current trajectory telemetry">
      <div className="telemetry-heading">
        <span className="eyebrow">Live state</span>
        <span className="source-chip">synthetic</span>
      </div>
      <dl>
        {items.map(([label, value]) => (
          <div key={label}>
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
    </section>
  )
}
