import { useEffect, useState } from 'react'

import { loadTrainingLog } from '../data/trainingData'
import { summarizeTrainingLog } from '../lib/trainingStats'

export function TrainingDashboard() {
  const [entries, setEntries] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    loadTrainingLog()
      .then((loaded) => {
        if (!cancelled) setEntries(loaded)
      })
      .catch((loadError) => {
        if (!cancelled) setError(loadError.message)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const stats = summarizeTrainingLog(entries)
  const polyline = stats.points
    .map((point) => `${point.x},${point.y}`)
    .join(' ')

  return (
    <section className="training-dashboard" aria-label="Training dashboard">
      <div className="telemetry-heading">
        <span className="eyebrow">Training dashboard</span>
        <span className="source-chip">mock log</span>
      </div>
      <p className="source-note">
        <strong>Synthetic training history</strong>
        <span>
          Loaded through <code>loadTrainingLog()</code>. Swap that one
          function to point at a real episode log later.
        </span>
      </p>
      {error && <p className="error-message">{error}</p>}
      <dl className="training-metrics">
        <div>
          <dt>Episodes</dt>
          <dd>{stats.episodeCount}</dd>
        </div>
        <div>
          <dt>Latest reward</dt>
          <dd>{stats.latestReward.toFixed(0)}</dd>
        </div>
        <div>
          <dt>Rolling success</dt>
          <dd>{Math.round(stats.rollingSuccessRate * 100)}%</dd>
        </div>
      </dl>
      <figure className="reward-chart" aria-label="Reward per episode">
        <svg viewBox="0 0 100 100" role="img">
          <title>Mock reward-per-episode line</title>
          <polyline
            fill="none"
            stroke="#55d9ff"
            strokeWidth="1.8"
            points={polyline}
          />
        </svg>
        <figcaption>Reward vs episode · last 10 used for success rate</figcaption>
      </figure>
    </section>
  )
}
