// ─────────────────────────────────────────────────────────────────────────────
// CycloneWatch — Global state store (Zustand)
//
// Refactored:
//  - All `any` types replaced with proper interfaces from types/api.ts
//  - API calls delegated to lib/api.ts (single import point)
//  - console.error replaced with structured error state
//  - getCurrentObservation properly typed
// ─────────────────────────────────────────────────────────────────────────────

import { create } from 'zustand';
import * as api from '../lib/api';
import type {
  ReplayResponse,
  MetricsResponse,
  ClassificationsResponse,
  CurrentObservation,
} from '../types/api';

// ── Live data shape ─────────────────────────────────────────────────────────

export interface LiveData {
  status: 'LIVE' | 'UPDATING' | 'STALE' | 'OFFLINE';
  lastUpdated: string | null;
  atmosphere: {
    windSpeed: number | null;
    windDirection: number | null;
    pressure: number | null;
    humidity: number | null;
    rainfall: number | null;
  };
  ocean: {
    sst: number | null;
    currentVelocity: number | null;
    currentDirection: number | null;
    waveHeight: number | null;
  };
  cyclone: {
    active: boolean;
    lat?: number;
    lng?: number;
    speed?: number;
  };
}

export type AppPage = 'home' | 'live' | 'historical' | 'architecture' | 'reports';

// ── Store interface ─────────────────────────────────────────────────────────

interface CycloneState {
  mode: 'LIVE' | 'HISTORICAL';
  activePage: AppPage;
  sidebarCollapsed: boolean;
  liveBasin: 'Bay of Bengal' | 'Arabian Sea';
  activeEventId: string;
  timelineIndex: number;
  isPlaying: boolean;
  introComplete: boolean;
  liveData: LiveData;
  evidenceOpen: boolean;

  // Typed API data (no more `any`)
  apiReplayData: ReplayResponse | null;
  apiMetricsData: MetricsResponse | null;
  apiClassificationsData: ClassificationsResponse | null;
  isLoadingData: boolean;

  // Actions
  setActivePage: (page: AppPage) => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setMode: (mode: 'LIVE' | 'HISTORICAL') => void;
  setLiveBasin: (basin: 'Bay of Bengal' | 'Arabian Sea') => void;
  setActiveCyclone: (cycloneId: string) => void;
  setTimelineIndex: (index: number) => void;
  togglePlay: () => void;
  setIntroComplete: (complete: boolean) => void;
  fetchLiveData: () => Promise<void>;
  openEvidence: () => void;
  closeEvidence: () => void;
  fetchEventData: (eventId: string) => Promise<void>;

  // Derived helpers
  getCurrentObservation: () => CurrentObservation | null;
}

// ── Default state ───────────────────────────────────────────────────────────

const DEFAULT_LIVE_DATA: LiveData = {
  status: 'UPDATING',
  lastUpdated: null,
  atmosphere: { windSpeed: null, windDirection: null, pressure: null, humidity: null, rainfall: null },
  ocean: { sst: null, currentVelocity: null, currentDirection: null, waveHeight: null },
  cyclone: { active: false },
};

// ── Store ───────────────────────────────────────────────────────────────────

export const useCycloneStore = create<CycloneState>((set, get) => ({
  mode: 'LIVE',
  activePage: 'home',
  sidebarCollapsed: false,
  liveBasin: 'Bay of Bengal',
  activeEventId: 'biparjoy_2023',
  timelineIndex: 0,
  isPlaying: false,
  introComplete: false,
  liveData: DEFAULT_LIVE_DATA,
  evidenceOpen: false,

  apiReplayData: null,
  apiMetricsData: null,
  apiClassificationsData: null,
  isLoadingData: false,

  setActivePage: (page) => set({ activePage: page }),
  setSidebarCollapsed: (collapsed) => set({ sidebarCollapsed: collapsed }),

  setMode: (mode) => {
    set({ mode });
    if (mode === 'LIVE') get().fetchLiveData();
  },

  setLiveBasin: (basin) => {
    set({ liveBasin: basin });
    get().fetchLiveData();
  },

  setActiveCyclone: (cycloneId) => {
    set({
      activeEventId: cycloneId,
      timelineIndex: 0,
      mode: 'HISTORICAL',
      isPlaying: false,
    });
    get().fetchEventData(cycloneId);
  },

  setTimelineIndex: (index) => {
    const { apiReplayData } = get();
    if (!apiReplayData?.steps?.length) return;
    const clamped = Math.max(0, Math.min(index, apiReplayData.steps.length - 1));
    set({ timelineIndex: clamped });
  },

  togglePlay: () => set((s) => ({ isPlaying: !s.isPlaying })),
  setIntroComplete: (c) => set({ introComplete: c }),
  openEvidence: () => set({ evidenceOpen: true }),
  closeEvidence: () => set({ evidenceOpen: false }),

  getCurrentObservation: (): CurrentObservation | null => {
    const { apiReplayData, apiClassificationsData, timelineIndex } = get();
    if (!apiReplayData?.steps || !apiClassificationsData?.classifications) return null;

    const step = apiReplayData.steps[timelineIndex];
    if (!step) return null;

    // Find the matching classification for the base time
    const classification =
      apiClassificationsData.classifications.find((c) => c.timestamp === step.time) ??
      apiClassificationsData.classifications[timelineIndex];

    if (!classification) return null;

    let prevLat: number | null = null;
    let prevLng: number | null = null;
    let hoursSincePrev: number | null = null;

    if (timelineIndex > 0) {
      const prevStep = apiReplayData.steps[timelineIndex - 1];
      const prevClass =
        apiClassificationsData.classifications.find((c) => c.timestamp === prevStep.time) ??
        apiClassificationsData.classifications[timelineIndex - 1];

      if (prevClass) {
        prevLat = prevClass.center.lat;
        prevLng = prevClass.center.lon;
        const currTime = new Date(step.time).getTime();
        const prevTime = new Date(prevStep.time).getTime();
        hoursSincePrev = (currTime - prevTime) / (1000 * 60 * 60);
      }
    }

    return {
      timestamp: step.time,
      lat: classification.center.lat,
      lng: classification.center.lon,
      prevLat,
      prevLng,
      hoursSincePrev,
      step,
      classification,
    };
  },

  // ── Data fetching (via centralized API client) ────────────────────────────

  fetchEventData: async (eventId: string) => {
    set({ isLoadingData: true });
    const [replay, metrics, classifications] = await Promise.all([
      api.fetchReplay(eventId),
      api.fetchMetrics(eventId),
      api.fetchClassifications(eventId),
    ]);
    set({
      apiReplayData: replay,
      apiMetricsData: metrics,
      apiClassificationsData: classifications,
      isLoadingData: false,
    });
  },

  fetchLiveData: async () => {
    set((s) => ({ liveData: { ...s.liveData, status: 'UPDATING' } }));
    try {
      const { liveBasin } = get();
      const lat = liveBasin === 'Bay of Bengal' ? 15.0 : 17.0;
      const lng = liveBasin === 'Bay of Bengal' ? 88.0 : 68.0;

      const [weather, marine] = await Promise.all([
        api.fetchWeather(lat, lng),
        api.fetchMarine(lat, lng),
      ]);

      set({
        liveData: {
          status: 'LIVE',
          lastUpdated: weather?.current?.time
            ? new Date(weather.current.time).toISOString()
            : new Date().toISOString(),
          atmosphere: {
            windSpeed: weather?.current?.wind_speed_10m ?? null,
            windDirection: weather?.current?.wind_direction_10m ?? null,
            pressure: weather?.current?.surface_pressure ?? null,
            humidity: weather?.current?.relative_humidity_2m ?? null,
            rainfall: weather?.current?.precipitation ?? null,
          },
          ocean: {
            sst: weather?.current?.temperature_2m ?? null,
            currentVelocity: marine?.current?.ocean_current_velocity ?? null,
            currentDirection: marine?.current?.ocean_current_direction ?? null,
            waveHeight: marine?.current?.wave_height ?? null,
          },
          cyclone: { active: false },
        },
      });
    } catch {
      set((s) => ({ liveData: { ...s.liveData, status: 'OFFLINE' } }));
    }
  },
}));
