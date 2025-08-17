import { color, drag, range, scaleOrdinal, select, selectAll, schemeCategory10 } from ".././vendors/d3-7.8.5/index.js";
import { gridPlanes3D, lineStrips3D, points3D } from ".././vendors/d3-3d-1.0.0/index.js";
import { UI_COLORS } from '../constants.js';
import { API } from '../api.js';

export class D3Plot {
  constructor({svg, button, container, refreshRate}) {
    this.button = button;
    this.container = container;
    this.interval = null;
    this.visible = false;
    this.refreshRate = refreshRate;

    this.origin = { x: 400, y: 200 };
    this.scale = 20;
    this.key = (d) => d.id;
    this.startAngle = 180;
    this.colorScale = scaleOrdinal(schemeCategory10);

    this.scatter = [];
    this.yLine = [];
    this.xGrid = [];

    this.beta = 0;
    this.alpha = 0;
    this.mx = 0;
    this.my = 0;
    this.mouseX = 0;
    this.mouseY = 0;

    this.svgSelector = select(svg)
      .call(
        drag()
          .on("drag", (event) => this.dragged(event))
          .on("start", (event) => this.dragStart(event))
          .on("end", (event) => this.dragEnd(event))
      )
      .append("g");

    this.grid3d = gridPlanes3D()
      .rows(20)
      .origin(this.origin)
      .rotateY(this.startAngle)
      .rotateX(-this.startAngle)
      .scale(this.scale);

    this.points3d = points3D()
      .origin(this.origin)
      .rotateY(this.startAngle)
      .rotateX(-this.startAngle)
      .scale(this.scale);

    this.yScale3d = lineStrips3D()
      .origin(this.origin)
      .rotateY(this.startAngle)
      .rotateX(-this.startAngle)
      .scale(this.scale);
  }

  processData(data, tt) {
    /* ----------- GRID ----------- */

    const xGrid = this.svgSelector.selectAll("path.grid").data(data[0], this.key);

    xGrid
      .enter()
      .append("path")
      .attr("class", "d3-3d grid")
      .merge(xGrid)
      .attr("stroke", "black")
      .attr("stroke-width", 0.3)
      .attr("fill", (d) => (d.ccw ? "#eee" : "#aaa"))
      .attr("fill-opacity", 0.8)
      .attr("d", this.grid3d.draw);

    xGrid.exit().remove();

    /* ----------- POINTS ----------- */

    const points = this.svgSelector.selectAll("circle").data(data[1], this.key);

    points
      .enter()
      .append("circle")
      .attr("class", "d3-3d")
      .attr("opacity", 0)
      .attr("cx", this.posPointX)
      .attr("cy", this.posPointY)
      .merge(points)
      // .transition() // returns a transition with the d3.transition.prototype
      // .duration(tt)
      .attr("r", 3)
      .attr("stroke", (d) => color(this.colorScale(d.id)).darker(3))
      .attr("fill", (d) => this.colorScale(d.id))
      .attr("opacity", 1)
      .attr("cx", this.posPointX)
      .attr("cy", this.posPointY);

    points.exit().remove();

    /* ----------- y-Scale ----------- */

    // const yScale = svg.selectAll("path.yScale").data(data[2]);

    // yScale
    //   .enter()
    //   .append("path")
    //   .attr("class", "d3-3d yScale")
    //   .merge(yScale)
    //   .attr("stroke", "black")
    //   .attr("stroke-width", 0.5)
    //   .attr("d", yScale3d.draw);

    // yScale.exit().remove();

    /* ----------- y-Scale Text ----------- */

    const yText = this.svgSelector.selectAll("text.yText").data(data[2][0]);

    yText
      .enter()
      .append("text")
      .attr("class", "d3-3d yText")
      .attr("font-family", "system-ui, sans-serif")
      .merge(yText)
      .each(function (d) {
        d.centroid = { x: d.rotated.x, y: d.rotated.y, z: d.rotated.z };
      })
      .attr("x", (d) => d.projected.x)
      .attr("y", (d) => d.projected.y)
      .text((d) => (d.y <= 0 ? d.y : ''));

    yText.exit().remove();

    selectAll(".d3-3d").sort(this.points3d.sort);
  }

  posPointX(d) {
    return d.projected.x;
  }

  posPointY(d) {
    return d.projected.y;
  }

  dragged(event) {
    if (this.scatter .length === 0) return;

    this.beta = (event.x - this.mx + this.mouseX) * (Math.PI / 230) * -1;
    this.alpha = (event.y - this.my + this.mouseY) * (Math.PI / 230) * -1;

    const data = [
      this.grid3d.rotateY(this.beta + this.startAngle).rotateX(this.alpha - this.startAngle)(this.xGrid),
      this.points3d.rotateY(this.beta + this.startAngle).rotateX(this.alpha - this.startAngle)(this.scatter),
      this.yScale3d.rotateY(this.beta + this.startAngle).rotateX(this.alpha - this.startAngle)([this.yLine]),
    ];

    this.processData(data, 0);
  }

  dragStart(event) {
    this.mx = event.x;
    this.my = event.y;
  }

  dragEnd(event) {
    this.mouseX = event.x - this.mx + this.mouseX;
    this.mouseY = event.y - this.my + this.mouseY;
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
    this.hide();
    this.svgSelector.selectAll('*').remove();
    this.xGrid = [];
    this.scatter = [];
    this.yLine = [];
    this.beta = 0;
    this.alpha = 0;
    this.mx = 0;
    this.my = 0;
    this.mouseX = 0;
    this.mouseY = 0;
  }

  start() {
    this.interval = setInterval(() => this.tick(), this.refreshRate);
  }

  stop() {
    clearInterval(this.interval);
  }

  async tick() {
    try {
      const data = await API.visualize3d();
      this.xGrid = [];
      this.scatter = [];
      this.yLine = [];
      let j = 10;
      let cnt = 0;

      this.scatter = data.signalCoordinates.map(pos => ({ x: pos[0], y: pos[1], z: pos[2], id: "point-" + cnt++ }));
      for (let z = -j; z < j; z++) {
        for (let x = -j; x < j; x++) {
          this.xGrid.push({ x: x, y: -10, z: z });
        }
      }
      range(-10, 0, 1).forEach((d) => {
        this.yLine.push({ x: -j, y: -d, z: -j });
      });
      const datas = [
        this.grid3d(this.xGrid),
        this.points3d(this.scatter),
        this.yScale3d([this.yLine]),
      ];
      this.processData(datas, 1000);
    } catch (err) {
      console.warn('Missing data for 3D plot.', err);
    }
  }
}
