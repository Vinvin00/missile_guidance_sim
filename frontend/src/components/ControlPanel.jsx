import { LiveParameterControls } from './LiveParameterControls'
import { SessionReplayPanel } from './SessionReplayPanel'
import { ViewModeToggle } from './ViewModeToggle'
import { useSimulationStore } from '../store/useSimulationStore'

function formatParameter(parameter) {
  const digits = parameter.value >= 100 ? 0 : 3
  return `${parameter.value.toLocaleString(undefined, {
    maximumFractionDigits: digits,
  })} ${parameter.unit}`
}

export function ControlPanel({ onRun, onReplay, onTrialCountChange }) {
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
  const selectedScenario = catalog?.scenarios.find(
    (scenario) => scenario.id === selectedScenarioId,
  )
  const selectedLaw = catalog?.guidance_laws.find(
    (law) => law.id === selectedGuidanceLaw,
  )

  return (
    <aside className="control-panel" aria-label="Simulation controls">
      <div className="panel-heading">
        <span className="eyebrow">Engagement setup</span>
        <span className={`status-dot status-${streamStatus}`}>
          {streamStatus}
        </span>
      </div>

      <label className="field-label" htmlFor="scenario-select">
        Scenario
      </label>
      <select
        id="scenario-select"
        value={selectedScenarioId}
        onChange={(event) => selectScenario(event.target.value)}
        disabled={!catalog || busy}
      >
        {catalog?.scenarios.map((scenario) => (
          <option key={scenario.id} value={scenario.id}>
            {scenario.label}
          </option>
        ))}
      </select>
      {selectedScenario && (
        <div className="selection-detail">
          <span>{selectedScenario.description}</span>
          <small>
            {(selectedScenario.initial_range_m / 1000).toFixed(1)} km range ·{' '}
            {(selectedScenario.altitude_m / 1000).toFixed(1)} km altitude
          </small>
        </div>
      )}

      <label className="field-label" htmlFor="guidance-select">
        Guidance law
      </label>
      <select
        id="guidance-select"
        value={selectedGuidanceLaw}
        onChange={(event) => selectGuidanceLaw(event.target.value)}
        disabled={!catalog || busy}
      >
        {catalog?.guidance_laws.map((law) => (
          <option key={law.id} value={law.id}>
            {law.label}
          </option>
        ))}
      </select>
      {selectedLaw && (
        <div className="selection-detail">
          <span>{selectedLaw.description}</span>
        </div>
      )}

      <LiveParameterControls />
      <ViewModeToggle onTrialCountChange={onTrialCountChange} />

      <button
        className="run-button"
        type="button"
        onClick={onRun}
        disabled={!catalog || busy}
      >
        {busy ? 'Receiving trajectory…' : 'Run synthetic preview'}
      </button>

      {error && <p className="error-message">{error}</p>}

      <SessionReplayPanel onReplay={onReplay} disabled={busy} />

      <div className="source-note">
        <strong>Synthetic stream</strong>
        <span>
          The transport and playback contract is live; checkpoint evaluation
          remains intentionally disconnected.
        </span>
      </div>

      <div className="profiles">
        {catalog?.vehicle_profiles.map((profile) => (
          <section className="profile-card" key={profile.name}>
            <div>
              <span>{profile.role}</span>
              <h2>{profile.name}</h2>
            </div>
            <dl>
              {['mass', 'maneuver_limit'].map((key) => (
                <div key={key}>
                  <dt>{key.replace('_', ' ')}</dt>
                  <dd>{formatParameter(profile.parameters[key])}</dd>
                </div>
              ))}
            </dl>
          </section>
        ))}
      </div>
    </aside>
  )
}
