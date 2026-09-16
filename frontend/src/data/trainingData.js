// Real episode log + checkpoint evals of the run behind CURRENT_RL_BASELINE.json.
export async function loadTrainingLog(source = '/api/training') {
  const response = await fetch(
    `${import.meta.env.VITE_API_BASE_URL ?? ''}${source}`,
  )
  if (!response.ok) {
    throw new Error(`Training log request failed (${response.status}).`)
  }
  const log = await response.json()
  if (
    !Array.isArray(log?.episodes) ||
    !Array.isArray(log.checkpoints) ||
    log.episodes.some(
      (entry) =>
        !Number.isInteger(entry.episode) ||
        !Number.isFinite(entry.reward) ||
        typeof entry.success !== 'boolean',
    )
  ) {
    throw new Error('Unsupported training log format.')
  }
  return log
}
