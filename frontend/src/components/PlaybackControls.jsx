import { useSimulationStore } from '../store/useSimulationStore'

function formatTime(seconds) {
  return `${seconds.toFixed(1)} s`
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

  return (
    <div className="playback-controls" aria-label="Trajectory playback">
      <div className="playback-buttons">
        <button
          type="button"
          onClick={restartPlayback}
          disabled={!hasFrames}
          aria-label="Restart playback"
        >
          ↺
        </button>
        <button
          className="play-pause"
          type="button"
          onClick={togglePlayback}
          disabled={!hasFrames}
          aria-label={isPlaying ? 'Pause playback' : 'Play trajectory'}
        >
          {isPlaying ? 'Ⅱ' : '▶'}
        </button>
      </div>

      <span className="time-readout">{formatTime(currentTime)}</span>
      <input
        className="timeline"
        type="range"
        min="0"
        max={Math.max(frames.length - 1, 0)}
        value={cursor}
        onChange={(event) => seekToIndex(Number(event.target.value))}
        disabled={!hasFrames}
        aria-label="Trajectory time"
      />
      <span className="time-readout">{formatTime(duration)}</span>

      <label className="rate-control">
        <span>Speed</span>
        <select
          value={playbackRate}
          onChange={(event) => setPlaybackRate(Number(event.target.value))}
          disabled={!hasFrames}
        >
          <option value="0.5">0.5×</option>
          <option value="1">1×</option>
          <option value="2">2×</option>
          <option value="4">4×</option>
        </select>
      </label>
    </div>
  )
}
