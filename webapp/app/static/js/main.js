import { UI } from './ui.js';
import { API } from './api.js';
import { OptionsUI } from './options.js';
import { HeatmapVisualizer } from './visualizers/heatmap.js';
import { RadarVisualizer } from './visualizers/radar.js';
import { LineChart } from './visualizers/linechart.js';
import { D3Plot } from './visualizers/d3plot.js';
import { MAIN } from './constants.js';

let monitorInterval = null;

const ampHeatmap = new HeatmapVisualizer({
  canvas: UI.nodes.amplitudeCanvas,
  button: UI.nodes.amplitudeHeatmapBtn,
  container: UI.nodes.amplitudeHeatmapContainer,
  type: 'amplitude',
  maxValue: parseFloat(UI.sliderNodes.amplitudeMaxSlider.value)
});

const phaseHeatmap = new HeatmapVisualizer({
  canvas: UI.nodes.phaseCanvas,
  button: UI.nodes.phaseHeatmapBtn,
  container: UI.nodes.phaseHeatmapContainer,
  type: 'phase',
  maxValue: parseFloat(UI.sliderNodes.phaseMaxSlider.value)
});

const gatesHeatmap = new HeatmapVisualizer({
  canvas: UI.nodes.gatesCanvas,
  button: UI.nodes.gatesHeatmapBtn,
  container: UI.nodes.gatesHeatmapContainer,
  type: 'mmwave',
  maxValue: parseFloat(UI.sliderNodes.gatesMaxSlider.value)
});

const expChart = new LineChart({
  context: UI.visualizers.expChartCanvasCtx,
  button: UI.nodes.expChartBtn,
  container: UI.nodes.expChartContainer
});

const radar = new RadarVisualizer({
  button: UI.nodes.targetRadarBtn,
  targetContainer: UI.nodes.targetContainer,
  radarContainer: UI.nodes.radarContainer,
  targetDistance: UI.nodes.target1Dist,
  setAsidesTexts: UI.setAsidesTexts.bind(UI)
});

const d3plot = new D3Plot({
  button: UI.nodes.d3PlotBtn,
  container: UI.nodes.d3PlotContainer,
});

function clearVisualizers() {
  // Assuming that monitoring is stopped
  radar.clear();
  ampHeatmap.clear();
  phaseHeatmap.clear();
  gatesHeatmap.clear();
  expChart.clear();
  d3plot.clear();
  
  UI.setHeaderDefault();
  UI.setAsidesDefault();
}

function stopVisualizers() {
  radar.stop();
  ampHeatmap.stop();
  phaseHeatmap.stop();
  gatesHeatmap.stop();
  d3plot.stop();

  UI.setHeaderDefault();
  UI.setAsidesDefault();

  // Ensure to remove the status bar and asides update from interval if mistimed
  // setTimeout(() => {
  //   UI.setHeaderDefault();
  //   UI.setAsidesDefault();
  // }, 500);
}

async function startRecording(recordModeBtn) {
  await API.startRecording(OptionsUI.getSelectedParameters());
  UI.setButtonActive(recordModeBtn);
  radar.start();
}

async function updateMonitorInfo() {
  try {
    const data = await API.fetchMonitorStatus();
    if (data.modeStatus === -1) {
      UI.stopRecording();
      return;
    }
    
    UI.nodes.packetCount.textContent = data.totalPacket;
    UI.nodes.packetLoss.textContent = `${data.packetLoss}%`;
    UI.nodes.expValue.textContent = data.rssi;

    if (parseInt(data.rssi) > -60) UI.nodes.presenceStatus.textContent = '?';
    else UI.nodes.presenceStatus.textContent = data.presence;
    if (expChart.visible) expChart.push(data.exp);
  } catch (err) {
    UI.setHeaderDefault();
    console.warn('Missing data for status bar.', err);
  }
}

function stopMonitoring() {
  clearInterval(monitorInterval);
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
  UI.setButtonActive(monitorModeBtn);
  monitorInterval = setInterval(() => updateMonitorInfo(), MAIN.delayMonitorInterval);

  if (radar.visible) radar.start();
  if (ampHeatmap.visible) ampHeatmap.start();
  if (phaseHeatmap.visible) phaseHeatmap.start();
  if (gatesHeatmap.visible) gatesHeatmap.start();
  if (d3plot.visible) d3plot.start();
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
    if (UI.isMonitoring()) stopMonitoring();
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
    if (UI.isMonitoring()) stopMonitoring();
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
    if (UI.isMonitoring()) {
      stopMonitoring();
      clearVisualizers();
      radar.hide();
    }
  });
}

function wireFloatingActionButtons() {
  UI.nodes.monitorModeBtn.addEventListener('click', () => {
    const monitorModeBtn = UI.nodes.monitorModeBtn;
    if (UI.isMonitoring()) stopMonitoring();
    else startMonitoring(monitorModeBtn);
  });

  UI.nodes.recordModeBtn.addEventListener('click', () => {
    const recordModeBtn = UI.nodes.recordModeBtn;
    if (UI.isButtonActive(recordModeBtn)) UI.stopRecording();
    else {
      if (UI.isMonitoring()) {
        API.stopCapturing();
        radar.stop();
        UI.setHeaderDefault();

        // Delay the recording due to suddent stop of monitoring
        setTimeout(() => startRecording(recordModeBtn), MAIN.delayRecordingAction);
      }
      else startRecording(recordModeBtn);
    }

    // Temporarily disable button to prevent multiple clicks
    UI.disableButton(recordModeBtn);
    setTimeout(() => UI.enableButton(recordModeBtn), MAIN.delayRecordingAction);
  });

  UI.nodes.targetRadarBtn.addEventListener('click', async () => {
    if (radar.visible) {
      if (UI.isMonitoring() && UI.isButtonActive(UI.sidebarNodes.datasetTab)) {
        stopMonitoring();
      }
      UI.setHeaderDefault();
      UI.setAsidesDefault();
      radar.stop();
    } else {
      radar.show();
      if (UI.isMonitoring()) radar.start();

      // If the user is in dataset tab
      if (UI.isButtonActive(UI.sidebarNodes.datasetTab)) {
        // Disable the button to prevent multiple clicks during the API call delay
        UI.disableButton(UI.nodes.targetRadarBtn);
        try { await API.startMonitoring(); }
        catch {
          // If the API call fails, re-enable the button
          UI.enableButton(UI.nodes.targetRadarBtn);
          radar.hide();
          return;
        }
        UI.enableButton(UI.nodes.targetRadarBtn);
        UI.setButtonActive(UI.nodes.monitorModeBtn);
        radar.start();
      }
    }
  });

  UI.nodes.amplitudeHeatmapBtn.addEventListener('click', () => {
    if (ampHeatmap.visible) ampHeatmap.clear();
    else {
      ampHeatmap.show();
      if (UI.isMonitoring()) ampHeatmap.start();
    }
  });

  UI.nodes.phaseHeatmapBtn.addEventListener('click', () => {
    if (phaseHeatmap.visible) phaseHeatmap.clear();
    else {
      phaseHeatmap.show();
      if (UI.isMonitoring()) phaseHeatmap.start();
    }
  });

  UI.nodes.gatesHeatmapBtn.addEventListener('click', () => {
    if (gatesHeatmap.visible) gatesHeatmap.clear();
    else {
      gatesHeatmap.show();
      if (UI.isMonitoring()) gatesHeatmap.start();
    }
  });

  UI.nodes.expChartBtn.addEventListener('click', () => {
    if (expChart.visible) expChart.clear();
    else expChart.init();
  });

  UI.nodes.d3PlotBtn.addEventListener('click', () => {
    if (d3plot.visible) {
      d3plot.stop();
      d3plot.clear();
    } else {
      d3plot.show();
      if (UI.isMonitoring()) d3plot.start();
    }
  });
}

function wireHeatmapSliders() {
  UI.sliderNodes.amplitudeMaxSlider.addEventListener('input', (e) => {
    const newMax = parseFloat(e.target.value);
    UI.setTextContent(UI.sliderNodes.amplitudeMaxValue, newMax);
    ampHeatmap.setMaxValue(newMax);
  });

  UI.sliderNodes.phaseMaxSlider.addEventListener('input', (e) => {
    const newMax = parseFloat(e.target.value);
    UI.setTextContent(UI.sliderNodes.phaseMaxValue, newMax);
    phaseHeatmap.setMaxValue(newMax);
  });

  UI.sliderNodes.gatesMaxSlider.addEventListener('input', (e) => {
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

  setInterval(UI.updateStatusBar.bind(UI), MAIN.delaySystemIconStatus);
  UI.list_csv_files();
  // TODO: Make some UI invisible by default
  UI.sidebarNodes.monitorTab.click(); // Set default tab to monitor
}

document.addEventListener('DOMContentLoaded', init);
