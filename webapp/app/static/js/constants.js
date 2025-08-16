// constants.js - selectors, options and defaults
export const SELECTORS = {
  collapseBtn: '#collapse-btn',
  sidebar: '#sidebar',
  sidebarText: '.sidebar-collapse',

  monitorElements: '.monitor-hidden',
  historyElements: '.history-hidden',
  datasetElements: '.dataset-hidden',

  monitordTab: '#monitor-btn',
  historyTab: '#history-btn',
  datasetTab: '#dataset-btn',
  // settingsBtn: '#settings-btn',
  // infoBtn: '#info-btn',
  // darkModeSwitch: '#dark-mode-switch',

  presenceStatus: '#presence-status',
  target1Dist: '#target-1-distance',
  packetCount: '#packets-count',
  packetLoss: '#packet-loss',
  expValue: '#exp-value',

  apStatus: "#ap-status",
  flaskStatus: "#flask-status",
  esp32Status: "#esp32-status",
  ld2420Status: "#ld2420-status",
  rd03dStatus: "#rd03d-status",
  portStatus: "#port-status",
  modelStatus: "#model-status",

  datasetList: '#dataset-list',

  pointsContainer: '#points',
  radarContainer: '#radar-container',

  target1Angle: '#target1-angle',
  target2Angle: '#target2-angle',
  target3Angle: '#target3-angle',
  target1Distance: '#target1-distance',
  target2Distance: '#target2-distance',
  target3Distance: '#target3-distance',
  target1Speed: '#target1-speed',
  target2Speed: '#target2-speed',
  target3Speed: '#target3-speed',
  target1DistRes: '#target1-distance-res',
  target2DistRes: '#target2-distance-res',
  target3DistRes: '#target3-distance-res',

  recordModeBtn: '#record-mode-btn',
  monitorModeBtn: '#monitor-mode-btn',
  targetRadarBtn: '#target-radar-btn',
  amplitudeHeatmapBtn: '#amplitude-heatmap-btn',
  phaseHeatmapBtn: '#phase-heatmap-btn',
  gatesHeatmapBtn: '#gates-heatmap-btn',
  expChartBtn: '#exp-line-chart-btn',
  d3PlotBtn: '#d3-plot-btn',

  amplitudeHeatmapContainer: '#amplitude-heatmap-container',
  phaseHeatmapContainer: '#phase-heatmap-container',
  gatesHeatmapContainer: '#gates-heatmap-container',
  expChartContainer: '#exp-chart-container',
  d3PlotContainer: '#d3-plot-container',

  amplitudeCanvas: '#amplitude-heatmap',
  phaseCanvas: '#phase-heatmap',
  gatesCanvas: '#gates-heatmap',

  amplitudeMaxSlider: '#amplitude-max-slider',
  phaseMaxSlider: '#phase-max-slider',
  gatesMaxSlider: '#gates-max-slider',
  
  amplitudeMaxValue: '#amplitude-max-value',
  phaseMaxValue: '#phase-max-value',
  gatesMaxValue: '#gates-max-value'
};

export const OPTIONS = {
    class: [
      { value: '0', label: 'Absence' },
      { value: '1', label: 'Presence' }
    ],
    target: [
      { value: '0', label: 'No Target' },
      { value: '1', label: '1' },
      { value: '2', label: '2' },
      { value: '3', label: '3' }
    ],
    state: [
      { value: '0', label: 'No State' },
      { value: '1', label: 'Motionless' },
      { value: '2', label: 'Moving' }
    ],
    activity: [
      { value: '0', label: 'No Activity' },
      { value: '1', label: 'Stand' },
      { value: '2', label: 'Sit' },
      { value: '3', label: 'Walking' },
      { value: '4', label: 'Running' },
    ],
    angle: [
      { value: '360', label: 'No Angle' },
      { value: '-45', label: '-45°' },
      { value: '-30', label: '-30°' },
      { value: '-15', label: '-15°' },
      { value: '0', label: '0°' },
      { value: '15', label: '15°' },
      { value: '30', label: '30°' },
      { value: '45', label: '45°' }
    ],
    distance: [
      { value: '-1', label: 'No Distance' },
      { value: '1', label: '1m' },
      { value: '2', label: '2m' },
      { value: '3', label: '3m' },
      { value: '4', label: '4m' },
      { value: '5', label: '5m' },
      { value: '6', label: '6m' },
      { value: '7', label: '7m' },
      { value: '8', label: '8m' },
      { value: '9', label: '9m' },
      { value: '10', label: '10m' }
    ],
    obstructed: [
      { value: '0', label: 'No' },
      { value: '1', label: 'Yes' }
    ],
    obstruction: [
      { value: '0', label: 'None' },
      { value: '1', label: 'Plastic' },
      { value: '2', label: 'Wood' },
      { value: '3', label: 'Glass' },
      { value: '4', label: 'Concrete' },
      { value: '5', label: 'Metal' }
    ],
    spacing: [
      { value: '3', label: '3m' },
      { value: '4', label: '4m' },
      { value: '5', label: '5m' },
      { value: '6', label: '6m' },
      { value: '7', label: '7m' },
      { value: '8', label: '8m' },
      { value: '9', label: '9m' },
      { value: '10', label: '10m' },
      { value: '11', label: '11m' },
      { value: '12', label: '12m' }
    ]
  };

export const DEFAULTS = {
  SUBCARRIER_COUNT: 85,
  MAX_COLS: 160,
  DOPPLER_BINS: 20,
  RANGE_GATES: 16,
  d3PlotRefreshRate: 1000,
  radarRefreshRate: 100,
  heatmapRefreshRate: 100,
  gatesHeatmapRefreshRate: 333,
  systemStatusInterval: 2000,
  recordingDelay: 1000
};

export const UI_COLORS = {
  tabSelectedColor: '#D1D5DB',
  tabDefaultColor: '#94A3B7',

  btnActiveColor: '#78350F',
  btnDefaultColor: '#1F2937',

  statusBarActiveColor: 'limegreen',
  statusBarInactiveColor: 'brown'
};
