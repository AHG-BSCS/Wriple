async function postJson(url, body = {}) {
  const response = await fetch(url, {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(body)
  });
  if (!response.ok) {
    const text = await response.text();
    const message = JSON.parse(text).message;
    alert(message);
    throw new Error(`API: ${url} STATUS: ${response.status} TEXT: ${text}`);
  }
  return response.json();
}

export const API = {
  fetchSystemIconStatus: () => postJson('/fetch_system_icon_status'),
  fetchMonitorStatus: () => postJson('/fetch_monitor_status'),
  
  startMonitoring: () => postJson(`/capture_data/monitor`),
  startRecording: (params) => postJson(`/capture_data/record`, params),
  stopCapturing: () => postJson('/capture_data/stop'),
  
  fetchAmplitudeData: () => postJson('/fetch_amplitude_data'),
  fetchPhaseData: () => postJson('/fetch_phase_data'),
  getRadarData: () => postJson('/get_radar_data'),
  getMMWaveHeatmap: () => postJson('/get_mmwave_heatmap_data'),
  visualize3d: () => postJson('/visualize_3d_plot'),
  
  listCsvFiles: () => postJson('/list_csv_files'),
  loadCsvFile: (filename) => postJson('/visualize_csv_file', filename),
};
