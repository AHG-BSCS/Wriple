import { API } from '../api.js';
import { UI_COLORS } from '../constants.js';

export class RadarVisualizer {
  constructor({button, targetContainer, radarContainer, targetDistance, refreshRate, setAsidesTexts}) {
    this.button = button;
    this.targetContainer = targetContainer;
    this.radarContainer = radarContainer;
    this.targetDistance = targetDistance;
    this.interval = null;
    this.visible = false;
    
    this.radarMaxDistance = 10_000;
    this.refreshRate = refreshRate;

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
    this.interval = setInterval(() => this.tick(), this.refreshRate);
    this.show();
  }

  clear() {
    this.targetContainer.innerHTML = '';
    this.hide();
  }

  stop() {
    clearInterval(this.interval);
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

  createRadarPoint(x, y) {
    const point = document.createElement('div');
    point.className = 'point';
    point.style.left = `${x}px`;
    point.style.top = `${y}px`;
    this.targetContainer.appendChild(point);
  }

  async tick() {
    try {
      const data = await API.getRadarData();

      if (data.target1[1] !== '0') {
        const distance = this.calculateDistance(data.target1[0], data.target1[1]);
        this.targetDistance.textContent = `${distance.toFixed(1)}m`;
      } else {
        this.targetDistance.textContent = '0.0m';
      }

      if (data.modeStatus === 1) {
        this.setAsidesTexts({
          target1Angle: this.calculateAngle(data.target1[0], data.target1[1]).toFixed(2) + '°',
          target2Angle: this.calculateAngle(data.target2[0], data.target2[1]).toFixed(2) + '°',
          target3Angle: this.calculateAngle(data.target3[0], data.target3[1]).toFixed(2) + '°',
          target1Distance: this.calculateDistance(data.target1[0], data.target1[1]).toFixed(2) + 'm',
          target2Distance: this.calculateDistance(data.target2[0], data.target2[1]).toFixed(2) + 'm',
          target3Distance: this.calculateDistance(data.target3[0], data.target3[1]).toFixed(2) + 'm',
          target1Speed: data.target1[2] + 'cm/s',
          target2Speed: data.target2[2] + 'cm/s',
          target3Speed: data.target3[2] + 'cm/s',
          target1DistRes: data.target1[3],
          target2DistRes: data.target2[3],
          target3DistRes: data.target3[3]
        });
      }

      this.targetContainer.innerHTML = '';
      [data.target1, data.target2, data.target3].forEach((t) => {
        if (t[1] !== 0) {
          const x = Math.floor((t[0] / this.radarMaxDistance) * (this.radarRect.width / 2));
          const y = Math.floor((t[1] / this.radarMaxDistance) * this.radarRect.height);
          this.createRadarPoint(this.centerX + x, this.radarRect.height - y);
        }
      });
    } catch (err) {
      this.stop();
      console.warn('Missing data for radar.', err);
    }
  }
}
