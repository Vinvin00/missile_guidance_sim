import { useMemo } from 'react'

import {
  parameterGroups,
  useSimulationStore,
} from '../store/useSimulationStore'

function readableName(name) {
  return name.replaceAll('_', ' ')
}

// Plain-English explainer per control, for viewers unfamiliar with the sim.
const PARAMETER_HELP = {
  'engagement.initial_range': 'How far apart the interceptor and target start, measured along the line between them.',
  'engagement.lateral_offset': 'How far the target starts to the side of the interceptor, instead of directly ahead.',
  'engagement.altitude_delta': "How much higher or lower the target starts relative to the interceptor's altitude.",
  'engagement.target_heading': "The target's compass heading at the start. 180° flies straight at the interceptor; 90°/270° cross its path.",
  'engagement.target_maneuver_g': 'How hard the target turns to evade, in g-force. Higher values make it harder for the interceptor to hit.',
  'interceptor.speed': "The interceptor's starting speed.",
  'target.speed': "The target's starting speed.",
}

export function LiveParameterControls() {
  const catalog = useSimulationStore((state) => state.catalog)
  const parameterValues = useSimulationStore(
    (state) => state.parameterValues,
  )
  const setLiveParameter = useSimulationStore(
    (state) => state.setLiveParameter,
  )

  const controls = useMemo(
    () =>
      parameterGroups(catalog).flatMap((group) =>
        Object.entries(group.parameters)
          .filter(([, parameter]) => parameter.live_control)
          .map(([name, parameter]) => ({
            id: `${group.prefix}.${name}`,
            label: `${group.name} ${readableName(name)}`,
            ...parameter,
          })),
      ),
    [catalog],
  )

  if (!controls.length) return null

  // Straight-line interceptor→target distance at t=0 (range is along-track only).
  const separationParts = ['initial_range', 'lateral_offset', 'altitude_delta']
    .map((name) => controls.find((c) => c.id === `engagement.${name}`))
    .filter(Boolean)
    .map((c) => parameterValues[c.id] ?? c.value)
  const separationKm =
    separationParts.length === 3 ? Math.hypot(...separationParts) / 1000 : null

  return (
    <section className="live-parameters" aria-labelledby="live-parameters-title">
      <div className="live-head">
        <span className="panel-kicker" id="live-parameters-title">
          LIVE PARAMETERS
        </span>
        <span className="muted-mono">300 MS RESTREAM</span>
      </div>
      {separationKm != null && (
        <div className="metric-row">
          <span>INITIAL SEPARATION</span>
          <strong>{separationKm.toFixed(2)} KM</strong>
        </div>
      )}
      {controls.map((control) => {
        const value = parameterValues[control.id] ?? control.value
        return (
          <label className="parameter-slider" key={control.id}>
            <span className="parameter-top">
              <span>{control.label.toUpperCase()}</span>
              <output>
                {value.toLocaleString()} {control.unit}
              </output>
            </span>
            <input
              type="range"
              min={control.reference_min}
              max={control.reference_max}
              step={
                control.control_step ??
                (control.reference_max - control.reference_min) / 100
              }
              value={value}
              onChange={(event) =>
                setLiveParameter(control.id, Number(event.target.value))
              }
              aria-label={control.label}
            />
            {PARAMETER_HELP[control.id] && (
              <p className="parameter-help">{PARAMETER_HELP[control.id]}</p>
            )}
            <small>
              GROUNDED RANGE {control.reference_min.toLocaleString()}–
              {control.reference_max.toLocaleString()} {control.unit}
            </small>
          </label>
        )
      })}
    </section>
  )
}
