import { UI_COLORS } from '../constants.js';

export class LineChart {
  constructor({context, button, container}) {
    this.ctx = document.querySelector(context).getContext('2d');
    this.button = button;
    this.container = container;
    this.chart = null;
    this.tick = 0;
    
    this.ctx.canvas.width = 680;
    this.ctx.canvas.height = 200;
  }

  show() {
    this.container.classList.remove('hidden');
    this.button.style.backgroundColor = UI_COLORS.btnActiveColor;
    this.button.dataset.active = '1';
  }

  hide() {
    this.container.classList.add('hidden');
    this.button.style.backgroundColor = UI_COLORS.btnDefaultColor;
    this.button.dataset.active = '0';
  }

  init() {
    this.show();
    if (this.chart) return;

    this.chart = new Chart(this.ctx, {
      type: 'line',
      data: {
        labels: [],
        datasets: [{
          label: 'Amplitude',
          data: [],
          borderColor: 'rgb(31, 41, 55)',
          backgroundColor: 'rgba(148, 163, 183, 0.1)',
          tension: 0.3,
          pointRadius: 0
        }]
      },
      options: {
        responsive: true,
        animation: true,
        scales: {
          x: {
            title: { display: true, text: 'Time (s)' },
            ticks: {
              callback: function (val, index) {
                // Show label every 5 seconds
                return index % 10 === 0 ? this.getLabelForValue(val) : '';
              }
            }
          },
          y: { title: { display: true, text: 'Amplitude' }, suggestedMin: -80, suggestedMax: -20}
        },
        plugins: { legend: { display: false }}
      }
    });
  }

  push(value) {
    if (!this.chart) this.init();
    if (this.chart.data.labels.length >= 120) { // 30 seconds of data at 1Hz
      this.chart.data.labels.shift();
      this.chart.data.datasets[0].data.shift();
    }
    if (this.tick % 5 == 0) {
      this.chart.data.labels.push(this.tick.toString() / 10);
      this.chart.data.datasets[0].data.push(value);
      this.chart.update();
    }
    this.tick++;
  }

  clear() {
    this.hide();
    if (!this.chart) return;
    
    this.ctx.clearRect(0, 0, this.ctx.canvas.width, this.ctx.canvas.height);
    this.chart.data.labels = [];
    this.chart.data.datasets[0].data = [];
    this.tick = 0;
    this.chart.update();
  }
}
