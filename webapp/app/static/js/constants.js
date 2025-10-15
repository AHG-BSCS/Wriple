export const SELECTORS = {
  recordModeBtn: '#record-mode-btn',
  monitorModeBtn: '#monitor-mode-btn',

  targetRadarBtn: '#target-radar-btn',
  amplitudeHeatmapBtn: '#amplitude-heatmap-btn',
  gatesHeatmapBtn: '#gates-heatmap-btn',
  expChartBtn: '#exp-line-chart-btn',
  d3PlotBtn: '#d3-plot-btn',

  sidebarContainer: '#sidebar-container',
  collapseBtn: '#collapse-btn',
  sidebarText: '.sidebar-collapse',

  monitorGroup: '.monitor-hidden',
  historyGroup: '.history-hidden',
  datasetGroup: '.dataset-hidden',

  monitorTabBtn: '#monitor-tab-btn',
  historyTabBtn: '#history-tab-btn',
  datasetTabBtn: '#dataset-tab-btn',
  settingsBtn: '#settings-tab-btn',
  infoBtn: '#info-tab-btn',
  darkModeSwitch: '#dark-mode-switch',

  presenceStatus: '#presence-status',
  signal_var: '#signal-var',
  packetCount: '#packets-count',
  packetLoss: '#packet-loss',
  expValue: '#exp-value',

  apStatus: "#ap-status",
  flaskStatus: "#flask-status",
  esp32Status: "#esp32-status",
  ld2420Status: "#ld2420-status",
  modelStatus: "#model-status",

  asideContainer: '#aside-container',
  
  targetAngle: '#target-angle',
  targetDistance: '#target-distance',
  targetEnergy: '#target-energy',

  metaClass: '#meta-class',
  metaTargetDistance: '#meta-target-distance',
  metaAngleRange: '#meta-angle-range',
  metaActivity: '#meta-activity',
  metaObstruction: '#meta-obstruction-type',
  metaPacketCount: '#meta-packet-count',
  metaSamplingRate: '#meta-sampling-rate',
  metaRecordingDate: '#meta-recording-date',

  targetContainer: '#points',
  radarContainer: '#radar-container',

  amplitudeCanvas: '#amplitude-heatmap',
  amplitudeHeatmapContainer: '#amplitude-heatmap-container',
  amplitudeMaxSlider: '#amplitude-max-slider',
  amplitudeMaxValue: '#amplitude-max-value',

  gatesCanvas: '#gates-heatmap',
  gatesHeatmapContainer: '#gates-heatmap-container',
  gatesMaxSlider: '#gates-max-slider',
  gatesMaxValue: '#gates-max-value',
  
  expLineChartCanvas: '#exp-chart',
  expLineChartContainer: '#exp-chart-container',

  d3PlotContainer: '#d3-plot-container',

  datasetList: '#dataset-list',
};

export const OPTIONS = {
    class: [
      { value: '0', label: 'Absence' },
      { value: '1', label: 'Presence' }
    ],
    target: [
      { value: '0', label: 'N/A' },
      { value: '1', label: '1' },
      { value: '2', label: '2' },
      { value: '3', label: '3' }
    ],
    state: [
      { value: '0', label: 'N/A' },
      { value: '1', label: 'Motionless' },
      { value: '2', label: 'Moving' }
    ],
    activity: [
      { value: '0', label: 'N/A' },
      { value: '1', label: 'Stand' },
      { value: '2', label: 'Sit' },
      { value: '3', label: 'Walking' },
      { value: '4', label: 'Running' }
    ],
    angle: [
      { value: '0', label: 'N/A' },
      { value: '1', label: '-60° to -21°' },
      { value: '2', label: '-20° to -6°' },
      { value: '3', label: '-5° to +5°' },
      { value: '4', label: '+6° to +20°' },
      { value: '5', label: '+21° to +60°' }
    ],
    distance: [
      { value: '0', label: 'N/A' },
      { value: '1', label: '1m' },
      { value: '2', label: '2m' },
      { value: '3', label: '3m' },
      { value: '4', label: '4m' },
      { value: '5', label: '5m' },
      { value: '6', label: '6m' },
      { value: '7', label: '7m' },
      { value: '8', label: '8m' },
      { value: '9', label: '9m' },
      { value: '10', label: '10m' },
      { value: '11', label: '11m' },
      { value: '12', label: '12m' },
      { value: '13', label: '13m' },
      { value: '14', label: '14m' },
      { value: '15', label: '15m' }
    ],
    obstructed: [
      { value: '0', label: 'No' },
      { value: '1', label: 'Yes' }
    ],
    obstruction: [
      { value: '0', label: 'None' },
      { value: '1', label: 'Concrete' },
      { value: '2', label: 'Wood' },
      { value: '3', label: 'Metal' }
    ],
    setup_spacing: [
      { value: '4', label: '4m' },
      { value: '5', label: '5m' },
      { value: '6', label: '6m' },
      { value: '7', label: '7m' },
      { value: '8', label: '8m' },
      { value: '9', label: '9m' },
      { value: '10', label: '10m' },
      { value: '11', label: '11m' },
      { value: '12', label: '12m' },
      { value: '13', label: '13m' },
      { value: '14', label: '14m' },
      { value: '15', label: '15m' },
      { value: '16', label: '16m' },
      { value: '17', label: '17m' },
      { value: '18', label: '18m' },
      { value: '19', label: '19m' },
      { value: '20', label: '20m' }
    ]
  };

export const MAIN = {
  delaySystemIconStatus: 2000,
  delayMonitorInterval: 125,
  delayPresenceInterval: 1000,
  delayRecordingAction: 1000
};

export const RADAR = {
  refreshRate: 333,
  maxDistance: 10_000
};

export const HEATMAP = {
  radius: 1,
  blur: 0,
  maxColumns: 150, // 5 seconds of data
  subcarriers: 79, // TODO: Update the subcarrier count on launch
  rangeGates: 16,
  dopplerBins: 20,
  delayCsi: 100,
  delayMmwave: 333 // Maximum LD2420 refresh rate
};

export const LINECHART = {
  height: 200,
  width: 680,
  tension: 0.3,
  pointRadius: 0,
  maxDataPoints: 120, // 30 seconds of data at 1Hz
  suggestedMin: 0,
  suggestedMax: 1
}

export const D3PLOT = {
  svgId: '#d3-plot',
  delayD3Plot: 333,
  gridStrokeColor: 'black',
  gridStrokeWidth: 0.3,
  gridFillOpacity: 0.8,
  pointRadius: 3,
  pointOpacity: 1,
  yScaleStrokeColor: 'black',
  yScaleStrokeWidth: 0.5,
  yTextFontFamily: 'system-ui, sans-serif',
  center: { x: 400, y: 350 },
  startYAngle: 90,
  startXAngle: 90.5,
  scale: 30,
  row: 20,
  dragRotateSensitivity: -360,
  animateDuration: 1000,
};

export const UI_COLORS = {
  tabSelectedColor: '#D1D5DB',
  tabDefaultColor: '#94A3B7',

  btnActiveColor: '#78350F',
  btnDefaultColor: '#1F2937',

  statusBarActiveColor: 'limegreen',
  statusBarInactiveColor: 'brown'
};
