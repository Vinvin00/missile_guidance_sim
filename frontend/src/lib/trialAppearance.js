export function trialAppearance(trial, index, total) {
  const progress = total <= 1 ? 1 : index / (total - 1)
  return {
    color: trial.success ? '#f2f2f2' : '#ff2d16',
    opacity: 0.1 + progress * 0.35,
    lineWidth: trial.success ? 1.4 : 1.1,
  }
}
