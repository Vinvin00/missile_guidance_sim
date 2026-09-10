import { useMemo } from 'react'

import { useSimulationStore } from '../store/useSimulationStore'

function readableName(name) {
  return name.replaceAll('_', ' ')
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
      (catalog?.vehicle_profiles ?? []).flatMap((profile) =>
        Object.entries(profile.parameters)
          .filter(([, parameter]) => parameter.live_control)
          .map(([name, parameter]) => ({
            id: `${profile.role}.${name}`,
            label: `${profile.name} ${readableName(name)}`,
            ...parameter,
          })),
      ),
    [catalog],
  )

  if (!controls.length) return null

  return (
    <section className="live-parameters" aria-labelledby="live-parameters-title">
      <div className="live-head">
        <span className="panel-kicker" id="live-parameters-title">
          LIVE PARAMETERS
        </span>
        <span className="muted-mono">300 MS RESTREAM</span>
      </div>
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
