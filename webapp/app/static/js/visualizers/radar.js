import { API } from '../api.js';
import { RADAR, UI_COLORS } from '../constants.js';

export class RadarVisualizer {
  constructor({button, targetContainer, radarContainer, targetDistance, setAsidesTexts}) {
    this.button = button;
    this.targetContainer = targetContainer;
    this.radarContainer = radarContainer;
    this.targetDistance = targetDistance;

    this.interval = null;
    this.visible = false;
    
    this.radarRect = radarContainer.getBoundingClientRect();
    this.centerX = targetContainer.offsetWidth / 2;

    this.setAsidesTexts = setAsidesTexts;
  }

  show() {
    // this.container.classList.remove('hidden');
    this.button.style.backgroundColor = UI_COLORS.btnActiveColor;
    this.visible = true;
  }

  hide() {
    // this.container.classList.add('hidden');
    this.button.style.backgroundColor = UI_COLORS.btnDefaultColor;
    this.visible = false;
  }

  start() {
    this.interval = setInterval(() => this.tick(), RADAR.refreshRate);
    this.show();
  }

  clear() {
    this.targetContainer.innerHTML = '';
    this.hide();
  }

  stop() {
    clearInterval(this.interval);
    this.clear();
    // Ensure to reset the radar container if mistimed
    setTimeout(() => this.targetContainer.innerHTML = '', 120);
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

  createRadarPoint(x, y) {
    // TODO: Add a distance text beside marker
    const point = document.createElement('div');
    point.className = 'point';
    point.style.left = `${x}px`;
    point.style.top = `${y}px`;
    this.targetContainer.appendChild(point);
  }

  async tick() {
    try {
      const data = await API.getRadarData();

      // if (data.modeStatus === 1) {
      //   this.setAsidesTexts({
      //     targetAngle: `${data.angle}°`,
      //     targetDistance: `${data.distance}m`,
      //   });
      // }

      this.targetContainer.innerHTML = '';
      const x = 0;
      const y = data.distance;
      this.createRadarPoint(this.centerX + x, this.radarRect.height - y * 45);
      this.createRadarPoint(this.centerX + x, this.radarRect.height - y);
    } catch (err) {
      this.stop();
      console.warn('Missing data for radar.', err);
    }
  }
}
