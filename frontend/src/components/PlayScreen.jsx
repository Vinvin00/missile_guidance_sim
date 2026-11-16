import { useCallback, useEffect, useRef, useState } from 'react'

import { usePlaybackClock } from '../hooks/usePlaybackClock'
import { websocketUrl } from '../hooks/useTrajectoryStream'
import { useSimulationStore } from '../store/useSimulationStore'
import { SimulationScene } from './SimulationScene'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

// key -> [stick axis, sign]. turn > 0 is left, pull > 0 is climb (server convention).
const KEYS = {
  ArrowLeft: ['turn', 1], a: ['turn', 1],
  ArrowRight: ['turn', -1], d: ['turn', -1],
  ArrowUp: ['pull', 1], w: ['pull', 1],
  ArrowDown: ['pull', -1], s: ['pull', -1],
}
const PAD = [
  ['ArrowUp', 'Climb', '↑'],
  ['ArrowLeft', 'Turn left', '←'],
  ['ArrowRight', 'Turn right', '→'],
  ['ArrowDown', 'Dive', '↓'],
]
const RADAR_RANGE_M = 7500

const HEADLINE = {
  caught: 'The model caught you',
  escaped: 'You got away',
  crashed: 'You hit the ground',
}

function Radar({ frame }) {
  const v = frame.target.velocity_m_s
  const heading = Math.atan2(v.y, v.x)
  const dx = frame.pursuer.position_m.x - frame.target.position_m.x
  const dy = frame.pursuer.position_m.y - frame.target.position_m.y
  const ahead = dx * Math.cos(heading) + dy * Math.sin(heading)
  const left = -dx * Math.sin(heading) + dy * Math.cos(heading)
  const k = 45 / Math.max(RADAR_RANGE_M, Math.hypot(ahead, left))
  const dz = frame.pursuer.position_m.z - frame.target.position_m.z
  return (
    <figure className="play-radar">
      <svg viewBox="0 0 100 100" role="img" aria-label="Radar: you are in the centre, facing up">
        <circle cx="50" cy="50" r="45" className="radar-field" />
        <circle cx="50" cy="50" r="30" className="radar-ring" />
        <circle cx="50" cy="50" r="15" className="radar-ring" />
        <path d="M50 44 L54 55 L50 52 L46 55 Z" className="radar-you" />
        <circle cx={50 - left * k} cy={50 - ahead * k} r="3.2" className="radar-threat" />
      </svg>
      <figcaption>
        Interceptor {Math.abs(dz) < 50 ? 'level with you' : `${Math.abs(dz).toFixed(0)} m ${dz > 0 ? 'above' : 'below'}`}
      </figcaption>
    </figure>
  )
}

export function PlayScreen() {
  const [phase, setPhase] = useState('idle') // idle | connecting | countdown | flying | done | error
  const [count, setCount] = useState(3)
  const [result, setResult] = useState(null)
  const [stats, setStats] = useState(null)
  const [message, setMessage] = useState('')
  const socketRef = useRef(null)
  const heldRef = useRef(new Set())
  const phaseRef = useRef(phase)
  const frame = useSimulationStore((state) => state.frames[state.cursor])
  usePlaybackClock()

  useEffect(() => {
    phaseRef.current = phase
  }, [phase])

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/play/stats`)
      .then((response) => (response.ok ? response.json() : null))
      .then(setStats)
      .catch(() => {})
    return () => {
      socketRef.current?.close(1000)
      useSimulationStore.getState().endLiveRound()
    }
  }, [])

  const press = useCallback((key, down) => {
    if (!KEYS[key]) return false
    heldRef.current[down ? 'add' : 'delete'](key)
    const stick = { turn: 0, pull: 0 }
    for (const held of heldRef.current) stick[KEYS[held][0]] += KEYS[held][1]
    if (phaseRef.current === 'flying' && socketRef.current?.readyState === 1) {
      socketRef.current.send(JSON.stringify(stick))
    }
    return true
  }, [])

  useEffect(() => {
    const handler = (event) => {
      const key = event.key.length === 1 ? event.key.toLowerCase() : event.key
      if (press(key, event.type === 'keydown')) event.preventDefault()
    }
    const release = () => {
      for (const key of [...heldRef.current]) press(key, false)
    }
    window.addEventListener('keydown', handler)
    window.addEventListener('keyup', handler)
    window.addEventListener('blur', release)
    return () => {
      window.removeEventListener('keydown', handler)
      window.removeEventListener('keyup', handler)
      window.removeEventListener('blur', release)
    }
  }, [press])

  // Countdown, then any message starts the server clock.
  useEffect(() => {
    if (phase !== 'countdown') return undefined
    const timer = setTimeout(() => {
      if (count > 1) {
        setCount(count - 1)
        return
      }
      socketRef.current?.send('{}')
      setPhase('flying')
    }, 1000)
    return () => clearTimeout(timer)
  }, [phase, count])

  const start = useCallback(() => {
    socketRef.current?.close(1000)
    heldRef.current.clear()
    setResult(null)
    setPhase('connecting')
    const socket = new WebSocket(websocketUrl('/ws/play'))
    socketRef.current = socket
    const store = useSimulationStore.getState()
    socket.onmessage = (event) => {
      if (socket !== socketRef.current) return
      const data = JSON.parse(event.data)
      if (data.type === 'play.ready') {
        store.beginLiveRound(data.frame)
        setCount(3)
        setPhase('countdown')
      } else if (data.type === 'trajectory.frame') {
        store.appendLiveFrame(data)
      } else if (data.type === 'play.completed') {
        store.endLiveRound()
        setResult(data)
        setStats(data.stats)
        setPhase('done')
      } else {
        setMessage(data.detail ?? 'The server sent something unexpected.')
        setPhase('error')
      }
    }
    socket.onclose = () => {
      if (socket !== socketRef.current || phaseRef.current === 'done' || phaseRef.current === 'error') return
      store.endLiveRound()
      setMessage('Lost the connection to the simulation server.')
      setPhase('error')
    }
  }, [])

  const flying = phase === 'flying' || phase === 'countdown'

  return (
    <main className="play-shell" data-phase={phase}>
      <div className="play-scene">
        <SimulationScene />
      </div>
      <header className="play-bar">
        <a href="#">← Outfly</a>
        <span>You are the target</span>
        <a href="#lab">Open the lab</a>
      </header>

      {frame && phase !== 'idle' && (
        <>
          <dl className="play-readout">
            <div>
              <dt>Time</dt>
              <dd>{frame.time_s.toFixed(1)} s</dd>
            </div>
            <div>
              <dt>Interceptor range</dt>
              <dd>{(frame.range_m / 1000).toFixed(2)} km</dd>
            </div>
          </dl>
          <Radar frame={frame} />
        </>
      )}

      {flying && (
        <div className="play-pad" aria-label="Flight controls">
          {PAD.map(([key, label, glyph]) => (
            <button
              key={key}
              type="button"
              aria-label={label}
              data-key={key}
              onPointerDown={(event) => {
                event.currentTarget.setPointerCapture(event.pointerId)
                press(key, true)
              }}
              onPointerUp={() => press(key, false)}
              onPointerCancel={() => press(key, false)}
              onContextMenu={(event) => event.preventDefault()}
            >
              {glyph}
            </button>
          ))}
        </div>
      )}

      {phase === 'countdown' && (
        <p className="play-count" aria-live="assertive">
          {count}
        </p>
      )}

      {!flying && (
        <section className="play-card" aria-live="polite">
          {phase === 'done' && result ? (
            <>
              <h1>{HEADLINE[result.outcome]}</h1>
              <p>
                {result.outcome === 'caught'
                  ? `Intercept after ${result.time_s.toFixed(1)} s. It passed within ${result.closest_approach_m.toFixed(1)} m of you; a hit is anything under 5 m.`
                  : `You lasted ${result.time_s.toFixed(1)} s and the closest it came was ${result.closest_approach_m.toFixed(1)} m.`}
              </p>
            </>
          ) : (
            <>
              <h1>Fly the target</h1>
              <p>
                A trained guidance model launches at you from 7 km. You pull up
                to 9 g; it pulls up to 25. Steer with the arrow keys or WASD, or
                the on-screen pad on a phone. Fly straight and it catches you.
                It can be beaten: timing is everything.
              </p>
            </>
          )}
          {phase === 'error' && <p role="alert" className="play-error">{message}</p>}
          {stats?.rounds > 0 && (
            <p className="play-stats">
              The model has caught the pilot in {stats.caught} of {stats.rounds} recorded rounds.
            </p>
          )}
          <div className="play-actions">
            <button type="button" className="play-go" disabled={phase === 'connecting'} onClick={start}>
              {phase === 'connecting' ? 'Waking the server…' : phase === 'done' ? 'Fly again' : 'Start round'}
            </button>
            {phase === 'done' && (
              <button type="button" onClick={() => useSimulationStore.getState().restartPlayback()}>
                Watch the replay
              </button>
            )}
          </div>
          <small>Each finished round is saved (stick inputs and outcome, nothing about you) to test and retrain the model.</small>
        </section>
      )}
    </main>
  )
}
