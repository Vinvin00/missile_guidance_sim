import { Grid, Line, OrbitControls, OrthographicCamera, PerspectiveCamera } from '@react-three/drei'
import { Canvas } from '@react-three/fiber'
import { useMemo } from 'react'

import { engagementOrigin, toScenePoint } from '../lib/coordinates'
import { trialAppearance } from '../lib/trialAppearance'
import { useSimulationStore } from '../store/useSimulationStore'

function VehicleMarker({ position, color, shape }) {
  return (
    <group position={position}>
      <mesh>
        {shape === 'cone' ? (
          <coneGeometry args={[0.075, 0.3, 16]} />
        ) : (
          <octahedronGeometry args={[0.1, 0]} />
        )}
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={0.45}
        />
      </mesh>
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
            color="#ff2d16"
            transparent
            opacity={0.18}
            lineWidth={1.2}
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
            color="#ffffff"
            transparent
            opacity={0.22}
            lineWidth={1}
          />
          <Line
            points={points.target}
            color="#ffffff"
            transparent
            opacity={0.13}
            lineWidth={1}
          />
        </>
      )}
      {visiblePursuer.length > 1 && (
        <Line points={visiblePursuer} color="#ffffff" lineWidth={2.2} />
      )}
      {visibleTarget.length > 1 && (
        <Line points={visibleTarget} color="#ff2d16" lineWidth={2} />
      )}
      {visiblePursuer.length > 0 && visibleTarget.length > 0 && (
        <Line
          points={[pursuerPosition, targetPosition]}
          color="#ffffff"
          transparent
          opacity={0.18}
          dashed
          dashSize={0.12}
          gapSize={0.08}
          lineWidth={1}
        />
      )}
      <VehicleMarker
        position={pursuerPosition}
        color="#ffffff"
        shape="cone"
      />
      <VehicleMarker
        position={targetPosition}
        color="#ff2d16"
        shape="target"
      />
    </>
  )
}

export function SimulationScene({ projection = '3d' }) {
  const hasFrames = useSimulationStore((state) => state.frames.length > 0)
  const viewMode = useSimulationStore((state) => state.viewMode)

  return (
    <div className="scene-shell">
      <Canvas dpr={[1, 2]} gl={{ antialias: true }}>
        {projection === '2d' ? (
          <OrthographicCamera
            makeDefault
            position={[0, 18, 0]}
            zoom={48}
            near={0.01}
            far={100}
          />
        ) : (
          <PerspectiveCamera
            makeDefault
            position={[1.6, 2.1, 6.2]}
            fov={42}
            near={0.01}
            far={200}
          />
        )}
        <color attach="background" args={['#0a0a0a']} />
        <fog attach="fog" args={['#0a0a0a', 12, 30]} />
        <ambientLight intensity={1.1} />
        <directionalLight position={[4, 9, 6]} intensity={1.4} />
        <Grid
          args={[40, 80]}
          cellSize={0.5}
          cellThickness={0.4}
          cellColor="#1c1c1c"
          sectionSize={2}
          sectionThickness={0.7}
          sectionColor="#333333"
          position={[0, -3.1, 0]}
          fadeDistance={28}
          fadeStrength={1.4}
          infiniteGrid
        />
        <Trajectories />
        <OrbitControls
          makeDefault
          enableDamping
          dampingFactor={0.07}
          minDistance={2}
          maxDistance={26}
          target={[0, 0.25, -0.4]}
          maxPolarAngle={projection === '2d' ? 0.01 : Math.PI}
          minPolarAngle={projection === '2d' ? 0 : 0}
        />
      </Canvas>
      {!hasFrames && (
        <div className="empty-scene">
          <span>3D ENGAGEMENT SPACE</span>
          <strong>
            {viewMode === 'trials'
              ? 'Run a preview to overlay mock trials'
              : 'Choose a scenario and run a preview'}
          </strong>
        </div>
      )}
    </div>
  )
}
