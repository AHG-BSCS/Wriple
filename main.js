const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let pyProc = null;
let mainWindow = null;

function getPythonExecutable() {
  if (process.platform === 'win32') return 'python';
  return 'python3';
}

function startPythonServer() {
  return new Promise((resolve, reject) => {
    const python = getPythonExecutable();
    const scriptPath = path.join(__dirname, 'run.py');

    pyProc = spawn(python, [scriptPath], { cwd: __dirname });

    let stdoutBuf = '';
    const timeout = setTimeout(() => {
      reject(new Error('Python did not print PORT in time'));
    }, 15000);

    pyProc.stdout.on('data', (data) => {
      const s = data.toString();
      stdoutBuf += s;
      console.log('[PY]', s);
      const m = stdoutBuf.match(/PORT:(\d+)/);
      if (m) {
        clearTimeout(timeout);
        const port = m[1];
        resolve(`http://127.0.0.1:${port}`);
      }
    });

    pyProc.stderr.on('data', (data) => {
      console.error('[PY-ERR]', data.toString());
    });

    pyProc.on('close', (code) => {
      console.log(`Python exited with code ${code}`);
      // If Python dies and window exists, quit app
      if (mainWindow) mainWindow.close();
    });
  });
}

function createWindow(url) {
  mainWindow = new BrowserWindow({
    width: 1366,
    height: 768,
    icon: path.join(__dirname, 'app', 'static', 'images', 'icon.png'),
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
    }
  });

  // Load the Web UI served by Flask
  mainWindow.loadURL(url);

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(async () => {
  try {
    const url = await startPythonServer();
    createWindow(url);
  } catch (err) {
    console.error('Failed to start Python server:', err);
    app.quit();
  }
});

// Quit when all windows closed (except macOS standard behavior)
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

// Ensure that we kill python on exit
app.on('will-quit', () => {
  if (pyProc) pyProc.kill();
});
