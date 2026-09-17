import { Grid, Html, Line, OrbitControls, PerspectiveCamera, useGLTF } from '@react-three/drei'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { Box3, Color, Float32BufferAttribute, Matrix4, Object3D, PlaneGeometry, Quaternion, Vector3 } from 'three'

import { engagementOrigin, toScenePoint, toSceneVector } from '../lib/coordinates'
import { useSimulationStore } from '../store/useSimulationStore'
import { useTrajectoryStream } from '../hooks/useTrajectoryStream'

// Monte Carlo trials have no ordering, so only the outcome drives styling; misses stand out.
function trialAppearance(trial) {
  return {
    color: trial.success ? '#f4f5f7' : '#ff5238',
    opacity: trial.success ? 0.3 : 0.65,
    lineWidth: trial.success ? 1.2 : 1.4,
  }
}

// Decorative, deterministic scenery in scene kilometres; never feeds physics.
// A low central valley keeps the initial engagement clear of the backdrop.
// eslint-disable-next-line react-refresh/only-export-components
export function terrainHeight(x, z) {
  const peaks = [
    [-13, -15, 6.8, 6], [-4, -21, 8.5, 5.5], [8, -17, 7, 6],
    [20, -12, 8, 7], [-23, -5, 6, 7], [25, 13, 5, 8], [-20, 20, 4, 8],
  ]
  let height = 0
  for (const [px, pz, h, width] of peaks) {
    height += h * Math.exp(-((x - px) ** 2 + (z - pz) ** 2) / (width ** 2))
  }
  const detail = Math.sin(x * 1.8 + z * 0.7) * Math.cos(z * 1.4) * 0.17
    + Math.sin(x * 4.1 - z * 2.8) * 0.065
  const clearing = 1 - Math.exp(-(x * x + z * z) / 65)
  return -0.18 + clearing * (height + 0.23 + detail)
}

// Fit a bounding sphere against BOTH frustum axes, with room for labels.
// eslint-disable-next-line react-refresh/only-export-components
export function fitDistance(radius, aspect, fov = 42) {
  const vertical = fov * Math.PI / 360
  const horizontal = Math.atan(Math.tan(vertical) * Math.max(aspect, 0.1))
  return radius / Math.sin(Math.min(vertical, horizontal)) * (aspect < 1 ? 1.5 : 1.22)
}

const FOREST_COUNT = 10000

function AlpineLandscape({ projection }) {
  const forestRef = useRef(null)
  const trunkRef = useRef(null)
  const terrain = useMemo(() => {
    const geometry = new PlaneGeometry(110, 110, 200, 200)
    geometry.rotateX(-Math.PI / 2)
    const vertices = geometry.attributes.position
    const colors = []
    const green = new Color('#617c66')
    const stone = new Color('#89958c')
    const snow = new Color('#d9e3de')
    for (let i = 0; i < vertices.count; i++) {
      const x = vertices.getX(i)
      const z = vertices.getZ(i)
      const h = terrainHeight(x, z)
      vertices.setY(i, h)
      const color = green.clone().lerp(stone, Math.min(1, Math.max(0, (h - 1.8) / 3)))
      color.lerp(snow, Math.min(1, Math.max(0, (h - 5.2 + Math.sin(x * 2 + z)) / 2)))
      color.multiplyScalar(0.94 + 0.06 * Math.sin(x * 3.2 + z * 2.1))
      colors.push(color.r, color.g, color.b)
    }
    geometry.setAttribute('color', new Float32BufferAttribute(colors, 3))
    geometry.computeVertexNormals()
    return geometry
  }, [])

  useLayoutEffect(() => {
    let seed = 917
    const random = () => {
      seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0
      return seed / 4294967296
    }
    const dummy = new Object3D()
    const color = new Color()
    for (let i = 0; i < FOREST_COUNT; i++) {
      const x = (random() - 0.5) * 65
      const z = (random() - 0.5) * 65
      const ground = terrainHeight(x, z)
      const height = (0.18 + random() * 0.3) * (ground > 4.6 ? 0 : 1)
      dummy.position.set(x, ground + height * 0.12, z)
      dummy.rotation.set(0, random() * Math.PI, 0)
      dummy.scale.set(height * 0.08, height * 0.45, height * 0.08)
      dummy.updateMatrix()
      trunkRef.current.setMatrixAt(i, dummy.matrix)
      for (let tier = 0; tier < 2; tier++) {
        dummy.position.y = ground + height * (0.42 + tier * 0.3)
        dummy.scale.set(height * (0.38 - tier * 0.1), height * 0.75, height * (0.38 - tier * 0.1))
        dummy.updateMatrix()
        forestRef.current.setMatrixAt(i * 2 + tier, dummy.matrix)
        color.setHSL(0.39 + random() * 0.035, 0.22 + random() * 0.15, 0.17 + random() * 0.14)
        forestRef.current.setColorAt(i * 2 + tier, color)
      }
    }
    for (const ref of [forestRef, trunkRef]) {
      ref.current.instanceMatrix.needsUpdate = true
      ref.current.computeBoundingSphere()
    }
    forestRef.current.instanceColor.needsUpdate = true
  }, [])

  return (
    <group>
      <mesh geometry={terrain}>
        <meshStandardMaterial vertexColors roughness={1} flatShading />
      </mesh>
      <instancedMesh ref={forestRef} args={[null, null, FOREST_COUNT * 2]} visible={projection === '3d'}>
        <coneGeometry args={[1, 1, 6]} />
        <meshStandardMaterial roughness={1} flatShading />
      </instancedMesh>
      <instancedMesh ref={trunkRef} args={[null, null, FOREST_COUNT]} visible={projection === '3d'}>
        <cylinderGeometry args={[1, 1, 1, 5]} />
        <meshStandardMaterial color="#655b46" roughness={1} />
      </instancedMesh>
    </group>
  )
}

// Poly.pizza models (CC-BY 3.0).
// Jet (Poly by Google): native mesh spans ~130 units, nose along +Z.
// Missile (Jarlan Perez): native mesh spans ~5 units along Y, nose along +Y.
const JET_MODEL_URL = '/models/fighter-jet.glb'
const JET_FORWARD = new Vector3(0, 0, 1)
const JET_UP = new Vector3(0, 1, 0)
const JET_SCALE = 0.0015
// True-to-life: ~15m fighter jet / 130 native units.
const JET_TRUE_SCALE = 15 / 1000 / 130

const MISSILE_MODEL_URL = '/models/missile-jarlan.glb'
const MISSILE_FORWARD = new Vector3(0, 1, 0)
const MISSILE_SCALE = 0.04
// True-to-life: ~3.7m air-to-air missile / 5 native units.
const MISSILE_TRUE_SCALE = 3.7 / 1000 / 5

function HeadingModel({ url, forward, modelUp, scale, trueScale, position, heading, up }) {
  const markerRef = useRef(null)
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

  const vehicleScale = useSimulationStore((state) => state.vehicleScale)

  useFrame(({ camera, size }) => {
    if (!markerRef.current) return
    if (vehicleScale === 'true') {
      markerRef.current.scale.setScalar(1)
      return
    }
    const distance = camera.position.distanceTo(markerRef.current.position)
    const unitsPerPixel = 2 * distance * Math.tan(camera.fov * Math.PI / 360) / Math.max(size.height, 1)
    // Presentation scale only: keep models legible at overview distances.
    markerRef.current.scale.setScalar(Math.max(1, Math.min(8, unitsPerPixel * 30 / 0.2)))
  })

  return (
    <group ref={markerRef} position={position}>
    <primitive
      object={clone}
      quaternion={quaternion}
      scale={vehicleScale === 'true' ? trueScale : scale}
    />
    </group>
  )
}
useGLTF.preload(JET_MODEL_URL)
useGLTF.preload(MISSILE_MODEL_URL)

function VehicleLabel({ position, color, children, side = 'left' }) {
  return (
    <group position={position}>
      <Html center zIndexRange={[1, 0]} style={{ pointerEvents: 'none' }}>
        <span
          className="vehicle-label"
          style={{
            display: 'block',
            transform: `translateY(${side === 'right' ? '-5.5em' : '-2.7em'})`,
            '--label-stem': side === 'right' ? '42px' : '12px',
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
        trueScale={MISSILE_TRUE_SCALE}
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
        trueScale={JET_TRUE_SCALE}
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
        trueScale={MISSILE_TRUE_SCALE}
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
        trueScale={JET_TRUE_SCALE}
        position={targetPosition}
        heading={toSceneVector(current.target.body_axis ?? current.target.velocity_m_s)}
        up={current.target.body_up && toSceneVector(current.target.body_up)}
      />
      <VehicleLabel position={targetPosition} color="#ff5238" side="right">
        TARGET
      </VehicleLabel>
    </>
  )
}

// Unit direction of the old fixed 3D camera position — kept as the default
// viewing angle, just scaled to whatever the scenario's extent turns out to be.
const OVERVIEW_DIRECTION = new Vector3(1.1, 1.25, 4.8).normalize()
const CHASE_BACK = 3.2
const CHASE_UP = 1.1
const DEFAULT_CENTER = new Vector3(0, 2.5, -2)

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
// ease into place instead of snapping. OrbitControls only takes over once
// the current pose has settled — while it's mounted it fights any external
// repositioning, so we keep it out of the tree during an in-flight
// transition. Once a chase cam (pursuer/target lock) settles behind its
// vehicle, orbit takes over there too: each frame we pan both the camera and
// the orbit target by however far the vehicle moved, which keeps the user's
// chosen orbit offset while still following the vehicle around. Fog and the
// orbit dolly range are re-derived from the live camera distance every
// frame since "2D" now sits hundreds of units back instead of a fixed 18.
function CameraDriver({ cameraMode, projection, viewMode, trialSet, frameAnchor, streamStatus, resetKey, aspect, desiredPosition, desiredTarget, desiredFov }) {
  const camRef = useRef(null)
  const controlsRef = useRef(null)
  const currentTarget = useRef(desiredTarget.clone())
  const [settledFor, setSettledFor] = useState(null)
  const vehicleScale = useSimulationStore((state) => state.vehicleScale)
  const viewConfiguration = useMemo(
    () => ({ cameraMode, projection, viewMode, trialSet, frameAnchor, streamStatus, resetKey, aspect }),
    [cameraMode, projection, viewMode, trialSet, frameAnchor, streamStatus, resetKey, aspect],
  )

  useLayoutEffect(() => {
    camRef.current?.position.copy(desiredPosition)
    camRef.current?.lookAt(desiredTarget)
    // Mount pose only — every later frame is driven by the easing loop below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const chase = cameraMode !== 'overview'
  const easing = settledFor !== viewConfiguration

  // OrbitControls just mounted (or re-mounted after a transition) — seed its
  // target from the pose we just settled at instead of the control's own
  // (0,0,0) default.
  useEffect(() => {
    if (!easing && controlsRef.current) {
      controlsRef.current.target.copy(currentTarget.current)
      controlsRef.current.update()
    }
  }, [easing])

  useFrame(({ scene }, delta) => {
    const cam = camRef.current
    if (!cam) return

    if (easing) {
      const t = 1 - Math.exp(-CAMERA_EASE_SPEED * delta)
      cam.position.lerp(desiredPosition, t)
      currentTarget.current.lerp(desiredTarget, t)
      cam.fov += (desiredFov - cam.fov) * t
      cam.lookAt(currentTarget.current)
      cam.updateProjectionMatrix()
      if (cam.position.distanceTo(desiredPosition) < SETTLE_DISTANCE) {
        // Finish exactly overhead in 2D; a tiny residual offset otherwise
        // produces an arbitrary map rotation near the lookAt singularity.
        cam.position.copy(desiredPosition)
        currentTarget.current.copy(desiredTarget)
        cam.fov = desiredFov
        cam.lookAt(desiredTarget)
        cam.updateProjectionMatrix()
        setSettledFor(viewConfiguration)
      }
    } else if (chase && controlsRef.current) {
      const trackDelta = desiredTarget.clone().sub(currentTarget.current)
      if (trackDelta.lengthSq() > 1e-10) {
        cam.position.add(trackDelta)
        controlsRef.current.target.add(trackDelta)
        currentTarget.current.copy(desiredTarget)
      }
    }

    if (scene.fog) {
      const distance = cam.position.distanceTo(currentTarget.current)
      scene.fog.near = Math.max(6, distance * 0.6)
      scene.fog.far = distance * 2.2 + 20
    }
  })

  const maxDistance = Math.max(80, desiredPosition.distanceTo(desiredTarget) * 6)

  return (
    <>
      <PerspectiveCamera ref={camRef} makeDefault fov={FOV_3D} near={0.01} far={20000} />
      {!easing && (
        <OrbitControls
          ref={controlsRef}
          makeDefault
          enableDamping
          dampingFactor={0.07}
          minDistance={vehicleScale === 'true' ? 0.05 : 0.5}
          maxDistance={maxDistance}
          maxPolarAngle={projection === '2d' ? 0.01 : Math.PI / 2.05}
          minPolarAngle={0}
        />
      )}
    </>
  )
}

function CameraRig({ projection, resetKey }) {
  const { size } = useThree()
  const aspect = size.width / Math.max(size.height, 1)
  const cameraMode = useSimulationStore((state) => state.cameraMode)
  const streamStatus = useSimulationStore((state) => state.streamStatus)
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
    const distance = topDownDistance(radius * TOP_DOWN_PAD / Math.min(aspect, 1) * (aspect < 1 ? 1.2 : 1))
    // Dead-center overhead is a degenerate lookAt, so nudge off-axis by a
    // hair — visually identical from directly above.
    desiredPosition = new Vector3(desiredTarget.x, desiredTarget.y + distance, desiredTarget.z + 0.001)
  } else if (tracked) {
    desiredTarget = new Vector3(...toScenePoint(tracked.position_m, origin))
    desiredFov = FOV_3D
    const heading = new Vector3(...toSceneVector(tracked.velocity_m_s))
    const forward = heading.lengthSq() > 1e-6 ? heading.normalize() : new Vector3(0, 0, 1)
    desiredPosition = desiredTarget.clone().addScaledVector(forward, -CHASE_BACK).add(new Vector3(0, CHASE_UP, 0))
  } else {
    desiredTarget = center
    desiredFov = FOV_3D
    desiredPosition = center.clone().addScaledVector(OVERVIEW_DIRECTION, fitDistance(radius, aspect))
  }

  return (
    <CameraDriver
      cameraMode={cameraMode}
      projection={projection}
      viewMode={viewMode}
      trialSet={trialSet}
      frameAnchor={frames[0]}
      streamStatus={streamStatus}
      resetKey={resetKey}
      aspect={aspect}
      desiredPosition={desiredPosition}
      desiredTarget={desiredTarget}
      desiredFov={desiredFov}
    />
  )
}

export function SimulationScene({ projection = '3d' }) {
  const [resetKey, setResetKey] = useState(0)
  const [telemetry, setTelemetry] = useState(true)
  const startStream = useTrajectoryStream()
  const setCameraMode = useSimulationStore((state) => state.setCameraMode)
  const catalog = useSimulationStore((state) => state.catalog)
  const streamStatus = useSimulationStore((state) => state.streamStatus)
  const error = useSimulationStore((state) => state.error)
  const hasFrames = useSimulationStore((state) =>
    state.viewMode === 'trials' || state.viewMode === 'training'
      ? (state.trialSet?.trials.length ?? 0) > 0
      : state.frames.length > 0,
  )
  const viewMode = useSimulationStore((state) => state.viewMode)

  return (
    <div className="scene-shell" data-telemetry={telemetry} data-projection={projection} data-has-frames={hasFrames}>
      <Canvas dpr={[1, 1.5]} gl={{ antialias: true, preserveDrawingBuffer: true }}>
        <CameraRig projection={projection} resetKey={resetKey} />
        <color attach="background" args={['#b5c9c9']} />
        <fog attach="fog" args={['#b5c9c9', 18, 70]} />
        <hemisphereLight args={['#e9f3ed', '#45564c', 1.7]} />
        <directionalLight position={[-12, 18, 8]} color="#fff0d3" intensity={2.3} />
        <AlpineLandscape projection={projection} />
        {projection === '2d' && <Grid
          args={[40, 80]}
          cellSize={0.5}
          cellThickness={0.4}
          cellColor="#96b9af"
          sectionSize={2}
          sectionThickness={0.7}
          sectionColor="#daf0e6"
          position={[0, 0.12, 0]}
          fadeDistance={60}
          fadeStrength={1.4}
          infiniteGrid
        />}
        <Trajectories />
      </Canvas>
      <div className="scene-toolbar" aria-label="Scene controls">
        <div className="landscape-title"><span className="landscape-dot" /><span>{projection === '3d' ? 'ALPINE VALLEY' : 'TOPOGRAPHIC VIEW'}</span><small>Illustrative terrain</small></div>
        <div className="scene-actions">
          <button type="button" onClick={() => { setCameraMode('overview'); setResetKey((key) => key + 1) }}>Fit both objects</button>
          <button type="button" aria-pressed={telemetry} onClick={() => setTelemetry((value) => !value)}>{telemetry ? 'Hide telemetry' : 'Show telemetry'}</button>
        </div>
      </div>
      {hasFrames && <div className="scene-legend" aria-label="Object legend"><span><i /> Interceptor</span><span><i /> Target</span><span>{projection === '3d' ? 'Drag to orbit · Scroll to zoom' : 'Top view · Grid 500 m'}</span></div>}
      {!hasFrames && (
        <div className="empty-scene">
          {viewMode === 'single' && <>
            <button className="scene-start" type="button" disabled={!catalog || streamStatus === 'connecting' || streamStatus === 'streaming'} onClick={startStream}>
              {streamStatus === 'connecting' || streamStatus === 'streaming' ? 'Preparing simulation…' : 'Run simulation'} <span aria-hidden="true">↗</span>
            </button>
            {error && <p role="alert" className="error-message">{error}</p>}
          </>}
        </div>
      )}
    </div>
  )
}
