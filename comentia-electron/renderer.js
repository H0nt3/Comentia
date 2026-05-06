let selectedDirectory = '';

document.getElementById('selectDirBtn').addEventListener('click', async () => {
    const directory = await window.electronAPI.selectDirectory();
    if (directory) {
        selectedDirectory = directory;
        document.getElementById('directoryDisplay').textContent = `📁 ${directory}`;
        document.getElementById('extractBtn').disabled = false;
    }
});

document.getElementById('extractBtn').addEventListener('click', async () => {
    const url = document.getElementById('url').value.trim();

    if (!url) {
        alert('Introduce la URL de la noticia');
        return;
    }

    if (!selectedDirectory) {
        alert('Selecciona una carpeta de destino');
        return;
    }

    document.getElementById('progressSection').style.display = 'block';
    document.getElementById('resultSection').style.display = 'none';
    document.getElementById('progressLog').innerHTML = '';
    document.getElementById('extractBtn').disabled = true;
    document.querySelector('.progress-bar').style.width = '0%';

    window.electronAPI.onExtractionProgress((data) => {
        const logDiv = document.getElementById('progressLog');
        logDiv.innerHTML += data + '\n';
        logDiv.scrollTop = logDiv.scrollHeight;
    });

    try {
        const result = await window.electronAPI.extractComments(url, selectedDirectory);
        document.getElementById('resultSection').style.display = 'block';
        document.getElementById('resultMessage').innerHTML =
            `<p>✅ Extracción completada con éxito</p>
             <p>📁 Archivos guardados en: ${selectedDirectory}</p>`;
        document.querySelector('.progress-bar').style.width = '100%';
    } catch (error) {
        alert('Error: ' + error.error);
    } finally {
        document.getElementById('extractBtn').disabled = false;
    }
});