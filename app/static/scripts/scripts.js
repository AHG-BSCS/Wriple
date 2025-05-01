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
  // const sideNavBar = document.getElementById("sidebar")
  const collapseBtn = document.getElementById("collapse-btn")

  const dashboardBtn = document.getElementById("dashboard-btn")
  // const historyBtn = document.getElementById("history-btn")
  const datasetBtn = document.getElementById("dataset-btn")
  // const settingBtn = document.getElementById("setting-btn")
  // const infoBtn = document.getElementById("info-btn")
  // const darkModeSwitch = document.getElementById("dark-mode-switch")

  const presence = document.getElementById('presence');
  const targetNumber = document.getElementById("target-number")
  const target1Distance = document.getElementById("target-1-distance")
  const packetNumber = document.getElementById("packets-number")

  const esp32Status = document.getElementById("esp32-status")
  const apStatus = document.getElementById("ap-status")
  const rd03dStatus = document.getElementById("rd03d-status")
  const flaskStatus = document.getElementById("flask-status")
  const connectionStatus = document.getElementById("connection-status")
  const modelStatus = document.getElementById("model-status")

  const datasetList = document.getElementById('dataset-list');
  // const thresholdList = document.getElementById('threshold-list');

  // const radarContainer = document.getElementById('radar-container');
  const pointsContainer = document.getElementById('points');

  const presenceSelect = document.getElementById('presence-select');
  const noPresenceSelect = document.getElementById('no-presence-select');
  const select1 = document.getElementById('1-select');
  const select2 = document.getElementById('2-select');
  const select3 = document.getElementById('3-select');
  const losInput = document.getElementById('los-input');
  const angleInput = document.getElementById('angle-input');
  const distanceInput = document.getElementById('distance-input');

  // const recordBtn = document.getElementById('record');
  const recordBtn = document.getElementById('record-btn');
  const monitorBtn = document.getElementById('monitor-btn');
  const radarBtn = document.getElementById('radar-btn');
  const D3PlotBtn = document.getElementById('3d-plot-btn');

  // Buttons States
  let isRecording = false;
  let isMonitoring = false;
  let isRadarActive = false;
  let is3dPlotActive = false;

  let packetCountInterval;
  let monitorVisualizeInterval;
  
  var btnDefaultColor = '#1F2937';
  var btnActiveColor = '#78350F';
  var lastMode = -1;

  const activityOptions = {
    '0': [
      { value: 'None', text: '' },
      { value: 'No_Presence', text: 'No Presence' },
      { value: 'No_Movement', text: 'No Movement' }
    ],
    '1': [
      { value: 'None', text: '' },
      { value: 'In_Place', text: 'In Place' },
      { value: 'Sit_Stand', text: 'Sit/Stand' },
      { value: 'Moving', text: 'Moving' },
      { value: 'Walking', text: 'Walking' },
      { value: 'Running', text: 'Running' }
    ]
  };

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
    D3PlotBtn.style.backgroundColor = btnActiveColor;
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
          packetNumber.textContent = `${data.total_packet}/250`;

          if (data.presence === 1)
            presence.textContent = "Movement Detected"
          else
            presence.textContent = null
        }
        else if (data.mode === 1) {
          lastMode = 1
          packetNumber.textContent = `${data.total_packet}`;

          if (data.presence === 1)
            presence.textContent = "Movement Detected"
          else
            presence.textContent = null
        }
        else {
          clearInterval(packetCountInterval);
          clearInterval(monitorVisualizeInterval);

          if (lastMode === 0) {
            recordBtn.style.backgroundColor = btnDefaultColor;
            recordBtn.style.backgroundImage = "url('static/images/record-start.png')";
            monitorBtn.disabled = false;
            D3PlotBtn.disabled = false;
            packetNumber.textContent = null
            presence.textContent = null
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
        D3PlotBtn.style.backgroundColor = btnActiveColor;
        xGrid = [];
        scatter = [];
        yLine = [];
        let j = 10;
        let cnt = 0;

        if (data.presence === 1)
          presence.textContent = "Movement Detected"
        else
          presence.textContent = null

        scatter = data.signalCoordinates.map(pos => ({ x: pos[0], y: pos[1], z: pos[2], id: "point-" + cnt++ }));

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
        const centerX = pointsContainer.offsetWidth / 2;
        const topY = 0;

        // Convert the radar coordinates into pixel positions
        for (let i = 0; i < 3; i++) {
          if (data.radarY[i] != '0') {
            const x = scaleXToRadar(data.radarX[i]);
            const y = scaleYToRadar(data.radarY[i]);
            createPoint((centerX + x), (topY + y));
          }
        }
      })
      .catch(err => {
        if (lastMode === 0) {
          D3PlotBtn.style.backgroundColor = btnDefaultColor;
          D3PlotBtn.disabled = false;
          svg.selectAll('*').remove();
        }
        console.log("No data to visualize." + err);
      });
  };

  function scaleXToRadar(x) {
    x = parseInt(x)
    return Math.floor((x / 13856) * (800 / 2));
  }

  function scaleYToRadar(y) {
    y = parseInt(y)
    return Math.floor((y / 8000) * 400);
  }

  function list_csv_files() {
    fetch('/list_csv_files')
      .then(response => response.json())
      .then(files => {
        datasetList.innerHTML = ''; // Clear existing options
        const defaultOption = document.createElement('option');
        defaultOption.value = 'no-selection';
        defaultOption.textContent = '';
        datasetList.appendChild(defaultOption);

        files.forEach(file => {
          const option = document.createElement('option');
          option.value = file;
          option.textContent = file;
          datasetList.appendChild(option);
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


  recordBtn.addEventListener('click', () => {
      if (isRecording) {
        fetch('/stop_recording', { method: "POST" });
        list_csv_files();
        clearInterval(packetCountInterval)

        radarBtn.disabled = false;
        radarBtn.style.backgroundColor = btnDefaultColor;
        D3PlotBtn.disabled = false;
        D3PlotBtn.style.backgroundColor = btnDefaultColor;
        recordBtn.style.backgroundColor = btnDefaultColor;
        isRecording = false;
      } else {
        setTimeout(() => {
          fetch('/start_recording/recording')
          .then(response => response.json())
          .then(data => {
            if (data.status === "error") throw new Error(data.message);
            
            radarBtn.disabled = true;
            D3PlotBtn.disabled = true;
            recordBtn.style.backgroundColor = btnActiveColor;
            packetCountInterval = setInterval(setPacketCount, 250);
            isRecording = true;
            lastMode = 0;
          })
          .catch(err => {
            fetch('/stop_recording', { method: "POST" });
            alert('Activity or Class is missing!');
            list_csv_files();
            clearInterval(packetCountInterval)

            radarBtn.disabled = false;
            radarBtn.style.backgroundColor = btnDefaultColor;
            D3PlotBtn.disabled = false;
            recordBtn.style.backgroundColor = btnDefaultColor;
            D3PlotBtn.style.backgroundColor = btnDefaultColor;
          })
        }, 1000);
      }
      button_timeout(recordBtn);
  });

  monitorBtn.addEventListener('click', () => {
      if (isMonitoring) {
        fetch('/stop_recording', { method: "POST" });
        clearInterval(packetCountInterval)
        clearInterval(monitorVisualizeInterval)

        radarBtn.disabled = false;
        radarBtn.style.backgroundColor = btnDefaultColor;
        D3PlotBtn.disabled = false;
        D3PlotBtn.style.backgroundColor = btnDefaultColor;
        monitorBtn.style.backgroundColor = btnDefaultColor;

        packetNumber.textContent = "0";
        presence.textContent = "No"
        svg.selectAll('*').remove();
        isMonitoring = false;
      } else {
        monitorBtn.style.backgroundColor = btnActiveColor;
        fetch('/start_recording/monitoring')
          .catch(error => alert(error));
        
        packetCountInterval = setInterval(setPacketCount, 250);
        isMonitoring = true;
        lastMode = 1;
      }
      button_timeout(monitorBtn);
  });

  D3PlotBtn.addEventListener('click', () => {
    if (is3dPlotActive) {
      D3PlotBtn.style.backgroundColor = btnDefaultColor;
      clearInterval(monitorVisualizeInterval);

      packetNumber.textContent = "0";
      presence.textContent = "No"
      svg.selectAll('*').remove();
      is3dPlotActive = false;
    } else {
      if (lastMode === 1) {
        monitorVisualizeInterval = setInterval(visualize, 200);
      }
      else {
        D3PlotBtn.style.backgroundColor = btnActiveColor;
        visualize();
      }
      is3dPlotActive = true;
    }
    button_timeout(D3PlotBtn);
  });

  datasetList.addEventListener('change', function() {
    const selectedFile = datasetList.value;
    if (selectedFile !== 'no-selection') {
      fetch(`/visualize_csv_file/${selectedFile}`)
        .catch(error => alert(error));
      setTimeout(() => {
        visualize();
        D3PlotBtn.style.backgroundColor = btnActiveColor;
      }, 50)
    }
  });

  // thresholdList.addEventListener('change', function() {
  //   const selectedValue = thresholdList.value;
  //   if (selectedValue) {
  //     fetch(`/set_threshold/${selectedValue}`)
  //       .catch(error => alert(error));
      
  //   }
  //   if (D3PlotBtn.style.backgroundColor === btnActiveColor) {
  //     setTimeout(() => {
  //       visualize();
  //     }, 50)
  //   }
  // });

  collapseBtn.addEventListener('click', () => {
    const sidebar = document.getElementById('sidebar');
    const texts = document.querySelectorAll('.sidebar-text');
    sidebar.classList.toggle('w-64');
    sidebar.classList.toggle('w-16');

    texts.forEach(t => {
      t.classList.toggle('hidden');
    });
  });


  /* Initial Loading */

  
  list_csv_files();
});
