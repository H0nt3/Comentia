const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    selectDirectory: () => ipcRenderer.invoke('select-directory'),
    extractComments: (url, directory) => ipcRenderer.invoke('extract-comments', url, directory),
    onExtractionProgress: (callback) => {
        ipcRenderer.on('extraction-progress', (event, data) => callback(data));
    }
});