import { API } from '../api.js';
import { HEATMAP, UI_COLORS } from '../constants.js';

export class HeatmapVisualizer {
  constructor({canvas, button, container, type, maxValue}) {
    this.button = button;
    this.container = container;

    this.type = type;
    this.visible = false;
    this.interval = null;

    this.heat = simpleheat(canvas);
    this.heat.radius(HEATMAP.radius, HEATMAP.blur);
    this.heat.gradient(HEATMAP.gradientWriple);
    this.heat.max(maxValue);
    this.buffer = Array.from({length: HEATMAP.subcarriers}, () => []);

    if (type === 'amplitude') {
      this.rows = HEATMAP.subcarriers;
      this.maxCols = HEATMAP.maxColumns;
      // Crop the heatmaps to canvas
      canvas.height = HEATMAP.subcarriers - 1;
      canvas.width = HEATMAP.maxColumns - 1;
    }
    else if (type === 'doppler') {
      this.rows = HEATMAP.rangeGates;
      this.maxCols = HEATMAP.dopplerBins;
      // Crop the heatmaps to canvas
      canvas.height = HEATMAP.rangeGates - 1;
      canvas.width = HEATMAP.dopplerBins - 1;
    }
  }

  show() {
    this.container.classList.remove('hidden');
    this.button.style.backgroundColor = UI_COLORS.btnActiveColor;
    this.visible = true;
  }

  hide() {
    this.container.classList.add('hidden');
    this.button.style.backgroundColor = UI_COLORS.btnDefaultColor;
    this.visible = false;
  }

  clear() {
    clearInterval(this.interval);
    this.buffer = Array.from({length: this.rows}, () => []);
    this.heat.clear().draw();
    this.hide();
  }

  start() {
    if (this.type === 'amplitude')
      this.interval = setInterval(() => this.fetchAndDrawCsi(), HEATMAP.delayCsi);
    else
      this.interval = setInterval(() => this.fetchAndDrawMmwave(), HEATMAP.delayMmwave);
  }

  stop() {
    clearInterval(this.interval);
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
      const data = await API.getchAmplitudeData();

      data.latestAmplitudes.forEach((val, i) => {
        this.buffer[i].push(val);
        if (this.buffer[i].length > this.maxCols)
          this.buffer[i].shift();
      });
      this.heat.data(this.flattenBufferHorizontal(this.buffer)).draw();
    } catch (err) {
      console.warn('Heatmap fetch failed', err);
    }
  }

  async fetchAndDrawMmwave() {
    try {
      const { latestDoppler } = await API.getRdmData();
      this.heat.clear();
      this.heat.data(latestDoppler).draw();
    } catch (err) {
      console.warn('Heatmap fetch failed', err);
    }
  }
}
