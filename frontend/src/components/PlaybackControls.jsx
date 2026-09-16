import { useSimulationStore } from '../store/useSimulationStore'

const RATES = [0.25, 0.5, 1, 2]

function formatTime(seconds) {
  return `${seconds.toFixed(2)}s`
}

export function PlaybackControls() {
  const frames = useSimulationStore((state) => state.frames)
  const cursor = useSimulationStore((state) => state.cursor)
  const isPlaying = useSimulationStore((state) => state.isPlaying)
  const playbackRate = useSimulationStore((state) => state.playbackRate)
  const seekToIndex = useSimulationStore((state) => state.seekToIndex)
  const togglePlayback = useSimulationStore((state) => state.togglePlayback)
  const restartPlayback = useSimulationStore(
    (state) => state.restartPlayback,
  )
  const setPlaybackRate = useSimulationStore(
    (state) => state.setPlaybackRate,
  )

  const currentTime = frames[cursor]?.time_s ?? 0
  const duration = frames.at(-1)?.time_s ?? 0
  const hasFrames = frames.length > 1
  const progress =
    duration > 0 ? `${(currentTime / duration) * 100}%` : '0%'

  return (
    <div className="playback-bar" aria-label="Trajectory playback">
      <div className="playback-buttons">
        <button
          type="button"
          onClick={togglePlayback}
          disabled={!hasFrames}
          aria-label={isPlaying ? 'Pause playback' : 'Play trajectory'}
        >
          <svg width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
            <path
              d={
                isPlaying
                  ? 'M3 2h2.6v9H3zM7.4 2H10v9H7.4z'
                  : 'M3 1.8 11 6.5 3 11.2z'
              }
              fill="currentColor"
            />
          </svg>
        </button>
        <button
          type="button"
          onClick={restartPlayback}
          disabled={!hasFrames}
          aria-label="Reset"
        >
          <svg width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
            <path
              d="M2 6.5a4.5 4.5 0 1 1 1.6 3.44"
              stroke="currentColor"
              strokeWidth="1.1"
            />
            <path
              d="M1 3.2v3.3h3.3"
              stroke="currentColor"
              strokeWidth="1.1"
            />
          </svg>
        </button>
      </div>

      <span className="time-readout">{formatTime(currentTime)}</span>

      <div className="scrub-track">
        <div className="scrub-base" />
        <div className="scrub-fill" style={{ width: progress }} />
        <div className="scrub-thumb" style={{ left: progress }} />
        <input
          type="range"
          min="0"
          max={Math.max(frames.length - 1, 0)}
          value={cursor}
          onChange={(event) => seekToIndex(Number(event.target.value))}
          disabled={!hasFrames}
          aria-label="Trajectory time"
        />
      </div>

      <span className="time-readout is-dim">{formatTime(duration)}</span>

      <div className="rate-group">
        <span>RATE</span>
        <div className="rate-buttons" role="group" aria-label="Playback rate">
          {RATES.map((rate) => (
            <button
              key={rate}
              type="button"
              className={rate === playbackRate ? 'is-active' : ''}
              onClick={() => setPlaybackRate(rate)}
              disabled={!hasFrames}
              aria-pressed={rate === playbackRate}
            >
              {rate}×
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
