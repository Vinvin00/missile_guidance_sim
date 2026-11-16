import { useEffect, useRef, useState } from 'react'

import { usePlaybackClock } from '../hooks/usePlaybackClock'
import { useSimulationStore } from '../store/useSimulationStore'
import { SimulationScene } from './SimulationScene'
import './landing.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

// Held-out test hits (of 50) after each 204,800-step training checkpoint of the
// current baseline: outputs/evasive_zemtgo10_seed8/rl_checkpoint_0N_eval.json.
const CHECKPOINT_HITS = [11, 27, 21, 28, 38, 45, 43, 45]

const VIEWS = [
  { name: 'Fly the target', image: 'play', alt: 'Play mode: a red jet banking left with the interceptor closing from behind, a radar and time and range readouts', note: 'Mid-round. Radar top right, range top left.' },
  { name: 'After the round', image: 'play-result', alt: 'Play mode result card saying the model caught you, with the miss distance', note: 'The result, and the running tally against every pilot.' },
  { name: 'Lab: one run', image: 'lab', alt: 'Lab view: interceptor and target paths meeting over a valley, with mission clock and guidance panels', note: 'Pick a scenario and a guidance law, then scrub the replay.' },
  { name: 'Lab: thirty runs', image: 'trials', alt: 'Lab trials view: thirty interceptor paths overlaid in one scene', note: 'The trained model on thirty varied starts at once.' },
  { name: 'Lab: training', image: 'training', alt: 'Lab training view: episode results and checkpoint scores', note: 'How the score moved during training.' },
]

// A 2D toy of the classical baseline: proportional navigation chasing the pointer.
function ChaseDemo() {
  const canvasRef = useRef(null)
  const [score, setScore] = useState({ hits: 0, best: 0 })

  useEffect(() => {
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return undefined
    const css = getComputedStyle(canvas)
    const ink = css.getPropertyValue('--text').trim()
    const accent = css.getPropertyValue('--accent').trim()
    const soft = css.getPropertyValue('--text-dim').trim()
    const still = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    let size = 1
    const fit = () => {
      size = canvas.clientWidth
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      canvas.width = canvas.height = size * dpr
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    }
    fit()
    const observer = new ResizeObserver(fit)
    observer.observe(canvas)

    // Units: fractions of the square per second.
    const N = 4, TARGET_SPEED = 0.42, PURSUER_SPEED = 0.62, MAX_TURN = 2.6, HIT = 0.03
    const target = { x: 0.7, y: 0.3 }
    const pursuer = { x: 0.08, y: 0.92, heading: -0.8 }
    let pointer = null, los = null, alive = 0, hits = 0, best = 0, flash = 0, trail = []
    const track = (event) => {
      const box = canvas.getBoundingClientRect()
      pointer = { x: (event.clientX - box.left) / box.width, y: (event.clientY - box.top) / box.height }
    }
    const drop = () => { pointer = null }
    canvas.addEventListener('pointermove', track)
    canvas.addEventListener('pointerdown', track)
    canvas.addEventListener('pointerleave', drop)

    let frame, last = performance.now()
    const step = (now) => {
      const dt = Math.min((now - last) / 1000, 0.05)
      last = now
      if (!still || pointer) {
        alive += dt
        const goal = pointer ?? { x: 0.5 + 0.32 * Math.sin(now / 1700), y: 0.5 + 0.3 * Math.sin(now / 1100) }
        const gx = goal.x - target.x, gy = goal.y - target.y, gap = Math.hypot(gx, gy)
        if (gap > 1e-6) {
          const move = Math.min(gap, TARGET_SPEED * dt)
          target.x += (gx / gap) * move
          target.y += (gy / gap) * move
        }
        const dx = target.x - pursuer.x, dy = target.y - pursuer.y
        const angle = Math.atan2(dy, dx)
        const wrap = (a) => Math.atan2(Math.sin(a), Math.cos(a))
        // Proportional navigation: turn rate = N x line-of-sight rate.
        let rate = los === null || dt === 0 ? 0 : (N * wrap(angle - los)) / dt
        los = angle
        const off = wrap(angle - pursuer.heading)
        if (Math.abs(off) > Math.PI / 2) rate = Math.sign(off) * MAX_TURN // overshot: come about
        pursuer.heading += Math.max(-MAX_TURN, Math.min(MAX_TURN, rate)) * dt
        pursuer.x += Math.cos(pursuer.heading) * PURSUER_SPEED * dt
        pursuer.y += Math.sin(pursuer.heading) * PURSUER_SPEED * dt
        trail.push([pursuer.x, pursuer.y])
        if (trail.length > 80) trail.shift()
        if (Math.hypot(dx, dy) < HIT) {
          hits += 1
          best = Math.max(best, alive)
          alive = 0
          flash = 1
          pursuer.x = target.x < 0.5 ? 0.95 : 0.05
          pursuer.y = target.y < 0.5 ? 0.95 : 0.05
          pursuer.heading = Math.atan2(target.y - pursuer.y, target.x - pursuer.x)
          los = null
          trail = []
          setScore({ hits, best })
        }
      }
      flash = Math.max(0, flash - dt * 2.5)
      ctx.clearRect(0, 0, size, size)
      ctx.lineWidth = 2
      ctx.strokeStyle = ink
      ctx.beginPath()
      trail.forEach(([x, y], index) => ctx[index ? 'lineTo' : 'moveTo'](x * size, y * size))
      ctx.stroke()
      ctx.setLineDash([4, 6])
      ctx.strokeStyle = soft
      ctx.beginPath()
      ctx.moveTo(pursuer.x * size, pursuer.y * size)
      ctx.lineTo(target.x * size, target.y * size)
      ctx.stroke()
      ctx.setLineDash([])
      ctx.fillStyle = ink
      ctx.beginPath()
      ctx.arc(pursuer.x * size, pursuer.y * size, 5, 0, Math.PI * 2)
      ctx.fill()
      ctx.fillStyle = accent
      ctx.beginPath()
      ctx.arc(target.x * size, target.y * size, 9 + flash * 22, 0, Math.PI * 2)
      ctx.fill()
      frame = requestAnimationFrame(step)
    }
    frame = requestAnimationFrame(step)
    return () => {
      cancelAnimationFrame(frame)
      observer.disconnect()
      canvas.removeEventListener('pointermove', track)
      canvas.removeEventListener('pointerdown', track)
      canvas.removeEventListener('pointerleave', drop)
    }
  }, [])

  return (
    <div className="chase" data-ui>
      <canvas ref={canvasRef} aria-label="A dot chases your pointer using proportional navigation">
        A dot chases your pointer using proportional navigation.
      </canvas>
      <p>
        <span>Move your pointer here. The green dot is you.</span>
        <span>Caught {score.hits} {score.hits === 1 ? 'time' : 'times'}{score.best > 0 && `, longest run ${score.best.toFixed(1)} s`}</span>
      </p>
    </div>
  )
}

// The hero is the real 3D scene replaying one recorded round (public/landing/round.json:
// a scripted pilot against the frozen model). Until it loads, the stage is the scene's sky colour.
function HeroScene() {
  const stageRef = useRef(null)
  const [round, setRound] = useState(null)
  const [visible, setVisible] = useState(true)
  usePlaybackClock()

  useEffect(() => {
    const still = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const store = useSimulationStore
    let stopped = false
    let timer
    fetch('/landing/round.json')
      .then((response) => (response.ok ? response.json() : null))
      .then((data) => {
        if (stopped || !data?.frames?.length) return
        store.setState({
          // Reduced motion: one still frame from the middle of the round.
          frames: data.frames, cursor: still ? Math.floor(data.frames.length * 0.6) : 0,
          playheadS: 0, isPlaying: !still, playbackRate: 1,
          viewMode: 'single', cameraMode: 'target', liveFollow: true,
          streamStatus: 'ready', trialSet: null, error: null,
        })
        setRound(data)
      })
      .catch(() => {})
    // Loop: hold the last frame for a moment, then fly it again.
    const unsubscribe = store.subscribe((state, previous) => {
      if (!still && previous.isPlaying && !state.isPlaying && state.frames.length > 1) {
        timer = setTimeout(() => store.getState().restartPlayback(), 2500)
      }
    })
    const observer = new IntersectionObserver(([entry]) => setVisible(entry.isIntersecting))
    observer.observe(stageRef.current)
    return () => {
      stopped = true
      clearTimeout(timer)
      unsubscribe()
      observer.disconnect()
      store.setState({
        frames: [], cursor: 0, playheadS: 0, isPlaying: false,
        liveFollow: false, cameraMode: 'overview', streamStatus: 'idle',
      })
    }
  }, [])

  return (
    <div className="l-stage" ref={stageRef}>
      {/* ponytail: the scene is unmounted off-screen to spare the GPU; it reloads on return. */}
      {round && visible && (
        <div className="l-scene" data-ui role="img" aria-label="3D replay of a recorded round: the interceptor closing on a red jet over an alpine valley">
          <SimulationScene />
        </div>
      )}
      {round && <HeroReadout round={round} />}
    </div>
  )
}

function HeroReadout({ round }) {
  const frame = useSimulationStore((state) => state.frames[state.cursor])
  if (!frame) return null
  return (
    <dl className="l-live" data-ui>
      <div><dt>Recorded round</dt><dd>{frame.time_s.toFixed(1)} s</dd></div>
      <div><dt>Interceptor range</dt><dd>{(frame.range_m / 1000).toFixed(2)} km</dd></div>
      <p>A scripted pilot, caught after {round.time_s.toFixed(1)} s at {round.closest_approach_m.toFixed(1)} m.</p>
    </dl>
  )
}

export function Landing() {
  const [view, setView] = useState(0)
  const [stats, setStats] = useState(null)

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/play/stats`)
      .then((response) => (response.ok ? response.json() : null))
      .then(setStats)
      .catch(() => {})
  }, [])

  const tallest = Math.max(...CHECKPOINT_HITS)

  return (
    <div className="landing">
      <header className="l-hero">
        <nav className="l-bar" aria-label="Main">
          <a className="l-mark" href="#">Guidance Sim</a>
          <span>
            <a href="#play">Fly the target</a>
            <a href="#lab">Open the lab</a>
          </span>
        </nav>
        <HeroScene />
        <div className="l-sheet">
          <h1>
            <span><i>Outfly a trained</i></span>
            <span><i>guidance model</i></span>
          </h1>
          <p>
            A 3D physics simulation where a model that learned by trial and
            error steers an interceptor. Fly the target yourself, or open the
            lab and watch it work.
          </p>
          <div className="l-actions">
            <a className="l-button" href="#play">Fly the target</a>
            <a className="l-link" href="#lab">Open the lab</a>
          </div>
        </div>
      </header>

      <main>
        <section className="l-stats" aria-labelledby="stats-title">
          <div className="l-split">
            <h2 id="stats-title" data-reveal>Scored on runs it never practised</h2>
            <p data-reveal>
              Those targets were scripted, and the model can be beaten: a
              scripted pilot holding a hard turn in the last seconds got away in
              42 of 120 tries.
            </p>
          </div>
          <div className="l-mosaic">
            <figure data-reveal>
              <img src="/landing/trials.jpg" alt={VIEWS[3].alt} width="1600" height="1000" loading="lazy" />
            </figure>
            <div className="l-tile l-tile-model" data-reveal>
              <strong>266</strong>
              <p>of 300 test runs hit by the trained model. Its worst miss was 16 m.</p>
            </div>
            <div className="l-tile l-tile-classic" data-reveal>
              <strong>218</strong>
              <p>of the same 300 hit by classical proportional navigation, on the same noisy sensor data. Its worst miss was 1,347 m.</p>
            </div>
          </div>
        </section>

        <section className="l-training" aria-labelledby="training-title">
          <div className="l-split">
            <h2 id="training-title" data-reveal>How it got there</h2>
            <p data-reveal>
              Hits out of 50 test runs, measured every 204,800 practice steps.
              Left is the start of training, right is the model you fly against.
            </p>
          </div>
          <ol className="l-bars" aria-label="Hits out of 50 test runs after each training checkpoint">
            {CHECKPOINT_HITS.map((hits, index) => (
              <li
                key={index}
                tabIndex={0}
                data-final={index === CHECKPOINT_HITS.length - 1}
                style={{ '--h': hits / tallest }}
              >
                <span>{hits} of 50</span>
              </li>
            ))}
          </ol>
        </section>

        <section className="l-how" aria-labelledby="how-title">
          <h2 id="how-title" data-reveal>How it works</h2>

          <div className="l-step">
            <div data-reveal>
              <h3>First, the physics runs.</h3>
              <p>Interceptor at 700 m/s, pulling up to 25 g. Target at 240 m/s, up to 9 g. 7 km apart. 50 steps a second.</p>
              <small>Gravity, drag and thinner air at altitude are worked out again at every step.</small>
            </div>
            <figure data-reveal>
              <img src="/landing/lab.jpg" alt={VIEWS[2].alt} width="1600" height="1000" loading="lazy" />
            </figure>
          </div>

          <div className="l-step">
            <div data-reveal>
              <h3>Then the model looks.</h3>
              <p>It gets 12 numbers each step: where the target seems to be, how fast the gap is closing, and how old and how shaky the tracker's estimate is.</p>
            </div>
            <dl className="l-readout" data-ui data-reveal>
              <div><dt>It never sees</dt><dd>the target's true position</dd></div>
              <div><dt>It answers with</dt><dd>2 numbers: a sideways push</dd></div>
              <div><dt>Hit means</dt><dd>passing within 5 m</dd></div>
            </dl>
          </div>

          <div className="l-step">
            <div data-reveal>
              <h3>Finally, it practised.</h3>
              <p>1,638,400 simulated steps of trial and error, rewarded for getting close without wasting effort.</p>
              <small>
                One recorded replay, same start. Left, the classical law misses by 52 m. Right, the trained model passes at 2.8 m. A picked example, not the average.
              </small>
            </div>
            <figure data-reveal>
              <video src="/landing/pn-vs-rl.mp4" poster="/landing/pn-vs-rl.jpg" width="1280" height="720" autoPlay muted loop playsInline />
            </figure>
          </div>
        </section>

        <section className="l-toy" aria-labelledby="toy-title">
          <div data-reveal>
            <h2 id="toy-title">Dodge the classical law</h2>
            <p>
              This is proportional navigation, the textbook law the model is
              scored against, flattened to two dimensions. Move your pointer
              over the square and see how long you last.
            </p>
            <small>A toy. The real rounds are 3D, with gravity, drag and a noisy sensor.</small>
          </div>
          <ChaseDemo />
        </section>

        <section className="l-modes" aria-labelledby="modes-title">
          <div className="l-split">
            <h2 id="modes-title" data-reveal>Two ways in</h2>
            <p data-reveal>Play a round as the target, or use the lab to run scenarios and compare guidance laws.</p>
          </div>
          <div className="l-panel" data-reveal>
            <figure>
              <img src={`/landing/${VIEWS[view].image}.jpg`} alt={VIEWS[view].alt} width="1600" height="1000" loading="lazy" />
              <figcaption>{VIEWS[view].note}</figcaption>
            </figure>
            <div className="l-controls" data-ui role="group" aria-label="Choose a screen to preview">
              {VIEWS.map((item, index) => (
                <button key={item.image} type="button" aria-pressed={index === view} onClick={() => setView(index)}>
                  {item.name}
                </button>
              ))}
              <div className="l-actions">
                <a className="l-button" href="#play">Fly the target</a>
                <a className="l-link" href="#lab">Open the lab</a>
              </div>
            </div>
          </div>
        </section>

        <section className="l-letter" aria-labelledby="letter-title">
          <div data-reveal>
            <h2 id="letter-title">What happens to your round</h2>
            <p className="l-lead">
              Every finished round is saved: your stick inputs, the random seed
              and how it ended. Nothing about you.
            </p>
            {stats?.rounds > 0 && (
              <p className="l-tally">
                So far it has caught the pilot in {stats.caught} of {stats.rounds} recorded rounds.
              </p>
            )}
          </div>
          <div data-reveal>
            <p>
              A saved round can be flown again, so the model can be tested
              against real people instead of scripted targets, and practise on
              the rounds it lost. A retrained copy only replaces this one if it
              scores better on rounds it never trained on.
            </p>
            <p>
              <mark>It does not change while you play.</mark> The model here is
              fixed; saved rounds are practice material for the next version.
            </p>
            <p>
              This is a study, not a weapon system. The vehicles use generic
              textbook-style numbers, the sensor is plain noise on an angle, and
              nothing here models real hardware.
            </p>
          </div>
        </section>
      </main>

      <footer className="l-footer">
        <nav aria-label="Footer">
          <a href="#play">Fly the target</a>
          <a href="#lab">Open the lab</a>
        </nav>
        <span>A 3D guidance study, 2026. 3D models: Poly by Google, Jarlan Perez (CC BY 3.0)</span>
        <svg viewBox="0 0 640 96" role="img" aria-label="Guidance Sim">
          <text x="0" y="80" textLength="640" lengthAdjust="spacingAndGlyphs">Guidance Sim</text>
        </svg>
      </footer>
    </div>
  )
}
