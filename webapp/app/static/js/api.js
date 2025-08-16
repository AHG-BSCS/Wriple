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
  checkSystemStatus: () => postJson('/check_system_status'),
  listCsvFiles: () => postJson('/list_csv_files'),
  setRecordParameter: (params) => postJson('/set_record_parameter', params),
  startRecording: (mode) => postJson(`/start_recording`, mode),
  stopRecording: () => postJson('/stop_recording'),
  fetchAmplitudeData: () => postJson('/fetch_amplitude_data'),
  fetchPhaseData: () => postJson('/fetch_phase_data'),
  getRadarData: () => postJson('/get_radar_data'),
  getMMWaveHeatmap: () => postJson('/get_mmwave_heatmap_data'),
  visualize3d: () => postJson('/visualize_3d_plot'),
  loadCsvFile: (filename) => postJson('/visualize_csv_file', filename)
};
