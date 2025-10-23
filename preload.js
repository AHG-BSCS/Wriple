const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // Add functions here if needed, e.g. to send/receive messages to the main process
  // For now we expose nothing sensitive; you can expand securely later.
});
