import { Grid, Html, Line, OrbitControls, PerspectiveCamera, useGLTF } from '@react-three/drei'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { Box3, Matrix4, Quaternion, Vector3 } from 'three'

import { engagementOrigin, toScenePoint, toSceneVector } from '../lib/coordinates'
import { trialAppearance } from '../lib/trialAppearance'
import { useSimulationStore } from '../store/useSimulationStore'

// Poly.pizza models (CC-BY 3.0).
// Jet (Poly by Google): native mesh spans ~130 units, nose along +Z.
// Missile (Jarlan Perez): native mesh spans ~5 units along Y, nose along +Y.
const JET_MODEL_URL = '/models/fighter-jet.glb'
const JET_FORWARD = new Vector3(0, 0, 1)
const JET_UP = new Vector3(0, 1, 0)
const JET_SCALE = 0.0015

const MISSILE_MODEL_URL = '/models/missile-jarlan.glb'
const MISSILE_FORWARD = new Vector3(0, 1, 0)
const MISSILE_SCALE = 0.04

function HeadingModel({ url, forward, modelUp, scale, position, heading, up }) {
  const { scene } = useGLTF(url)
  const clone = useMemo(() => scene.clone(), [scene])
  const quaternion = useMemo(() => {
    const dir = new Vector3(...heading)
    if (dir.lengthSq() < 1e-6) return new Quaternion()
    dir.normalize()
    if (!up || !modelUp) return new Quaternion().setFromUnitVectors(forward, dir)
    // Full attitude: map the model's (forward, up, side) basis onto the
    // streamed (nose, canopy, side) basis so bank shows as roll.
    const worldUp = new Vector3(...up).normalize()
    const model = new Matrix4().makeBasis(
      forward, modelUp, new Vector3().crossVectors(forward, modelUp),
    )
    const world = new Matrix4().makeBasis(
      dir, worldUp, new Vector3().crossVectors(dir, worldUp),
    )
    return new Quaternion().setFromRotationMatrix(world.multiply(model.transpose()))
  }, [forward, modelUp, heading, up])

  return (
    <primitive
      object={clone}
      position={position}
      quaternion={quaternion}
      scale={scale}
    />
  )
}
useGLTF.preload(JET_MODEL_URL)
useGLTF.preload(MISSILE_MODEL_URL)

function VehicleLabel({ position, color, children }) {
  return (
    <group position={position}>
      <Html center distanceFactor={8} style={{ pointerEvents: 'none' }}>
        <span
          style={{
            display: 'block',
            transform: 'translateY(-1.6em)',
            fontFamily: 'var(--mono)',
            fontSize: '11px',
            letterSpacing: '0.12em',
            color,
            whiteSpace: 'nowrap',
          }}
        >
          {children}
        </span>
      </Html>
    </group>
  )
}

const NO_TRIALS = []

function TrialOverlay({ origin }) {
  // Stable fallback: a fresh [] per call makes zustand re-render forever.
  const trials = useSimulationStore(
    (state) => state.trialSet?.trials ?? NO_TRIALS,
  )

  return trials.map((trial) => {
    const appearance = trialAppearance(trial)
    const points = trial.frames.map((frame) =>
      toScenePoint(frame.pursuer.position_m, origin),
    )
    if (points.length < 2) return null
    // Each trial has its own perturbed geometry, so draw its own target too.
    const targetPoints = trial.frames.map((frame) =>
      toScenePoint(frame.target.position_m, origin),
    )
    return (
      <group key={trial.episode}>
        <Line
          points={targetPoints}
          color="#ff5238"
          transparent
          opacity={0.12}
          lineWidth={1}
        />
        <Line
          points={points}
          color={appearance.color}
          transparent
          opacity={appearance.opacity}
          lineWidth={appearance.lineWidth}
        />
      </group>
    )
  })
}

// Cycling through episodes one at a time reads better sped up than at
// real-time rates — 4x keeps a full engagement under a few seconds.
const SEQUENTIAL_SPEED = 4

function SequentialTrialPlayback({ origin }) {
  const trials = useSimulationStore(
    (state) => state.trialSet?.trials ?? NO_TRIALS,
  )
  const [trialIndex, setTrialIndex] = useState(0)
  const [frameIndex, setFrameIndex] = useState(0)
  const clock = useRef(0)

  useEffect(() => {
    setTrialIndex(0)
    setFrameIndex(0)
    clock.current = 0
  }, [trials])

  const trial = trials.length ? trials[trialIndex % trials.length] : null

  useFrame((_, delta) => {
    if (!trial) return
    clock.current += delta * SEQUENTIAL_SPEED
    const frames = trial.frames
    const finished = clock.current >= frames.at(-1).time_s
    if (finished) {
      clock.current = 0
      setFrameIndex(0)
      setTrialIndex((index) => (index + 1) % trials.length)
      return
    }
    let next = frameIndex
    while (next < frames.length - 1 && frames[next + 1].time_s <= clock.current) {
      next += 1
    }
    if (next !== frameIndex) setFrameIndex(next)
  })

  if (!trial) return null
  const frames = trial.frames
  const current = frames[Math.min(frameIndex, frames.length - 1)]
  const pursuerPosition = toScenePoint(current.pursuer.position_m, origin)
  const targetPosition = toScenePoint(current.target.position_m, origin)
  const visiblePursuer = frames
    .slice(0, frameIndex + 1)
    .map((frame) => toScenePoint(frame.pursuer.position_m, origin))
  const visibleTarget = frames
    .slice(0, frameIndex + 1)
    .map((frame) => toScenePoint(frame.target.position_m, origin))
  const appearance = trialAppearance(trial)

  return (
    <group key={trialIndex}>
      {visiblePursuer.length > 1 && (
        <Line points={visiblePursuer} color={appearance.color} lineWidth={2.2} />
      )}
      {visibleTarget.length > 1 && (
        <Line
          points={visibleTarget}
          color="#ff5238"
          transparent
          opacity={0.5}
          lineWidth={1.6}
        />
      )}
      <HeadingModel
        url={MISSILE_MODEL_URL}
        forward={MISSILE_FORWARD}
        scale={MISSILE_SCALE}
        position={pursuerPosition}
        heading={toSceneVector(current.pursuer.velocity_m_s)}
      />
      <VehicleLabel position={pursuerPosition} color="#ffffff">
        EP{String(trial.episode).padStart(2, '0')} ·{' '}
        {trial.success ? 'INTERCEPT' : 'MISS'}
      </VehicleLabel>
      <HeadingModel
        url={JET_MODEL_URL}
        forward={JET_FORWARD}
        modelUp={JET_UP}
        scale={JET_SCALE}
        position={targetPosition}
        heading={toSceneVector(current.target.body_axis ?? current.target.velocity_m_s)}
        up={current.target.body_up && toSceneVector(current.target.body_up)}
      />
    </group>
  )
}

function Trajectories() {
  const frames = useSimulationStore((state) => state.frames)
  const cursor = useSimulationStore((state) => state.cursor)
  const viewMode = useSimulationStore((state) => state.viewMode)
  const trainingPlayMode = useSimulationStore((state) => state.trainingPlayMode)
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
        <TrialOverlay origin={origin} />
      </>
    )
  }

  if (viewMode === 'training') {
    return trainingPlayMode === 'sequential' ? (
      <SequentialTrialPlayback origin={origin} />
    ) : (
      <TrialOverlay origin={origin} />
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
        <Line points={visibleTarget} color="#ff5238" lineWidth={2} />
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
      <HeadingModel
        url={MISSILE_MODEL_URL}
        forward={MISSILE_FORWARD}
        scale={MISSILE_SCALE}
        position={pursuerPosition}
        heading={toSceneVector(current.pursuer.velocity_m_s)}
      />
      <VehicleLabel position={pursuerPosition} color="#ffffff">
        INTERCEPTOR
      </VehicleLabel>
      <HeadingModel
        url={JET_MODEL_URL}
        forward={JET_FORWARD}
        modelUp={JET_UP}
        scale={JET_SCALE}
        position={targetPosition}
        heading={toSceneVector(current.target.body_axis ?? current.target.velocity_m_s)}
        up={current.target.body_up && toSceneVector(current.target.body_up)}
      />
      <VehicleLabel position={targetPosition} color="#ff5238">
        TARGET
      </VehicleLabel>
    </>
  )
}

// Unit direction of the old fixed 3D camera position — kept as the default
// viewing angle, just scaled to whatever the scenario's extent turns out to be.
const OVERVIEW_DIRECTION = new Vector3(1.6, 2.1, 6.2).normalize()
const CHASE_BACK = 3.2
const CHASE_UP = 1.1
const DEFAULT_CENTER = new Vector3(0, 0.25, -0.4)

function useSceneBounds() {
  const frames = useSimulationStore((state) => state.frames)
  const viewMode = useSimulationStore((state) => state.viewMode)
  const trials = useSimulationStore(
    (state) => state.trialSet?.trials ?? NO_TRIALS,
  )
  const origin = useMemo(() => engagementOrigin(frames[0]), [frames])
  // Trials/training overlay many dispersed episodes, so the camera must fit
  // their spread rather than whatever single run happened to be loaded before.
  const boundsFrames =
    viewMode === 'trials' || viewMode === 'training'
      ? trials.flatMap((trial) => trial.frames)
      : frames

  return useMemo(() => {
    if (!boundsFrames.length) return { center: DEFAULT_CENTER, radius: 3 }
    const box = new Box3()
    for (const frame of boundsFrames) {
      box.expandByPoint(
        new Vector3(...toScenePoint(frame.pursuer.position_m, origin)),
      )
      box.expandByPoint(
        new Vector3(...toScenePoint(frame.target.position_m, origin)),
      )
    }
    const center = box.getCenter(new Vector3())
    const radius = Math.max(box.getSize(new Vector3()).length() / 2, 1.5)
    return { center, radius }
  }, [boundsFrames, origin])
}

const CAMERA_EASE_SPEED = 4 // per second; higher = snappier convergence
const SETTLE_DISTANCE = 0.03

// "2D" is a single persistent perspective camera pulled way back on a very
// narrow FOV rather than a separate orthographic camera — a camera swap
// can't be animated (the projections aren't interpolable), but dollying the
// same camera out while narrowing its FOV reads as parallel projection and
// can be eased like everything else.
const FOV_3D = 42
const FOV_2D = 3.5
const TOP_DOWN_PAD = 1.35
function topDownDistance(halfHeight) {
  return halfHeight / Math.tan((FOV_2D * Math.PI) / 360)
}

// One persistent camera, driven imperatively so mode and projection switches
// (and the chase cams following a moving vehicle) ease into place instead of
// snapping. OrbitControls only takes over once overview has settled — while
// it's mounted it fights any external repositioning, so we keep it out of
// the tree entirely during a chase or an in-flight transition. Fog and the
// orbit dolly range are re-derived from the live camera distance every
// frame since "2D" now sits hundreds of units back instead of a fixed 18.
function CameraDriver({ cameraMode, projection, viewMode, trialSet, desiredPosition, desiredTarget, desiredFov }) {
  const { scene } = useThree()
  const camRef = useRef(null)
  const controlsRef = useRef(null)
  const currentTarget = useRef(desiredTarget.clone())
  const [settled, setSettled] = useState(false)

  useLayoutEffect(() => {
    camRef.current?.position.copy(desiredPosition)
    camRef.current?.lookAt(desiredTarget)
    // Mount pose only — every later frame is driven by the easing loop below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    // viewMode changes (e.g. hud -> trials/training) bring a whole new set
    // of scene bounds, and trials load asynchronously after the mode switch
    // (trialSet arrives later) — re-ease into them instead of leaving
    // OrbitControls parked on wherever the previous view happened to settle.
    if (cameraMode === 'overview') setSettled(false)
  }, [cameraMode, projection, viewMode, trialSet])

  const chase = cameraMode !== 'overview'
  const easing = chase || !settled

  useFrame((_, delta) => {
    const cam = camRef.current
    if (!cam) return

    if (easing) {
      const t = 1 - Math.exp(-CAMERA_EASE_SPEED * delta)
      cam.position.lerp(desiredPosition, t)
      currentTarget.current.lerp(desiredTarget, t)
      cam.fov += (desiredFov - cam.fov) * t
      cam.lookAt(currentTarget.current)
      cam.updateProjectionMatrix()
      if (!chase && cam.position.distanceTo(desiredPosition) < SETTLE_DISTANCE) {
        setSettled(true)
      }
    }

    if (scene.fog) {
      const distance = cam.position.distanceTo(currentTarget.current)
      scene.fog.near = Math.max(6, distance * 0.6)
      scene.fog.far = distance * 2.2 + 20
    }
  })

  const maxDistance = Math.max(26, desiredPosition.distanceTo(desiredTarget) * 1.4)

  return (
    <>
      <PerspectiveCamera ref={camRef} makeDefault fov={FOV_3D} near={0.01} far={20000} />
      {!easing && (
        <OrbitControls
          ref={controlsRef}
          makeDefault
          enableDamping
          dampingFactor={0.07}
          minDistance={2}
          maxDistance={maxDistance}
          target={currentTarget.current.toArray()}
          maxPolarAngle={projection === '2d' ? 0.01 : Math.PI}
          minPolarAngle={0}
        />
      )}
    </>
  )
}

function CameraRig({ projection }) {
  const cameraMode = useSimulationStore((state) => state.cameraMode)
  const viewMode = useSimulationStore((state) => state.viewMode)
  const trialSet = useSimulationStore((state) => state.trialSet)
  const frames = useSimulationStore((state) => state.frames)
  const cursor = useSimulationStore((state) => state.cursor)
  const origin = useMemo(() => engagementOrigin(frames[0]), [frames])
  const { center, radius } = useSceneBounds()

  const current = frames[Math.min(cursor, frames.length - 1)]
  const tracked =
    cameraMode === 'pursuer'
      ? current?.pursuer
      : cameraMode === 'target'
        ? current?.target
        : null

  let desiredTarget
  let desiredPosition
  let desiredFov
  if (projection === '2d') {
    desiredTarget = tracked ? new Vector3(...toScenePoint(tracked.position_m, origin)) : center
    desiredFov = FOV_2D
    const distance = topDownDistance(radius * TOP_DOWN_PAD)
    // Dead-center overhead is a degenerate lookAt, so nudge off-axis by a
    // hair — visually identical from directly above.
    desiredPosition = new Vector3(desiredTarget.x, distance, desiredTarget.z + 0.001)
  } else if (tracked) {
    desiredTarget = new Vector3(...toScenePoint(tracked.position_m, origin))
    desiredFov = FOV_3D
    const heading = new Vector3(...toSceneVector(tracked.velocity_m_s))
    const forward = heading.lengthSq() > 1e-6 ? heading.normalize() : new Vector3(0, 0, 1)
    desiredPosition = desiredTarget.clone().addScaledVector(forward, -CHASE_BACK).add(new Vector3(0, CHASE_UP, 0))
  } else {
    desiredTarget = center
    desiredFov = FOV_3D
    desiredPosition = center.clone().addScaledVector(OVERVIEW_DIRECTION, radius * 1.9)
  }

  return (
    <CameraDriver
      cameraMode={cameraMode}
      projection={projection}
      viewMode={viewMode}
      trialSet={trialSet}
      desiredPosition={desiredPosition}
      desiredTarget={desiredTarget}
      desiredFov={desiredFov}
    />
  )
}

export function SimulationScene({ projection = '3d' }) {
  const hasFrames = useSimulationStore((state) =>
    state.viewMode === 'trials' || state.viewMode === 'training'
      ? (state.trialSet?.trials.length ?? 0) > 0
      : state.frames.length > 0,
  )
  const viewMode = useSimulationStore((state) => state.viewMode)

  return (
    <div className="scene-shell">
      <Canvas dpr={[1, 2]} gl={{ antialias: true }}>
        <CameraRig projection={projection} />
        <color attach="background" args={['#0b0c0e']} />
        <fog attach="fog" args={['#0b0c0e', 12, 30]} />
        <ambientLight intensity={1.1} />
        <directionalLight position={[4, 9, 6]} intensity={1.4} />
        <Grid
          args={[40, 80]}
          cellSize={0.5}
          cellThickness={0.4}
          cellColor="#24282e"
          sectionSize={2}
          sectionThickness={0.7}
          sectionColor="#454b54"
          position={[0, -3.1, 0]}
          fadeDistance={28}
          fadeStrength={1.4}
          infiniteGrid
        />
        <Trajectories />
      </Canvas>
      {!hasFrames && (
        <div className="empty-scene">
          <span>3D ENGAGEMENT SPACE</span>
          <strong>
            {viewMode === 'trials' || viewMode === 'training'
              ? 'Run a preview to overlay RL trials'
              : 'Choose a scenario and run a preview'}
          </strong>
        </div>
      )}
    </div>
  )
}
