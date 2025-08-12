import {
  color,
  drag,
  range,
  scaleOrdinal,
  select,
  selectAll,
  schemeCategory10
} from "./vendors/d3-7.8.5/index.js";

import {
  gridPlanes3D,
  lineStrips3D,
  points3D,
} from "./vendors/d3-3d-1.0.0/index.js";

document.addEventListener('DOMContentLoaded', () => {
  const collapseBtn = document.getElementById("collapse-btn");
  const dashboardBtn = document.getElementById("dashboard-btn");
  const historyBtn = document.getElementById("history-btn");
  const datasetBtn = document.getElementById("dataset-btn");
  // const settingBtn = document.getElementById("setting-btn");
  // const infoBtn = document.getElementById("info-btn");
  // const darkModeSwitch = document.getElementById("dark-mode-switch");

  // Sidebar Buttons States
  let isMonitorActive = false;
  let isHistoryActive = false;
  let isDatasetActive = false;

  const presenceStatus = document.getElementById('presence-status');
  const target1Dist = document.getElementById("target-1-distance");
  const packetCount = document.getElementById("packets-count");
  const packetLoss = document.getElementById("packet-loss");
  const experimentalValue = document.getElementById("exp-value");

  const apStatus = document.getElementById("ap-status");
  const flaskStatus = document.getElementById("flask-status");
  const esp32Status = document.getElementById("esp32-status");
  const ld2420Status = document.getElementById("ld2420-status");
  const rd03dStatus = document.getElementById("rd03d-status");
  const portStatus = document.getElementById("port-status");
  const modelStatus = document.getElementById("model-status");

  const datasetList = document.getElementById('dataset-list');

  const radarContainer = document.getElementById('radar-container');
  const pointsContainer = document.getElementById('points');

  const classSelection = document.getElementById('class-select');
  const targetSelection = document.getElementById('target-select');
  const stateSelection = document.getElementById('state-select');
  const activitySelection = document.getElementById('activity-select');
  const angleSelection = document.getElementById('angle-select');
  const distanceSelection = document.getElementById('distance-select');
  const obstructedSelection = document.getElementById('obstructed-select');
  const obstructionSelection = document.getElementById('obstruction-select');
  const spacingSelection = document.getElementById('spacing-select');

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

  const recordModeBtn = document.getElementById('record-mode-btn');
  const monitorModeBtn = document.getElementById('monitor-mode-btn');
  const targetRadarBtn = document.getElementById('target-radar-btn');
  const amplitudeHeatmapBtn = document.getElementById('amplitude-heatmap-btn');
  const phaseHeatmapBtn = document.getElementById('phase-heatmap-btn');
  const gatesHeatmapBtn = document.getElementById('gates-heatmap-btn');
  const expChartBtn = document.getElementById('exp-line-chart-btn');
  const d3PlotBtn = document.getElementById('3d-plot-btn');

  const amplitudeHeatmapContainer = document.getElementById('amplitude-heatmap-container');
  const phaseHeatmapContainer = document.getElementById('phase-heatmap-container');
  const gatesHeatmapContainer = document.getElementById('gates-heatmap-container');
  const expChartContainer = document.getElementById('exp-chart-container');
  const d3PlotContainer = document.getElementById('3d-plot-container');

  const amplitudeCanvas = document.getElementById('amplitude-heatmap');
  const phaseCanvas = document.getElementById('phase-heatmap');
  const gatesCanvas = document.getElementById('gates-heatmap');
  const expCanvasCtx = document.getElementById('exp-chart').getContext('2d');
  let expChart;

  const amplitudeMaxSlider = document.getElementById("amplitude-max-slider");
  const amplitudeMaxValue = document.getElementById("amplitude-max-value");
  const phaseMaxSlider = document.getElementById("phase-max-slider");
  const phaseMaxValue = document.getElementById("phase-max-value");
  const gatesMaxSlider = document.getElementById("gates-max-slider");
  const gatesMaxValue = document.getElementById("gates-max-value");

  // Buttons States
  let isRecording = false;
  let isMonitoring = false;
  let isAmpitudeHeatmapVisible = false;
  let isPhaseHeatmapVisible = false;
  let isGateHeatmapVisible = false;
  let isExpChartVisible = false;
  let isRadarVisible = false;
  let is3DPlotVisible = false;

  let d3PlotVisualizerInterval;
  let radarVisualizerInterval;
  let amplitudeHeatmapInterval;
  let phaseHeatmapInterval;
  let gatesHeatmapInterval;
  // let expHistogramInterval;
  const d3PlotRefreshRate = 1000;
  const radarRefreshRate = 100;
  const recordingDelay = 1000;
  const heatmapRefreshRate = 100;
  const gatesHeatmapRefreshRate = 333;
  const systemStatusInterval = 2000;

  const radarMaxDistance = 10_000;
  
  // Sidebar Tab
  const btnSelectedColor = '#D1D5DB';
  const btnUnselectedColor = '#94A3B7';
  // Status Bar Icons
  const statusBarActiveColor = 'limegreen';
  const statusBarInactiveColor = 'brown';
  // Floating Buttons
  const btnDefaultColor = '#1F2937';
  const btnActiveColor = '#78350F';

  const amplitudeHeatmap = simpleheat(amplitudeCanvas);
  const phaseHeatmap = simpleheat(phaseCanvas);
  const gatesHeatmap = simpleheat(gatesCanvas);
  const SUBCARRIER_COUNT = 85;
  const MAX_COLS = 160;
  const DOPPLER_BINS = 20;
  const RANGE_GATES = 16;

  const MAX_EXP_POINTS = 120; // 30 seconds of data at 1Hz
  const EXP_TICK_INTERVAL = 10; // seconds

  let amplitudeBuffer = Array.from({ length: SUBCARRIER_COUNT }, () => []);
  let phaseBuffer = Array.from({ length: SUBCARRIER_COUNT }, () => []);
  let tick = 0;

  const OPTIONS = {
    class: [
      { value: '0', label: 'Absence' },
      { value: '1', label: 'Presence' }
    ],
    target: [
      { value: '0', label: 'No Target' },
      { value: '1', label: '1' },
      { value: '2', label: '2' },
      { value: '3', label: '3' }
    ],
    state: [
      { value: '0', label: 'No State' },
      { value: '1', label: 'Motionless' },
      { value: '2', label: 'Moving' }
    ],
    activity: [
      { value: '0', label: 'No Activity' },
      { value: '1', label: 'Stand' },
      { value: '2', label: 'Sit' },
      { value: '3', label: 'Walking' },
      { value: '4', label: 'Running' },
    ],
    angle: [
      { value: '360', label: 'No Angle' },
      { value: '-45', label: '-45°' },
      { value: '-30', label: '-30°' },
      { value: '-15', label: '-15°' },
      { value: '0', label: '0°' },
      { value: '15', label: '15°' },
      { value: '30', label: '30°' },
      { value: '45', label: '45°' }
    ],
    distance: [
      { value: '-1', label: 'No Distance' },
      { value: '1', label: '1m' },
      { value: '2', label: '2m' },
      { value: '3', label: '3m' },
      { value: '4', label: '4m' },
      { value: '5', label: '5m' },
      { value: '6', label: '6m' },
      { value: '7', label: '7m' },
      { value: '8', label: '8m' },
      { value: '9', label: '9m' },
      { value: '10', label: '10m' }
    ],
    obstructed: [
      { value: '0', label: 'No' },
      { value: '1', label: 'Yes' }
    ],
    obstruction: [
      { value: '0', label: 'None' },
      { value: '1', label: 'Plastic' },
      { value: '2', label: 'Wood' },
      { value: '3', label: 'Glass' },
      { value: '4', label: 'Concrete' },
      { value: '5', label: 'Metal' }
    ],
    spacing: [
      { value: '3', label: '3m' },
      { value: '4', label: '4m' },
      { value: '5', label: '5m' },
      { value: '6', label: '6m' },
      { value: '7', label: '7m' },
      { value: '8', label: '8m' },
      { value: '9', label: '9m' },
      { value: '10', label: '10m' },
      { value: '11', label: '11m' },
      { value: '12', label: '12m' }
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
  
  const svg = select("#d3-plot")
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
    d3PlotBtn.style.backgroundColor = btnActiveColor;
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
    target1Dist.textContent = "0.00m";
    packetCount.textContent = "0";
    packetLoss.textContent = "0%";
    experimentalValue.textContent = "0";
  }

  function setAsideTextToDefault() {
    target1Angle.textContent = "0.00°";
    target2Angle.textContent = "0.00°";
    target3Angle.textContent = "0.00°";
    target1Distance.textContent = "0.00m";
    target2Distance.textContent = "0.00m";
    target3Distance.textContent = "0.00m";
    target1Speed.textContent = "0cm/s";
    target2Speed.textContent = "0cm/s";
    target3Speed.textContent = "0cm/s";
    target1DistRes.textContent = "0";
    target2DistRes.textContent = "0";
    target3DistRes.textContent = "0";
  }

  function calculateDistance(x, y) {
    x = parseInt(x)
    y = parseInt(y)
    return (Math.sqrt(Math.pow(x, 2) + Math.pow(y, 2))) * 0.001;
  }

  function calculateAngle(x, y) {
    x = parseInt(x)
    y = parseInt(y)
    return Math.atan2(x, y) * (180 / Math.PI);
  }

  function visualize3DPlot() {
    fetch('/visualize_3d_plot', { method: "POST" })
      .then(response => response.json())
      .then(data => {
        d3PlotBtn.style.backgroundColor = btnActiveColor;
        xGrid = [];
        scatter = [];
        yLine = [];
        let j = 10;
        let cnt = 0;

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
        console.log("Missing data for 3D plot." + err);
      });
  }

  function visualizeRadarData(target) {
    const radarRect = radarContainer.getBoundingClientRect();
    const centerX = pointsContainer.offsetWidth / 2;
    

    if (target[1] != '0') {
      const x = scaleXToRadar(target[0], radarRect.width);
      const y = scaleYToRadar(target[1], radarRect.height);
      createPoint((centerX + x), (radarRect.height - y));
    }
  }

  function countTarget(data) {
    let targetCount = 0;
    if (data.target1[1] != '0') targetCount += 1;
    if (data.target2[1] != '0') targetCount += 1;
    if (data.target3[1] != '0') targetCount += 1;
    return targetCount;
  }

  function visualizeExperimental(exp) {
    if (expChart.data.labels.length >= MAX_EXP_POINTS) {
      expChart.data.labels.shift();
      expChart.data.datasets[0].data.shift();
    }
    
    if (tick % 5 == 0) {
      expChart.data.labels.push(tick / 10);
      expChart.data.datasets[0].data.push(exp);
      expChart.update();
    }
    tick++;
  }

  function setRadarData() {
    fetch('/get_radar_data', { method: "POST" })
      .then(response => response.json())
      .then(data => {
        if (data.modeStatus != -1) {
          if (parseInt(data.rssi) > -60) presenceStatus.textContent = "Too Close";
          else presenceStatus.textContent = data.presence;

          if (data.target1[1] != '0')
            target1Dist.textContent = calculateDistance(data.target1[0], data.target1[1]).toFixed(2) + "m";
          else target1Dist.textContent = "0m";

          if (isMonitoring) {
            target1Angle.textContent = calculateAngle(data.target1[0], data.target1[1]).toFixed(2) + "°";
            target2Angle.textContent = calculateAngle(data.target2[0], data.target2[1]).toFixed(2) + "°";
            target3Angle.textContent = calculateAngle(data.target3[0], data.target3[1]).toFixed(2) + "°";
            target1Distance.textContent = calculateDistance(data.target1[0], data.target1[1]).toFixed(2) + "m";
            target2Distance.textContent = calculateDistance(data.target2[0], data.target2[1]).toFixed(2) + "m";
            target3Distance.textContent = calculateDistance(data.target3[0], data.target3[1]).toFixed(2) + "m";
            target1Speed.textContent = data.target1[2] + "cm/s";
            target2Speed.textContent = data.target2[2] + "cm/s";
            target3Speed.textContent = data.target3[2] + "cm/s";
            target1DistRes.textContent = data.target1[3];
            target2DistRes.textContent = data.target2[3];
            target3DistRes.textContent = data.target3[3];
          }

          // This data must be updated
          if (isExpChartVisible) visualizeExperimental(data.exp);
          if (isRadarVisible) {
            pointsContainer.innerHTML = ''; // Clear previous points
            visualizeRadarData(data.target1);
            visualizeRadarData(data.target2);
            visualizeRadarData(data.target3);
          }
          packetCount.textContent = data.totalPacket;
          packetLoss.textContent = `${data.packetLoss}%`;
          experimentalValue.textContent = data.rssi;
        }
        else stopRecording();
      })
      .catch(err => {
        setHeaderTextToDefault();
        console.log("Missing data for radar." + err);
      });
  }

  function scaleXToRadar(x, width) {
    x = parseInt(x)
    return Math.floor((x / radarMaxDistance) * (width / 2));
  }

  function scaleYToRadar(y, height) {
    y = parseInt(y)
    return Math.floor((y / radarMaxDistance) * height);
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


  function checkSystemStatus() {
    fetch('/check_system_status', { method: "POST" })
      .then(response => response.json())
      .then(data => {
        if (data.ap) apStatus.style.fill = statusBarActiveColor;
        else apStatus.style.fill = statusBarInactiveColor;
        
        flaskStatus.style.fill = statusBarActiveColor;

        if (data.esp32) esp32Status.style.fill = statusBarActiveColor;
        else esp32Status.style.fill = statusBarInactiveColor;
        
        if (data.ld2420) ld2420Status.style.fill = statusBarActiveColor;
        else ld2420Status.style.fill = statusBarInactiveColor;

        if (data.rd03d) rd03dStatus.style.fill = statusBarActiveColor;
        else rd03dStatus.style.fill = statusBarInactiveColor;

        if (data.port) portStatus.style.fill = statusBarActiveColor;
        else portStatus.style.fill = statusBarInactiveColor;

        if (data.model) modelStatus.style.fill = statusBarActiveColor;
        else modelStatus.style.fill = statusBarInactiveColor;
      })
      .catch(err => {
        flaskStatus.style.fill = statusBarInactiveColor;
        esp32Status.style.fill = statusBarInactiveColor;
        ld2420Status.style.fill = statusBarInactiveColor;
        rd03dStatus.style.fill = statusBarInactiveColor;
        modelStatus.style.fill = statusBarInactiveColor;
      });
  }

  async function setRecordParameter() {
     const response = await fetch('/set_record_parameter', {
      method: "POST",
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        class_label: classSelection.value,
        target_count: targetSelection.value,
        state: stateSelection.value,
        activity: activitySelection.value,
        angle: angleSelection.value,
        distance_t1: distanceSelection.value,
        obstructed: obstructedSelection.value,
        obstruction: obstructionSelection.value,
        spacing: spacingSelection.value
      })
    })
    const data = await response.json();
    if (data.status === 'error') {
      alert('Missing or invalid recording parameters.');
      return false;
    }
    return true;
  }

  async function startRecording() {
    const isParameterSet = await setRecordParameter();
    if (isParameterSet) {
      fetch('/start_recording/recording')
        .then(response => response.json())
        .then(data => {
          if (data.status === 'error') throw new Error(data.error);

          recordModeBtn.style.backgroundColor = btnActiveColor;
          isRecording = true;
          
          if (!isRadarVisible) {
            isRadarVisible = true;
            targetRadarBtn.style.backgroundColor = btnActiveColor;
            radarVisualizerInterval = setInterval(setRadarData, radarRefreshRate);
          }
        })
    }
  }

  function stopRecording() {
    fetch('/stop_recording', { method: "POST" });
    list_csv_files();
    clearInterval(radarVisualizerInterval)
    setHeaderTextToDefault();

    isRecording = false;
    isRadarVisible = false;
    targetRadarBtn.style.backgroundColor = btnDefaultColor;
    recordModeBtn.style.backgroundColor = btnDefaultColor;
    pointsContainer.innerHTML = '';
  }

  recordModeBtn.addEventListener('click', () => {
    if (isRecording) {
      stopRecording();
    } else {
      if (isMonitoring) {
        fetch('/stop_recording', { method: "POST" });
        clearInterval(radarVisualizerInterval)
        isRadarVisible = false;
        setHeaderTextToDefault();
      }
      setTimeout(() => {
        startRecording();
      }, recordingDelay); // Delay the recording
    }
    button_timeout(recordModeBtn);
  });

  function stopMonitoring() {
    fetch('/stop_recording', { method: "POST" });
    clearInterval(radarVisualizerInterval);
    clearInterval(d3PlotVisualizerInterval);
    clearInterval(amplitudeHeatmapInterval);
    clearInterval(phaseHeatmapInterval);
    stopGatesHeatmap();

    isMonitoring = false;
    isRadarVisible = false;
    targetRadarBtn.disabled = true;
    d3PlotBtn.disabled = true;
    targetRadarBtn.style.backgroundColor = btnDefaultColor;
    d3PlotBtn.style.backgroundColor = btnDefaultColor;
    monitorModeBtn.style.backgroundColor = btnDefaultColor;

    packetCount.textContent = "0";
    presenceStatus.textContent = "No"
    svg.selectAll('*').remove();
    d3PlotContainer.classList.add('hidden');
    pointsContainer.innerHTML = '';

    setTimeout(() => {
      setHeaderTextToDefault();
      setAsideTextToDefault();
    }, 50); // Wait for events interval to finished
  }

  function startMonitoring() {
    fetch('/start_recording/monitoring')
      .then(response => response.json())
      .then(data => {
        if (data.status === "error") throw new Error(data.message);
        if (isAmpitudeHeatmapVisible) {
          fetch('/request_csi_data', { method: "POST" });
          amplitudeHeatmapInterval = setInterval(fetchAmplitudeData, heatmapRefreshRate);
        }

        if (isPhaseHeatmapVisible) {
          fetch('/request_csi_data', { method: "POST" });
          phaseHeatmapInterval = setInterval(fetchPhaseData, heatmapRefreshRate);
        }
        
        d3PlotBtn.disabled = false;
        targetRadarBtn.disabled = false;
        monitorModeBtn.style.backgroundColor = btnActiveColor;
        isMonitoring = true;
        radarVisualizerInterval = setInterval(setRadarData, radarRefreshRate);
      })
  }

  monitorModeBtn.addEventListener('click', () => {
      if (isMonitoring) stopMonitoring();
      else startMonitoring();
  });

  targetRadarBtn.addEventListener('click', () => {
    if (isRadarVisible) {
      if (isMonitoring && isDatasetActive) {
        stopMonitoring();
        setHeaderTextToDefault();
        clearInterval(radarVisualizerInterval)
        targetRadarBtn.disabled = false;
      }
      targetRadarBtn.style.backgroundColor = btnDefaultColor;
      setHeaderTextToDefault();
      setAsideTextToDefault();
      pointsContainer.innerHTML = '';
      isRadarVisible = false;
    } else {
      targetRadarBtn.style.backgroundColor = btnActiveColor;
      isRadarVisible = true;
      
      // Start the radar when in Dataset Tab
      if (isDatasetActive) {
        fetch('/start_recording/monitoring');
        isMonitoring = true;
        radarVisualizerInterval = setInterval(setRadarData, radarRefreshRate);
      }
    }
  });

  function startAmplitudeHeatmap() {
    amplitudeHeatmapBtn.style.backgroundColor = btnActiveColor;
    amplitudeHeatmapContainer.classList.remove('hidden');
    isAmpitudeHeatmapVisible = true;
    amplitudeHeatmapInterval = setInterval(fetchAmplitudeData, heatmapRefreshRate);
  }

  function stopAmplitudeHeatmap() {
    amplitudeHeatmapBtn.style.backgroundColor = btnDefaultColor;
    amplitudeHeatmapContainer.classList.add('hidden');
    clearInterval(amplitudeHeatmapInterval);
    setTimeout(() => {}, heatmapRefreshRate);
    amplitudeBuffer = Array.from({ length: SUBCARRIER_COUNT }, () => []);
    amplitudeHeatmap.clear().draw();
    isAmpitudeHeatmapVisible = false;
  }

  amplitudeHeatmapBtn.addEventListener('click', () => {
    if (isAmpitudeHeatmapVisible) stopAmplitudeHeatmap();
    else startAmplitudeHeatmap();
  });

  function startPhaseHeatmap() {
    phaseHeatmapBtn.style.backgroundColor = btnActiveColor;
    phaseHeatmapContainer.classList.remove('hidden');
    isPhaseHeatmapVisible = true;
    phaseHeatmapInterval = setInterval(fetchPhaseData, heatmapRefreshRate);
  }

  function stopPhaseHeatmap() {
    phaseHeatmapBtn.style.backgroundColor = btnDefaultColor;
    phaseHeatmapContainer.classList.add('hidden');
    clearInterval(phaseHeatmapInterval);
    setTimeout(() => {}, heatmapRefreshRate);
    phaseBuffer = Array.from({ length: SUBCARRIER_COUNT }, () => []);
    phaseHeatmap.clear().draw();
    isPhaseHeatmapVisible = false;
  }

  phaseHeatmapBtn.addEventListener('click', () => {
    if (isPhaseHeatmapVisible) stopPhaseHeatmap();
    else startPhaseHeatmap();
  });

  async function fetchMMWaveData() {
    const res = await fetch('/get_mmwave_heatmap_data', { method: 'POST' });
    const { heatmap } = await res.json();
    gatesHeatmap.clear();
    gatesHeatmap.data(heatmap).draw();
  }

  function startGatesHeatmap() {
    gatesHeatmapBtn.style.backgroundColor = btnActiveColor;
    gatesHeatmapContainer.classList.remove('hidden');
    isGateHeatmapVisible = true;
    gatesHeatmapInterval = setInterval(fetchMMWaveData, gatesHeatmapRefreshRate);
  }

  function stopGatesHeatmap() {
    gatesHeatmapBtn.style.backgroundColor = btnDefaultColor;
    gatesHeatmapContainer.classList.add('hidden');
    clearInterval(gatesHeatmapInterval);
    setTimeout(() => {}, gatesHeatmapRefreshRate);
    // phaseBuffer = Array.from({ length: SUBCARRIER_COUNT }, () => []);
    gatesHeatmap.clear().draw();
    isGateHeatmapVisible = false;
  }

  gatesHeatmapBtn.addEventListener('click', () => {
    if (isGateHeatmapVisible) stopGatesHeatmap();
    else startGatesHeatmap();
  });

  d3PlotBtn.addEventListener('click', () => {
    if (is3DPlotVisible) {
      d3PlotBtn.style.backgroundColor = btnDefaultColor;
      d3PlotContainer.classList.add('hidden');
      clearInterval(d3PlotVisualizerInterval);
      setHeaderTextToDefault();
      svg.selectAll('*').remove();
      is3DPlotVisible = false;
    } else {
      d3PlotBtn.style.backgroundColor = btnActiveColor;
      d3PlotContainer.classList.remove('hidden');
      d3PlotVisualizerInterval = setInterval(visualize3DPlot, d3PlotRefreshRate);
      is3DPlotVisible = true;
    }
  });

  datasetList.addEventListener('change', function() {
    const selectedFile = datasetList.value;
    if (selectedFile !== 'no-selection') {
      // fetch(`/visualize_csv_file/${selectedFile}`)
      //   .catch(error => alert(error));
      // setTimeout(() => {
      //   visualize();
      //   D3PlotBtn.style.backgroundColor = btnActiveColor;
      // }, 50)
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
      targetRadarBtn.disabled = true;

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
      hideVisualizers();
    }

    if (isRecording) stopRecording();
    if (isMonitoring) {
      stopMonitoring();
      targetRadarBtn.disabled = true;
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
      targetRadarBtn.disabled = true;

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

    if (isMonitoring) stopMonitoring();
    if (isRecording) stopRecording();
  });

  datasetBtn.addEventListener('click', () => {
    if (!isDatasetActive) {
      dashboardBtn.style.backgroundColor = btnUnselectedColor;
      historyBtn.style.backgroundColor = btnUnselectedColor;
      datasetBtn.style.backgroundColor = btnSelectedColor;
      isMonitorActive = false;
      isHistoryActive = false;
      isDatasetActive = true;
      targetRadarBtn.disabled = false;

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
      targetRadarBtn.disabled = false;
    }
  });

  function fetchAmplitudeData() {
    fetch('/fetch_amplitude_data', { method: "POST" })
      .then(res => res.json())
      .then(data => {
        // Push new time column for amplitude
        data.latestAmplitudes.forEach((val, i) => {
          amplitudeBuffer[i].push(val);
          if (amplitudeBuffer[i].length > MAX_COLS) amplitudeBuffer[i].shift();
        });
  
        amplitudeHeatmap.data(flattenBufferHorizontal(amplitudeBuffer)).draw();
      })
      .catch(err => console.error("Amplitude heatmap fetch failed:", err));
  }

  function fetchPhaseData() {
    fetch('/fetch_phase_data', { method: "POST" })
      .then(res => res.json())
      .then(data => {
        // Push new time column for phase
        data.latestPhases.forEach((val, i) => {
          phaseBuffer[i].push(val);
          if (phaseBuffer[i].length > MAX_COLS) phaseBuffer[i].shift();
        });

        phaseHeatmap.data(flattenBufferHorizontal(phaseBuffer)).draw();
      })
      .catch(err => console.error("Phase heatmap fetch failed:", err));
  }
  
  function flattenBufferHorizontal(buffer) {
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

  function hideVisualizers() {
    amplitudeHeatmapContainer.classList.add('hidden');
    phaseHeatmapContainer.classList.add('hidden');
    gatesHeatmapContainer.classList.add('hidden');
    expChartContainer.classList.add('hidden');
    d3PlotContainer.classList.add('hidden');
  }

  function tempConfigUI() {
    amplitudeHeatmap.radius(1, 0);
    amplitudeHeatmap.max(amplitudeMaxSlider.value);
    phaseHeatmap.radius(1, 0);
    phaseHeatmap.max(phaseMaxSlider.value);
    gatesHeatmap.radius(1, 0);
    gatesHeatmap.max(1);

    // Crop the heatmaps to canvas
    amplitudeCanvas.height = SUBCARRIER_COUNT - 1;
    amplitudeCanvas.width = MAX_COLS - 1;
    phaseCanvas.height = SUBCARRIER_COUNT - 1;
    phaseCanvas.width = MAX_COLS - 1;
    gatesCanvas.height = RANGE_GATES - 1;
    gatesCanvas.width = DOPPLER_BINS - 1;
    
    // Prevent Experimental Line Chart from exceeding the layout size
    expCanvasCtx.canvas.width = 680;
    expCanvasCtx.canvas.height = 200;
    
    // // Disable visualizer buttons
    d3PlotBtn.disabled = true;
    targetRadarBtn.disabled = true;

    // Load the initial tab
    dashboardBtn.click();
    isMonitorActive = true;
  }

  amplitudeMaxSlider.addEventListener("input", (e) => {
    const newMax = parseFloat(e.target.value);
    amplitudeMaxValue.textContent = newMax;
    amplitudeHeatmap.max(newMax).draw();
  });

  phaseMaxSlider.addEventListener("input", (e) => {
    const newMax = parseFloat(e.target.value);
    phaseMaxValue.textContent = newMax;
    phaseHeatmap.max(newMax).draw();
  });

  gatesMaxSlider.addEventListener("input", (e) => {
    const newMax = parseFloat(e.target.value);
    gatesMaxValue.textContent = newMax;
    gatesHeatmap.max(newMax).draw();
  });

  function initializeExpChart() {
    expCanvasCtx.canvas.width = 680;
    expCanvasCtx.canvas.height = 200;
    expChart = new Chart(expCanvasCtx, {
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
                return index % EXP_TICK_INTERVAL === 0 ? this.getLabelForValue(val) : '';
              }
            }
          },
          y: {
            title: { display: true, text: 'Ampltitude' },
            suggestedMin: -80,
            suggestedMax: -20
          }
        },
        plugins: { legend: { display: false } }
      }
    });
  }

  expChartBtn.addEventListener('click', () => {
    if (isExpChartVisible) {
      expChartBtn.style.backgroundColor = btnDefaultColor;
      expChartContainer.classList.add('hidden');
      isExpChartVisible = false;

      expCanvasCtx.clearRect(0, 0, expCanvasCtx.canvas.width, expCanvasCtx.canvas.height);
      expChart.data.labels = [];
      expChart.data.datasets[0].data = [];
      tick = 0;
    } else {
      expChartBtn.style.backgroundColor = btnActiveColor;
      expChartContainer.classList.remove('hidden');
      if (expChart === undefined) initializeExpChart();
      expChart.update();
      isExpChartVisible = true;
    }
  });


  function populateSelect(select, options, allowedValues = null) {
    select.innerHTML = '';
    options.forEach(opt => {
      if (!allowedValues || allowedValues.includes(opt.value)) {
        const option = document.createElement('option');
        option.value = opt.value;
        option.textContent = opt.label;
        select.appendChild(option);
      }
    });
  }

  function updateOptionsForClass(classValue) {
    if (classValue === '0') { // Absence
      // Only the first option for each (index 0)
      populateSelect(targetSelection, OPTIONS.target, [OPTIONS.target[0].value]);
      populateSelect(stateSelection, OPTIONS.state, [OPTIONS.state[0].value]);
      populateSelect(activitySelection, OPTIONS.activity, [OPTIONS.activity[0].value]);
      populateSelect(angleSelection, OPTIONS.angle, [OPTIONS.angle[0].value]);
      populateSelect(distanceSelection, OPTIONS.distance, [OPTIONS.distance[0].value]);
    } else if (classValue === '1') { // Presence
      // All except the first option for each (index 1+)
      populateSelect(targetSelection, OPTIONS.target, OPTIONS.target.slice(1).map(opt => opt.value));
      populateSelect(stateSelection, OPTIONS.state, OPTIONS.state.slice(1).map(opt => opt.value));
      populateSelect(activitySelection, OPTIONS.activity, [OPTIONS.activity[1].value, OPTIONS.activity[2].value]);
      populateSelect(angleSelection, OPTIONS.angle, OPTIONS.angle.slice(1).map(opt => opt.value));
      populateSelect(distanceSelection, OPTIONS.distance, OPTIONS.distance.slice(1).map(opt => opt.value));
    }
  }
  
  // Update obstruction options based on obstructed selection
  function updateObstructionOptions(obstructedValue) {
    if (obstructedValue === '0') { // Not obstructed, only show "None"
      populateSelect(obstructionSelection, OPTIONS.obstruction, [OPTIONS.obstruction[0].value]);
    } else { // Obstructed, show all except "None"
      populateSelect(obstructionSelection, OPTIONS.obstruction, OPTIONS.obstruction.slice(1).map(opt => opt.value));
    }
  }

  function updateActivityOptions(stateValue) {
    if (stateValue === '0') { // No State
      populateSelect(activitySelection, OPTIONS.activity, [OPTIONS.activity[0].value]);
    } else if (stateValue === '1') { // Motionless
      populateSelect(activitySelection, OPTIONS.activity, [OPTIONS.activity[1].value, OPTIONS.activity[2].value]);
    } else if (stateValue === '2') { // Moving
      populateSelect(activitySelection, OPTIONS.activity, OPTIONS.activity.slice(1).map(opt => opt.value));
    }
  }

  classSelection.addEventListener('change', (e) => { updateOptionsForClass(e.target.value); });
  obstructedSelection.addEventListener('change', (e) => { updateObstructionOptions(e.target.value); });
  stateSelection.addEventListener('change', (e) => { updateActivityOptions(e.target.value); });


  /* Initial Loading */


  populateSelect(classSelection, OPTIONS.class);
  populateSelect(targetSelection, OPTIONS.target);
  populateSelect(stateSelection, OPTIONS.state);
  populateSelect(activitySelection, OPTIONS.activity);
  populateSelect(angleSelection, OPTIONS.angle);
  populateSelect(distanceSelection, OPTIONS.distance);
  populateSelect(obstructedSelection, OPTIONS.obstructed);
  populateSelect(obstructionSelection, OPTIONS.obstruction);
  populateSelect(spacingSelection, OPTIONS.spacing);

  updateOptionsForClass(classSelection.value);
  updateObstructionOptions(obstructedSelection.value);
  
  list_csv_files();
  checkSystemStatus();
  setInterval(checkSystemStatus, systemStatusInterval);
  tempConfigUI();
  hideVisualizers();
});
