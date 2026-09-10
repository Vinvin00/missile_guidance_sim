export function summarizeTrainingLog(entries, windowSize = 10) {
  const ordered = [...entries].sort((a, b) => a.episode - b.episode)
  const last = ordered.at(-1)
  const recent = ordered.slice(-windowSize)
  const rewards = ordered.map((entry) => entry.reward)
  const minReward = rewards.length ? Math.min(...rewards) : 0
  const maxReward = rewards.length ? Math.max(...rewards) : 1
  const range = Math.max(maxReward - minReward, 1)

  return {
    episodeCount: ordered.length,
    latestEpisode: last?.episode ?? 0,
    latestReward: last?.reward ?? 0,
    rollingSuccessRate:
      recent.length === 0
        ? 0
        : recent.filter((entry) => entry.success).length / recent.length,
    points: ordered.map((entry) => ({
      ...entry,
      x: ((entry.episode - ordered[0].episode) / Math.max(ordered.length - 1, 1)) * 100,
      y: 100 - ((entry.reward - minReward) / range) * 100,
    })),
  }
}
