export function trialAppearance(trial, index, total) {
  const progress = total <= 1 ? 1 : index / (total - 1)
  return {
    color: trial.success ? '#7dffb3' : '#ff8aa8',
    opacity: 0.12 + progress * 0.78,
    lineWidth: trial.success ? 1.6 : 1.1,
  }
}
