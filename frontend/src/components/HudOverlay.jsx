import { engagementMetrics } from '../lib/engagementMetrics'
import { useSimulationStore } from '../store/useSimulationStore'

export function HudOverlay() {
  const frames = useSimulationStore((state) => state.frames)
  const cursor = useSimulationStore((state) => state.cursor)
  const streamResult = useSimulationStore((state) => state.streamResult)
  const selectedGuidanceLaw = useSimulationStore(
    (state) => state.selectedGuidanceLaw,
  )
  const catalog = useSimulationStore((state) => state.catalog)

  const frame = frames[cursor]
  const previous = cursor > 0 ? frames[cursor - 1] : null
  const m = engagementMetrics(frame, previous, streamResult)
  const law =
    catalog?.guidance_laws.find((item) => item.id === selectedGuidanceLaw) ??
    null
  const lawStatus = law
    ? `${law.id.toUpperCase()} ACTIVE · N=4`
    : 'PN ACTIVE · N=4'

  const interceptor = catalog?.vehicle_profiles.find(
    (p) => p.role === 'interceptor',
  )
  const target = catalog?.vehicle_profiles.find((p) => p.role === 'target')
  const massTxt = interceptor
    ? interceptor.parameters.mass.value.toLocaleString()
    : '200'
  const gLimTxt = target
    ? target.parameters.maneuver_limit.value.toFixed(1)
    : '9.0'

  return (
    <div className="hud-overlay" aria-label="Engagement HUD">
      <section className="glass-panel mission-panel">
        <span className="panel-kicker">MISSION CLOCK</span>
        <span className="clock-readout">T{m.clock}</span>
        <div className="panel-rule" />
        <div className="metric-stack">
          <div className="metric-row">
            <span>RANGE</span>
            <strong>{m.rangeTxt}</strong>
          </div>
          <div className="metric-row">
            <span>CLOSING V</span>
            <strong>{m.closingTxt}</strong>
          </div>
          <div className="metric-row">
            <span>TIME TO GO</span>
            <strong>{m.tgoTxt}</strong>
          </div>
        </div>
      </section>

      <section className="glass-panel guidance-panel">
        <span className="panel-kicker">GUIDANCE</span>
        <div className="law-stack">
          <div className="law-row">
            <span className="law-dot is-hot" />
            <span>{lawStatus}</span>
          </div>
          <div className="law-row is-dim">
            <span className="law-dot" />
            <span>RL AGENT STANDBY</span>
          </div>
        </div>
        <div className="panel-rule" />
        <div className="g-block">
          <div className="metric-row">
            <span>LATERAL G</span>
            <strong style={{ color: m.gColor }} className="g-value">
              {m.gTxt}
            </strong>
          </div>
          <div className="g-bar">
            <div className="g-fill" style={{ width: m.gPct, background: m.gColor }} />
            <div className="g-warn-mark" />
          </div>
          <div className="g-scale">
            <span>0</span>
            <span>20 WARN</span>
            <span>25 G LIMIT</span>
          </div>
        </div>
      </section>

      <section className="glass-panel entities-panel">
        <span className="panel-kicker">ENTITIES</span>
        <div className="entity-block">
          <div className="entity-name">
            <span className="law-dot is-hot" />
            <span>INTERCEPTOR A</span>
          </div>
          <div className="entity-grid">
            <div>
              <span>ALT</span>
              <strong>{m.altI}</strong>
            </div>
            <div>
              <span>SPD</span>
              <strong>{m.spdI}</strong>
            </div>
            <div>
              <span>MASS</span>
              <strong>{massTxt}</strong>
            </div>
          </div>
        </div>
        <div className="panel-rule" />
        <div className="entity-block is-target">
          <div className="entity-name">
            <span className="law-dot is-soft" />
            <span>TARGET B</span>
          </div>
          <div className="entity-grid">
            <div>
              <span>ALT</span>
              <strong>{m.altT}</strong>
            </div>
            <div>
              <span>SPD</span>
              <strong>{m.spdT}</strong>
            </div>
            <div>
              <span>G LIM</span>
              <strong>{gLimTxt}</strong>
            </div>
          </div>
        </div>
      </section>

      <section className="glass-panel solution-panel">
        <span className="panel-kicker">SOLUTION</span>
        <div className="pk-block">
          <span className="pk-value" style={{ color: m.pkColor }}>
            {m.pkTxt}
          </span>
          <span className="pk-label">INTERCEPT PROBABILITY</span>
        </div>
        <div className="panel-rule" />
        <div className="metric-stack">
          <div className="metric-row">
            <span>PRED. MISS</span>
            <strong>{m.missTxt}</strong>
          </div>
          <div className="metric-row">
            <span>LOS RATE</span>
            <strong>{m.losTxt}</strong>
          </div>
        </div>
      </section>

      {m.alert && (
        <div className="hud-alert" style={{ borderColor: m.alert.color }}>
          <span className="law-dot" style={{ background: m.alert.color }} />
          <span style={{ color: m.alert.color }}>{m.alert.text}</span>
        </div>
      )}

      <p className="scene-hint">
        DRAG TO ORBIT · SCROLL TO ZOOM · Z-UP · SCENE UNITS KM
      </p>
    </div>
  )
}
