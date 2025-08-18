import { SELECTORS, UI_COLORS } from './constants.js';
import { API } from './api.js';

function $(sel) { return document.querySelector(sel); }
function $$(sel) { return document.querySelectorAll(sel); }

// TODO: Further refactor the UI.nodes
export const UI = {
  sidebarNodes: {
    collapseBtn: $(SELECTORS.collapseBtn),
    sidebar: $(SELECTORS.sidebar),
    sidebarText: $$(SELECTORS.sidebarText),

    monitorElements: $$(SELECTORS.monitorElements),
    historyElements: $$(SELECTORS.historyElements),
    datasetElements: $$(SELECTORS.datasetElements),

    monitorTab: $(SELECTORS.monitordTab),
    historyTab: $(SELECTORS.historyTab),
    datasetTab: $(SELECTORS.datasetTab),
  },

  nodes: {
    presenceStatus: $(SELECTORS.presenceStatus),
    target1Dist: $(SELECTORS.target1Dist),
    packetCount: $(SELECTORS.packetCount),
    packetLoss: $(SELECTORS.packetLoss),
    expValue: $(SELECTORS.expValue),

    recordModeBtn: $(SELECTORS.recordModeBtn),
    monitorModeBtn: $(SELECTORS.monitorModeBtn),

    targetRadarBtn: $(SELECTORS.targetRadarBtn),
    amplitudeHeatmapBtn: $(SELECTORS.amplitudeHeatmapBtn),
    phaseHeatmapBtn: $(SELECTORS.phaseHeatmapBtn),
    gatesHeatmapBtn: $(SELECTORS.gatesHeatmapBtn),
    expChartBtn: $(SELECTORS.expChartBtn),
    d3PlotBtn: $(SELECTORS.d3PlotBtn),

    datasetList: $(SELECTORS.datasetList),

    targetContainer: $(SELECTORS.targetContainer),
    radarContainer: $(SELECTORS.radarContainer),

    amplitudeHeatmapContainer: $(SELECTORS.amplitudeHeatmapContainer),
    phaseHeatmapContainer: $(SELECTORS.phaseHeatmapContainer),
    gatesHeatmapContainer: $(SELECTORS.gatesHeatmapContainer),
    expChartContainer: $(SELECTORS.expChartContainer),
    d3PlotContainer: $(SELECTORS.d3PlotContainer),

    amplitudeCanvas: $(SELECTORS.amplitudeCanvas),
    phaseCanvas: $(SELECTORS.phaseCanvas),
    gatesCanvas: $(SELECTORS.gatesCanvas),

    apStatus: $(SELECTORS.apStatus),
    flaskStatus: $(SELECTORS.flaskStatus),
    esp32Status: $(SELECTORS.esp32Status),
    ld2420Status: $(SELECTORS.ld2420Status),
    rd03dStatus: $(SELECTORS.rd03dStatus),
    portStatus: $(SELECTORS.portStatus),
    modelStatus: $(SELECTORS.modelStatus),
  },

  sliderNodes: {
    amplitudeMaxSlider: $(SELECTORS.amplitudeMaxSlider),
    phaseMaxSlider: $(SELECTORS.phaseMaxSlider),
    gatesMaxSlider: $(SELECTORS.gatesMaxSlider),

    amplitudeMaxValue: $(SELECTORS.amplitudeMaxValue),
    phaseMaxValue: $(SELECTORS.phaseMaxValue),
    gatesMaxValue: $(SELECTORS.gatesMaxValue)
  },

  asideNodes: {
    target1Angle: $(SELECTORS.target1Angle),
    target2Angle: $(SELECTORS.target2Angle),
    target3Angle: $(SELECTORS.target3Angle),
    target1Distance: $(SELECTORS.target1Distance),
    target2Distance: $(SELECTORS.target2Distance),
    target3Distance: $(SELECTORS.target3Distance),
    target1Speed: $(SELECTORS.target1Speed),
    target2Speed: $(SELECTORS.target2Speed),
    target3Speed: $(SELECTORS.target3Speed),
    target1DistRes: $(SELECTORS.target1DistRes),
    target2DistRes: $(SELECTORS.target2DistRes),
    target3DistRes: $(SELECTORS.target3DistRes)
  },

  async updateStatusBar() {
    const n = this.nodes;
    try {
      const status = await API.fetchSystemIconStatus();
      if (status.ap) n.apStatus.style.fill = UI_COLORS.statusBarActiveColor;
      else n.apStatus.style.fill = UI_COLORS.statusBarInactiveColor;
      
      n.flaskStatus.style.fill = UI_COLORS.statusBarActiveColor;

      if (status.esp32) n.esp32Status.style.fill = UI_COLORS.statusBarActiveColor;
      else n.esp32Status.style.fill = UI_COLORS.statusBarInactiveColor;
      
      if (status.ld2420) n.ld2420Status.style.fill = UI_COLORS.statusBarActiveColor;
      else n.ld2420Status.style.fill = UI_COLORS.statusBarInactiveColor;

      if (status.rd03d) n.rd03dStatus.style.fill = UI_COLORS.statusBarActiveColor;
      else n.rd03dStatus.style.fill = UI_COLORS.statusBarInactiveColor;

      if (status.port) n.portStatus.style.fill = UI_COLORS.statusBarActiveColor;
      else n.portStatus.style.fill = UI_COLORS.statusBarInactiveColor;

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
      n.rd03dStatus.style.fill = UI_COLORS.statusBarInactiveColor;
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

  setTextContent(node, text) {
    node.textContent = text;
  },

  setHeaderDefault() {
    const n = this.nodes;
    this.setTextContent(n.presenceStatus, '?');
    this.setTextContent(n.target1Dist, '0.0m');
    this.setTextContent(n.packetCount, '0');
    this.setTextContent(n.packetLoss, '0%');
    this.setTextContent(n.expValue, '0');
  },

  setAsidesDefault() {
    const n = this.asideNodes;
    this.setTextContent(n.target1Angle, '0.00°');
    this.setTextContent(n.target2Angle, '0.00°');
    this.setTextContent(n.target3Angle, '0.00°');

    this.setTextContent(n.target1Distance, '0.00m');
    this.setTextContent(n.target2Distance, '0.00m');
    this.setTextContent(n.target3Distance, '0.00m');

    this.setTextContent(n.target1Speed, '0cm/s');
    this.setTextContent(n.target2Speed, '0cm/s');
    this.setTextContent(n.target3Speed, '0cm/s');

    this.setTextContent(n.target1DistRes, '0');
    this.setTextContent(n.target2DistRes, '0');
    this.setTextContent(n.target3DistRes, '0');
  },

  setAsidesTexts(texts) {
    const n = this.asideNodes;
    this.setTextContent(n.target1Angle, texts.target1Angle);
    this.setTextContent(n.target2Angle, texts.target2Angle);
    this.setTextContent(n.target3Angle, texts.target3Angle);
    this.setTextContent(n.target1Distance, texts.target1Distance);
    this.setTextContent(n.target2Distance, texts.target2Distance);
    this.setTextContent(n.target3Distance, texts.target3Distance);
    this.setTextContent(n.target1Speed, texts.target1Speed);
    this.setTextContent(n.target2Speed, texts.target2Speed);
    this.setTextContent(n.target3Speed, texts.target3Speed);
    this.setTextContent(n.target1DistRes, texts.target1DistRes);
    this.setTextContent(n.target2DistRes, texts.target2DistRes);
    this.setTextContent(n.target3DistRes, texts.target3DistRes);
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
    return this.nodes.monitorModeBtn.dataset.active === '1';
  },

  hideVisualizers() {
    const n = this.nodes;
    // this.hideUI(n.radarContainer);
    this.hideUI(n.amplitudeHeatmapContainer);
    this.hideUI(n.phaseHeatmapContainer);
    this.hideUI(n.gatesHeatmapContainer);
    this.hideUI(n.expChartContainer);
    this.hideUI(n.d3PlotContainer);
  },

  stopRecording() {
    const n = this.nodes;
    API.stopCapturing();
    this.list_csv_files();
    n.recordModeBtn.dataset.active = '0';
    n.targetRadarBtn.dataset.active = '0';
    this.setHeaderDefault();
    this.setButtonDefault(n.recordModeBtn);
    // this.setButtonDefault(n.targetRadarBtn);
    n.targetContainer.innerHTML = '';
  },
};
