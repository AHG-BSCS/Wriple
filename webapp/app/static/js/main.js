import { UI } from './ui.js';
import { API } from './api.js';
import { OptionsUI } from './options.js';
import { HeatmapVisualizer } from './visualizers/heatmap.js';
import { RadarVisualizer } from './visualizers/radar.js';
import { LineChart } from './visualizers/linechart.js';
import { MAIN_DELAYS } from './constants.js';

let monitorInterval = null;
let predictionInterval = null;

const ampHeatmap = new HeatmapVisualizer({
  canvas: UI.visualizerNodes.amplitudeCanvas,
  button: UI.floatingButtonNodes.amplitudeHeatmapBtn,
  container: UI.visualizerNodes.amplitudeHeatmapContainer,
  type: 'amplitude',
  maxValue: parseFloat(UI.sliderNodes.amplitudeMaxSlider.value)
});

const dopplerHeatmap = new HeatmapVisualizer({
  canvas: UI.visualizerNodes.dopplerCanvas,
  button: UI.floatingButtonNodes.gatesHeatmapBtn,
  container: UI.visualizerNodes.dopplerHeatmapContainer,
  type: 'doppler',
  maxValue: parseFloat(UI.sliderNodes.dopplerMaxSlider.value)
});

const noiseChart = new LineChart({
  context: UI.visualizerNodes.noiseChartCanvasCtx,
  button: UI.floatingButtonNodes.noiseChartBtn,
  container: UI.visualizerNodes.noiseChartContainer,
  type: 'noise'
});

const detectionChart = new LineChart({
  context: UI.visualizerNodes.detectionChartCanvasCtx,
  button: UI.floatingButtonNodes.detectionChartBtn,
  container: UI.visualizerNodes.detectionChartContainer,
  type: 'detection'
});

const radar = new RadarVisualizer({
  button: UI.floatingButtonNodes.targetRadarBtn,
  targetContainer: UI.visualizerNodes.targetContainer,
  radarContainer: UI.visualizerNodes.radarContainer,
  targetDistance: UI.headerNodes.signalVar,
  setAsidesTexts: UI.setAsidesTexts.bind(UI)
});

function clearVisualizers() {
  // Assuming that monitoring is stopped
  radar.clear();
  ampHeatmap.clear();
  dopplerHeatmap.clear();
  noiseChart.clear();
  
  UI.setHeaderTexts();
  UI.setAsidesTexts();
}

function stopVisualizers() {
  radar.stop();
  ampHeatmap.stop();
  dopplerHeatmap.stop();
  noiseChart.stop();

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
  if (detectionChart.visible) {
    if (data.presence === 'Yes') detectionChart.push(1);
    else detectionChart.push(0);
  }
}

async function updateMonitorDisplay() {
  const data = await API.getMonitorStatus();
  if (data.modeStatus === -1) {
    UI.stopRecording();
    clearInterval(monitorInterval);
    return;
  }
  
  UI.setHeaderTexts(data);
}

async function startRecording(recordModeBtn) {
  if (UI.statusBarStates.esp32 === false) {
    alert('ESP32 is not connected.');
    return;
  }
  await API.startRecording(OptionsUI.getSelectedParameters());
  UI.setButtonActive(recordModeBtn);
  monitorInterval = setInterval(() => updateMonitorDisplay(), MAIN_DELAYS.delayMonitorInterval);
}

function stopMonitoring() {
  clearInterval(monitorInterval);
  clearInterval(predictionInterval);
  UI.setButtonDefault(UI.floatingButtonNodes.monitorModeBtn);
  stopVisualizers();
  UI.setPresenceTexts();
  // Delay the stopCapturing to ensure all visualizers have stopped fetching data
  setTimeout(() => API.stopCapturing(), 100);
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
  monitorInterval = setInterval(() => updateMonitorDisplay(), MAIN_DELAYS.delayMonitorInterval);
  predictionInterval = setInterval(() => updatePresenceDisplay(), MAIN_DELAYS.delayPresenceInterval);

  if (radar.visible) radar.start();
  if (ampHeatmap.visible) ampHeatmap.start();
  if (dopplerHeatmap.visible) dopplerHeatmap.start();
  if (noiseChart.visible) noiseChart.start();
}

async function updateStatusBar() {
  let status = null;
  try {
    status = await API.getSystemStatus();
    const monitorModeBtn = UI.floatingButtonNodes.monitorModeBtn;

    if (!status.esp32) {
      if (UI.isMonitoring()) stopMonitoring();
      if (!monitorModeBtn.disabled) UI.disableButton(monitorModeBtn);
    }
    else {
      if (monitorModeBtn.disabled) UI.enableButton(monitorModeBtn);
    }
    UI.updateStatusBar(status);
  } catch {
    UI.updateStatusBar(status);
    console.error('Server is down');
  }
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
    setTimeout(() => UI.enableButton(recordModeBtn), MAIN_DELAYS.delayRecordingAction);
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

  UI.floatingButtonNodes.gatesHeatmapBtn.addEventListener('click', () => {
    if (dopplerHeatmap.visible) dopplerHeatmap.clear();
    else {
      dopplerHeatmap.show();
      if (UI.isMonitoring())
        dopplerHeatmap.start();
    }
  });

  UI.floatingButtonNodes.noiseChartBtn.addEventListener('click', () => {
    if (noiseChart.visible) noiseChart.clear();
    else if (UI.isMonitoring()) noiseChart.start();
    else noiseChart.init();
  });

  UI.floatingButtonNodes.detectionChartBtn.addEventListener('click', () => {
    if (detectionChart.visible) detectionChart.clear();
    else detectionChart.init();
  });
}

function wireHeatmapSliders() {
  UI.sliderNodes.amplitudeMaxSlider.addEventListener('input', (e) => {
    const newMax = parseFloat(e.target.value);
    UI.sliderNodes.amplitudeMaxValue.textContent = newMax;
    ampHeatmap.setMaxValue(newMax);
  });

  UI.sliderNodes.dopplerMaxSlider.addEventListener('input', (e) => {
    const newMax = parseFloat(e.target.value);
    UI.sliderNodes.dopplerMaxValue.textContent = newMax;
    dopplerHeatmap.setMaxValue(newMax);
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
  // UI.hideElements();
  wireSidebar();
  wireFloatingActionButtons();
  wireHeatmapSliders();
  wireSelections();

  setInterval(() => updateStatusBar(), MAIN_DELAYS.delaySystemIconStatus);
  updateStatusBar();
  UI.list_csv_files();
  UI.sidebarNodes.monitorTabBtn.click(); // Set default tab to monitor
}

document.addEventListener('DOMContentLoaded', init);
