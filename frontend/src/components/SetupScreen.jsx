import { LiveParameterControls } from './LiveParameterControls'
import { useSimulationStore } from '../store/useSimulationStore'

function formatParameter(parameter) {
  const digits = parameter.value >= 100 ? 0 : 3
  return `${parameter.value.toLocaleString(undefined, {
    maximumFractionDigits: digits,
  })} ${parameter.unit}`
}

function profileRows(profile) {
  const order = [
    'mass',
    'reference_area',
    'drag_coefficient',
    'max_normal_force_coefficient',
    'maneuver_limit',
  ]
  const labels = {
    mass: 'MASS',
    reference_area: 'REFERENCE AREA',
    drag_coefficient: 'DRAG COEFFICIENT',
    max_normal_force_coefficient: 'MAX NORMAL FORCE Cn',
    maneuver_limit: 'MANEUVER LIMIT',
  }
  return order
    .filter((key) => profile.parameters[key])
    .map((key) => ({
      k: labels[key],
      v: formatParameter(profile.parameters[key]),
    }))
}

export function SetupScreen({ onRun }) {
  const catalog = useSimulationStore((state) => state.catalog)
  const selectedScenarioId = useSimulationStore(
    (state) => state.selectedScenarioId,
  )
  const selectedGuidanceLaw = useSimulationStore(
    (state) => state.selectedGuidanceLaw,
  )
  const selectScenario = useSimulationStore((state) => state.selectScenario)
  const selectGuidanceLaw = useSimulationStore(
    (state) => state.selectGuidanceLaw,
  )
  const streamStatus = useSimulationStore((state) => state.streamStatus)
  const error = useSimulationStore((state) => state.error)
  const busy = streamStatus === 'connecting' || streamStatus === 'streaming'

  return (
    <div className="setup-screen" aria-label="Scenario setup">
      <div className="setup-grid">
        <div className="setup-main">
          <div className="setup-block">
            <span className="panel-kicker">SCENARIO</span>
            {(catalog?.scenarios ?? []).map((scenario) => {
              const active = scenario.id === selectedScenarioId
              return (
                <button
                  key={scenario.id}
                  type="button"
                  className={active ? 'scenario-row is-active' : 'scenario-row'}
                  onClick={() => selectScenario(scenario.id)}
                  disabled={!catalog || busy}
                >
                  <span className="scenario-copy">
                    <span className="scenario-title">
                      <span className={active ? 'law-dot is-hot' : 'law-dot'} />
                      <span>{scenario.label.toUpperCase()}</span>
                    </span>
                    <span className="scenario-desc">{scenario.description}</span>
                  </span>
                </button>
              )
            })}
          </div>

          <div className="setup-block">
            <span className="panel-kicker">GUIDANCE LAW</span>
            <div className="law-grid">
              {(catalog?.guidance_laws ?? []).map((law) => {
                const active = law.id === selectedGuidanceLaw
                return (
                  <button
                    key={law.id}
                    type="button"
                    className={active ? 'law-card is-active' : 'law-card'}
                    onClick={() => selectGuidanceLaw(law.id)}
                    disabled={!catalog || busy}
                  >
                    <span className="law-code">{law.id.toUpperCase()}</span>
                    <span className="law-label">{law.label}</span>
                    <span className="law-desc">{law.description}</span>
                  </button>
                )
              })}
            </div>
          </div>

          <LiveParameterControls />

          <button
            className="run-preview"
            type="button"
            onClick={onRun}
            disabled={!catalog || busy}
          >
            {busy ? 'RECEIVING…' : 'RUN LIVE ENGAGEMENT'}
          </button>
          {error && <p className="error-message">{error}</p>}
        </div>

        <div className="setup-side">
          <span className="panel-kicker">VEHICLE PROFILES</span>
          {(catalog?.vehicle_profiles ?? []).map((profile) => (
            <div className="profile-block" key={profile.name}>
              <div className="profile-head">
                <span>{profile.name.toUpperCase()}</span>
                <span>{profile.role.toUpperCase()}</span>
              </div>
              <div className="profile-rows">
                {profileRows(profile).map((row) => (
                  <div key={row.k} className="metric-row">
                    <span>{row.k}</span>
                    <strong>{row.v}</strong>
                  </div>
                ))}
              </div>
            </div>
          ))}
          <p className="setup-note">
            Values are synthesized from public reference ranges. Target B is a
            fighter/attack-aircraft class surrogate (speed aligned with its
            mass/area/g-limit). Every run is simulated live: PN/APN/OGL are
            classical laws, RL runs the frozen baseline checkpoint. Engagement
            sliders set the initial geometry.
          </p>
        </div>
      </div>
    </div>
  )
}
