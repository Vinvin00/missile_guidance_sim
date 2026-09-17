import { useEffect, useMemo, useState } from 'react'

import { loadTrainingLog } from '../data/trainingData'
import { summarizeTrainingLog } from '../lib/trainingStats'
import { useSimulationStore } from '../store/useSimulationStore'

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

const NO_ENTRIES = []

export function TrainingDashboard() {
  const [log, setLog] = useState(null)
  const [error, setError] = useState(null)
  const trainingPlayMode = useSimulationStore((state) => state.trainingPlayMode)
  const setTrainingPlayMode = useSimulationStore(
    (state) => state.setTrainingPlayMode,
  )
  const trialsLoading = useSimulationStore((state) => state.trialsLoading)
  const loadTrials = useSimulationStore((state) => state.loadTrials)

  useEffect(() => {
    let cancelled = false
    loadTrainingLog()
      .then((loaded) => {
        if (!cancelled) setLog(loaded)
      })
      .catch((loadError) => {
        if (!cancelled) setError(loadError.message)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const entries = log?.episodes ?? NO_ENTRIES
  const checkpoints = log?.checkpoints ?? []
  const finalEval = checkpoints.at(-1)
  const stats = summarizeTrainingLog(entries)
  const rewardPoly = stats.points
    .map((point) => `${(point.x * 4).toFixed(1)},${(point.y * 1.36).toFixed(1)}`)
    .join(' ')
  const meanPoly = useMemo(
    () => rollingMeanPolyline(stats.points),
    [stats.points],
  )

  const metrics = [
    { k: 'EPISODES', v: stats.episodeCount.toLocaleString() },
    { k: 'LATEST REWARD', v: stats.latestReward.toFixed(0) },
    {
      k: 'ROLLING SUCCESS',
      v: `${Math.round(stats.rollingSuccessRate * 100)}%`,
    },
    {
      k: 'FINAL EVAL HITS',
      v: finalEval ? `${finalEval.hits}/${finalEval.cases}` : '—',
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

        <div className="reward-head">
          <div className="reward-head-left">
            <span className="panel-kicker">
              {trialsLoading ? (
                <>
                  <span className="spinner" /> RUNNING RL ROLLOUTS…
                </>
              ) : (
                'ROLLOUT VIEW'
              )}
            </span>
            <button
              type="button"
              className="rerun-button rerun-button-compact"
              onClick={() => loadTrials()}
              disabled={trialsLoading}
            >
              {trialsLoading ? 'RUNNING…' : 'RE-RUN ROLLOUTS'}
            </button>
          </div>
          <div className="projection-toggle" role="group" aria-label="Rollout view mode">
            <button
              type="button"
              aria-pressed={trainingPlayMode === 'all'}
              className={trainingPlayMode === 'all' ? 'is-active' : ''}
              onClick={() => setTrainingPlayMode('all')}
            >
              ALL AT ONCE
            </button>
            <button
              type="button"
              aria-pressed={trainingPlayMode === 'sequential'}
              className={trainingPlayMode === 'sequential' ? 'is-active' : ''}
              onClick={() => setTrainingPlayMode('sequential')}
            >
              ONE BY ONE · 4X
            </button>
          </div>
        </div>

        <figure className="reward-chart">
          <div className="reward-head">
            <span className="panel-kicker">REWARD PER EPISODE</span>
            <span className="muted-mono">
              {log ? (
                log.branch_name.toUpperCase()
              ) : (
                <>
                  <span className="spinner" /> LOADING…
                </>
              )}
            </span>
          </div>
          <svg
            viewBox="0 0 400 140"
            preserveAspectRatio="none"
            role="img"
            aria-label="Reward per episode"
          >
            <title>Training reward-per-episode line</title>
            <polyline
              points={rewardPoly}
              fill="none"
              stroke="#cfd4db"
              strokeWidth="1.2"
            />
            <polyline
              points={meanPoly}
              fill="none"
              stroke="#ff5238"
              strokeWidth="1.8"
            />
          </svg>
          <figcaption>
            <span className="chart-key is-episode">Episode reward</span>
            <span className="chart-key is-mean">20-episode mean</span>
          </figcaption>
        </figure>

        <div className="profile-rows">
          <span className="panel-kicker">FIXED EVAL PER CHECKPOINT</span>
          {checkpoints.map((cp) => (
            <div key={cp.checkpoint} className="metric-row">
              <span>
                CP{String(cp.checkpoint).padStart(2, '0')} ·{' '}
                {(cp.timesteps / 1000).toFixed(0)}K STEPS
              </span>
              <strong>
                {cp.hits}/{cp.cases} HITS · MEDIAN MISS{' '}
                {cp.median_miss_m.toFixed(1)} M
              </strong>
            </div>
          ))}
        </div>

        {error && <p className="error-message">{error}</p>}
        {log && (
          <p className="setup-note">
            Real PPO training episodes and fixed 9-case evaluations for{' '}
            <code>{log.model_path}</code>, the checkpoint the RL guidance law
            and trials overlay fly.
          </p>
        )}
      </div>
    </div>
  )
}
