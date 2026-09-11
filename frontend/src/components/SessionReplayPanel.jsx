const MOCK_SESSIONS = [
  {
    id: 'SESS-0412 · PN · CROSSING',
    detail: 'Recorded 09-08 14:22 · 201 frames',
    outcome: 'INTERCEPT',
    miss: '3.2 m',
  },
  {
    id: 'SESS-0411 · APN · EVASIVE',
    detail: 'Recorded 09-08 13:57 · 241 frames',
    outcome: 'INTERCEPT',
    miss: '2.1 m',
  },
  {
    id: 'SESS-0409 · PN · EVASIVE',
    detail: 'Recorded 09-07 18:04 · 241 frames',
    outcome: 'MISS',
    miss: '38.7 m',
  },
]

export function SessionReplayPanel({ onReplay, disabled }) {
  return (
    <div className="replay-screen" aria-labelledby="session-replay-title">
      <div className="replay-inner">
        <div className="replay-intro">
          <span className="panel-kicker" id="session-replay-title">
            LAST SESSION
          </span>
          <p>
            Load a saved JSON trajectory into the viewer and playback controls.
            The built-in sample is synthetic; a real RL log uses the same
            schema.
          </p>
          <span className="source-chip">mock log</span>
        </div>

        <div className="session-list">
          {MOCK_SESSIONS.map((session) => (
            <button
              key={session.id}
              type="button"
              className="session-row"
              disabled={disabled}
              onClick={() => onReplay()}
            >
              <span className="session-copy">
                <span className="session-id">{session.id}</span>
                <span className="session-detail">{session.detail}</span>
              </span>
              <span
                className={
                  session.outcome === 'INTERCEPT'
                    ? 'session-outcome'
                    : 'session-outcome is-miss'
                }
              >
                {session.outcome}
              </span>
              <span className="session-miss">{session.miss}</span>
            </button>
          ))}
        </div>

        <div className="session-actions">
          <label className="file-input">
            LOAD JSON FILE
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
          <button
            type="button"
            onClick={() => onReplay()}
            disabled={disabled}
          >
            Load mock session
          </button>
        </div>
      </div>
    </div>
  )
}
