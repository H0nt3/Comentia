#!/usr/bin/env python3
"""Aplicación de escritorio con PyQt5 para Comentia."""

import sys
import re
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QTextEdit, QProgressBar, QFileDialog, QMessageBox,
                             QGroupBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

# Importar núcleo común
# Calcular ruta absoluta a src/
root_dir = Path(__file__).parent.parent
src_path = str(root_dir / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)
from comentia.core import (extraer_id_noticia, descargar_comentarios,
                           exportar_comentarios, generar_estadisticas_txt)


class ExtractionThread(QThread):
    progress = pyqtSignal(str)
    progress_bar = pyqtSignal(int, int)
    finished = pyqtSignal(dict, int, list)
    error = pyqtSignal(str)

    def __init__(self, url: str, directorio: Path):
        super().__init__()
        self.url = url
        self.directorio = directorio

    def run(self):
        try:
            noticia_id = extraer_id_noticia(self.url)
            if not noticia_id:
                self.error.emit("No se pudo obtener el ID de la noticia")
                return

            self.progress.emit(f"✅ ID detectado: {noticia_id}")

            subdir = self.directorio / f"noticia_{noticia_id}"
            subdir.mkdir(parents=True, exist_ok=True)

            tiempo_inicio = time.time()
            comentarios, total, errores = descargar_comentarios(noticia_id)
            tiempo_ejecucion = time.time() - tiempo_inicio

            exportar_comentarios(comentarios, noticia_id, subdir, self.url)
            generar_estadisticas_txt(noticia_id, self.url, comentarios,
                                     total, tiempo_ejecucion, subdir, errores)

            self.progress.emit(f"✅ {len(comentarios)}/{total} comentarios guardados")
            self.finished.emit(comentarios, total, errores)

        except Exception as e:
            self.error.emit(str(e))


class ComentiaQtWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.directorio = None
        self.extraction_thread = None
        self._setup_ui()
        self._apply_style()

    def _setup_ui(self):
        self.setWindowTitle("📝 Comentia - Extractor de comentarios")
        self.setMinimumSize(750, 600)
        self.resize(800, 650)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Título
        title = QLabel("📝 Comentia")
        title.setFont(QFont("Arial", 28, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Extractor de comentarios de Marca.com")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #aaaaaa;")
        layout.addWidget(subtitle)
        layout.addSpacing(10)

        # Directorio
        dir_group = QGroupBox("📁 Directorio de destino")
        dir_layout = QHBoxLayout(dir_group)
        self.dir_label = QLabel("Ninguna carpeta seleccionada")
        self.dir_label.setStyleSheet("padding: 10px; background: #3c3c3c; border-radius: 5px;")
        dir_layout.addWidget(self.dir_label, 2)
        self.btn_dir = QPushButton("📂 Seleccionar")
        self.btn_dir.setFixedWidth(120)
        self.btn_dir.clicked.connect(self._seleccionar_directorio)
        dir_layout.addWidget(self.btn_dir)
        layout.addWidget(dir_group)

        # URL
        url_group = QGroupBox("🔗 URL de la noticia")
        url_layout = QVBoxLayout(url_group)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.marca.com/...")
        self.url_input.setMinimumHeight(40)
        url_layout.addWidget(self.url_input)
        layout.addWidget(url_group)

        # Botón extraer
        self.btn_extract = QPushButton("🚀 Extraer comentarios")
        self.btn_extract.setFixedHeight(50)
        self.btn_extract.setEnabled(False)
        self.btn_extract.clicked.connect(self._iniciar_extraccion)
        layout.addWidget(self.btn_extract)

        # Progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(25)
        layout.addWidget(self.progress_bar)

        # Log
        log_group = QGroupBox("📄 Progreso")
        log_layout = QVBoxLayout(log_group)
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(200)
        self.log_area.setStyleSheet("font-family: monospace; font-size: 11px;")
        log_layout.addWidget(self.log_area)
        layout.addWidget(log_group)

        # Estado
        self.status_label = QLabel("✅ Listo")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #4CAF50;")
        layout.addWidget(self.status_label)

    def _apply_style(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #2b2b2b; }
            QGroupBox { color: white; border: 2px solid #555; border-radius: 8px;
                        margin-top: 10px; padding-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QLabel { color: white; }
            QLineEdit { background: #3c3c3c; color: white; border: 2px solid #555;
                        border-radius: 5px; padding: 5px; }
            QTextEdit { background: #1e1e1e; color: #d4d4d4; border: 1px solid #555;
                        border-radius: 5px; }
            QPushButton { background-color: #4CAF50; color: white; border: none;
                          border-radius: 5px; font-weight: bold; }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #666; }
            QProgressBar { border: 2px solid #555; border-radius: 5px; text-align: center;
                           color: white; }
            QProgressBar::chunk { background-color: #4CAF50; border-radius: 3px; }
        """)

    def _seleccionar_directorio(self):
        directorio = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta")
        if directorio:
            self.directorio = Path(directorio)
            self.dir_label.setText(str(self.directorio))
            self.btn_extract.setEnabled(True)
            self._log(f"✅ Carpeta seleccionada: {directorio}")

    def _log(self, mensaje):
        self.log_area.append(mensaje)
        self.log_area.verticalScrollBar().setValue(
            self.log_area.verticalScrollBar().maximum()
        )

    def _iniciar_extraccion(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Introduce una URL")
            return

        self.btn_extract.setEnabled(False)
        self.btn_dir.setEnabled(False)
        self.url_input.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("⏳ Extrayendo comentarios...")
        self.status_label.setStyleSheet("color: #FF9800;")
        self.log_area.clear()

        self.extraction_thread = ExtractionThread(url, self.directorio)
        self.extraction_thread.progress.connect(self._log)
        self.extraction_thread.progress_bar.connect(self._actualizar_progreso)
        self.extraction_thread.finished.connect(self._extraccion_finalizada)
        self.extraction_thread.error.connect(self._extraccion_error)
        self.extraction_thread.start()

    def _actualizar_progreso(self, actual, total):
        if total > 0:
            pct = int((actual / total) * 100)
            self.progress_bar.setValue(pct)
            self.progress_bar.setFormat(f"{actual}/{total} ({pct}%)")

    def _extraccion_finalizada(self, comentarios, total, errores):
        obtenidos = len(comentarios)
        exito = obtenidos >= total * 0.95 if total > 0 else obtenidos > 0

        self.btn_extract.setEnabled(True)
        self.btn_dir.setEnabled(True)
        self.url_input.setEnabled(True)
        self.progress_bar.setVisible(False)

        if exito:
            self.status_label.setText(f"✅ ¡Éxito! {obtenidos}/{total} comentarios")
            self.status_label.setStyleSheet("color: #4CAF50;")
            QMessageBox.information(self, "Completado",
                f"✅ Extracción finalizada\n\n{obtenidos}/{total} comentarios\n📁 {self.directorio}")
        else:
            self.status_label.setText(f"⚠️ {obtenidos}/{total} comentarios")
            self.status_label.setStyleSheet("color: #f44336;")
            QMessageBox.warning(self, "Errores",
                f"⚠️ Extracción con errores\n\n{obtenidos}/{total} comentarios")

    def _extraccion_error(self, error):
        self.btn_extract.setEnabled(True)
        self.btn_dir.setEnabled(True)
        self.url_input.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("❌ Error")
        self.status_label.setStyleSheet("color: #f44336;")
        QMessageBox.critical(self, "Error", f"Error: {error}")


def main():
    app = QApplication(sys.argv)
    window = ComentiaQtWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()