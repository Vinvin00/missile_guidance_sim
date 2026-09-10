export function SessionReplayPanel({ onReplay, disabled }) {
  return (
    <section className="session-replay" aria-labelledby="session-replay-title">
      <div className="section-heading">
        <span className="eyebrow" id="session-replay-title">
          Last session
        </span>
        <span className="source-chip">mock log</span>
      </div>
      <p>
        Load a saved JSON trajectory into the existing viewer and playback
        controls. The built-in sample is synthetic; a real RL log can use
        the same schema later.
      </p>
      <div className="session-replay-actions">
        <button
          type="button"
          onClick={() => onReplay()}
          disabled={disabled}
        >
          Load mock session
        </button>
        <label className="file-input">
          Load JSON file
          <input
            type="file"
            accept="application/json,.json"
            aria-label="Load JSON file"
            disabled={disabled}
            onChange={(event) => {
              const file = event.target.files?.[0]
              if (file) onReplay(file)
              event.target.value = ''
            }}
          />
        </label>
      </div>
    </section>
  )
}
