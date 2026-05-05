const { contextBridge } = require('electron');
const { spawn } = require('child_process');

contextBridge.exposeInMainWorld('api', {
  runPython: (url) => {
    const process = spawn('python', ['backend/comentia.py', url]);

    process.stdout.on('data', (data) => {
      const log = document.getElementById('log');
      log.textContent += data.toString();
    });
  }
});