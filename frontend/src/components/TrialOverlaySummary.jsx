import { useSimulationStore } from '../store/useSimulationStore'

export function TrialOverlaySummary() {
  const trialSet = useSimulationStore((state) => state.trialSet)
  const trials = trialSet?.trials ?? []
  const successes = trials.filter((trial) => trial.success).length

  return (
    <div className="trial-overlay-summary">
      <div>
        <span className="trial-legend failed" />
        Miss
      </div>
      <div>
        <span className="trial-legend success" />
        Intercept
      </div>
      <strong>
        {trials.length
          ? `${successes}/${trials.length} mock successes`
          : 'Run a preview to generate mock trials'}
      </strong>
      <small>Opacity increases with episode index</small>
    </div>
  )
}
