import { SELECTORS, UI_COLORS } from './constants.js';
import { API } from './api.js';

function $(sel) { return document.querySelector(sel); }
function $$(sel) { return document.querySelectorAll(sel); }

export const UI = {
  floatingButtonNodes: {
    recordModeBtn: $(SELECTORS.recordModeBtn),
    monitorModeBtn: $(SELECTORS.monitorModeBtn),

    targetRadarBtn: $(SELECTORS.targetRadarBtn),
    amplitudeHeatmapBtn: $(SELECTORS.amplitudeHeatmapBtn),
    phaseHeatmapBtn: $(SELECTORS.phaseHeatmapBtn),
    gatesHeatmapBtn: $(SELECTORS.gatesHeatmapBtn),
    expChartBtn: $(SELECTORS.expChartBtn),
    d3PlotBtn: $(SELECTORS.d3PlotBtn)
  },

  sidebarNodes: {
    sidebarContainer: $(SELECTORS.sidebarContainer),
    collapseBtn: $(SELECTORS.collapseBtn),
    sidebarText: $$(SELECTORS.sidebarText),

    monitorGroup: $$(SELECTORS.monitorGroup),
    historyGroup: $$(SELECTORS.historyGroup),
    datasetGroup: $$(SELECTORS.datasetGroup),

    monitorTabBtn: $(SELECTORS.monitorTabBtn),
    historyTabBtn: $(SELECTORS.historyTabBtn),
    datasetTabBtn: $(SELECTORS.datasetTabBtn)
  },

  headerNodes: {
    presenceStatus: $(SELECTORS.presenceStatus),
    targetDist: $(SELECTORS.targetDist),
    packetCount: $(SELECTORS.packetCount),
    packetLoss: $(SELECTORS.packetLoss),
    expValue: $(SELECTORS.expValue),

    apStatus: $(SELECTORS.apStatus),
    flaskStatus: $(SELECTORS.flaskStatus),
    esp32Status: $(SELECTORS.esp32Status),
    ld2420Status: $(SELECTORS.ld2420Status),
    modelStatus: $(SELECTORS.modelStatus)
  },

  asideNodes: {
    targetDistance: $(SELECTORS.targetDistance),
    targetAngle: $(SELECTORS.targetAngle),
    targetEnergy: $(SELECTORS.targetEnergy)
  },

  visualizerNodes: {
    targetContainer: $(SELECTORS.targetContainer),
    radarContainer: $(SELECTORS.radarContainer),

    amplitudeCanvas: $(SELECTORS.amplitudeCanvas),
    amplitudeHeatmapContainer: $(SELECTORS.amplitudeHeatmapContainer),

    phaseCanvas: $(SELECTORS.phaseCanvas),
    phaseHeatmapContainer: $(SELECTORS.phaseHeatmapContainer),

    gatesCanvas: $(SELECTORS.gatesCanvas),
    gatesHeatmapContainer: $(SELECTORS.gatesHeatmapContainer),

    expLineChartCanvasCtx: document.querySelector(SELECTORS.expLineChartCanvas).getContext('2d'),
    expLineChartContainer: $(SELECTORS.expLineChartContainer),

    d3PlotContainer: $(SELECTORS.d3PlotContainer),
  },

  sliderNodes: {
    amplitudeMaxSlider: $(SELECTORS.amplitudeMaxSlider),
    phaseMaxSlider: $(SELECTORS.phaseMaxSlider),
    gatesMaxSlider: $(SELECTORS.gatesMaxSlider),

    amplitudeMaxValue: $(SELECTORS.amplitudeMaxValue),
    phaseMaxValue: $(SELECTORS.phaseMaxValue),
    gatesMaxValue: $(SELECTORS.gatesMaxValue)
  },

  nodes: {
    datasetList: $(SELECTORS.datasetList),
  },

  async updateStatusBar() {
    const n = this.headerNodes;
    try {
      const status = await API.fetchSystemIconStatus();
      if (status.ap) n.apStatus.style.fill = UI_COLORS.statusBarActiveColor;
      else n.apStatus.style.fill = UI_COLORS.statusBarInactiveColor;
      
      n.flaskStatus.style.fill = UI_COLORS.statusBarActiveColor;

      if (status.esp32) n.esp32Status.style.fill = UI_COLORS.statusBarActiveColor;
      else n.esp32Status.style.fill = UI_COLORS.statusBarInactiveColor;
      
      if (status.ld2420) n.ld2420Status.style.fill = UI_COLORS.statusBarActiveColor;
      else n.ld2420Status.style.fill = UI_COLORS.statusBarInactiveColor;

      if (status.model) n.modelStatus.style.fill = UI_COLORS.statusBarActiveColor;
      else n.modelStatus.style.fill = UI_COLORS.statusBarInactiveColor;
      // map status fields to UI nodes as needed
      // if (status && n.presenceStatus) {
      //   n.presenceStatus.textContent = status.presence ?? n.presenceStatus.textContent;
      // }
    } catch (err) {
      console.warn('System status check failed', err);
      n.flaskStatus.style.fill = UI_COLORS.statusBarInactiveColor;
      n.esp32Status.style.fill = UI_COLORS.statusBarInactiveColor;
      n.ld2420Status.style.fill = UI_COLORS.statusBarInactiveColor;
      n.modelStatus.style.fill = UI_COLORS.statusBarInactiveColor;
    }
  },

  async list_csv_files() {
    const n = this.nodes;
    try {
      const files = await API.listCsvFiles();
      // TODO: populate dataset list UI if needed
      if (n.datasetList && Array.isArray(files)) {
        // n.datasetList.innerHTML = ''; // Clear existing options
        n.datasetList.innerHTML = files.map(f => `<option value="${f}">${f}</option>`).join('\n');
      }
    } catch(e) { console.warn('Could not load CSV list', e); }
  },

  setHeaderTexts(text = {}) {
    const n = this.headerNodes;
    n.presenceStatus.textContent = text?.presence || '?';
    n.targetDist.textContent = text?.targetDistance || '0m';
    n.packetCount.textContent = text?.packetCount || '0';
    n.packetLoss.textContent = text?.packetLoss || '0%';
    n.expValue.textContent = text?.rssi || '0';
  },

  setAsidesTexts(texts = {}) {
    const n = this.asideNodes;
    n.targetDistance.textContent = texts?.targetDistance || '0m';
    n.targetAngle.textContent = texts?.targetAngle || '0°';
    n.targetEnergy.textContent = texts?.targetEnergy || '0';
  },

  setButtonActive(buttonNode) {
    buttonNode.style.backgroundColor = UI_COLORS.btnActiveColor;
    buttonNode.dataset.active = '1';
  },

  setButtonDefault(buttonNode) {
    buttonNode.style.backgroundColor = UI_COLORS.btnDefaultColor;
    buttonNode.dataset.active = '0';
  },

  setTabSelected(tabNode) {
    tabNode.style.backgroundColor = UI_COLORS.tabSelectedColor;
    tabNode.dataset.active = '1';
  },

  setTabDefault(tabNode) {
    tabNode.style.backgroundColor = UI_COLORS.tabDefaultColor;
    tabNode.dataset.active = '0';
  },

  enableButton(buttonNode) {
    buttonNode.disabled = false;
  },

  disableButton(buttonNode) {
    buttonNode.disabled = true;
  },

  isButtonActive(buttonNode) {
    return buttonNode.dataset.active === '1';
  },

  hideUI(ui) {
    ui.classList.add('hidden');
  },

  showUI(ui) {
    ui.classList.remove('hidden');
  },

  isMonitoring() {
    return this.floatingButtonNodes.monitorModeBtn.dataset.active === '1';
  },

  hideVisualizers() {
    const n = this.visualizerNodes;
    // this.hideUI(n.radarContainer);
    this.hideUI(n.amplitudeHeatmapContainer);
    this.hideUI(n.phaseHeatmapContainer);
    this.hideUI(n.gatesHeatmapContainer);
    this.hideUI(n.expLineChartContainer);
    this.hideUI(n.d3PlotContainer);
  },

  stopRecording() {
    const n = this.nodes;
    API.stopCapturing();
    this.list_csv_files();
    this.floatingButtonNodes.recordModeBtn.dataset.active = '0';
    this.setHeaderTexts();
    this.setButtonDefault(this.floatingButtonNodes.recordModeBtn);
    // Ensure to reset the status bar if mistimed
    setTimeout(() => this.setHeaderTexts(), 120);
  },
};
