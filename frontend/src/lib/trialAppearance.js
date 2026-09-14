// Monte Carlo trials have no ordering, so only the outcome drives styling; misses stand out.
export function trialAppearance(trial) {
  return {
    color: trial.success ? '#f4f5f7' : '#ff5238',
    opacity: trial.success ? 0.3 : 0.65,
    lineWidth: trial.success ? 1.2 : 1.4,
  }
}
