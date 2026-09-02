// ─────────────────────────────────────────────────────────────────────────────
// CycloneWatch — cyclone data
// Sources: IMD/RSMC New Delhi preliminary reports, IBTrACS v4.01, dossiers
// ─────────────────────────────────────────────────────────────────────────────

export type AlertLevel = 'NORMAL' | 'WATCH' | 'WARNING' | 'HAZARDOUS' | 'CRITICAL';
export type CycloneStatus =
  | 'FORMATION'
  | 'DEVELOPING'
  | 'ACTIVE'
  | 'PEAK INTENSITY'
  | 'LANDFALL'
  | 'DISSIPATING'
  | 'HISTORICAL';
export type CycloneCategory = 'CS' | 'SCS' | 'VSCS' | 'ESCS' | 'SUCS';

export interface Observation {
  timestamp: string;       // ISO-8601 UTC
  windSpeed: number;       // km/h sustained
  gustSpeed: number;       // km/h
  pressure: number;        // hPa
  lat: number;
  lng: number;
  sst: number;             // °C sea surface temperature
  currentVelocity: number; // m/s ocean current
  rainfall24h: number;     // mm
  movementSpeed: number;   // km/h
  heading: number;         // degrees
  status: CycloneStatus;
  category: CycloneCategory;
}

export interface Cyclone {
  id: string;
  name: string;
  year: number;
  basin: string;           // "Arabian Sea" | "Bay of Bengal"
  peakWind: number;        // km/h
  minPressure: number;     // hPa
  trackLengthKm: number;
  landfallRegion: string;
  landfallTime: string;    // ISO-8601 UTC
  observations: Observation[];
  forecastTrack: { lat: number; lng: number }[];
  // For CycloneWatch ML positioning — was this a gap-case for IMD?
  imdGapCase: boolean;
  imdGapNote?: string;
}

export const CYCLONES: Cyclone[] = [

  // ── BIPARJOY 2023 ─────────────────────────────────────────────────────────
  {
    id: 'biparjoy-2023',
    name: 'BIPARJOY',
    year: 2023,
    basin: 'Arabian Sea',
    peakWind: 165,
    minPressure: 958,
    trackLengthKm: 2400,
    landfallRegion: 'Near Jakhau Port, Gujarat, India',
    landfallTime: '2023-06-15T13:30:00Z',
    imdGapCase: false,
    forecastTrack: [
      { lat: 17.5, lng: 67.5 },
      { lat: 19.0, lng: 67.0 },
      { lat: 21.0, lng: 68.0 },
      { lat: 22.8, lng: 68.8 },
    ],
    observations: [
      {
        timestamp: '2023-06-06T06:00:00Z',
        windSpeed: 65, gustSpeed: 85, pressure: 994,
        lat: 11.9, lng: 66.0,
        sst: 30.5, currentVelocity: 1.1, rainfall24h: 30,
        movementSpeed: 8, heading: 345,
        status: 'FORMATION', category: 'CS',
      },
      {
        timestamp: '2023-06-09T12:00:00Z',
        windSpeed: 95, gustSpeed: 115, pressure: 985,
        lat: 13.5, lng: 65.8,
        sst: 31.0, currentVelocity: 1.3, rainfall24h: 55,
        movementSpeed: 6, heading: 340,
        status: 'DEVELOPING', category: 'SCS',
      },
      {
        timestamp: '2023-06-13T00:00:00Z',
        windSpeed: 140, gustSpeed: 160, pressure: 968,
        lat: 16.2, lng: 67.1,
        sst: 31.5, currentVelocity: 1.8, rainfall24h: 95,
        movementSpeed: 10, heading: 10,
        status: 'ACTIVE', category: 'VSCS',
      },
      {
        timestamp: '2023-06-14T12:00:00Z',
        windSpeed: 165, gustSpeed: 185, pressure: 958,
        lat: 20.2, lng: 67.4,
        sst: 30.8, currentVelocity: 2.0, rainfall24h: 130,
        movementSpeed: 14, heading: 355,
        status: 'PEAK INTENSITY', category: 'ESCS',
      },
      {
        timestamp: '2023-06-15T13:30:00Z',
        windSpeed: 120, gustSpeed: 140, pressure: 976,
        lat: 23.1, lng: 68.8,
        sst: 29.0, currentVelocity: 1.4, rainfall24h: 180,
        movementSpeed: 18, heading: 350,
        status: 'LANDFALL', category: 'VSCS',
      },
    ],
  },

  // ── AMPHAN 2020 ───────────────────────────────────────────────────────────
  {
    id: 'amphan-2020',
    name: 'AMPHAN',
    year: 2020,
    basin: 'Bay of Bengal',
    peakWind: 240,
    minPressure: 920,
    trackLengthKm: 2200,
    landfallRegion: 'West Bengal / Bangladesh Coast',
    landfallTime: '2020-05-20T10:00:00Z',
    imdGapCase: false,
    forecastTrack: [
      { lat: 18.5, lng: 87.0 },
      { lat: 20.5, lng: 87.8 },
      { lat: 22.5, lng: 88.5 },
      { lat: 24.0, lng: 89.5 },
    ],
    observations: [
      {
        timestamp: '2020-05-16T00:00:00Z',
        windSpeed: 65, gustSpeed: 85, pressure: 994,
        lat: 10.4, lng: 87.0,
        sst: 31.0, currentVelocity: 1.2, rainfall24h: 45,
        movementSpeed: 10, heading: 360,
        status: 'FORMATION', category: 'CS',
      },
      {
        timestamp: '2020-05-17T12:00:00Z',
        windSpeed: 110, gustSpeed: 135, pressure: 980,
        lat: 12.5, lng: 86.5,
        sst: 31.5, currentVelocity: 1.5, rainfall24h: 85,
        movementSpeed: 12, heading: 350,
        status: 'DEVELOPING', category: 'SCS',
      },
      {
        timestamp: '2020-05-18T00:00:00Z',
        windSpeed: 240, gustSpeed: 265, pressure: 920,
        lat: 15.0, lng: 86.2,
        sst: 32.0, currentVelocity: 2.1, rainfall24h: 184,
        movementSpeed: 18, heading: 62,
        status: 'PEAK INTENSITY', category: 'SUCS',
      },
      {
        timestamp: '2020-05-19T12:00:00Z',
        windSpeed: 200, gustSpeed: 230, pressure: 940,
        lat: 18.5, lng: 87.0,
        sst: 30.5, currentVelocity: 1.8, rainfall24h: 210,
        movementSpeed: 22, heading: 45,
        status: 'ACTIVE', category: 'ESCS',
      },
      {
        timestamp: '2020-05-20T10:00:00Z',
        windSpeed: 155, gustSpeed: 180, pressure: 965,
        lat: 22.0, lng: 88.5,
        sst: 28.0, currentVelocity: 1.0, rainfall24h: 250,
        movementSpeed: 28, heading: 40,
        status: 'LANDFALL', category: 'VSCS',
      },
    ],
  },

  // ── FANI 2019 ─────────────────────────────────────────────────────────────
  // Source: IMD Preliminary Report on ESCS FANI (2019); peak 115 kt / 932 hPa
  {
    id: 'fani-2019',
    name: 'FANI',
    year: 2019,
    basin: 'Bay of Bengal',
    peakWind: 213,
    minPressure: 932,
    trackLengthKm: 3030,
    landfallRegion: 'Near Puri, Odisha, India',
    landfallTime: '2019-05-03T02:30:00Z',
    imdGapCase: false,
    imdGapNote: 'IMD accurately forecast this landfall 72h out — strong IMD performance case. Contrast with Ockhi.',
    forecastTrack: [
      { lat: 16.5, lng: 84.8 },
      { lat: 18.5, lng: 85.2 },
      { lat: 20.2, lng: 85.8 },
    ],
    observations: [
      {
        timestamp: '2019-04-27T00:00:00Z',
        windSpeed: 65, gustSpeed: 80, pressure: 993,
        lat: 7.0, lng: 84.5,
        sst: 30.5, currentVelocity: 1.0, rainfall24h: 35,
        movementSpeed: 9, heading: 330,
        status: 'FORMATION', category: 'CS',
      },
      {
        timestamp: '2019-04-30T12:00:00Z',
        windSpeed: 130, gustSpeed: 155, pressure: 968,
        lat: 10.5, lng: 84.0,
        sst: 31.0, currentVelocity: 1.4, rainfall24h: 75,
        movementSpeed: 10, heading: 330,
        status: 'DEVELOPING', category: 'VSCS',
      },
      {
        timestamp: '2019-05-02T12:00:00Z',
        windSpeed: 213, gustSpeed: 240, pressure: 932,
        lat: 16.5, lng: 84.8,
        sst: 31.0, currentVelocity: 1.8, rainfall24h: 150,
        movementSpeed: 15, heading: 350,
        status: 'PEAK INTENSITY', category: 'ESCS',
      },
      {
        timestamp: '2019-05-03T02:30:00Z',
        windSpeed: 185, gustSpeed: 205, pressure: 950,
        lat: 19.8, lng: 85.8,
        sst: 29.5, currentVelocity: 1.2, rainfall24h: 220,
        movementSpeed: 20, heading: 20,
        status: 'LANDFALL', category: 'ESCS',
      },
    ],
  },

  // ── VAYU 2019 ─────────────────────────────────────────────────────────────
  // Source: IMD VSCS VAYU report; no landfall — skirted Gujarat coast
  {
    id: 'vayu-2019',
    name: 'VAYU',
    year: 2019,
    basin: 'Arabian Sea',
    peakWind: 148,
    minPressure: 970,
    trackLengthKm: 1862,
    landfallRegion: 'No landfall — skirted Gujarat coast',
    landfallTime: '2019-06-13T00:00:00Z', // closest approach
    imdGapCase: true,
    imdGapNote: 'Track shifted at last minute — initial landfall forecast changed substantially. Classic forecast uncertainty case.',
    forecastTrack: [
      { lat: 22.5, lng: 68.0 },
      { lat: 23.5, lng: 67.0 },
    ],
    observations: [
      {
        timestamp: '2019-06-10T00:00:00Z',
        windSpeed: 65, gustSpeed: 85, pressure: 993,
        lat: 14.5, lng: 69.0,
        sst: 31.0, currentVelocity: 1.1, rainfall24h: 40,
        movementSpeed: 10, heading: 350,
        status: 'FORMATION', category: 'CS',
      },
      {
        timestamp: '2019-06-12T00:00:00Z',
        windSpeed: 148, gustSpeed: 165, pressure: 970,
        lat: 19.0, lng: 69.5,
        sst: 31.5, currentVelocity: 1.6, rainfall24h: 90,
        movementSpeed: 13, heading: 340,
        status: 'PEAK INTENSITY', category: 'VSCS',
      },
      {
        timestamp: '2019-06-13T00:00:00Z',
        windSpeed: 120, gustSpeed: 140, pressure: 980,
        lat: 22.0, lng: 68.5,
        sst: 30.0, currentVelocity: 1.3, rainfall24h: 120,
        movementSpeed: 15, heading: 320,
        status: 'ACTIVE', category: 'SCS',
      },
      {
        timestamp: '2019-06-16T00:00:00Z',
        windSpeed: 75, gustSpeed: 95, pressure: 990,
        lat: 22.5, lng: 66.0,
        sst: 29.0, currentVelocity: 1.0, rainfall24h: 50,
        movementSpeed: 10, heading: 290,
        status: 'DISSIPATING', category: 'CS',
      },
    ],
  },

  // ── TAUKTAE 2021 ──────────────────────────────────────────────────────────
  // Source: IMD Preliminary Report ESCS TAUKTAE; peak 100 kt / 950 hPa
  {
    id: 'tauktae-2021',
    name: 'TAUKTAE',
    year: 2021,
    basin: 'Arabian Sea',
    peakWind: 185,
    minPressure: 950,
    trackLengthKm: 1880,
    landfallRegion: 'Saurashtra coast, Gujarat',
    landfallTime: '2021-05-17T15:30:00Z',
    imdGapCase: false,
    forecastTrack: [
      { lat: 18.0, lng: 71.5 },
      { lat: 20.5, lng: 71.0 },
      { lat: 22.5, lng: 70.5 },
    ],
    observations: [
      {
        timestamp: '2021-05-14T00:00:00Z',
        windSpeed: 70, gustSpeed: 90, pressure: 991,
        lat: 10.0, lng: 73.0,
        sst: 31.5, currentVelocity: 1.0, rainfall24h: 50,
        movementSpeed: 10, heading: 355,
        status: 'FORMATION', category: 'CS',
      },
      {
        timestamp: '2021-05-15T12:00:00Z',
        windSpeed: 130, gustSpeed: 155, pressure: 968,
        lat: 13.5, lng: 72.0,
        sst: 32.0, currentVelocity: 1.5, rainfall24h: 100,
        movementSpeed: 12, heading: 348,
        status: 'DEVELOPING', category: 'VSCS',
      },
      {
        timestamp: '2021-05-16T18:00:00Z',
        windSpeed: 185, gustSpeed: 210, pressure: 950,
        lat: 17.0, lng: 71.5,
        sst: 32.5, currentVelocity: 2.0, rainfall24h: 175,
        movementSpeed: 14, heading: 345,
        status: 'PEAK INTENSITY', category: 'ESCS',
      },
      {
        timestamp: '2021-05-17T15:30:00Z',
        windSpeed: 150, gustSpeed: 175, pressure: 966,
        lat: 20.9, lng: 71.1,
        sst: 30.0, currentVelocity: 1.4, rainfall24h: 200,
        movementSpeed: 16, heading: 340,
        status: 'LANDFALL', category: 'ESCS',
      },
    ],
  },

  // ── YAAS 2021 ─────────────────────────────────────────────────────────────
  // Source: IMD Preliminary Report VSCS YAAS; peak 75-85 kt / ~970 hPa
  {
    id: 'yaas-2021',
    name: 'YAAS',
    year: 2021,
    basin: 'Bay of Bengal',
    peakWind: 155,
    minPressure: 970,
    trackLengthKm: 703,
    landfallRegion: 'Near Balasore, North Odisha Coast',
    landfallTime: '2021-05-26T03:30:00Z',
    imdGapCase: false,
    forecastTrack: [
      { lat: 20.0, lng: 87.5 },
      { lat: 21.5, lng: 87.2 },
    ],
    observations: [
      {
        timestamp: '2021-05-23T00:00:00Z',
        windSpeed: 65, gustSpeed: 85, pressure: 993,
        lat: 16.5, lng: 89.5,
        sst: 30.5, currentVelocity: 1.0, rainfall24h: 45,
        movementSpeed: 9, heading: 340,
        status: 'FORMATION', category: 'CS',
      },
      {
        timestamp: '2021-05-25T12:00:00Z',
        windSpeed: 155, gustSpeed: 175, pressure: 970,
        lat: 18.5, lng: 88.5,
        sst: 31.0, currentVelocity: 1.5, rainfall24h: 140,
        movementSpeed: 12, heading: 335,
        status: 'PEAK INTENSITY', category: 'VSCS',
      },
      {
        timestamp: '2021-05-26T03:30:00Z',
        windSpeed: 130, gustSpeed: 145, pressure: 980,
        lat: 21.1, lng: 87.0,
        sst: 29.5, currentVelocity: 1.2, rainfall24h: 185,
        movementSpeed: 15, heading: 330,
        status: 'LANDFALL', category: 'VSCS',
      },
    ],
  },

  // ── MOCHA 2023 ────────────────────────────────────────────────────────────
  // Source: IMD ESCS MOCHA report; peak 110 kt / ~938 hPa
  {
    id: 'mocha-2023',
    name: 'MOCHA',
    year: 2023,
    basin: 'Bay of Bengal',
    peakWind: 204,
    minPressure: 938,
    trackLengthKm: 2000,
    landfallRegion: 'Kyaukpyu region, Myanmar / Bangladesh border',
    landfallTime: '2023-05-14T06:00:00Z',
    imdGapCase: false,
    forecastTrack: [
      { lat: 17.0, lng: 92.5 },
      { lat: 20.0, lng: 92.8 },
    ],
    observations: [
      {
        timestamp: '2023-05-09T00:00:00Z',
        windSpeed: 55, gustSpeed: 70, pressure: 997,
        lat: 10.0, lng: 88.5,
        sst: 31.0, currentVelocity: 1.0, rainfall24h: 30,
        movementSpeed: 8, heading: 30,
        status: 'FORMATION', category: 'CS',
      },
      {
        timestamp: '2023-05-11T12:00:00Z',
        windSpeed: 120, gustSpeed: 145, pressure: 968,
        lat: 13.5, lng: 89.5,
        sst: 31.0, currentVelocity: 1.5, rainfall24h: 80,
        movementSpeed: 12, heading: 25,
        status: 'DEVELOPING', category: 'VSCS',
      },
      {
        timestamp: '2023-05-13T12:00:00Z',
        windSpeed: 204, gustSpeed: 225, pressure: 938,
        lat: 16.0, lng: 91.0,
        sst: 31.5, currentVelocity: 2.2, rainfall24h: 200,
        movementSpeed: 16, heading: 30,
        status: 'PEAK INTENSITY', category: 'ESCS',
      },
      {
        timestamp: '2023-05-14T06:00:00Z',
        windSpeed: 175, gustSpeed: 200, pressure: 955,
        lat: 19.5, lng: 92.9,
        sst: 30.0, currentVelocity: 1.7, rainfall24h: 260,
        movementSpeed: 22, heading: 35,
        status: 'LANDFALL', category: 'ESCS',
      },
    ],
  },

  // ── OCKHI 2017 ────────────────────────────────────────────────────────────
  // The IMD gap case — first advisory issued ~36-48h after formation
  {
    id: 'ockhi-2017',
    name: 'OCKHI',
    year: 2017,
    basin: 'Arabian Sea',
    peakWind: 165,
    minPressure: 976,
    trackLengthKm: 2200,
    landfallRegion: 'Gujarat coast (weakening remnant)',
    landfallTime: '2017-12-05T00:00:00Z',
    imdGapCase: true,
    imdGapNote:
      'CRITICAL GAP CASE: Ockhi formed off Sri Lanka on 29 Nov. IMD issued the first cyclone watch only on 1 Dec — ~36-48h late. 218+ fishermen were lost at sea with no warning. CycloneWatch would have flagged curved_band → banding structural signatures at T-36h.',
    forecastTrack: [
      { lat: 18.0, lng: 70.5 },
      { lat: 21.0, lng: 68.0 },
    ],
    observations: [
      {
        timestamp: '2017-11-29T00:00:00Z',
        windSpeed: 45, gustSpeed: 60, pressure: 1000,
        lat: 7.5, lng: 79.0,
        sst: 30.5, currentVelocity: 0.8, rainfall24h: 25,
        movementSpeed: 7, heading: 330,
        status: 'FORMATION', category: 'CS',
      },
      {
        timestamp: '2017-11-30T12:00:00Z',
        windSpeed: 85, gustSpeed: 105, pressure: 988,
        lat: 9.5, lng: 76.5,
        sst: 30.8, currentVelocity: 1.2, rainfall24h: 65,
        movementSpeed: 10, heading: 320,
        status: 'DEVELOPING', category: 'SCS',
      },
      {
        timestamp: '2017-12-01T12:00:00Z',
        windSpeed: 130, gustSpeed: 155, pressure: 980,
        lat: 12.0, lng: 73.5,
        sst: 31.0, currentVelocity: 1.5, rainfall24h: 110,
        movementSpeed: 14, heading: 310,
        status: 'ACTIVE', category: 'VSCS',
      },
      {
        timestamp: '2017-12-02T12:00:00Z',
        windSpeed: 165, gustSpeed: 185, pressure: 976,
        lat: 15.0, lng: 70.5,
        sst: 31.5, currentVelocity: 1.8, rainfall24h: 130,
        movementSpeed: 18, heading: 305,
        status: 'PEAK INTENSITY', category: 'ESCS',
      },
      {
        timestamp: '2017-12-05T00:00:00Z',
        windSpeed: 80, gustSpeed: 100, pressure: 992,
        lat: 22.0, lng: 67.5,
        sst: 28.5, currentVelocity: 0.9, rainfall24h: 60,
        movementSpeed: 22, heading: 350,
        status: 'DISSIPATING', category: 'CS',
      },
    ],
  },

  // ── REMAL 2024 ────────────────────────────────────────────────────────────
  {
    id: 'remal-2024',
    name: 'REMAL',
    year: 2024,
    basin: 'Bay of Bengal',
    peakWind: 135,
    minPressure: 978,
    trackLengthKm: 850,
    landfallRegion: 'West Bengal / Bangladesh',
    landfallTime: '2024-05-26T18:00:00Z',
    imdGapCase: false,
    forecastTrack: [
      { lat: 21.0, lng: 89.3 },
      { lat: 22.0, lng: 89.2 },
    ],
    observations: [
      {
        timestamp: '2024-05-25T00:00:00Z',
        windSpeed: 75, gustSpeed: 95, pressure: 990,
        lat: 18.0, lng: 89.5,
        sst: 30.5, currentVelocity: 1.1, rainfall24h: 55,
        movementSpeed: 12, heading: 360,
        status: 'DEVELOPING', category: 'CS',
      },
      {
        timestamp: '2024-05-26T06:00:00Z',
        windSpeed: 135, gustSpeed: 150, pressure: 978,
        lat: 20.0, lng: 89.5,
        sst: 31.0, currentVelocity: 1.4, rainfall24h: 130,
        movementSpeed: 14, heading: 355,
        status: 'PEAK INTENSITY', category: 'SCS',
      },
      {
        timestamp: '2024-05-26T18:00:00Z',
        windSpeed: 110, gustSpeed: 130, pressure: 985,
        lat: 21.8, lng: 89.2,
        sst: 29.5, currentVelocity: 1.2, rainfall24h: 180,
        movementSpeed: 16, heading: 350,
        status: 'LANDFALL', category: 'SCS',
      },
    ],
  },
];

// Default map center for each basin
export const BASIN_CENTERS: Record<string, [number, number]> = {
  'Arabian Sea': [17.0, 68.0],
  'Bay of Bengal': [15.0, 88.0],
};

export const BASELINES = {
  windSpeed: 220,      // km/h — threshold for hazardous display
  pressureDropRate: 10, // hPa/6hr
  rainfall24h: 150,    // mm
};

// Pattern label display names (must match backend taxonomy)
export const PATTERN_LABELS: Record<string, string> = {
  eye: 'Eye',
  banding: 'Banding',
  curved_band: 'Curved Band',
  shear_affected: 'Shear-Affected',
  disorganized: 'Disorganized',
  unlabeled: 'Analyzing...',
};

export const PATTERN_COLORS: Record<string, string> = {
  eye: '#ef4444',
  banding: '#f97316',
  curved_band: '#eab308',
  shear_affected: '#a855f7',
  disorganized: '#6b7280',
  unlabeled: '#4FC3E0',
};
