import { useEffect, useMemo, useState } from 'react'

import { loadTrainingLog } from '../data/trainingData'
import { summarizeTrainingLog } from '../lib/trainingStats'

function rollingMeanPolyline(points, windowSize = 20) {
  if (!points.length) return ''
  return points
    .map((_, index) => {
      const slice = points.slice(Math.max(0, index - windowSize + 1), index + 1)
      const mean =
        slice.reduce((sum, point) => sum + point.reward, 0) / slice.length
      const minY = Math.min(...points.map((p) => p.reward))
      const maxY = Math.max(...points.map((p) => p.reward))
      const range = Math.max(maxY - minY, 1)
      const x = points[index].x * 4
      const y = 136 - ((mean - minY) / range) * 132
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')
}

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
  const rewardPoly = stats.points
    .map((point) => `${(point.x * 4).toFixed(1)},${(point.y * 1.36).toFixed(1)}`)
    .join(' ')
  const meanPoly = useMemo(
    () => rollingMeanPolyline(stats.points),
    [stats.points],
  )
  const meanMissValues = entries
    .map((entry) => entry.miss_m ?? entry.miss)
    .filter((value) => typeof value === 'number')
  const meanMiss =
    meanMissValues.length > 0
      ? meanMissValues.reduce((a, b) => a + b, 0) / meanMissValues.length
      : null

  const metrics = [
    { k: 'EPISODES', v: stats.episodeCount.toLocaleString() },
    { k: 'LATEST REWARD', v: stats.latestReward.toFixed(0) },
    {
      k: 'ROLLING SUCCESS',
      v: `${Math.round(stats.rollingSuccessRate * 100)}%`,
    },
    {
      k: 'MEAN MISS',
      v: meanMiss == null ? '—' : `${meanMiss.toFixed(1)} m`,
    },
  ]

  return (
    <div className="train-screen" aria-label="Training dashboard">
      <div className="train-inner">
        <div className="train-metrics">
          {metrics.map((metric) => (
            <div key={metric.k}>
              <span className="panel-kicker">{metric.k}</span>
              <strong>{metric.v}</strong>
            </div>
          ))}
        </div>

        <figure className="reward-chart">
          <div className="reward-head">
            <span className="panel-kicker">REWARD PER EPISODE</span>
            <span className="muted-mono">MOCK LOG</span>
          </div>
          <svg
            viewBox="0 0 400 140"
            preserveAspectRatio="none"
            role="img"
            aria-label="Reward per episode"
          >
            <title>Mock reward-per-episode line</title>
            <polyline
              points={rewardPoly}
              fill="none"
              stroke="#f2f2f2"
              strokeWidth="1"
            />
            <polyline
              points={meanPoly}
              fill="none"
              stroke="#ff2d16"
              strokeWidth="1"
            />
          </svg>
          <figcaption>
            WHITE: EPISODE REWARD · RED: 20-EPISODE MEAN
          </figcaption>
        </figure>

        {error && <p className="error-message">{error}</p>}
        <p className="setup-note">
          Synthetic training history loaded through{' '}
          <code>loadTrainingLog()</code>. Swap that one function to point at a
          real episode log later. Do not read these curves as trained-policy
          results.
        </p>
      </div>
    </div>
  )
}
