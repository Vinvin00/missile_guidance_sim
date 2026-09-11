export async function loadTrainingLog(
  source = '/mock/training-log.json',
) {
  // Isolated swap point: replace this fetch with a real training-loop log.
  const response = await fetch(source)
  if (!response.ok) {
    throw new Error(`Training log request failed (${response.status}).`)
  }
  const entries = await response.json()
  if (
    !Array.isArray(entries) ||
    entries.some(
      (entry) =>
        !Number.isInteger(entry.episode) ||
        !Number.isFinite(entry.reward) ||
        typeof entry.success !== 'boolean',
    )
  ) {
    throw new Error('Unsupported training log format.')
  }
  return entries
}
