import { API } from '../api.js';

export class HeatmapVisualizer {
  constructor({canvas, type, maxValue, maxCols, subcarrierCount, refreshRate}) {
    this.canvas = canvas;
    this.type = type;
    this.heat = simpleheat(canvas);
    this.maxCols = maxCols;
    this.subcarrierCount = subcarrierCount;
    this.buffer = Array.from({length: subcarrierCount}, () => []);
    this.interval = null;
    this.refreshRate = refreshRate;

    this.heat.radius(1, 0);
    this.heat.max(maxValue);

    // Crop the heatmaps to canvas
    this.canvas.height = subcarrierCount - 1;
    this.canvas.width = maxCols - 1;
  }

  start() {
    if (this.interval) return;
    if (this.type !== 'gates')
      this.interval = setInterval(() => this.fetchAndDrawCsi(), this.refreshRate);
    else
      this.interval = setInterval(() => this.fetchAndDrawMmwave(), this.refreshRate);
  }

  clear() {
    if (this.interval) clearInterval(this.interval);
    this.interval = null;
    this.buffer = Array.from({length: this.subcarrierCount}, () => []);
    this.heat.clear().draw();
  }

  stop() {
    clearInterval(this.interval);
    setTimeout(() => {}, this.refreshRate);
    this.interval = null;
    // this.buffer = Array.from({length: this.subcarrierCount}, () => []);
    // this.heat.clear().draw();
  }

  setMaxValue(newMax) {
    this.heat.max(newMax).draw();
  }

  flattenBufferHorizontal(buffer) {
    const flat = [];
    const height = buffer.length;
    const width = buffer[0]?.length || 0;
    for (let x = 0; x < width; x++) {
      for (let y = 0; y < height; y++) {
        flat.push([x, y, buffer[y][x]]);
      }
    }
    return flat;
  }

  async fetchAndDrawCsi() {
    try {
      const data = (this.type === 'phase') ? await API.fetchPhaseData() : await API.fetchAmplitudeData();
      const arr = (this.type === 'phase') ? data.latestPhases : data.latestAmplitudes;

      arr.forEach((val, i) => {
        this.buffer[i].push(val);
        if (this.buffer[i].length > this.maxCols) this.buffer[i].shift();
      });
      this.heat.data(this.flattenBufferHorizontal(this.buffer)).draw();
    } catch (err) {
      console.warn('Heatmap fetch failed', err);
    }
  }

  async fetchAndDrawMmwave() {
    try {
      const { latestDoppler } = await API.getMMWaveHeatmap();
      this.heat.clear();
      this.heat.data(latestDoppler).draw();
    } catch (err) {
      console.warn('Heatmap fetch failed', err);
    }
  }
}
