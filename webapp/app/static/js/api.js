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

async function getJson(url) {
  const response = await fetch(url, {
    method: 'GET',
    headers: {'Content-Type':'application/json'}
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
  getSystemStatus: () => getJson('/get_system_status'),
  getMonitorStatus: () => getJson('/get_monitor_status'),
  getPresenceStatus: () => getJson('/get_presence_status'),
  
  startMonitoring: () => postJson(`/start_monitoring`),
  startRecording: (params) => postJson(`/start_recording`, params),
  stopCapturing: () => postJson('/stop_capturing'),
  
  getchAmplitudeData: () => getJson('/get_amplitude_data'),
  getchPhaseData: () => getJson('/get_phase_data'),
  getRadarData: () => getJson('/get_radar_data'),
  getRdmData: () => getJson('/get_rdm_data'),
  get3dPlotData: () => getJson('/get_3d_plot_data'),
  
  getCsvFiles: () => getJson('/get_csv_files'),
  readCsvFileMeta: (filename) => postJson('/read_csv_file_meta', filename),
};
