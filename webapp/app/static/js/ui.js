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
    signal_var: $(SELECTORS.signal_var),
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
    asideContainer: $(SELECTORS.asideContainer),

    targetDistance: $(SELECTORS.targetDistance),
    targetAngle: $(SELECTORS.targetAngle),
    targetEnergy: $(SELECTORS.targetEnergy),

    metaClass: $(SELECTORS.metaClass),
    metaTargetDistance: $(SELECTORS.metaTargetDistance),
    metaAngleRange: $(SELECTORS.metaAngleRange),
    metaActivity: $(SELECTORS.metaActivity),
    metaObstruction: $(SELECTORS.metaObstruction),
    metaPacketCount: $(SELECTORS.metaPacketCount),
    metaSamplingRate: $(SELECTORS.metaSamplingRate),
    metaRecordingDate: $(SELECTORS.metaRecordingDate)
  },

  visualizerNodes: {
    targetContainer: $(SELECTORS.targetContainer),
    radarContainer: $(SELECTORS.radarContainer),

    amplitudeCanvas: $(SELECTORS.amplitudeCanvas),
    amplitudeHeatmapContainer: $(SELECTORS.amplitudeHeatmapContainer),

    gatesCanvas: $(SELECTORS.gatesCanvas),
    gatesHeatmapContainer: $(SELECTORS.gatesHeatmapContainer),

    expLineChartCanvasCtx: document.querySelector(SELECTORS.expLineChartCanvas).getContext('2d'),
    expLineChartContainer: $(SELECTORS.expLineChartContainer),

    d3PlotContainer: $(SELECTORS.d3PlotContainer),
  },

  sliderNodes: {
    amplitudeMaxSlider: $(SELECTORS.amplitudeMaxSlider),
    gatesMaxSlider: $(SELECTORS.gatesMaxSlider),

    amplitudeMaxValue: $(SELECTORS.amplitudeMaxValue),
    gatesMaxValue: $(SELECTORS.gatesMaxValue)
  },

  nodes: {
    datasetList: $(SELECTORS.datasetList),
  },

  statusBarStates: {
    ap: false,
    flask: false,
    esp32: false,
    ld2420: false,
    model: false
  },

  async updateStatusBar() {
    const statusBarIcon = this.headerNodes;
    const statusBarStates = this.statusBarStates;
    try {
      const status = await API.getSystemStatus();
      statusBarStates.ap = status.ap;
      statusBarStates.flask = status.flask;
      statusBarStates.esp32 = status.esp32;
      statusBarStates.ld2420 = status.ld2420;
      statusBarStates.model = status.model;

      if (status.ap) statusBarIcon.apStatus.style.fill = UI_COLORS.statusBarActiveColor;
      else statusBarIcon.apStatus.style.fill = UI_COLORS.statusBarInactiveColor;
      
      statusBarIcon.flaskStatus.style.fill = UI_COLORS.statusBarActiveColor;

      if (status.esp32) statusBarIcon.esp32Status.style.fill = UI_COLORS.statusBarActiveColor;
      else statusBarIcon.esp32Status.style.fill = UI_COLORS.statusBarInactiveColor;
      
      if (status.ld2420) statusBarIcon.ld2420Status.style.fill = UI_COLORS.statusBarActiveColor;
      else statusBarIcon.ld2420Status.style.fill = UI_COLORS.statusBarInactiveColor;
      
      if (status.model) statusBarIcon.modelStatus.style.fill = UI_COLORS.statusBarActiveColor;
      else statusBarIcon.modelStatus.style.fill = UI_COLORS.statusBarInactiveColor;
      // map status fields to UI nodes as needed
      // if (status && n.presenceStatus) {
      //   n.presenceStatus.textContent = status.presence ?? n.presenceStatus.textContent;
      // }
    } catch (err) {
      statusBarStates.ap = false;
      statusBarStates.flask = false;
      statusBarStates.esp32 = false;
      statusBarStates.ld2420 = false;
      statusBarStates.model = false;

      statusBarIcon.flaskStatus.style.fill = UI_COLORS.statusBarInactiveColor;
      statusBarIcon.esp32Status.style.fill = UI_COLORS.statusBarInactiveColor;
      statusBarIcon.ld2420Status.style.fill = UI_COLORS.statusBarInactiveColor;
      statusBarIcon.modelStatus.style.fill = UI_COLORS.statusBarInactiveColor;
    }
  },

  async list_csv_files() {
    const fileSelection = this.nodes.datasetList;
    try {
      const files = await API.getCsvFiles();
      if (fileSelection && Array.isArray(files)) {
        fileSelection.innerHTML = files.map(f => `<option value="${f}">${f}</option>`).join('\n');
        
        // Set the last file as selected by default
        if (files.length > 0) {
          fileSelection.value = files[files.length - 1];
          fileSelection.dispatchEvent(new Event('change'));
        } else {
          fileSelection.value = '';
        }
      }
    } catch(e) { console.warn('Could not load CSV list', e); }
  },

  setHeaderTexts(text = {}) {
    const n = this.headerNodes;
    n.packetCount.textContent = text?.packetCount || '0';
    n.expValue.textContent = text?.rssi || '0';
  },
  
  setPresenceTexts(text = {}) {
    const n = this.headerNodes;
    n.presenceStatus.textContent = text?.presence || '?';
    n.packetLoss.textContent = text?.loss || '0%';
    n.signal_var.textContent = text?.noise || '0';
  },

  setAsidesTexts(texts = {}) {
    const n = this.asideNodes;
    n.targetDistance.textContent = texts?.targetDistance || '0m';
    n.targetAngle.textContent = texts?.targetAngle || '0°';
    n.targetEnergy.textContent = texts?.targetEnergy || '0';
  },

  updateMetadataTexts(meta = {}) {
    const n = this.asideNodes;
    n.metaClass.textContent = meta?.Presence ?? '';
    n.metaTargetDistance.textContent = meta?.Distance ?? '';
    n.metaAngleRange.textContent = meta?.Angle ?? '';
    n.metaActivity.textContent = meta?.Activity ?? '';
    n.metaObstruction.textContent = meta?.Obstruction ?? '';
    n.metaPacketCount.textContent = meta?.packet_count ?? '';
    n.metaSamplingRate.textContent = meta?.sampling_rate ?? '';
    n.metaRecordingDate.textContent = meta?.recording_date ?? '';
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
    this.hideUI(n.gatesHeatmapContainer);
    this.hideUI(n.expLineChartContainer);
    this.hideUI(n.d3PlotContainer);
  },

  hideElements() {
    this.sidebarNodes.historyTabBtn.classList.add('hidden');
    this.sidebarNodes.datasetTabBtn.classList.add('hidden');
    this.sidebarNodes.historyGroup.forEach(el => this.hideUI(el));
    this.sidebarNodes.datasetGroup.forEach(el => this.hideUI(el));
    this.asideNodes.asideContainer.classList.add('hidden');
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
