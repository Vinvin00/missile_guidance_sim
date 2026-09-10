import { useSimulationStore } from '../store/useSimulationStore'

export function ViewModeToggle({ onTrialCountChange }) {
  const viewMode = useSimulationStore((state) => state.viewMode)
  const setViewMode = useSimulationStore((state) => state.setViewMode)
  const trialCount = useSimulationStore((state) => state.trialCount)
  const setTrialCount = useSimulationStore((state) => state.setTrialCount)

  return (
    <section className="view-mode-control" aria-label="Trajectory view mode">
      <span className="field-label">View mode</span>
      <div className="segmented-control">
        <button
          type="button"
          aria-pressed={viewMode === 'single'}
          onClick={() => setViewMode('single')}
        >
          Single trajectory
        </button>
        <button
          type="button"
          aria-pressed={viewMode === 'trials'}
          onClick={() => setViewMode('trials')}
        >
          All trials
        </button>
      </div>
      {viewMode === 'trials' && (
        <label className="trial-count">
          <span>Mock episodes</span>
          <select
            value={trialCount}
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
      )}
    </section>
  )
}
