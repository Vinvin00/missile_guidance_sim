import { G_LIMIT, engagementMetrics, num } from '../lib/engagementMetrics'
import { useSimulationStore } from '../store/useSimulationStore'

export function HudOverlay() {
  const frames = useSimulationStore((state) => state.frames)
  const cursor = useSimulationStore((state) => state.cursor)
  const streamResult = useSimulationStore((state) => state.streamResult)
  const selectedGuidanceLaw = useSimulationStore(
    (state) => state.selectedGuidanceLaw,
  )
  const catalog = useSimulationStore((state) => state.catalog)
  const streamMeta = useSimulationStore((state) => state.streamMeta)
  const selectedScenarioId = useSimulationStore(
    (state) => state.selectedScenarioId,
  )

  const interceptor = catalog?.vehicle_profiles.find(
    (p) => p.role === 'interceptor',
  )
  // Limit of the scenario that produced the frames on screen, not the picker.
  const scenarioId = streamMeta?.scenario_id ?? selectedScenarioId
  const gLimit =
    catalog?.scenarios.find((s) => s.id === scenarioId)?.pursuer_g_limit ??
    interceptor?.parameters.maneuver_limit?.value ??
    G_LIMIT

  const frame = frames[cursor]
  const previous = cursor > 0 ? frames[cursor - 1] : null
  const m = engagementMetrics(frame, previous, streamResult, gLimit)
  const law =
    catalog?.guidance_laws.find((item) => item.id === selectedGuidanceLaw) ??
    null
  const lawStatus = !law
    ? 'PN ACTIVE · N=4'
    : law.id === 'rl'
      ? 'RL POLICY ACTIVE'
      : `${law.id.toUpperCase()} ACTIVE · N=${law.id === 'ogl' ? 3 : 4}`

  const target = catalog?.vehicle_profiles.find((p) => p.role === 'target')
  const massTxt = interceptor
    ? interceptor.parameters.mass.value.toLocaleString()
    : '200'
  const gLimTxt = target
    ? target.parameters.maneuver_limit.value.toFixed(1)
    : '9.0'

  return (
    <div className="hud-overlay" aria-label="Engagement HUD">
      <div className="hud-panel-stack">
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
            <span>{num(gLimit * 0.8, 0)} WARN</span>
            <span>{num(gLimit, 0)} G LIMIT</span>
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
      </div>

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
