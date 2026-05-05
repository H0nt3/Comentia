#!/usr/bin/env python3
"""
Comentia - Extractor de comentarios de Marca.com
Versión PyQt5 - App de escritorio con tema oscuro
"""

import sys
import os
import re
import time
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
from collections import Counter

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QProgressBar,
    QFileDialog, QMessageBox, QGroupBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

# ========================
# CONFIGURACIÓN
# ========================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
}

DELAY_ENTRE_PAGINAS = 0.3
MAX_REINTENTOS = 3
TIMEOUT = 15


# ========================
# HILO DE EXTRACCIÓN
# ========================
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
            # Extraer ID
            noticia_id = self._extraer_id()
            if not noticia_id:
                self.error.emit("No se pudo obtener el ID de la noticia")
                return
            
            self.progress.emit(f"✅ ID detectado: {noticia_id}")
            
            # Crear subcarpeta
            subdir = self.directorio / f"noticia_{noticia_id}"
            subdir.mkdir(parents=True, exist_ok=True)
            
            # Descargar comentarios
            comentarios, total, errores = self._descargar_comentarios(noticia_id)
            
            # Exportar
            self._exportar(comentarios, noticia_id, subdir, self.url)
            self._generar_estadisticas(comentarios, noticia_id, self.url, total, subdir, errores)
            
            self.finished.emit(comentarios, total, errores)
            
        except Exception as e:
            self.error.emit(str(e))
    
    def _extraer_id(self) -> Optional[str]:
        entrada = self.url
        if entrada.isdigit():
            return entrada
        
        patrones_url = [
            r'/noticia[/-](\d+)',
            r'/comentarios[/-](\d+)',
            r'noticia=(\d+)',
            r'/(\d{6,})/'
        ]
        
        for patron in patrones_url:
            match = re.search(patron, entrada)
            if match:
                return match.group(1)
        
        try:
            response = requests.get(entrada, headers=HEADERS, timeout=TIMEOUT)
            html = response.text
            
            patrones_html = [
                r'"commentId"\s*:\s*"(\d+)"',
                r'commentId["\']?\s*[:=]\s*["\']?(\d+)',
                r'data-noticia=["\'](\d+)'
            ]
            
            for patron in patrones_html:
                match = re.search(patron, html)
                if match:
                    return match.group(1)
            
            numeros = re.findall(r'\b(\d{6,})\b', html)
            if numeros:
                return Counter(numeros).most_common(1)[0][0]
        except:
            pass
        
        return None
    
    def _peticion_segura(self, noticia_id: str, pagina: Optional[int] = None) -> Optional[dict]:
        url = "https://www.marca.com/servicios/noticias/comentarios/comunidad/listar.html"
        params = {"noticia": noticia_id, "version": "v2"}
        if pagina:
            params["pagina"] = pagina
        
        for intento in range(MAX_REINTENTOS):
            try:
                response = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
                if response.status_code == 200:
                    return response.json()
            except:
                time.sleep(DELAY_ENTRE_PAGINAS)
        
        return None
    
    def _descargar_comentarios(self, noticia_id: str):
        comentarios = {}
        ultimo_order = None
        total_esperado = None
        page_num = 1
        errores = []
        
        while True:
            data = self._peticion_segura(noticia_id, ultimo_order)
            
            if not data:
                errores.append(f"Fallo al descargar página {page_num}")
                break
            
            if total_esperado is None:
                total_esperado = data.get("total", 0)
                self.progress_bar.emit(0, total_esperado)
            
            items = data.get("items", [])
            if not items:
                break
            
            for item in items:
                order = item.get("order")
                if order and order not in comentarios:
                    comentarios[order] = {
                        "id": item.get("id"),
                        "order": order,
                        "user": item.get("user"),
                        "body": item.get("body"),
                        "date": item.get("date"),
                        "time": item.get("time"),
                        "references": item.get("references", [])
                    }
            
            self.progress.emit(f"📄 Página {page_num}: +{len(items)} comentarios")
            self.progress_bar.emit(len(comentarios), total_esperado)
            
            if data.get("lastPage"):
                break
            
            if items:
                ultimo_order = items[-1]["order"]
            
            page_num += 1
            time.sleep(DELAY_ENTRE_PAGINAS)
        
        return comentarios, total_esperado or 0, errores
    
    def _exportar(self, comentarios_dict: Dict[int, dict], noticia_id: str, 
                  directorio: Path, url_noticia: str = ""):
        comentarios_lista = sorted(comentarios_dict.values(), key=lambda x: x["order"])
        
        datos_exportar = {
            "metadata": {
                "noticia_id": noticia_id,
                "url_noticia": url_noticia,
                "total_comentarios": len(comentarios_lista),
                "fecha_exportacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "fuente": "Marca.com"
            },
            "comentarios": comentarios_lista
        }
        
        archivo_completo = directorio / f"comentarios_{noticia_id}_completo.json"
        with open(archivo_completo, "w", encoding="utf-8") as f:
            json.dump(datos_exportar, f, ensure_ascii=False, indent=2)
        
        archivo_simplificado = directorio / f"comentarios_{noticia_id}_simplificado.json"
        comentarios_simples = [
            {"order": c["order"], "usuario": c["user"], 
             "comentario": c["body"], "fecha": f"{c['date']} {c['time']}"}
            for c in comentarios_lista
        ]
        with open(archivo_simplificado, "w", encoding="utf-8") as f:
            json.dump(comentarios_simples, f, ensure_ascii=False, indent=2)
    
    def _generar_estadisticas(self, comentarios_dict: Dict[int, dict], noticia_id: str,
                              url_noticia: str, total_esperado: int, directorio: Path,
                              errores: List[str]):
        comentarios_reales = list(comentarios_dict.values())
        total_obtenidos = len(comentarios_reales)
        
        usuarios = {}
        fechas = {}
        comentarios_con_referencias = 0
        palabras_comunes = {}
        
        for c in comentarios_reales:
            user = c.get("user", "anónimo")
            usuarios[user] = usuarios.get(user, 0) + 1
            fecha = c.get("date", "desconocida")
            fechas[fecha] = fechas.get(fecha, 0) + 1
            if c.get("references"):
                comentarios_con_referencias += 1
            
            palabras = re.findall(r'\b\w{4,}\b', c.get("body", "").lower())
            for palabra in palabras:
                if palabra not in ['como', 'cuando', 'donde', 'este', 'esta', 'esto', 'para', 'porque']:
                    palabras_comunes[palabra] = palabras_comunes.get(palabra, 0) + 1
        
        top_usuarios = sorted(usuarios.items(), key=lambda x: x[1], reverse=True)[:10]
        top_palabras = sorted(palabras_comunes.items(), key=lambda x: x[1], reverse=True)[:15]
        longitudes = [len(c.get("body", "")) for c in comentarios_reales]
        longitud_promedio = sum(longitudes) / len(longitudes) if longitudes else 0
        porcentaje_exito = (total_obtenidos / total_esperado * 100) if total_esperado > 0 else 0
        
        # Calcular huecos
        if comentarios_reales:
            orders = set(comentarios_dict.keys())
            max_order = max(orders)
            min_order = min(orders)
            huecos = sorted(set(range(min_order, max_order + 1)) - orders)
        else:
            huecos = []
        
        archivo = directorio / f"comentarios_{noticia_id}_estadisticas.txt"
        
        with open(archivo, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write("📊 COMENTIA - ESTADÍSTICAS DE COMENTARIOS\n")
            f.write("=" * 80 + "\n\n")
            
            f.write("📰 INFORMACIÓN BÁSICA\n")
            f.write("-" * 40 + "\n")
            f.write(f"ID de la noticia: {noticia_id}\n")
            f.write(f"URL: {url_noticia if url_noticia else 'No disponible'}\n")
            f.write(f"Fecha de extracción: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("📊 RESUMEN\n")
            f.write("-" * 40 + "\n")
            f.write(f"Esperados: {total_esperado}\n")
            f.write(f"Obtenidos: {total_obtenidos}\n")
            f.write(f"Éxito: {porcentaje_exito:.2f}%\n")
            f.write(f"Huecos: {len(huecos)}\n\n")
            
            f.write("👥 TOP 10 USUARIOS\n")
            f.write("-" * 40 + "\n")
            for i, (user, count) in enumerate(top_usuarios, 1):
                f.write(f"{i:2}. {user:<20} - {count:3}\n")
            f.write("\n")
            
            f.write("🔤 PALABRAS MÁS UTILIZADAS\n")
            f.write("-" * 40 + "\n")
            for i, (palabra, count) in enumerate(top_palabras[:10], 1):
                f.write(f"{i:2}. {palabra:<15} - {count:3}\n")
            f.write("\n")
            
            f.write("📁 ARCHIVOS GENERADOS\n")
            f.write("-" * 40 + "\n")
            f.write(f"• comentarios_{noticia_id}_completo.json\n")
            f.write(f"• comentarios_{noticia_id}_simplificado.json\n")
            f.write(f"• comentarios_{noticia_id}_estadisticas.txt\n")
            
            if errores:
                f.write("\n⚠️ ERRORES DETECTADOS\n")
                f.write("-" * 40 + "\n")
                for error in errores[:5]:
                    f.write(f"• {error}\n")
        
        self.progress.emit(f"📊 Estadísticas guardadas en: {archivo.name}")


# ========================
# VENTANA PRINCIPAL (PyQt5 con tema oscuro)
# ========================
class ComentiaWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.directorio = None
        self.extraction_thread = None
        self.init_ui()
        self.apply_dark_theme()
    
    def init_ui(self):
        self.setWindowTitle("📝 Comentia - Extractor de comentarios de Marca.com")
        self.setMinimumSize(750, 650)
        self.resize(800, 700)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Título
        title_layout = QHBoxLayout()
        title = QLabel("📝 Comentia")
        title_font = QFont("Arial", 28, QFont.Bold)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(title)
        main_layout.addLayout(title_layout)
        
        # Subtítulo
        subtitle = QLabel("Extractor de comentarios de Marca.com")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #aaaaaa; font-size: 12px;")
        main_layout.addWidget(subtitle)
        
        main_layout.addSpacing(10)
        
        # Grupo: Directorio
        dir_group = QGroupBox("📁 Directorio de destino")
        dir_layout = QHBoxLayout(dir_group)
        
        self.dir_label = QLabel("Ninguna carpeta seleccionada")
        self.dir_label.setStyleSheet("padding: 10px; background: #3c3c3c; border-radius: 5px; color: #ffffff;")
        self.dir_label.setWordWrap(True)
        dir_layout.addWidget(self.dir_label, 2)
        
        self.btn_select_dir = QPushButton("📂 Seleccionar")
        self.btn_select_dir.setFixedWidth(120)
        self.btn_select_dir.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.btn_select_dir.clicked.connect(self.seleccionar_directorio)
        dir_layout.addWidget(self.btn_select_dir)
        
        main_layout.addWidget(dir_group)
        
        # Grupo: URL
        url_group = QGroupBox("🔗 URL de la noticia")
        url_layout = QVBoxLayout(url_group)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.marca.com/... o ID de la noticia")
        self.url_input.setMinimumHeight(40)
        self.url_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #555;
                border-radius: 5px;
                padding: 8px;
                font-size: 13px;
                background: #3c3c3c;
                color: #ffffff;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
        """)
        url_layout.addWidget(self.url_input)
        
        main_layout.addWidget(url_group)
        
        # Botón extraer
        self.btn_extract = QPushButton("🚀 Extraer comentarios")
        self.btn_extract.setFixedHeight(50)
        self.btn_extract.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #666;
            }
        """)
        self.btn_extract.clicked.connect(self.iniciar_extraccion)
        main_layout.addWidget(self.btn_extract)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(25)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #555;
                border-radius: 5px;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        main_layout.addWidget(self.progress_bar)
        
        # Área de log
        log_group = QGroupBox("📄 Progreso")
        log_layout = QVBoxLayout(log_group)
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(200)
        self.log_area.setStyleSheet("""
            QTextEdit {
                font-family: monospace;
                font-size: 11px;
                background: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #555;
                border-radius: 5px;
            }
        """)
        log_layout.addWidget(self.log_area)
        
        main_layout.addWidget(log_group)
        
        # Estado
        self.status_label = QLabel("✅ Listo")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #4CAF50; padding: 5px; font-weight: bold;")
        main_layout.addWidget(self.status_label)
    
    def apply_dark_theme(self):
        """Aplica tema oscuro a toda la aplicación"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
            }
            QGroupBox {
                color: #ffffff;
                font-weight: bold;
                border: 2px solid #555;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #2b2b2b;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
        """)
    
    def seleccionar_directorio(self):
        directorio = QFileDialog.getExistingDirectory(
            self, "Seleccionar carpeta de destino", str(Path.home())
        )
        if directorio:
            self.directorio = Path(directorio)
            self.dir_label.setText(str(self.directorio))
            self.status_label.setText("✅ Carpeta seleccionada")
    
    def iniciar_extraccion(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Por favor, introduce la URL de la noticia")
            return
        
        if not self.directorio:
            QMessageBox.warning(self, "Error", "Por favor, selecciona una carpeta de destino")
            return
        
        # Deshabilitar botones
        self.btn_extract.setEnabled(False)
        self.btn_select_dir.setEnabled(False)
        self.url_input.setEnabled(False)
        
        # Limpiar log
        self.log_area.clear()
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("⏳ Extrayendo comentarios...")
        self.status_label.setStyleSheet("color: #FF9800; padding: 5px; font-weight: bold;")
        
        # Iniciar hilo
        self.extraction_thread = ExtractionThread(url, self.directorio)
        self.extraction_thread.progress.connect(self.agregar_log)
        self.extraction_thread.progress_bar.connect(self.actualizar_progreso)
        self.extraction_thread.finished.connect(self.extraccion_finalizada)
        self.extraction_thread.error.connect(self.extraccion_error)
        self.extraction_thread.start()
    
    def agregar_log(self, mensaje: str):
        self.log_area.append(mensaje)
        scroll = self.log_area.verticalScrollBar()
        scroll.setValue(scroll.maximum())
    
    def actualizar_progreso(self, actual: int, total: int):
        if total > 0:
            porcentaje = int((actual / total) * 100)
            self.progress_bar.setValue(porcentaje)
            self.progress_bar.setFormat(f"{actual}/{total} comentarios ({porcentaje}%)")
    
    def extraccion_finalizada(self, comentarios: dict, total: int, errores: list):
        obtenidos = len(comentarios)
        exito = obtenidos >= total * 0.95 if total > 0 else obtenidos > 0
        
        self.btn_extract.setEnabled(True)
        self.btn_select_dir.setEnabled(True)
        self.url_input.setEnabled(True)
        
        if exito:
            self.status_label.setText(f"✅ ¡Éxito! {obtenidos}/{total} comentarios guardados")
            self.status_label.setStyleSheet("color: #4CAF50; padding: 5px; font-weight: bold;")
            QMessageBox.information(
                self, "Operación completada",
                f"✅ Extracción finalizada con éxito\n\n"
                f"📊 Comentarios obtenidos: {obtenidos}/{total}\n"
                f"📁 Ubicación: {self.directorio}"
            )
        else:
            self.status_label.setText(f"⚠️ {obtenidos}/{total} comentarios - Con errores")
            self.status_label.setStyleSheet("color: #f44336; padding: 5px; font-weight: bold;")
            msg = f"⚠️ Operación con errores\n\n{obtenidos}/{total} comentarios obtenidos"
            if errores:
                msg += f"\n\nErrores:\n" + "\n".join(errores[:5])
            QMessageBox.warning(self, "Operación con errores", msg)
        
        self.progress_bar.setVisible(False)
        self.agregar_log(f"\n✅ Proceso completado: {obtenidos}/{total} comentarios")
    
    def extraccion_error(self, error: str):
        self.btn_extract.setEnabled(True)
        self.btn_select_dir.setEnabled(True)
        self.url_input.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("❌ Error en la extracción")
        self.status_label.setStyleSheet("color: #f44336; padding: 5px; font-weight: bold;")
        QMessageBox.critical(self, "Error", f"Error durante la extracción:\n\n{error}")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Comentia")
    
    window = ComentiaWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()