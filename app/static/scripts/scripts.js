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
  const monitorButton = document.getElementById('monitor');
  const visualizeButton = document.getElementById('visualize');
  const packetcount = document.getElementById('packet-count');
  const prediction = document.getElementById('prediction');
  const filesList = document.getElementById('files-list');
  const activityList = document.getElementById('activity-list');
  const classList = document.getElementById('class-list');
  const thresholdList = document.getElementById('threshold-list');
  const pointsContainer = document.getElementById('points');

  let packetCountInterval;
  let monitorVisualizeInterval;
  
  var buttonActiveColor = '#323A3F';
  var buttonInactiveColor = 'saddlebrown';
  var lastMode = -1;


  /* Visualizer Functions */


  const origin = { x: 400, y: 200 };
  const scale = 20;
  const key = (d) => d.id;
  const startAngle = 180;
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
      .attr("fill-opacity", 0.8)
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
      // .transition() // returns a transition with the d3.transition.prototype
      // .duration(tt)
      .attr("r", 3)
      .attr("stroke", (d) => color(colorScale(d.id)).darker(3))
      .attr("fill", (d) => colorScale(d.id))
      .attr("opacity", 1)
      .attr("cx", posPointX)
      .attr("cy", posPointY);

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
    visualizeButton.style.backgroundColor = buttonInactiveColor;
    beta = (event.x - mx + mouseX) * (Math.PI / 230) * -1;
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


  function setPacketCount() {
    fetch('/recording_status', { method: "POST" })
      .then(response => response.json())
      .then(data => {
        if (data.mode === 0) {
          lastMode = 0
          packetcount.textContent = `${data.total_packet}/250`;

          if (data.prediction === 1)
            prediction.textContent = "Movement Detected"
          else
            prediction.textContent = null
        }
        else if (data.mode === 1) {
          lastMode = 1
          packetcount.textContent = `${data.total_packet}`;

          if (data.prediction === 1)
            prediction.textContent = "Movement Detected"
          else
            prediction.textContent = null
        }
        else {
          clearInterval(packetCountInterval);
          clearInterval(monitorVisualizeInterval);

          if (lastMode === 0) {
            recordButton.style.backgroundColor = buttonActiveColor;
            recordButton.style.backgroundImage = "url('static/images/record-start.png')";
            monitorButton.disabled = false;
            visualizeButton.disabled = false;
            packetcount.textContent = null
            prediction.textContent = null
            list_csv_files();
            visualize();
          }
          lastMode = -1;
        }
      })
      .catch(err => alert("Fetch Error: " + err));
  }

  function visualize() {
    fetch('/visualize_data', { method: "POST" })
      .then(response => response.json())
      .then(data => {
        visualizeButton.style.backgroundColor = buttonInactiveColor;
        xGrid = [];
        scatter = [];
        yLine = [];
        let j = 10;
        let cnt = 0;

        if (data.prediction === 1)
          prediction.textContent = "Movement Detected"
        else
          prediction.textContent = null

        scatter = data.signal_coordinates.map(pos => ({ x: pos[0], y: pos[1], z: pos[2], id: "point-" + cnt++ }));

        for (let z = -j; z < j; z++) {
          for (let x = -j; x < j; x++) {
            xGrid.push({ x: x, y: -10, z: z});
          }
        }
    
        range(-10, 0, 1).forEach((d) => {
          yLine.push({ x: -j, y: -d, z: -j });
        });
    
        const datas = [
          grid3d(xGrid),
          points3d(scatter),
          yScale3d([yLine]),
        ];
        processData(datas, 1000);

        pointsContainer.innerHTML = ''; // Clear previous points
        // Convert the radar coordinates into pixel positions
        const x1 = scale_x(data.radar_x[0]);
        const y1 = scale_y(data.radar_y[0]);

        const x2 = scale_x(data.radar_x[1]);
        const y2 = scale_y(data.radar_y[1]);

        const x3 = scale_x(data.radar_x[2]);
        const y3 = scale_y(data.radar_y[2]);
        const centerX = pointsContainer.offsetWidth / 2;
        const topY = 0;

        createPoint((centerX + x1), (topY + y1));
        createPoint((centerX + x2), (topY + y2));
        createPoint((centerX + x3), (topY + y3));
      })
      .catch(err => {
        if (lastMode === 0) {
          visualizeButton.style.backgroundColor = buttonActiveColor;
          visualizeButton.disabled = false;
          svg.selectAll('*').remove();
        }
        console.log("No data to visualize." + err);
      });
  };

  function scale_x(x) {
    x = parseInt(x)
    return Math.floor((x / 13856) * (800 / 2));
  }

  function scale_y(y) {
    y = parseInt(y)
    return Math.floor((y / 8000) * 400);
  }

  function list_csv_files() {
    fetch('/list_csv_files')
      .then(response => response.json())
      .then(files => {
        filesList.innerHTML = ''; // Clear existing options
        const defaultOption = document.createElement('option');
        defaultOption.value = 'no-selection';
        defaultOption.textContent = '';
        filesList.appendChild(defaultOption);

        files.forEach(file => {
          const option = document.createElement('option');
          option.value = file;
          option.textContent = file;
          filesList.appendChild(option);
        });
      })
      .catch(err => console.error("Error fetching CSV files:", err));
  }
  
  function button_timeout(button) {
    button.disabled = true;
    setTimeout(() => {
      button.disabled = false;
    }, 1000);
  }

  function createPoint(x, y) {
    const point = document.createElement('div');
    point.className = 'point';
    point.style.left = `${x}px`;
    point.style.top = `${y}px`;
    pointsContainer.appendChild(point);
  }


  /* Elements Event Listener */


  recordButton.addEventListener('click', () => {
      if (recordButton.style.backgroundColor === buttonInactiveColor) {
        fetch('/stop_recording', { method: "POST" });
        list_csv_files();
        clearInterval(packetCountInterval)

        monitorButton.disabled = false;
        visualizeButton.disabled = false;
        recordButton.style.backgroundColor = buttonActiveColor;
        recordButton.style.backgroundImage = "url('static/images/record-start.png')";
        visualizeButton.style.backgroundColor = buttonActiveColor;
      } else {
        recordButton.disabled = true;
        setTimeout(() => {
          fetch('/start_recording/recording')
          .then(response => response.json())
          .then(data => {
            if (data.status === "error") {
              throw new Error(data.message);
            }
            monitorButton.disabled = true;
            visualizeButton.disabled = true;
            recordButton.style.backgroundColor = buttonInactiveColor;
            recordButton.style.backgroundImage = "url('static/images/record-stop.png')";
            packetCountInterval = setInterval(setPacketCount, 250);
            lastMode = 0;
          })
          .catch(err => {
            alert('Activity or Class is missing!');
            monitorButton.disabled = false;
            visualizeButton.disabled = false;
            recordButton.style.backgroundColor = buttonActiveColor;
            recordButton.style.backgroundImage = "url('static/images/record-start.png')";
            visualizeButton.style.backgroundColor = buttonActiveColor;
          })
        }, 1000);
      }
      recordButton.disabled = false;
      button_timeout(recordButton);
  });

  monitorButton.addEventListener('click', () => {
      if (monitorButton.style.backgroundColor === buttonInactiveColor) {
        fetch('/stop_recording', { method: "POST" });
        clearInterval(packetCountInterval)
        clearInterval(monitorVisualizeInterval)

        recordButton.disabled = false;
        visualizeButton.disabled = false;
        monitorButton.style.backgroundColor = buttonActiveColor;
        monitorButton.style.backgroundImage = "url('static/images/monitor-start.png')";
        visualizeButton.style.backgroundColor = buttonActiveColor;
        packetcount.textContent = null;
        prediction.textContent = null
        svg.selectAll('*').remove();
      } else {
        recordButton.disabled = true;
        monitorButton.style.backgroundColor = buttonInactiveColor;
        monitorButton.style.backgroundImage = "url('static/images/monitor-stop.png')";
        fetch('/start_recording/monitoring')
          .catch(error => alert(error));
        
        packetCountInterval = setInterval(setPacketCount, 2000);
        lastMode = 1;
      }
      if (visualizeButton.style.backgroundColor === buttonInactiveColor) {
        monitorVisualizeInterval = setInterval(visualize, 500);
      }
      button_timeout(monitorButton);
  });

  visualizeButton.addEventListener('click', () => {
    if (visualizeButton.style.backgroundColor === buttonInactiveColor) {
      visualizeButton.style.backgroundColor = buttonActiveColor;
      clearInterval(monitorVisualizeInterval);
      svg.selectAll('*').remove();
      packetcount.textContent = null;
      prediction.textContent = null
    } else {
      if (lastMode === 1) {
        monitorVisualizeInterval = setInterval(visualize, 100);
      }
      else {
        visualizeButton.style.backgroundColor = buttonInactiveColor;
        visualize();
      }
    }
    button_timeout(visualizeButton);
  });


  /* JQuery Elements */
  
  
  filesList.addEventListener('change', function() {
    const selectedFile = filesList.value;
    if (selectedFile !== 'no-selection') {
      fetch(`/visualize_csv_file/${selectedFile}`)
        .catch(error => alert(error));
      setTimeout(() => {
        visualize();
        visualizeButton.style.backgroundColor = buttonInactiveColor;
      }, 50)
    }
  });

  activityList.addEventListener('change', function() {
    const selectedAct = activityList.value;
    console.log(selectedAct)
    if (selectedAct) {
      fetch(`/set_activity/${selectedAct}`)
        .catch(error => alert(error));
    }
  });

  classList.addEventListener('change', function() {
    const selectedClass = classList.value;
    if (selectedClass) {
      fetch(`/set_class/${selectedClass}`)
        .catch(error => alert(error));
        if (selectedClass === '0') {
          activityList.innerHTML = ''; // Clear existing options
          const noneOption = document.createElement('option');
          noneOption.value = 'None';
          noneOption.textContent = '';
          activityList.appendChild(noneOption);

          const noPresenceOption = document.createElement('option');
          noPresenceOption.value = 'No_Presence';
          noPresenceOption.textContent = 'No Presence';
          activityList.appendChild(noPresenceOption);

          const noMovementOption = document.createElement('option');
          noMovementOption.value = 'No_Movement';
          noMovementOption.textContent = 'No Movement';
          activityList.appendChild(noMovementOption);
        } else if (selectedClass === '1') {
          activityList.innerHTML = ''; // Clear existing options
          const noneOption = document.createElement('option');
          noneOption.value = 'None';
          noneOption.textContent = '';
          activityList.appendChild(noneOption);

          const inPlaceOption = document.createElement('option');
          inPlaceOption.value = 'In_Place';
          inPlaceOption.textContent = 'In Place';
          activityList.appendChild(inPlaceOption);

          const sitStandOption = document.createElement('option');
          sitStandOption.value = 'Sit_Stand';
          sitStandOption.textContent = 'Sit/Stand';
          activityList.appendChild(sitStandOption);

          const movingOption = document.createElement('option');
          movingOption.value = 'Moving';
          movingOption.textContent = 'Moving';
          activityList.appendChild(movingOption);

          const walkingOption = document.createElement('option');
          walkingOption.value = 'Walking';
          walkingOption.textContent = 'Walking';
          activityList.appendChild(walkingOption);

          const runningOption = document.createElement('option');
          runningOption.value = 'Running';
          runningOption.textContent = 'Running';
          activityList.appendChild(runningOption);
        } else {
          activityList.innerHTML = ''; // Clear existing options
        }
    }
  });

  thresholdList.addEventListener('change', function() {
    const selectedValue = thresholdList.value;
    if (selectedValue) {
      fetch(`/set_threshold/${selectedValue}`)
        .catch(error => alert(error));
      
    }
    if (visualizeButton.style.backgroundColor === buttonInactiveColor) {
      setTimeout(() => {
        visualize();
      }, 50)
    }
  });


  /* Initial Loading */

  
  list_csv_files();
});
