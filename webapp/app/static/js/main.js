import { UI } from './ui.js';
import { API } from './api.js';
import { OptionsUI } from './options.js';
import { HeatmapVisualizer } from './visualizers/heatmap.js';
import { RadarVisualizer } from './visualizers/radar.js';
import { LineChart } from './visualizers/linechart.js';
import { D3Plot } from './visualizers/d3plot.js';
import { MAIN } from './constants.js';

let monitorInterval = null;
let predictionInterval = null;

const ampHeatmap = new HeatmapVisualizer({
  canvas: UI.visualizerNodes.amplitudeCanvas,
  button: UI.floatingButtonNodes.amplitudeHeatmapBtn,
  container: UI.visualizerNodes.amplitudeHeatmapContainer,
  type: 'amplitude',
  maxValue: parseFloat(UI.sliderNodes.amplitudeMaxSlider.value)
});

const phaseHeatmap = new HeatmapVisualizer({
  canvas: UI.visualizerNodes.phaseCanvas,
  button: UI.floatingButtonNodes.phaseHeatmapBtn,
  container: UI.visualizerNodes.phaseHeatmapContainer,
  type: 'phase',
  maxValue: parseFloat(UI.sliderNodes.phaseMaxSlider.value)
});

const gatesHeatmap = new HeatmapVisualizer({
  canvas: UI.visualizerNodes.gatesCanvas,
  button: UI.floatingButtonNodes.gatesHeatmapBtn,
  container: UI.visualizerNodes.gatesHeatmapContainer,
  type: 'mmwave',
  maxValue: parseFloat(UI.sliderNodes.gatesMaxSlider.value)
});

const expChart = new LineChart({
  context: UI.visualizerNodes.expLineChartCanvasCtx,
  button: UI.floatingButtonNodes.expChartBtn,
  container: UI.visualizerNodes.expLineChartContainer
});

const radar = new RadarVisualizer({
  button: UI.floatingButtonNodes.targetRadarBtn,
  targetContainer: UI.visualizerNodes.targetContainer,
  radarContainer: UI.visualizerNodes.radarContainer,
  targetDistance: UI.headerNodes.signal_var,
  setAsidesTexts: UI.setAsidesTexts.bind(UI)
});

const d3plot = new D3Plot({
  button: UI.floatingButtonNodes.d3PlotBtn,
  container: UI.visualizerNodes.d3PlotContainer,
});

function clearVisualizers() {
  // Assuming that monitoring is stopped
  radar.clear();
  ampHeatmap.clear();
  phaseHeatmap.clear();
  gatesHeatmap.clear();
  expChart.clear();
  d3plot.clear();
  
  UI.setHeaderTexts();
  UI.setAsidesTexts();
}

function stopVisualizers() {
  radar.stop();
  ampHeatmap.stop();
  phaseHeatmap.stop();
  gatesHeatmap.stop();
  d3plot.stop();

  UI.setHeaderTexts();
  UI.setAsidesTexts();

  // Ensure to reset the status bar and asides update if mistimed
  setTimeout(() => {
    UI.setHeaderTexts();
    UI.setAsidesTexts();
  }, 120);
}

async function updatePresenceDisplay() {
  const data = await API.getPresenceStatus();
  UI.setPresenceTexts(data);
}

async function updateMonitorDisplay() {
  const data = await API.getMonitorStatus();
  if (data.modeStatus === -1) {
    UI.stopRecording();
    clearInterval(monitorInterval);
    return;
  }
  
  UI.setHeaderTexts(data);
  if (expChart.visible)
    expChart.push(data.exp);
}

async function startRecording(recordModeBtn) {
  if (UI.statusBarStates.esp32 === false) {
    alert('ESP32 is not connected.');
    return;
  }
  await API.startRecording(OptionsUI.getSelectedParameters());
  UI.setButtonActive(recordModeBtn);
  monitorInterval = setInterval(() => updateMonitorDisplay(), MAIN.delayMonitorInterval);
}

function stopMonitoring() {
  clearInterval(monitorInterval);
  clearInterval(predictionInterval);
  API.stopCapturing();
  UI.setButtonDefault(UI.floatingButtonNodes.monitorModeBtn);
  stopVisualizers();
  UI.setPresenceTexts();
}

async function startMonitoring(monitorModeBtn) {
  // Disable the button to prevent multiple clicks during the API call delay
  UI.disableButton(monitorModeBtn);
  try {
    if (UI.statusBarStates.esp32 === false) {
      alert('ESP32 is not connected.');
      UI.enableButton(monitorModeBtn);
      return;
    }
    await API.startMonitoring();
  }
  catch {
    // If the API call fails, re-enable the button
    UI.enableButton(monitorModeBtn);
    return;
  }
  UI.enableButton(monitorModeBtn);
  UI.setButtonActive(monitorModeBtn);
  monitorInterval = setInterval(() => updateMonitorDisplay(), MAIN.delayMonitorInterval);
  predictionInterval = setInterval(() => updatePresenceDisplay(), MAIN.delayPresenceInterval);

  if (radar.visible) radar.start();
  if (ampHeatmap.visible) ampHeatmap.start();
  if (phaseHeatmap.visible) phaseHeatmap.start();
  if (gatesHeatmap.visible) gatesHeatmap.start();
  if (d3plot.visible) d3plot.start();
}

function wireSidebar() {
  UI.sidebarNodes.collapseBtn.addEventListener('click', () => {
    UI.sidebarNodes.sidebarContainer.classList.toggle('w-20');
    UI.sidebarNodes.sidebarText.forEach(t => {
      t.classList.toggle('hidden');
    });
  });

  UI.sidebarNodes.monitorTabBtn.addEventListener('click', () => {
    if (UI.sidebarNodes.monitorTabBtn.dataset.active === '0') {
      UI.setTabSelected(UI.sidebarNodes.monitorTabBtn);
      UI.setTabDefault(UI.sidebarNodes.historyTabBtn);
      UI.setTabDefault(UI.sidebarNodes.datasetTabBtn);

      UI.sidebarNodes.monitorGroup.forEach(t => { UI.hideUI(t); });
      UI.sidebarNodes.historyGroup.forEach(t => { UI.showUI(t); });
      UI.sidebarNodes.datasetGroup.forEach(t => { UI.showUI(t); });

      UI.hideVisualizers();
      clearVisualizers();
    }

    if (UI.isButtonActive(UI.floatingButtonNodes.recordModeBtn)) {
      UI.stopRecording();
      clearInterval(monitorInterval);
      clearInterval(predictionInterval);
    }
    if (UI.isMonitoring())
      stopMonitoring();
  });

  UI.sidebarNodes.historyTabBtn.addEventListener('click', () => {
    if (UI.sidebarNodes.historyTabBtn.dataset.active === '0') {
      UI.setTabDefault(UI.sidebarNodes.monitorTabBtn);
      UI.setTabSelected(UI.sidebarNodes.historyTabBtn);
      UI.setTabDefault(UI.sidebarNodes.datasetTabBtn);

      UI.sidebarNodes.monitorGroup.forEach(t => { UI.showUI(t); });
      UI.sidebarNodes.historyGroup.forEach(t => { UI.hideUI(t); });
      UI.sidebarNodes.datasetGroup.forEach(t => { UI.showUI(t); });

      UI.hideVisualizers();
      clearVisualizers();
    }

    // If user switch to history tab while monitoring or recording
    if (UI.isButtonActive(UI.floatingButtonNodes.recordModeBtn)) {
      UI.stopRecording();
      clearInterval(monitorInterval);
      clearInterval(predictionInterval);
    }
    if (UI.isMonitoring())
      stopMonitoring();
  });

  UI.sidebarNodes.datasetTabBtn.addEventListener('click', () => {
    if (UI.sidebarNodes.datasetTabBtn.dataset.active === '0') {
      UI.setTabDefault(UI.sidebarNodes.monitorTabBtn);
      UI.setTabDefault(UI.sidebarNodes.historyTabBtn);
      UI.setTabSelected(UI.sidebarNodes.datasetTabBtn);

      UI.sidebarNodes.monitorGroup.forEach(t => { UI.showUI(t); });
      UI.sidebarNodes.historyGroup.forEach(t => { UI.showUI(t); });
      UI.sidebarNodes.datasetGroup.forEach(t => { UI.hideUI(t); });

      UI.hideVisualizers();
      clearVisualizers();
    }

    // If user switch to dataset tab while monitoring
    if (UI.isMonitoring()) {
      stopMonitoring();
      clearVisualizers();
      radar.hide();
    }
  });
}

function wireFloatingActionButtons() {
  UI.floatingButtonNodes.monitorModeBtn.addEventListener('click', () => {
    const monitorModeBtn = UI.floatingButtonNodes.monitorModeBtn;
    if (UI.isMonitoring()) stopMonitoring();
    else startMonitoring(monitorModeBtn);
  });

  UI.floatingButtonNodes.recordModeBtn.addEventListener('click', () => {
    const recordModeBtn = UI.floatingButtonNodes.recordModeBtn;
    if (UI.isButtonActive(recordModeBtn)) {
      UI.stopRecording();
      clearInterval(monitorInterval);
    }
    else startRecording(recordModeBtn);

    // Temporarily disable button to prevent multiple clicks
    UI.disableButton(recordModeBtn);
    setTimeout(() => UI.enableButton(recordModeBtn), MAIN.delayRecordingAction);
  });

  UI.floatingButtonNodes.targetRadarBtn.addEventListener('click', async () => {
    if (radar.visible) {
      if (UI.isMonitoring() && UI.isButtonActive(UI.sidebarNodes.datasetTabBtn)) {
        stopMonitoring();
      }
      UI.setHeaderTexts();
      UI.setAsidesTexts();
      radar.stop();
    } else {
      radar.show();
      if (UI.isMonitoring())
        radar.start();
    }
  });

  UI.floatingButtonNodes.amplitudeHeatmapBtn.addEventListener('click', () => {
    if (ampHeatmap.visible) ampHeatmap.clear();
    else {
      ampHeatmap.show();
      if (UI.isMonitoring())
        ampHeatmap.start();
    }
  });

  UI.floatingButtonNodes.phaseHeatmapBtn.addEventListener('click', () => {
    if (phaseHeatmap.visible) phaseHeatmap.clear();
    else {
      phaseHeatmap.show();
      if (UI.isMonitoring())
        phaseHeatmap.start();
    }
  });

  UI.floatingButtonNodes.gatesHeatmapBtn.addEventListener('click', () => {
    if (gatesHeatmap.visible) gatesHeatmap.clear();
    else {
      gatesHeatmap.show();
      if (UI.isMonitoring())
        gatesHeatmap.start();
    }
  });

  UI.floatingButtonNodes.expChartBtn.addEventListener('click', () => {
    if (expChart.visible) expChart.clear();
    else expChart.init();
  });

  UI.floatingButtonNodes.d3PlotBtn.addEventListener('click', () => {
    if (d3plot.visible) {
      d3plot.stop();
      d3plot.clear();
    } else {
      d3plot.show();
      if (UI.isMonitoring())
        d3plot.start();
    }
  });
}

function wireHeatmapSliders() {
  UI.sliderNodes.amplitudeMaxSlider.addEventListener('input', (e) => {
    const newMax = parseFloat(e.target.value);
    UI.sliderNodes.amplitudeMaxValue.textContent = newMax;
    ampHeatmap.setMaxValue(newMax);
  });

  UI.sliderNodes.phaseMaxSlider.addEventListener('input', (e) => {
    const newMax = parseFloat(e.target.value);
    UI.sliderNodes.phaseMaxValue.textContent = newMax;
    phaseHeatmap.setMaxValue(newMax);
  });

  UI.sliderNodes.gatesMaxSlider.addEventListener('input', (e) => {
    const newMax = parseFloat(e.target.value);
    UI.sliderNodes.gatesMaxValue.textContent = newMax;
    gatesHeatmap.setMaxValue(newMax);
  });
}

function wireSelections() {
  UI.nodes.datasetList.addEventListener('change', async (e) => {
    const selectedDataset = e.target.value;
    if (selectedDataset) {
      const meta = await API.readCsvFileMeta(selectedDataset);
      UI.updateMetadataTexts(meta);
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

  // TODO: Stop status bar update when monitoring or recording
  setInterval(UI.updateStatusBar.bind(UI), MAIN.delaySystemIconStatus);
  UI.list_csv_files();
  // TODO: Make some UI invisible by default
  UI.sidebarNodes.monitorTabBtn.click(); // Set default tab to monitor
}

document.addEventListener('DOMContentLoaded', init);
