// preload.js
const { contextBridge } = require('electron');
const { spawn } = require('child_process');

contextBridge.exposeInMainWorld('api', {
  runPython: (url) => {
    const isWin = process.platform === 'win32';
    const cmd = isWin ? 'backend/comentia.exe' : './backend/comentia';

    const proc = spawn(cmd, [url]);

    proc.stdout.on('data', (data) => {
      const lines = data.toString().split('\n').filter(Boolean);

      lines.forEach(line => {
        try {
          const msg = JSON.parse(line);
          window.dispatchEvent(new CustomEvent('py-event', { detail: msg }));
        } catch (e) {
          console.log("Salida no JSON:", line);
        }
      });
    });

    proc.stderr.on('data', (err) => {
      window.dispatchEvent(new CustomEvent('py-event', {
        detail: { event: 'error', message: err.toString() }
      }));
    });
  }
});