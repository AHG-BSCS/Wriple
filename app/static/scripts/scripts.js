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
  const historyBtn = document.getElementById("history-btn")
  const datasetBtn = document.getElementById("dataset-btn")
  // const settingBtn = document.getElementById("setting-btn")
  // const infoBtn = document.getElementById("info-btn")
  // const darkModeSwitch = document.getElementById("dark-mode-switch")

  // Sidebar Buttons States
  let isMonitorActive = false;
  let isHistoryActive = false;
  let isDatasetActive = false;

  const presenceStatus = document.getElementById('presence-status');
  const targetDetected = document.getElementById("target-detected")
  const target1Dist = document.getElementById("target-1-distance")
  const packetCount = document.getElementById("packets-count")
  const rssiValue = document.getElementById("rssi-value")

  const esp32Status = document.getElementById("esp32-status")
  const apStatus = document.getElementById("ap-status")
  const rd03dStatus = document.getElementById("rd03d-status")
  const flaskStatus = document.getElementById("flask-status")
  const connectionStatus = document.getElementById("connection-status")
  const modelStatus = document.getElementById("model-status")

  const datasetList = document.getElementById('dataset-list');

  const radarContainer = document.getElementById('radar-container');
  const pointsContainer = document.getElementById('points');

  const presenceGroup = document.querySelectorAll('.group-presence-btn');
  let presenceClass = -1;
  const targetGroup = document.querySelectorAll('.group-target-btn');
  let targetClass;
  const losInput = document.getElementById('los-input');
  const angleInput = document.getElementById('angle-input');
  const distanceInput = document.getElementById('distance-input');

  const target1Angle = document.getElementById('target1-angle');
  const target2Angle = document.getElementById('target2-angle');
  const target3Angle = document.getElementById('target3-angle');
  const target1Distance = document.getElementById('target1-distance');
  const target2Distance = document.getElementById('target2-distance');
  const target3Distance = document.getElementById('target3-distance');
  const target1Speed = document.getElementById('target1-speed');
  const target2Speed = document.getElementById('target2-speed');
  const target3Speed = document.getElementById('target3-speed');
  const target1DistRes = document.getElementById('target1-distance-res');
  const target2DistRes = document.getElementById('target2-distance-res');
  const target3DistRes = document.getElementById('target3-distance-res');

  const recordBtn = document.getElementById('record-btn');
  const monitorBtn = document.getElementById('monitor-btn');
  const radarBtn = document.getElementById('radar-btn');
  const D3PlotBtn = document.getElementById('3d-plot-btn');

  // Buttons States
  let isRecording = false;
  let isMonitoring = false;
  let isRadarActive = false;
  let is3dPlotActive = false;

  let monitorVisualizeInterval;
  const d3PlotRefreshRate = 1000;
  let radarVisualizerInterval;
  const radarRefreshRate = 120;
  
  var btnDefaultColor = '#1F2937';
  var btnActiveColor = '#78350F';
  var btnSelectedColor = '#D1D5DB';
  var btnUnselectedColor = '#94A3B7';

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


  function setHeaderTextToDefault() {
    presenceStatus.textContent = "No";
    targetDetected.textContent = "0";
    target1Dist.textContent = "0m";
    packetCount.textContent = "0";
    rssiValue.textContent = "0";
  }

  function setAsideTextToDefault() {
    target1Angle.textContent = "0°";
    target2Angle.textContent = "0°";
    target3Angle.textContent = "0°";
    target1Distance.textContent = "0m";
    target2Distance.textContent = "0m";
    target3Distance.textContent = "0m";
    target1Speed.textContent = "0cm/s";
    target2Speed.textContent = "0cm/s";
    target3Speed.textContent = "0cm/s";
    target1DistRes.textContent = "0m";
    target2DistRes.textContent = "0m";
    target3DistRes.textContent = "0m";
  }

  function calculateDistance(x, y) {
    x = parseInt(x)
    y = parseInt(y)
    return (Math.sqrt(Math.pow(x, 2) + Math.pow(y, 2))) * 0.001;
  }

  function calculateAngle(x, y) {
    x = parseInt(x)
    y = parseInt(y)
    if (x == 0 && y == 0) return 0;
    else if (x > 0 && y > 0) return Math.atan2(x, y) * (180 / Math.PI);
    else if (x < 0 && y > 0) return Math.atan2(x, y) * (90 / Math.PI);
    // else if (x == 0 && y > 0) return 90;
    // else if (x == 0 && y < 0) return -90;
    // else if (y == 0 && x > 0) return 0;
    else return -1;
    // return Math.atan(y / x) * (180 / Math.PI) + 90;
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
          presence.textContent = "Yes"
        else
          presence.textContent = "No"

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
      })
      .catch(err => {
        setHeaderTextToDefault();
        console.log("Missing data for 3D plot." + err);
      });
  };

  function visualizeRadarData(data) {
    const radarRect = radarContainer.getBoundingClientRect();
    const centerX = pointsContainer.offsetWidth / 2;
    pointsContainer.innerHTML = ''; // Clear previous points

    for (let i = 0; i < 3; i++) {
      if (data.radarY[i] != '0') {
        const x = scaleXToRadar(data.radarX[i], radarRect.width);
        const y = scaleYToRadar(data.radarY[i], radarRect.height);
        createPoint((centerX + x), (radarRect.height - y));
      }
    }
  }

  function countTarget(data) {
    let targetCount = 0;
    for (let i = 0; i < 3; i++) {
      if (data.radarY[i] != '0') targetCount += 1;
    }
    return targetCount;
  }

  function setRadarData() {
    fetch('/get_radar_data', { method: "POST" })
      .then(response => response.json())
      .then(data => {
        const targetCount = countTarget(data);

        if (isRadarActive) visualizeRadarData(data);
        if (targetCount > 0) presenceStatus.textContent = "Yes";
        else presenceStatus.textContent = "No";
        if (data.radarY[0] != '0') {
            target1Dist.textContent = calculateDistance(data.radarX[0], data.radarY[0]).toFixed(2) + "m";
        }
        else target1Dist.textContent = "0m";

        if (data.modeStatus == -1) stopRecording();

        targetDetected.textContent = targetCount;
        packetCount.textContent = data.totalPacket;
        rssiValue.textContent = data.rssi;

        if (isMonitoring) {
          target1Angle.textContent = calculateAngle(data.radarX[0], data.radarY[0]).toFixed(2) + "°";
          target2Angle.textContent = calculateAngle(data.radarX[1], data.radarY[1]).toFixed(2) + "°";
          target3Angle.textContent = calculateAngle(data.radarX[2], data.radarY[2]).toFixed(2) + "°";
          target1Distance.textContent = calculateDistance(data.radarX[0], data.radarY[0]).toFixed(2) + "m";
          target2Distance.textContent = calculateDistance(data.radarX[1], data.radarY[1]).toFixed(2) + "m";
          target3Distance.textContent = calculateDistance(data.radarX[2], data.radarY[2]).toFixed(2) + "m";
          target1Speed.textContent = data.radarSpeed[0] + "cm/s";
          target2Speed.textContent = data.radarSpeed[1] + "cm/s";
          target3Speed.textContent = data.radarSpeed[2] + "cm/s";
          target1DistRes.textContent = data.radarDistRes[0];
          target2DistRes.textContent = data.radarDistRes[1];
          target3DistRes.textContent = data.radarDistRes[2];
        }

      })
      .catch(err => {
        setHeaderTextToDefault();
        console.log("Missing data for radar." + err);
      });
  }

  function scaleXToRadar(x, width) {
    x = parseInt(x)
    return Math.floor((x / 13856) * (width / 2));
  }

  function scaleYToRadar(y, height) {
    y = parseInt(y)
    return Math.floor((y / 8000) * height);
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


  function setRecordingData() {
    // Set target count to 0 if no target
    if (presenceClass == 0) targetClass = 0;
    else if (presenceClass != -1) {
      fetch('/set_recording_data', {
        method: "POST",
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            presence: presenceClass,
            target: targetClass,
            los: losInput.value,
            angle: angleInput.value,
            distance: distanceInput.value
        })
      })
    }
  }

  function stopRecording() {
    fetch('/stop_recording', { method: "POST" });
    list_csv_files();
    clearInterval(radarVisualizerInterval)
    setHeaderTextToDefault();

    isRecording = false;
    radarBtn.disabled = true;
    D3PlotBtn.disabled = true;
    radarBtn.style.backgroundColor = btnDefaultColor;
    D3PlotBtn.style.backgroundColor = btnDefaultColor;
    recordBtn.style.backgroundColor = btnDefaultColor;
    pointsContainer.innerHTML = '';
  }

  function startRecording() {
    setRecordingData();
    fetch('/start_recording/recording')
      .then(response => response.json())
      .then(data => {
        if (data.status === "error") throw new Error(data.message);
        
        radarBtn.disabled = false;
        recordBtn.style.backgroundColor = btnActiveColor;
        radarVisualizerInterval = setInterval(setRadarData, radarRefreshRate);
        isRecording = true;
      })
      .catch(err => {
        fetch('/stop_recording', { method: "POST" });
        alert('Missing or invalid data for recording.');
        list_csv_files();
        clearInterval(radarVisualizerInterval);

        isRecording = true;
        radarBtn.disabled = false;
        radarBtn.style.backgroundColor = btnDefaultColor;
        D3PlotBtn.disabled = false;
        recordBtn.style.backgroundColor = btnDefaultColor;
        D3PlotBtn.style.backgroundColor = btnDefaultColor;
      })
  }

  recordBtn.addEventListener('click', () => {
      if (isRecording) {
        stopRecording();
      } else {
        // Delay the recording
        setTimeout(() => {
          startRecording();
        }, 1000);
      }
      button_timeout(recordBtn);
  });

  function stopMonitoring() {
    fetch('/stop_recording', { method: "POST" });
    clearInterval(radarVisualizerInterval)
    clearInterval(monitorVisualizeInterval)
    setHeaderTextToDefault();
    setAsideTextToDefault();

    isMonitoring = false;
    radarBtn.disabled = true;
    D3PlotBtn.disabled = true;
    radarBtn.style.backgroundColor = btnDefaultColor;
    D3PlotBtn.style.backgroundColor = btnDefaultColor;
    monitorBtn.style.backgroundColor = btnDefaultColor;

    packetCount.textContent = "0";
    presenceStatus.textContent = "No"
    svg.selectAll('*').remove();
    pointsContainer.innerHTML = '';
  }

  function startMonitoring() {
    fetch('/start_recording/monitoring')
      .then(response => response.json())
      .then(data => {
        if (data.status === "error") throw new Error(data.message);
        
        D3PlotBtn.disabled = false;
        radarBtn.disabled = false;
        monitorBtn.style.backgroundColor = btnActiveColor;
        isMonitoring = true;
        radarVisualizerInterval = setInterval(setRadarData, radarRefreshRate);
      })
  }

  monitorBtn.addEventListener('click', () => {
      if (isMonitoring) stopMonitoring();
      else startMonitoring();
  });

  radarBtn.addEventListener('click', () => {
    if (isRadarActive) {
      radarBtn.style.backgroundColor = btnDefaultColor;
      setHeaderTextToDefault();
      setAsideTextToDefault();
      pointsContainer.innerHTML = '';
      isRadarActive = false;
    } else {
      radarBtn.style.backgroundColor = btnActiveColor;
      isRadarActive = true;
    }
});

  D3PlotBtn.addEventListener('click', () => {
    if (is3dPlotActive) {
      D3PlotBtn.style.backgroundColor = btnDefaultColor;
      clearInterval(monitorVisualizeInterval);
      setHeaderTextToDefault();
      svg.selectAll('*').remove();
      is3dPlotActive = false;
    } else {
      monitorVisualizeInterval = setInterval(visualize, d3PlotRefreshRate);
      D3PlotBtn.style.backgroundColor = btnActiveColor;
      is3dPlotActive = true;
    }
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

  collapseBtn.addEventListener('click', () => {
    const sidebar = document.getElementById('sidebar');
    const texts = document.querySelectorAll('.sidebar-collapse');
    sidebar.classList.toggle('w-20');

    texts.forEach(t => {
      t.classList.toggle('hidden');
    });
  });

  dashboardBtn.addEventListener('click', () => {
    if (!isMonitorActive) {
      dashboardBtn.style.backgroundColor = btnSelectedColor;
      historyBtn.style.backgroundColor = btnUnselectedColor;
      datasetBtn.style.backgroundColor = btnUnselectedColor;
      isMonitorActive = true;
      isHistoryActive = false;
      isDatasetActive = false;

      const monitorDivs = document.querySelectorAll('.monitor-hidden');
      monitorDivs.forEach(t => {
        t.classList.add('hidden');
      });

      const historyDivs = document.querySelectorAll('.history-hidden');
      historyDivs.forEach(t => {
        t.classList.remove('hidden');
      });

      const datasetDivs = document.querySelectorAll('.dataset-hidden');
      datasetDivs.forEach(t => {
        t.classList.remove('hidden');
      });
    }

    if (isRecording) {
      stopRecording();
      isRecording = false;
    }
  });

  historyBtn.addEventListener('click', () => {
    if (!isHistoryActive) {
      dashboardBtn.style.backgroundColor = btnUnselectedColor;
      historyBtn.style.backgroundColor = btnSelectedColor;
      datasetBtn.style.backgroundColor = btnUnselectedColor;
      isMonitorActive = false;
      isHistoryActive = true;
      isDatasetActive = false;

      const monitorDivs = document.querySelectorAll('.monitor-hidden');
      monitorDivs.forEach(t => {
        t.classList.remove('hidden');
      });

      const historyDivs = document.querySelectorAll('.history-hidden');
      historyDivs.forEach(t => {
        t.classList.add('hidden');
      });

      const datasetDivs = document.querySelectorAll('.dataset-hidden');
      datasetDivs.forEach(t => {
        t.classList.remove('hidden');
      });
    }

    if (isMonitoring) {
      stopMonitoring();
      isMonitoring = false;
      pointsContainer.innerHTML = '';
    }

    if (isRecording) {
      stopRecording();
      isRecording = false;
    }
  });

  datasetBtn.addEventListener('click', () => {
    if (!isDatasetActive) {
      dashboardBtn.style.backgroundColor = btnUnselectedColor;
      historyBtn.style.backgroundColor = btnUnselectedColor;
      datasetBtn.style.backgroundColor = btnSelectedColor;
      isMonitorActive = false;
      isHistoryActive = false;
      isDatasetActive = true;

      const monitorDivs = document.querySelectorAll('.monitor-hidden');
      monitorDivs.forEach(t => {
        t.classList.remove('hidden');
      });

      const historyDivs = document.querySelectorAll('.history-hidden');
      historyDivs.forEach(t => {
        t.classList.remove('hidden');
      });

      const datasetDivs = document.querySelectorAll('.dataset-hidden');
      datasetDivs.forEach(t => {
        t.classList.add('hidden');
      });
    }

    if (isMonitoring) {
      stopMonitoring();
      pointsContainer.innerHTML = '';
      isMonitoring = false;
    }
  });


  /* Initial Loading */

  presenceGroup.forEach(button => {
    button.addEventListener('click', () => {
      // Remove the active button
      presenceGroup.forEach(btn => btn.classList.remove('bg-amber-800'));
      
      // Set the active button
      button.classList.add('bg-amber-800');

      if (button.textContent === "Presence") presenceClass = 1;
      else presenceClass = 0;
    });
  });

  targetGroup.forEach(button => {
    button.addEventListener('click', () => {
      // Remove the active button
      targetGroup.forEach(btn => btn.classList.remove('bg-amber-800'));
      
      // Set the active button
      button.classList.add('bg-amber-800');
      targetClass = button.textContent;
    });
  });

  list_csv_files();
  dashboardBtn.click();
  isMonitorActive = true;

  D3PlotBtn.disabled = true;
  radarBtn.disabled = true;
});
