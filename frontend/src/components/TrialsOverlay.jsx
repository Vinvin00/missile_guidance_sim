import { useSimulationStore } from '../store/useSimulationStore'

export function TrialsOverlay({ onTrialCountChange }) {
  const trialSet = useSimulationStore((state) => state.trialSet)
  const trialCount = useSimulationStore((state) => state.trialCount)
  const setTrialCount = useSimulationStore((state) => state.setTrialCount)
  const trials = trialSet?.trials ?? []
  const successes = trials.filter((trial) => trial.success).length
  const misses = trials
    .map((trial) => {
      const last = trial.frames?.at(-1)
      return last?.range_m
    })
    .filter((value) => value != null)
  const meanMiss =
    misses.length > 0
      ? misses.reduce((a, b) => a + b, 0) / misses.length
      : null
  const sorted = [...misses].sort((a, b) => a - b)
  const p95 =
    sorted.length > 0
      ? sorted[Math.min(sorted.length - 1, Math.floor(sorted.length * 0.95))]
      : null

  return (
    <div className="trials-overlay" aria-label="Trial overlay">
      <section className="glass-panel trials-summary">
        <span className="panel-kicker">TRIAL OVERLAY</span>
        <span className="clock-readout trials-count">
          {trials.length ? successes : '—'}
          <span className="is-muted">
            /{trials.length || trialCount}
          </span>
        </span>
        <span className="pk-label">MOCK INTERCEPTS</span>
        <div className="panel-rule" />
        <div className="trial-legend-list">
          <div>
            <span className="trial-line intercept" />
            <span>INTERCEPT</span>
          </div>
          <div>
            <span className="trial-line miss" />
            <span>MISS</span>
          </div>
        </div>
        <span className="muted-mono">OPACITY BY EPISODE INDEX</span>
        <label className="trial-count-hud">
          <span>MOCK EPISODES</span>
          <select
            value={trialCount}
            aria-label="Mock episodes"
            onChange={(event) => {
              const nextCount = Number(event.target.value)
              setTrialCount(nextCount)
              onTrialCountChange?.(nextCount)
            }}
          >
            <option value="20">20</option>
            <option value="30">30</option>
            <option value="50">50</option>
          </select>
        </label>
      </section>

      <section className="glass-panel trials-dispersion">
        <span className="panel-kicker">DISPERSION</span>
        <div className="metric-stack">
          <div className="metric-row">
            <span>MEAN MISS</span>
            <strong>
              {meanMiss == null ? '—' : `${meanMiss.toFixed(1)} m`}
            </strong>
          </div>
          <div className="metric-row">
            <span>P95 MISS</span>
            <strong>{p95 == null ? '—' : `${p95.toFixed(1)} m`}</strong>
          </div>
          <div className="metric-row">
            <span>EPISODES</span>
            <strong>{trials.length || trialCount}</strong>
          </div>
        </div>
      </section>
    </div>
  )
}
