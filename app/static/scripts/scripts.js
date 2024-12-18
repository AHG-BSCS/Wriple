import {
  color,
  drag,
  range,
  scaleOrdinal,
  select,
  selectAll,
  schemeCategory10
} from "./d3-7.8.5/index.js";

import {
  gridPlanes3D,
  lineStrips3D,
  points3D,
} from "./d3-3d-1.0.0/index.js";

document.addEventListener('DOMContentLoaded', () => {
  const recordButton = document.getElementById('record');
  const visualizeButton = document.getElementById('visualize');
  const fileList = document.getElementById('files-list');
  const packetcount = document.getElementById('image-count');

  /* Visualizer Functions */

  const origin = { x: 480, y: 250 };
  const j = 10;
  const scale = 20;
  const key = (d) => d.id;
  const startAngle = Math.PI / 4;
  const colorScale = scaleOrdinal(schemeCategory10);
  
  let scatter = [];
  let yLine = [];
  let xGrid = [];
  let beta = 0;
  let alpha = 0;
  let mx, my, mouseX = 0, mouseY = 0;
  
  const svg = select("svg")
    .call(
      drag()
        .on("drag", dragged)
        .on("start", dragStart)
        .on("end", dragEnd)
    )
    .append("g");
  
  const grid3d = gridPlanes3D()
    .rows(20)
    .origin(origin)
    .rotateY(startAngle)
    .rotateX(-startAngle)
    .scale(scale);

  const points3d = points3D()
    .origin(origin)
    .rotateY(startAngle)
    .rotateX(-startAngle)
    .scale(scale);

  const yScale3d = lineStrips3D()
    .origin(origin)
    .rotateY(startAngle)
    .rotateX(-startAngle)
    .scale(scale);

  function processData(data, tt) {
    /* ----------- GRID ----------- */

    const xGrid = svg.selectAll("path.grid").data(data[0], key);

    xGrid
      .enter()
      .append("path")
      .attr("class", "d3-3d grid")
      .merge(xGrid)
      .attr("stroke", "black")
      .attr("stroke-width", 0.3)
      .attr("fill", (d) => (d.ccw ? "#eee" : "#aaa"))
      .attr("fill-opacity", 0.9)
      .attr("d", grid3d.draw);

    xGrid.exit().remove();

    /* ----------- POINTS ----------- */

    const points = svg.selectAll("circle").data(data[1], key);

    points
      .enter()
      .append("circle")
      .attr("class", "d3-3d")
      .attr("opacity", 0)
      .attr("cx", posPointX)
      .attr("cy", posPointY)
      .merge(points)
      // .transition() returns a transition with the d3.transition.prototype
      // .duration(tt)
      .attr("r", 3)
      .attr("stroke", (d) => color(colorScale(d.id)).darker(3))
      .attr("fill", (d) => colorScale(d.id))
      .attr("opacity", 1)
      .attr("cx", posPointX)
      .attr("cy", posPointY);

    points.exit().remove();

    /* ----------- y-Scale ----------- */

    const yScale = svg.selectAll("path.yScale").data(data[2]);

    yScale
      .enter()
      .append("path")
      .attr("class", "d3-3d yScale")
      .merge(yScale)
      .attr("stroke", "black")
      .attr("stroke-width", 0.5)
      .attr("d", yScale3d.draw);

    yScale.exit().remove();

    /* ----------- y-Scale Text ----------- */

    const yText = svg.selectAll("text.yText").data(data[2][0]);

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

    selectAll(".d3-3d").sort(points3d.sort);
  }

  function posPointX(d) {
    return d.projected.x;
  }

  function posPointY(d) {
    return d.projected.y;
  }

  function dragStart(event) {
    mx = event.x;
    my = event.y;
  }

  function dragged(event) {
    beta = (event.x - mx + mouseX) * (Math.PI / 230);
    alpha = (event.y - my + mouseY) * (Math.PI / 230) * -1;

    const data = [
      grid3d.rotateY(beta + startAngle).rotateX(alpha - startAngle)(xGrid),
      points3d.rotateY(beta + startAngle).rotateX(alpha - startAngle)(scatter),
      yScale3d.rotateY(beta + startAngle).rotateX(alpha - startAngle)([yLine]),
    ];

    processData(data, 0);
  }

  function dragEnd(event) {
    mouseX = event.x - mx + mouseX;
    mouseY = event.y - my + mouseY;
  }

  /* Element Functions */

  function isRecording() {
    fetch('/recording_status', { method: "POST" })
      .then(response => response.json())
      .then(data => {
        if (data.status === true) {
          packetcount.textContent = `${data.total_packet_count}/100`
          setTimeout(() => {
            isRecording();
          }, 1000);
        }
        else {
          recordButton.style.backgroundColor = '#6a3acb';
          visualizeButton.style.backgroundColor = 'maroon';
          recordButton.style.backgroundImage = "url('static/images/record-start.png')";

          if (data.total_packet_count > 95) {
            packetcount.textContent = '100/100';
          }
          else {
            packetcount.textContent = `${data.total_packet_count}/100`;
          }

          fetch('/stop_recording', { method: "POST" });
          visualize();
          list_csv_files();
        }
      })
      .catch(err => alert("Fetch Error: " + err));
  }

  function visualize() {
    fetch('/visualize', { method: "POST" })
      .then(response => response.json())
      .then(data => {
        xGrid = [];
        scatter = [];
        yLine = [];

        let cnt = 0;
        const ap = data.ap_position;
        const device = data.device_position;
        scatter = data.reflected_positions.map(pos => ({ x: pos[0], y: pos[1], z: pos[2], id: "point-" + cnt++ }));
            
        for (let z = -j; z < j; z++) {
          for (let x = -j; x < j; x++) {
            xGrid.push({ x: x, y: 1, z: z});
          }
        }
    
        range(-1, 11, 1).forEach((d) => {
          yLine.push({ x: -j, y: -d, z: -j });
        });
    
        const datas = [
          grid3d(xGrid),
          points3d(scatter),
          yScale3d([yLine]),
        ];
        processData(datas, 1000);
      })
      .catch(err => {
        visualizeButton.style.backgroundColor = '#6a3acb';
        svg.selectAll('*').remove();
        alert("No data to visualize. Please record first." + err);
      });
      timeout(visualizeButton);
  };

  function list_csv_files() {
    fetch('/list_csv_files')
    .then(response => response.json())
    .then(files => {
      fileList.innerHTML = '';
      files.forEach(file => {
          const option = document.createElement('option');
          option.value = file;
          option.textContent = file;
          fileList.appendChild(option);
      });
    });
  }
  
  // Set timer to prevent spamming
  function timeout(button) {
    setTimeout(() => {
      button.disabled = false;
    }, 1000);
  }

  /* Elements Event Listener */

  recordButton.addEventListener('click', () => {
    recordButton.disabled = true;
      if (recordButton.style.backgroundColor === 'maroon') {
        recordButton.style.backgroundColor = '#6a3acb';
        recordButton.style.backgroundImage = "url('static/images/record-start.png')";
        fetch('/stop_recording', { method: "POST" });
        list_csv_files();
      } else {
        recordButton.style.backgroundColor = 'maroon';
        recordButton.style.backgroundImage = "url('static/images/record-stop.png')";
          fetch('/start_recording', { method: "POST" });
          isRecording();
      }
      timeout(recordButton);
  });

  visualizeButton.addEventListener('click', () => {
    if (visualizeButton.style.backgroundColor === 'maroon') {
      visualizeButton.style.backgroundColor = '#6a3acb';
      svg.selectAll('*').remove();
      packetcount.textContent = null;
    } else {
      visualizeButton.style.backgroundColor = 'maroon';
      visualize();
    }
    timeout(visualizeButton);
  });

  fileList.addEventListener('change', () => {
    const selectedFile = fileList.value;
    if (selectedFile) {
      fetch(`/visualize_csv/${selectedFile}`)
        .catch(error => alert(error));
      visualize();
      visualizeButton.style.backgroundColor = 'maroon';
    }
  });

  /* Initial Loading */

  list_csv_files();
});
