import { useMemo } from 'react'

import { useSimulationStore } from '../store/useSimulationStore'

// Bounds come from /api/catalog live_control flags. Marking mass/Cd/Cn
// live in the catalog is enough to surface those sliders later.

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
      <div className="section-heading">
        <span className="eyebrow" id="live-parameters-title">
          Live parameters
        </span>
        <small>300 ms restream</small>
      </div>
      {controls.map((control) => {
        const value = parameterValues[control.id] ?? control.value
        return (
          <label className="parameter-slider" key={control.id}>
            <span>
              <strong>{control.label}</strong>
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
              grounded range {control.reference_min.toLocaleString()}–
              {control.reference_max.toLocaleString()} {control.unit}
            </small>
          </label>
        )
      })}
    </section>
  )
}
