import { UI } from './ui.js';
import { API } from './api.js';
import { OptionsUI } from './options.js';
import { HeatmapVisualizer } from './visualizers/heatmap.js';
import { RadarVisualizer } from './visualizers/radar.js';
import { LineChart } from './visualizers/linechart.js';
import { D3Plot } from './visualizers/d3plot.js';
import { DEFAULTS } from './constants.js';

const ampHeatmap = new HeatmapVisualizer({
  canvas: UI.nodes.amplitudeCanvas,
  button: UI.nodes.amplitudeHeatmapBtn,
  container: UI.nodes.amplitudeHeatmapContainer,
  type: 'amplitude',
  maxValue: parseFloat(UI.sliderNodes.amplitudeMaxSlider.value),
  maxCols: DEFAULTS.MAX_COLS,
  subcarrierCount: DEFAULTS.SUBCARRIER_COUNT,
  refreshRate: DEFAULTS.heatmapRefreshRate
});

const phaseHeatmap = new HeatmapVisualizer({
  canvas: UI.nodes.phaseCanvas,
  button: UI.nodes.phaseHeatmapBtn,
  container: UI.nodes.phaseHeatmapContainer,
  type: 'phase',
  maxValue: parseFloat(UI.sliderNodes.phaseMaxSlider.value),
  maxCols: DEFAULTS.MAX_COLS,
  subcarrierCount: DEFAULTS.SUBCARRIER_COUNT,
  refreshRate: DEFAULTS.heatmapRefreshRate
});

const gatesHeatmap = new HeatmapVisualizer({
  canvas: UI.nodes.gatesCanvas,
  button: UI.nodes.gatesHeatmapBtn,
  container: UI.nodes.gatesHeatmapContainer,
  type: 'gates',
  maxValue: parseFloat(UI.sliderNodes.gatesMaxSlider.value),
  maxCols: DEFAULTS.DOPPLER_BINS,
  subcarrierCount: DEFAULTS.RANGE_GATES,
  refreshRate: DEFAULTS.heatmapRefreshRate
});

const expChart = new LineChart({
  context: '#exp-chart',
  button: UI.nodes.expChartBtn,
  container: UI.nodes.expChartContainer
});

const radar = new RadarVisualizer({
  ui: UI,
  expChart: expChart,
  button: UI.nodes.targetRadarBtn,
  pointsContainer: UI.nodes.pointsContainer
});

const d3plot = new D3Plot({
  svg: "#d3-plot",
  button: UI.nodes.d3PlotBtn,
  container: UI.nodes.d3PlotContainer,
  refreshRate: DEFAULTS.d3PlotRefreshRate
});

function clearVisualizers() {
  // Assuming that monitoring is stopped
  radar.clear();
  ampHeatmap.clear();
  phaseHeatmap.clear();
  gatesHeatmap.clear();
  expChart.clear();
  d3plot.clear();
  
  UI.setButtonDefault(UI.nodes.targetRadarBtn);
  UI.setHeaderDefault();
  UI.setAsidesDefault();
}

function stopVisualizers() {
  radar.stop();
  ampHeatmap.stop();
  phaseHeatmap.stop();
  gatesHeatmap.stop();
  d3plot.stop();

  UI.setButtonDefault(UI.nodes.targetRadarBtn);
  UI.setHeaderDefault();
  UI.setAsidesDefault();

  // Ensure to remove the status bar and asides update from interval if mistimed
  setTimeout(() => {
    UI.setHeaderDefault();
    UI.setAsidesDefault();
  }, DEFAULTS.radarRefreshRate);
}

async function startRecording(recordModeBtn) {
  await API.startRecording(OptionsUI.getSelectedParameters());
  
  UI.setButtonActive(recordModeBtn);
  UI.setButtonActive(UI.nodes.targetRadarBtn);
  radar.start();
}

function stopMonitoring() {
  API.stopCapturing();
  UI.setButtonDefault(UI.nodes.monitorModeBtn);
  stopVisualizers();
}

async function startMonitoring(monitorModeBtn) {
  // Disable the button to prevent multiple clicks during the API call delay
  UI.disableButton(monitorModeBtn);
  try { await API.startMonitoring(); } 
  catch {
    // If the API call fails, re-enable the button
    UI.enableButton(monitorModeBtn);
    return;
  }
  UI.enableButton(monitorModeBtn);

  if (UI.isButtonActive(UI.nodes.amplitudeHeatmapBtn)) ampHeatmap.start();
  if (UI.isButtonActive(UI.nodes.phaseHeatmapBtn)) phaseHeatmap.start();
  if (UI.isButtonActive(UI.nodes.gatesHeatmapBtn)) gatesHeatmap.start();
  if (UI.isButtonActive(UI.nodes.d3PlotBtn)) d3plot.start();
  
  UI.setButtonActive(monitorModeBtn);
  radar.start();
}

function wireSidebar() {
  UI.sidebarNodes.collapseBtn.addEventListener('click', () => {
    UI.sidebarNodes.sidebar.classList.toggle('w-20');
    UI.sidebarNodes.sidebarText.forEach(t => {
      t.classList.toggle('hidden');
    });
  });

  UI.sidebarNodes.monitorTab.addEventListener('click', () => {
    if (UI.sidebarNodes.monitorTab.dataset.active === '0') {
      UI.setTabSelected(UI.sidebarNodes.monitorTab);
      UI.setTabDefault(UI.sidebarNodes.historyTab);
      UI.setTabDefault(UI.sidebarNodes.datasetTab);

      UI.sidebarNodes.monitorElements.forEach(t => { UI.hideUI(t); });
      UI.sidebarNodes.historyElements.forEach(t => { UI.showUI(t); });
      UI.sidebarNodes.datasetElements.forEach(t => { UI.showUI(t); });

      UI.hideVisualizers();
      clearVisualizers();
    }

    if (UI.nodes.recordModeBtn.dataset.active === '1') UI.stopRecording();
    if (UI.nodes.monitorModeBtn.dataset.active === '1') stopMonitoring();
  });

  UI.sidebarNodes.historyTab.addEventListener('click', () => {
    if (UI.sidebarNodes.historyTab.dataset.active === '0') {
      UI.setTabDefault(UI.sidebarNodes.monitorTab);
      UI.setTabSelected(UI.sidebarNodes.historyTab);
      UI.setTabDefault(UI.sidebarNodes.datasetTab);

      UI.sidebarNodes.monitorElements.forEach(t => { UI.showUI(t); });
      UI.sidebarNodes.historyElements.forEach(t => { UI.hideUI(t); });
      UI.sidebarNodes.datasetElements.forEach(t => { UI.showUI(t); });

      UI.hideVisualizers();
      clearVisualizers();
    }

    // If user switch to history tab while monitoring or recording
    if (UI.isButtonActive(UI.nodes.recordModeBtn)) UI.stopRecording();
    if (UI.isButtonActive(UI.nodes.monitorModeBtn)) stopMonitoring();
  });

  UI.sidebarNodes.datasetTab.addEventListener('click', () => {
    if (UI.sidebarNodes.datasetTab.dataset.active === '0') {
      UI.setTabDefault(UI.sidebarNodes.monitorTab);
      UI.setTabDefault(UI.sidebarNodes.historyTab);
      UI.setTabSelected(UI.sidebarNodes.datasetTab);

      UI.sidebarNodes.monitorElements.forEach(t => { UI.showUI(t); });
      UI.sidebarNodes.historyElements.forEach(t => { UI.showUI(t); });
      UI.sidebarNodes.datasetElements.forEach(t => { UI.hideUI(t); });

      UI.hideVisualizers();
      clearVisualizers();
    }

    // If user switch to dataset tab while monitoring
    if (UI.isButtonActive(UI.nodes.monitorModeBtn)) {
      stopMonitoring();
      clearVisualizers();
      UI.setButtonDefault(UI.nodes.targetRadarBtn);
    }
  });
}

function wireFloatingActionButtons() {
  UI.nodes.monitorModeBtn.addEventListener('click', () => {
    const monitorModeBtn = UI.nodes.monitorModeBtn;
    if (UI.isButtonActive(monitorModeBtn)) stopMonitoring();
    else startMonitoring(monitorModeBtn);
  });

  UI.nodes.recordModeBtn.addEventListener('click', () => {
    const recordModeBtn = UI.nodes.recordModeBtn;
    if (UI.isButtonActive(recordModeBtn)) UI.stopRecording();
    else {
      if (UI.isButtonActive(UI.nodes.monitorModeBtn)) {
        API.stopCapturing();
        radar.stop();
        UI.setHeaderDefault();

        // Delay the recording due to suddent stop of monitoring
        setTimeout(() => startRecording(recordModeBtn), DEFAULTS.recordingDelay);
      }
      else startRecording(recordModeBtn);
    }

    // Temporarily disable button to prevent multiple clicks
    UI.disableButton(recordModeBtn);
    setTimeout(() => UI.enableButton(recordModeBtn), DEFAULTS.recordingDelay);
  });

  UI.nodes.targetRadarBtn.addEventListener('click', async () => {
    if (UI.isButtonActive(UI.nodes.targetRadarBtn)) {
      if (UI.isButtonActive(UI.nodes.monitorModeBtn) && UI.isButtonActive(UI.sidebarNodes.datasetTab)) {
        stopMonitoring();
        radar.stop();
        UI.enableButton(UI.nodes.targetRadarBtn)
      }
      UI.setButtonDefault(UI.nodes.targetRadarBtn);
      UI.setHeaderDefault();
      UI.setAsidesDefault();
      radar.clear();
    } else {
      UI.setButtonActive(UI.nodes.targetRadarBtn);
      // TODO: Separate the radar to the status bar updates

      if (UI.isButtonActive(UI.sidebarNodes.datasetTab)) {
        try { await API.startMonitoring(); }
        catch {
          UI.setButtonDefault(UI.nodes.targetRadarBtn);
          return;
        }
        
        UI.setButtonActive(UI.nodes.monitorModeBtn);
        radar.start();
      }
    }
  });

  UI.nodes.amplitudeHeatmapBtn.addEventListener('click', () => {
    const ampHeatmapBtn = UI.nodes.amplitudeHeatmapBtn;
    if (UI.isButtonActive(ampHeatmapBtn)) ampHeatmap.clear();
    else {
      ampHeatmap.show();
      if (UI.isButtonActive(UI.nodes.monitorModeBtn)) ampHeatmap.start();
    }
  });

  UI.nodes.phaseHeatmapBtn.addEventListener('click', () => {
    const phaseHeatmapBtn = UI.nodes.phaseHeatmapBtn;
    if (UI.isButtonActive(phaseHeatmapBtn)) phaseHeatmap.clear();
    else {
      phaseHeatmap.show();
      if (UI.isButtonActive(UI.nodes.monitorModeBtn)) phaseHeatmap.start();
    }
  });

  UI.nodes.gatesHeatmapBtn.addEventListener('click', () => {
    const gatesHeatmapBtn = UI.nodes.gatesHeatmapBtn;
    if (UI.isButtonActive(gatesHeatmapBtn)) gatesHeatmap.clear();
    else {
      gatesHeatmap.show();
      if (UI.isButtonActive(UI.nodes.monitorModeBtn)) gatesHeatmap.start();
    }
  });

  UI.nodes.expChartBtn.addEventListener('click', () => {
    const expChartBtn = UI.nodes.expChartBtn;
    if (UI.isButtonActive(expChartBtn)) expChart.clear();
    else expChart.init();
  });

  UI.nodes.d3PlotBtn.addEventListener('click', () => {
    const d3PlotBtn = UI.nodes.d3PlotBtn;
    if (UI.isButtonActive(d3PlotBtn)) {
      d3plot.stop();
      d3plot.clear();
    } else {
      d3plot.show();
      if (UI.isButtonActive(UI.nodes.monitorModeBtn)) d3plot.start();
    }
  });
}

function wireHeatmapSliders() {
  UI.sliderNodes.amplitudeMaxSlider.addEventListener("input", (e) => {
    const newMax = parseFloat(e.target.value);
    UI.setTextContent(UI.sliderNodes.amplitudeMaxValue, newMax);
    ampHeatmap.setMaxValue(newMax);
  });

  UI.sliderNodes.phaseMaxSlider.addEventListener("input", (e) => {
    const newMax = parseFloat(e.target.value);
    UI.setTextContent(UI.sliderNodes.phaseMaxValue, newMax);
    phaseHeatmap.setMaxValue(newMax);
  });

  UI.sliderNodes.gatesMaxSlider.addEventListener("input", (e) => {
    const newMax = parseFloat(e.target.value);
    UI.setTextContent(UI.sliderNodes.gatesMaxValue, newMax);
    gatesHeatmap.setMaxValue(newMax);
  });
}

function wireSelections() {
  UI.nodes.datasetList.addEventListener('change', async (e) => {
    const selectedDataset = e.target.value;
    if (selectedDataset) {
      // TODO: Load the dataset and update the UI accordingly
      // const response = await API.loadCsvFile(selectedDataset);
      // if (response.status === 'error') throw new Error(response.error);
    }
  });

  OptionsUI.init({
    classSelection: document.getElementById('class-selection'),
    targetSelection: document.getElementById('target-selection'),
    stateSelection: document.getElementById('state-selection'),
    activitySelection: document.getElementById('activity-selection'),
    angleSelection: document.getElementById('angle-selection'),
    distanceSelection: document.getElementById('distance-selection'),
    obstructedSelection: document.getElementById('obstructed-selection'),
    obstructionSelection: document.getElementById('obstruction-selection'),
    spacingSelection: document.getElementById('spacing-selection')
  });
}

function init() {
  wireSidebar();
  wireFloatingActionButtons();
  wireHeatmapSliders();
  wireSelections();

  setInterval(UI.updateStatusBar.bind(UI), DEFAULTS.systemStatusInterval);
  UI.list_csv_files();
  // TODO: Make some UI invisible by default
  UI.sidebarNodes.monitorTab.click(); // Set default tab to monitor
}

document.addEventListener('DOMContentLoaded', init);
