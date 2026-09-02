import { create } from 'zustand';
import { CYCLONES } from '../data/cyclones';
import type { Cyclone, Observation } from '../data/cyclones';

export interface LiveData {
  status: 'LIVE' | 'UPDATING' | 'STALE' | 'OFFLINE';
  lastUpdated: string | null;
  atmosphere: {
    windSpeed:     number | null;
    windDirection: number | null;
    pressure:      number | null;
    humidity:      number | null;
    rainfall:      number | null;
  };
  ocean: {
    sst:              number | null;
    currentVelocity:  number | null;
    currentDirection: number | null;
    waveHeight:       number | null;
  };
  cyclone: { active: boolean };
}

interface CycloneState {
  mode:            'LIVE' | 'HISTORICAL';
  liveBasin:       'Bay of Bengal' | 'Arabian Sea';
  activeCyclone:   Cyclone;
  timelineIndex:   number;
  isPlaying:       boolean;
  introComplete:   boolean;
  liveData:        LiveData;
  evidenceOpen:    boolean;        // ← new: controls EvidenceDrawer

  // Actions
  setMode:           (mode: 'LIVE' | 'HISTORICAL') => void;
  setLiveBasin:      (basin: 'Bay of Bengal' | 'Arabian Sea') => void;
  setActiveCyclone:  (cycloneId: string) => void;
  setTimelineIndex:  (index: number) => void;
  togglePlay:        () => void;
  setIntroComplete:  (complete: boolean) => void;
  fetchLiveData:     () => Promise<void>;
  openEvidence:      () => void;
  closeEvidence:     () => void;

  // Derived helpers
  getCurrentObservation: () => Observation;
}

const DEFAULT_LIVE_DATA: LiveData = {
  status:      'UPDATING',
  lastUpdated: null,
  atmosphere:  { windSpeed: null, windDirection: null, pressure: null, humidity: null, rainfall: null },
  ocean:       { sst: null, currentVelocity: null, currentDirection: null, waveHeight: null },
  cyclone:     { active: false },
};

export const useCycloneStore = create<CycloneState>((set, get) => ({
  mode:          'LIVE',
  liveBasin:     'Bay of Bengal',
  activeCyclone: CYCLONES[0],
  timelineIndex: 0,
  isPlaying:     false,
  introComplete: false,
  liveData:      DEFAULT_LIVE_DATA,
  evidenceOpen:  false,

  setMode: (mode) => {
    set({ mode });
    if (mode === 'LIVE') get().fetchLiveData();
  },

  setLiveBasin: (basin) => {
    set({ liveBasin: basin });
    get().fetchLiveData();
  },

  setActiveCyclone: (cycloneId) => {
    const cyclone = CYCLONES.find(c => c.id === cycloneId);
    if (cyclone) {
      set({ activeCyclone: cyclone, timelineIndex: 0, mode: 'HISTORICAL', isPlaying: false });
    }
  },

  setTimelineIndex: (index) => {
    const { activeCyclone } = get();
    const clamped = Math.max(0, Math.min(index, activeCyclone.observations.length - 1));
    set({ timelineIndex: clamped });
  },

  togglePlay:       () => set(s => ({ isPlaying: !s.isPlaying })),
  setIntroComplete: (c) => set({ introComplete: c }),
  openEvidence:     () => set({ evidenceOpen: true }),
  closeEvidence:    () => set({ evidenceOpen: false }),

  getCurrentObservation: () => {
    const { activeCyclone, timelineIndex } = get();
    return activeCyclone.observations[timelineIndex];
  },

  fetchLiveData: async () => {
    set(s => ({ liveData: { ...s.liveData, status: 'UPDATING' } }));
    try {
      const { liveBasin } = get();
      // Bay of Bengal approx center (15N, 88E), Arabian Sea approx center (17N, 68E)
      const lat = liveBasin === 'Bay of Bengal' ? 15.0 : 17.0;
      const lng = liveBasin === 'Bay of Bengal' ? 88.0 : 68.0;

      const [weatherRes, marineRes] = await Promise.all([
        fetch(`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lng}&current=temperature_2m,relative_humidity_2m,precipitation,surface_pressure,wind_speed_10m,wind_direction_10m&wind_speed_unit=kmh`),
        fetch(`https://marine-api.open-meteo.com/v1/marine?latitude=${lat}&longitude=${lng}&current=wave_height,ocean_current_velocity,ocean_current_direction`),
      ]);

      const weather = await weatherRes.json();
      const marine  = await marineRes.json();

      set({
        liveData: {
          status:      'LIVE',
          lastUpdated: new Date().toISOString(),
          atmosphere: {
            windSpeed:     weather.current?.wind_speed_10m     ?? null,
            windDirection: weather.current?.wind_direction_10m ?? null,
            pressure:      weather.current?.surface_pressure   ?? null,
            humidity:      weather.current?.relative_humidity_2m ?? null,
            rainfall:      weather.current?.precipitation       ?? null,
          },
          ocean: {
            sst:              weather.current?.temperature_2m         ?? null,
            currentVelocity:  marine.current?.ocean_current_velocity  ?? null,
            currentDirection: marine.current?.ocean_current_direction ?? null,
            waveHeight:       marine.current?.wave_height             ?? null,
          },
          cyclone: { active: false },
        },
      });
    } catch {
      set(s => ({ liveData: { ...s.liveData, status: 'OFFLINE' } }));
    }
  },
}));
