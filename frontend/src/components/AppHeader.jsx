import { SCREENS } from './AppNav'
import { useSimulationStore } from '../store/useSimulationStore'

const STATUS_LABEL = {
  idle: 'READY',
  connecting: 'CONNECTING',
  streaming: 'STREAMING',
  ready: 'READY',
  error: 'ERROR',
}

export function AppHeader({ screen, projection, onProjection }) {
  const streamStatus = useSimulationStore((state) => state.streamStatus)
  const isPlaying = useSimulationStore((state) => state.isPlaying)
  const cameraMode = useSimulationStore((state) => state.cameraMode)
  const setCameraMode = useSimulationStore((state) => state.setCameraMode)
  const title =
    (SCREENS.find((item) => item.id === screen) || SCREENS[0]).title.toUpperCase()

  let status = STATUS_LABEL[streamStatus] ?? 'READY'
  if (streamStatus === 'ready' && isPlaying) status = 'STREAMING'
  if (streamStatus === 'idle' && isPlaying) status = 'STREAMING'

  const linkError = streamStatus === 'error'

  return (
    <header className="hud-header">
      <div className="hud-brand">
        <span className="brand-name">GUIDANCE SIM</span>
        <span className="brand-screen">{title}</span>
      </div>
      <div className="hud-header-right">
        <div className="stream-chip">
          <span>LIVE STREAM</span>
          <span
            className={linkError ? 'stream-dot is-error' : 'stream-dot'}
          />
          <span className="stream-status">{status}</span>
        </div>
        <div className="projection-group">
          <span className="projection-group-label">Camera</span>
          <div className="projection-toggle" role="group" aria-label="Camera">
            <button
              type="button"
              className={cameraMode === 'overview' ? 'is-active' : ''}
              onClick={() => setCameraMode('overview')}
            >
              3/4
            </button>
            <span className="projection-rule" aria-hidden="true" />
            <button
              type="button"
              className={cameraMode === 'pursuer' ? 'is-active' : ''}
              onClick={() => setCameraMode('pursuer')}
            >
              INTERCEPTOR
            </button>
            <span className="projection-rule" aria-hidden="true" />
            <button
              type="button"
              className={cameraMode === 'target' ? 'is-active' : ''}
              onClick={() => setCameraMode('target')}
            >
              TARGET
            </button>
          </div>
        </div>
        <div className="projection-group">
          <span className="projection-group-label">View</span>
          <div className="projection-toggle" role="group" aria-label="Projection">
            <button
              type="button"
              className={projection === '3d' ? 'is-active' : ''}
              onClick={() => onProjection('3d')}
            >
              3D
            </button>
            <span className="projection-rule" aria-hidden="true" />
            <button
              type="button"
              className={projection === '2d' ? 'is-active' : ''}
              onClick={() => onProjection('2d')}
            >
              2D
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}
