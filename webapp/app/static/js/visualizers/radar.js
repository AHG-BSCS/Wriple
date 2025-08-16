import { API } from '../api.js';
import { DEFAULTS } from '../constants.js';

export class RadarVisualizer {
  constructor({ui, expChart, pointsContainer}) {
    this.ui = ui; // ui should provide nodes and helper funcs
    this.expChart = expChart;
    this.pointsContainer = pointsContainer;
    this.interval = null;
    this.running = false;
    this.radarMaxDistance = 10_000;
    this.refreshRate = DEFAULTS.radarRefreshRate;
  }

  start() {
    if (this.running) return;
    this.running = true;
    this.interval = setInterval(() => this.tick(), this.refreshRate);
  }

  clear() {
    this.pointsContainer.innerHTML = '';
  }

  stop() {
    clearInterval(this.interval);
    this.interval = null;
    this.running = false;
    this.clear();
  }

  calculateDistance(x, y) {
    x = parseFloat(x);
    y = parseFloat(y);
    if (Number.isNaN(x) || Number.isNaN(y)) return 0;
    return Math.sqrt(x * x + y * y) * 0.001;
  }

  calculateAngle(x, y) {
    x = parseFloat(x);
    y = parseFloat(y);
    if (Number.isNaN(x) || Number.isNaN(y)) return 0;
    return Math.atan2(x, y) * (180 / Math.PI);
  }

  async tick() {
    try {
      const data = await API.getRadarData();
      if (!data || data.modeStatus === -1) {
        this.stop();
        this.ui.stopRecording();
        return;
      }
      const uiNodes = this.ui.nodes;
      const asideNodes = this.ui.asideNodes
      if (parseInt(data.rssi) > -60) uiNodes.presenceStatus.textContent = "?";
      else uiNodes.presenceStatus.textContent = data.presence ?? uiNodes.presenceStatus.textContent;

      if (data.target1[1] !== '0') {
        const distance = this.calculateDistance(data.target1[0], data.target1[1]);
        uiNodes.target1Dist.textContent = `${distance.toFixed(1)}m`;
      } else {
        uiNodes.target1Dist.textContent = '0.0m';
      }

      if (data.modeStatus === 1) {
        asideNodes.target1Angle.textContent = this.calculateAngle(data.target1[0], data.target1[1]).toFixed(2) + '°';
        asideNodes.target2Angle.textContent = this.calculateAngle(data.target2[0], data.target1[1]).toFixed(2) + '°';
        asideNodes.target3Angle.textContent = this.calculateAngle(data.target3[0], data.target1[1]).toFixed(2) + '°';
        asideNodes.target1Distance.textContent = this.calculateDistance(data.target1[0], data.target1[1]).toFixed(2) + 'm';
        asideNodes.target2Distance.textContent = this.calculateDistance(data.target2[0], data.target2[1]).toFixed(2) + 'm';
        asideNodes.target3Distance.textContent = this.calculateDistance(data.target3[0], data.target3[1]).toFixed(2) + 'm';
        asideNodes.target1Speed.textContent = data.target1[2] + 'cm/s';
        asideNodes.target2Speed.textContent = data.target2[2] + 'cm/s';
        asideNodes.target3Speed.textContent = data.target3[2] + 'cm/s';
        asideNodes.target1DistRes.textContent = data.target1[3];
        asideNodes.target2DistRes.textContent = data.target2[3];
        asideNodes.target3DistRes.textContent = data.target3[3];
      }

      uiNodes.packetCount.textContent = data.totalPacket;
      uiNodes.packetLoss.textContent = `${data.packetLoss}%`;
      uiNodes.expValue.textContent = data.rssi;

      if (uiNodes.expChartBtn.dataset.active === '1') {
        this.expChart.push(data.exp)
      }

      if (this.ui.nodes.targetRadarBtn.dataset.active === '1') {
        this.clear();
        const radarRect = this.ui.nodes.radarContainer.getBoundingClientRect();
        const centerX = this.ui.nodes.pointsContainer.offsetWidth / 2;
        [data.target1, data.target2, data.target3].forEach((t) => {
          if (t[1] !== 0) {
            const x = Math.floor((t[0] / this.radarMaxDistance) * (radarRect.width / 2));
            const y = Math.floor((t[1] / this.radarMaxDistance) * radarRect.height);
            this.ui.createRadarPoint(centerX + x, radarRect.height - y);
          }
        });
      }
    } catch (err) {
      this.ui.setHeaderDefault();
      console.warn('Missing data for radar.', err);
    }
  }
}
