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

  targetContainer: '#points',
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
  gatesMaxValue: '#gates-max-value',

  expLineChartCanvas: '#exp-chart',
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
      { value: '0', label: 'No Angle' },
      { value: '1', label: '-60° ~ -45°' },
      { value: '2', label: '-45° ~ -14°' },
      { value: '3', label: '-15° ~ +14°' },
      { value: '4', label: '+15° ~ +44°' },
      { value: '5', label: '+45° ~ +60°' }
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
      { value: '1', label: 'Wood' },
      { value: '2', label: 'Concrete' },
      { value: '3', label: 'Metal' }
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
      { value: '12', label: '12m' },
      { value: '13', label: '13m' },
      { value: '14', label: '14m' },
      { value: '15', label: '15m' }
    ]
  };

export const MAIN = {
  delaySystemIconStatus: 2000,
  delayMonitorInterval: 100,
  delayRecordingAction: 1000
};

export const RADAR = {
  refreshRate: 100,
  maxDistance: 10_000
};

export const HEATMAP = {
  radius: 1,
  blur: 0,
  maxColumns: 150, // 5 seconds of data
  subcarriers: 85, // TODO: Update the subcarrier count on launch
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
  suggestedMin: -80,
  suggestedMax: -20
}

export const D3PLOT = {
  svgId: '#d3-plot',
  delayD3Plot: 1000,
  gridStrokeColor: 'black',
  gridStrokeWidth: 0.3,
  gridFillOpacity: 0.8,
  pointRadius: 3,
  pointOpacity: 1,
  yScaleStrokeColor: 'black',
  yScaleStrokeWidth: 0.5,
  yTextFontFamily: 'system-ui, sans-serif',
  origin: { x: 400, y: 200 }, // Center of the plot
  startAngle: 180, // Initial rotation angle
  scale: 20, // Scale factor for the plot
  dragRotateFactor: 230,
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
