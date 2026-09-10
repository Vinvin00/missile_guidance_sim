import { Grid, Html, Line, OrbitControls } from '@react-three/drei'
import { Canvas } from '@react-three/fiber'
import { useMemo } from 'react'

import { TrialOverlaySummary } from './TrialOverlaySummary'
import { engagementOrigin, toScenePoint } from '../lib/coordinates'
import { trialAppearance } from '../lib/trialAppearance'
import { useSimulationStore } from '../store/useSimulationStore'

function VehicleMarker({ label, position, color, shape }) {
  return (
    <group position={position}>
      <mesh>
        {shape === 'cone' ? (
          <coneGeometry args={[0.09, 0.3, 10]} />
        ) : (
          <octahedronGeometry args={[0.12, 0]} />
        )}
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={0.35}
        />
      </mesh>
      <Html center position={[0, 0.27, 0]} distanceFactor={8}>
        <span className="vehicle-label">{label}</span>
      </Html>
    </group>
  )
}

function TrialOverlay({ origin }) {
  const trials = useSimulationStore((state) => state.trialSet?.trials ?? [])

  return trials.map((trial, index) => {
    const appearance = trialAppearance(trial, index, trials.length)
    const points = trial.frames.map((frame) =>
      toScenePoint(frame.pursuer.position_m, origin),
    )
    if (points.length < 2) return null
    return (
      <Line
        key={trial.episode}
        points={points}
        color={appearance.color}
        transparent
        opacity={appearance.opacity}
        lineWidth={appearance.lineWidth}
      />
    )
  })
}

function Trajectories() {
  const frames = useSimulationStore((state) => state.frames)
  const cursor = useSimulationStore((state) => state.cursor)
  const viewMode = useSimulationStore((state) => state.viewMode)
  const origin = useMemo(() => engagementOrigin(frames[0]), [frames])

  const points = useMemo(
    () => ({
      pursuer: frames.map((frame) =>
        toScenePoint(frame.pursuer.position_m, origin),
      ),
      target: frames.map((frame) =>
        toScenePoint(frame.target.position_m, origin),
      ),
    }),
    [frames, origin],
  )

  if (!frames.length) return null

  const current = frames[Math.min(cursor, frames.length - 1)]
  const pursuerPosition = toScenePoint(current.pursuer.position_m, origin)
  const targetPosition = toScenePoint(current.target.position_m, origin)
  const visiblePursuer = points.pursuer.slice(0, cursor + 1)
  const visibleTarget = points.target.slice(0, cursor + 1)

  if (viewMode === 'trials') {
    return (
      <>
        {points.target.length > 1 && (
          <Line
            points={points.target}
            color="#ff648f"
            transparent
            opacity={0.28}
            lineWidth={1.4}
          />
        )}
        <TrialOverlay origin={origin} />
      </>
    )
  }

  return (
    <>
      {points.pursuer.length > 1 && (
        <>
          <Line
            points={points.pursuer}
            color="#16495a"
            transparent
            opacity={0.55}
            lineWidth={1}
          />
          <Line
            points={points.target}
            color="#542b45"
            transparent
            opacity={0.55}
            lineWidth={1}
          />
        </>
      )}
      {visiblePursuer.length > 1 && (
        <Line points={visiblePursuer} color="#55d9ff" lineWidth={2.6} />
      )}
      {visibleTarget.length > 1 && (
        <Line points={visibleTarget} color="#ff648f" lineWidth={2.4} />
      )}
      <VehicleMarker
        label="Interceptor A"
        position={pursuerPosition}
        color="#55d9ff"
        shape="cone"
      />
      <VehicleMarker
        label="Target B"
        position={targetPosition}
        color="#ff648f"
        shape="target"
      />
    </>
  )
}

export function SimulationScene() {
  const hasFrames = useSimulationStore((state) => state.frames.length > 0)
  const viewMode = useSimulationStore((state) => state.viewMode)

  return (
    <div className="scene-shell">
      <Canvas
        camera={{ position: [7.5, 7, 9], fov: 43, near: 0.01, far: 100 }}
        dpr={[1, 2]}
        gl={{ antialias: true }}
      >
        <color attach="background" args={['#080c13']} />
        <fog attach="fog" args={['#080c13', 15, 34]} />
        <ambientLight intensity={0.8} />
        <directionalLight position={[4, 10, 5]} intensity={1.8} />
        <Grid
          args={[24, 24]}
          cellSize={0.5}
          cellThickness={0.45}
          cellColor="#253346"
          sectionSize={2}
          sectionThickness={0.9}
          sectionColor="#344a62"
          fadeDistance={28}
          fadeStrength={1.5}
          infiniteGrid
        />
        <axesHelper args={[1.5]} position={[-5, 0.01, 4]} />
        <Trajectories />
        <OrbitControls
          makeDefault
          enableDamping
          dampingFactor={0.08}
          minDistance={3}
          maxDistance={28}
          target={[0, 3.5, 0]}
        />
      </Canvas>
      {!hasFrames && (
        <div className="empty-scene">
          <span>3D engagement space</span>
          <strong>
            {viewMode === 'trials'
              ? 'Run a preview to overlay mock trials'
              : 'Choose a scenario and run a preview'}
          </strong>
          <small>Drag to orbit · scroll to zoom · right-drag to pan</small>
        </div>
      )}
      {viewMode === 'trials' && <TrialOverlaySummary />}
      <div className="axis-legend" aria-label="Scene units">
        z-up simulation · scene units in km
      </div>
    </div>
  )
}
