import { create } from 'zustand'

import { loadTrialSet } from '../data/trajectoryData'

// Vehicle profiles plus the engagement geometry group, as { prefix, name, parameters }.
export function parameterGroups(catalog) {
  return [
    ...(catalog?.vehicle_profiles ?? []).map((profile) => ({
      prefix: profile.role,
      name: profile.name,
      parameters: profile.parameters,
    })),
    {
      prefix: 'engagement',
      name: 'Engagement',
      parameters: catalog?.engagement_parameters ?? {},
    },
  ]
}

function liveParameterValues(catalog, currentValues) {
  const values = {}
  for (const group of parameterGroups(catalog)) {
    for (const [name, parameter] of Object.entries(group.parameters)) {
      if (!parameter.live_control) continue
      const id = `${group.prefix}.${name}`
      const current = currentValues[id]
      values[id] =
        current >= parameter.reference_min &&
        current <= parameter.reference_max
          ? current
          : parameter.value
    }
  }
  return values
}

export const useSimulationStore = create((set, get) => ({
  catalog: null,
  selectedScenarioId: 'evasive-climb',
  selectedGuidanceLaw: 'pn',
  parameterValues: {},
  viewMode: 'single',
  cameraMode: 'overview',
  vehicleScale: 'legible',
  trialCount: 30,
  trialSet: null,
  trialsLoading: false,
  trainingPlayMode: 'all',
  trialsRequestId: 0,
  activeDataSource: 'rollout',
  streamStatus: 'idle',
  streamMeta: null,
  streamResult: null,
  frames: [],
  cursor: 0,
  playheadS: 0,
  isPlaying: false,
  playbackRate: 1,
  error: null,

  setCatalog: (catalog) =>
    set((state) => {
      const scenarioExists = catalog.scenarios.some(
        (scenario) => scenario.id === state.selectedScenarioId,
      )
      const lawExists = catalog.guidance_laws.some(
        (law) => law.id === state.selectedGuidanceLaw,
      )
      return {
        catalog,
        selectedScenarioId: scenarioExists
          ? state.selectedScenarioId
          : catalog.scenarios[0]?.id,
        selectedGuidanceLaw: lawExists
          ? state.selectedGuidanceLaw
          : catalog.guidance_laws[0]?.id,
        parameterValues: liveParameterValues(
          catalog,
          state.parameterValues,
        ),
      }
    }),

  selectScenario: (scenarioId) =>
    set((state) => ({
      selectedScenarioId: scenarioId,
      parameterValues: {
        ...state.parameterValues,
        ...(state.catalog?.scenarios.find((s) => s.id === scenarioId)
          ?.parameter_defaults ?? {}),
      },
    })),
  selectGuidanceLaw: (guidanceLaw) =>
    set({ selectedGuidanceLaw: guidanceLaw }),
  setLiveParameter: (parameterId, value) =>
    set((state) => ({
      parameterValues: {
        ...state.parameterValues,
        [parameterId]: value,
      },
    })),
  setViewMode: (viewMode) =>
    set({
      viewMode,
      isPlaying: false,
    }),
  setCameraMode: (cameraMode) => set({ cameraMode }),
  setVehicleScale: (vehicleScale) => set({ vehicleScale }),
  setTrialCount: (trialCount) => set({ trialCount }),
  setTrialSet: (trialSet) => set({ trialSet }),
  setTrainingPlayMode: (trainingPlayMode) => set({ trainingPlayMode }),
  // Real frozen-RL-policy rollouts around the current setup; latest request wins.
  loadTrials: async () => {
    const { selectedScenarioId, parameterValues, trialCount } = get()
    const requestId = get().trialsRequestId + 1
    set({ trialsRequestId: requestId, trialsLoading: true, trialSet: null })
    try {
      const trialSet = await loadTrialSet({
        scenarioId: selectedScenarioId,
        parameterOverrides: parameterValues,
        count: trialCount,
      })
      if (get().trialsRequestId === requestId) {
        set({ trialSet, trialsLoading: false })
      }
    } catch (error) {
      if (get().trialsRequestId === requestId) {
        set({ trialsLoading: false, error: error.message })
      }
    }
  },

  beginStream: () =>
    set({
      activeDataSource: 'rollout',
      cameraMode: 'overview',
      streamStatus: 'connecting',
      streamMeta: null,
      streamResult: null,
      trialSet: null,
      frames: [],
      cursor: 0,
      playheadS: 0,
      isPlaying: false,
      error: null,
    }),

  markStreamStarted: (streamMeta) =>
    set({
      streamStatus: 'streaming',
      streamMeta,
      activeDataSource: streamMeta?.data_source ?? 'rollout',
    }),

  appendFrame: (frame) =>
    set((state) => ({
      frames: [...state.frames, frame],
      streamStatus: 'streaming',
    })),

  completeStream: (streamResult) =>
    set((state) => ({
      streamStatus: 'ready',
      streamResult,
      cursor: 0,
      playheadS: 0,
      isPlaying: state.frames.length > 1,
    })),

  loadReplay: (trajectoryLog) =>
    set({
      cameraMode: 'overview',
      selectedScenarioId: trajectoryLog.scenario_id,
      selectedGuidanceLaw: trajectoryLog.guidance_law,
      activeDataSource: trajectoryLog.source,
      streamStatus: 'ready',
      streamMeta: {
        stream_id: trajectoryLog.session_id,
        scenario_id: trajectoryLog.scenario_id,
        guidance_law: trajectoryLog.guidance_law,
        frame_count: trajectoryLog.frames.length,
        dt_s: trajectoryLog.dt_s,
        data_source: trajectoryLog.source,
      },
      streamResult: {
        outcome: trajectoryLog.outcome,
        closest_approach_m: trajectoryLog.closest_approach_m,
        frame_count: trajectoryLog.frames.length,
        data_source: trajectoryLog.source,
      },
      frames: trajectoryLog.frames,
      trialSet: null,
      viewMode: 'single',
      cursor: 0,
      playheadS: 0,
      isPlaying: false,
      error: null,
    }),

  failStream: (message) =>
    set({
      streamStatus: 'error',
      error: message,
      isPlaying: false,
    }),

  setPlaybackRate: (playbackRate) => set({ playbackRate }),

  seekToIndex: (requestedIndex) =>
    set((state) => {
      if (!state.frames.length) return {}
      const cursor = Math.min(
        Math.max(Math.round(requestedIndex), 0),
        state.frames.length - 1,
      )
      return {
        cursor,
        playheadS: state.frames[cursor].time_s,
      }
    }),

  togglePlayback: () =>
    set((state) => {
      if (state.frames.length < 2) return {}
      if (state.cursor === state.frames.length - 1) {
        return { cursor: 0, playheadS: 0, isPlaying: true }
      }
      return { isPlaying: !state.isPlaying }
    }),

  restartPlayback: () =>
    set((state) => ({
      cursor: 0,
      playheadS: 0,
      isPlaying: state.frames.length > 1,
    })),

  advancePlayback: (elapsedS) => {
    const state = get()
    if (!state.isPlaying || state.frames.length < 2) return

    const finalIndex = state.frames.length - 1
    const finalTime = state.frames[finalIndex].time_s
    const playheadS = state.playheadS + elapsedS * state.playbackRate
    if (playheadS >= finalTime) {
      set({
        cursor: finalIndex,
        playheadS: finalTime,
        isPlaying: false,
      })
      return
    }

    let cursor = state.cursor
    while (
      cursor < finalIndex &&
      state.frames[cursor + 1].time_s <= playheadS
    ) {
      cursor += 1
    }
    set({ cursor, playheadS })
  },
}))
