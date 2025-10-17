import { API } from '../api.js';
import { LINECHART, UI_COLORS } from '../constants.js';

export class LineChart {
  constructor({context, button, container, type}) {
    this.context = context;
    this.button = button;
    this.container = container;
    this.chart = null;

    this.type = type
    this.visible = false;
    this.interval = null;
    this.tick = 0;

    this.context.canvas.height = LINECHART.height;
    this.context.canvas.width = LINECHART.width;

    if (this.type === 'noise') {
      this.xAxisTickDelay = Math.floor(5000 / LINECHART.noiseChartDelay);
      this.xAxisTickDivider = this.xAxisTickDelay / 5
    }
    else if (this.type === 'detection') {
      this.xAxisTickDelay = Math.floor(5000 / LINECHART.detectionChartDelay);
      this.xAxisTickDivider = this.xAxisTickDelay / 5
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

  init() {
    this.show();
    if (this.chart) return;
    
    const yLabel = this.type === 'noise' ? 'Variance' : 'Presence';
    const xAxisTickDelay = this.xAxisTickDelay;
    const xAxisTickDivider = this.xAxisTickDivider;
    const fontSize = 18

    this.chart = new Chart(this.context, {
      type: 'line',
      data: {
      labels: [],
      datasets: [{
        label: yLabel,
        data: [],
        borderColor: 'rgb(31, 41, 55)',
        backgroundColor: 'rgba(148, 163, 183, 0.1)',
        tension: LINECHART.tension,
        pointRadius: LINECHART.pointRadius,
      }]
      },
      options: {
      responsive: true,
      animation: true,
      scales: {
        x: {
        title: { display: true, text: 'Time (s)', font: { size: fontSize }, color: 'black' },
        ticks: {
          font: { size: fontSize },
          callback: function (val, index) {
          // Show label every 5 seconds based
          return val % xAxisTickDelay === 0 ? val / xAxisTickDivider : '';
          }
        }
        },
        y: { 
        title: { display: true, text: yLabel, font: { size: fontSize }, color: 'black' },
        ticks: { font: { size: fontSize }, color: 'black' },
        suggestedMin: LINECHART.suggestedMin,
        suggestedMax: LINECHART.suggestedMax
        }
      },
      plugins: { 
        legend: { display: false, labels: { font: { size: fontSize } } },
        tooltip: { titleFont: { size: fontSize }, bodyFont: { size: fontSize } }
      }
      }
    });
  }

  async pushData() {
    if (!this.visible) return;
    const data = await API.getSignalVar();
    this.push(data.ampVariance);
  }

  start() {
    this.init();
    this.interval = setInterval(() => this.pushData(), LINECHART.noiseChartDelay);
  }

  stop() {
    clearInterval(this.interval);
  }

  clear() {
    this.hide();
    this.stop();
    if (!this.chart) return;

    this.context.clearRect(0, 0, this.context.canvas.width, this.context.canvas.height);
    this.chart.data.labels = [];
    this.chart.data.datasets[0].data = [];
    this.tick = 0;
    this.chart.update();
  }

  push(value) {
    // 30 seconds of data at 1Hz
    this.chart.data.labels.push(this.tick.toString() / 10);
    this.chart.data.datasets[0].data.push(value);
    this.chart.update();
    this.tick++;
    if (this.chart.data.labels.length >= LINECHART.maxDataPoints) {
      this.chart.data.labels.shift();
      this.chart.data.datasets[0].data.shift();
    }
  }
}
