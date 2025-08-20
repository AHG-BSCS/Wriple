import { LINECHART, UI_COLORS } from '../constants.js';

export class LineChart {
  constructor({context, button, container}) {
    this.context = context;
    this.button = button;
    this.container = container;
    this.chart = null;

    this.visible = false;
    this.tick = 0;

    this.context.canvas.height = LINECHART.height;
    this.context.canvas.width = LINECHART.width;
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

    this.chart = new Chart(this.context, {
      type: 'line',
      data: {
        labels: [],
        datasets: [{
          label: 'Amplitude',
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
            title: { display: true, text: 'Time (s)' },
            ticks: {
              callback: function (val, index) {
                // Show label every 5 seconds based on monitoring interval
                return index % 10 === 0 ? this.getLabelForValue(val) : '';
              }
            }
          },
          y: { 
            title: { display: true, text: 'Amplitude' },
            suggestedMin: LINECHART.suggestedMin,
            suggestedMax: LINECHART.suggestedMax
          }
        },
        plugins: { legend: { display: false }}
      }
    });
  }

  clear() {
    this.hide();
    if (!this.chart) return;

    this.context.clearRect(0, 0, this.context.canvas.width, this.context.canvas.height);
    this.chart.data.labels = [];
    this.chart.data.datasets[0].data = [];
    this.tick = 0;
    this.chart.update();
  }

  push(value) {
    if (!this.chart) this.init();
    // 30 seconds of data at 1Hz
    if (this.chart.data.labels.length >= LINECHART.maxDataPoints) {
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
}
