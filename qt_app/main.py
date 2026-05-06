#!/usr/bin/env python3
"""
Comentia - Extractor de comentarios de Marca.com
Versión PyQt5 - Mejorada con extracción por lotes y progreso en tiempo real
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
    QFileDialog, QMessageBox, QGroupBox, QTabWidget, QFrame,
    QCheckBox, QCompleter, QDialog, QDialogButtonBox, QTextBrowser,
    QListWidget, QListWidgetItem, QSplitter, QSpinBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSettings, QTimer
from PyQt5.QtGui import QFont, QDragEnterEvent, QDropEvent

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
# CONFIGURACIÓN PERSISTENTE
# ========================
class Configuracion:
    """Gestiona la configuración guardada del usuario."""
    
    CONFIG_FILE = Path.home() / ".comentia_config.json"
    
    @classmethod
    def guardar_ultimo_directorio(cls, directorio: str):
        config = cls.cargar_configuracion()
        config["ultimo_directorio"] = directorio
        cls._guardar_configuracion(config)
    
    @classmethod
    def obtener_ultimo_directorio(cls) -> str:
        config = cls.cargar_configuracion()
        return config.get("ultimo_directorio", "")
    
    @classmethod
    def guardar_ultimas_urls(cls, url: str):
        config = cls.cargar_configuracion()
        ultimas = config.get("ultimas_urls", [])
        if url in ultimas:
            ultimas.remove(url)
        ultimas.insert(0, url)
        config["ultimas_urls"] = ultimas[:5]
        cls._guardar_configuracion(config)
    
    @classmethod
    def obtener_ultimas_urls(cls) -> list:
        config = cls.cargar_configuracion()
        return config.get("ultimas_urls", [])
    
    @classmethod
    def guardar_archivo_lotes(cls, archivo: str):
        config = cls.cargar_configuracion()
        config["ultimo_archivo_lotes"] = archivo
        cls._guardar_configuracion(config)
    
    @classmethod
    def obtener_archivo_lotes(cls) -> str:
        config = cls.cargar_configuracion()
        return config.get("ultimo_archivo_lotes", "")
    
    @classmethod
    def cargar_configuracion(cls) -> dict:
        if cls.CONFIG_FILE.exists():
            try:
                with open(cls.CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    @classmethod
    def _guardar_configuracion(cls, config: dict):
        try:
            with open(cls.CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except:
            pass


# ========================
# DIÁLOGO DE VISTA PREVIA
# ========================
class VistaPreviaDialog(QDialog):
    def __init__(self, comentarios, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Vista previa de comentarios")
        self.setModal(False)
        self.resize(650, 450)
        
        layout = QVBoxLayout(self)
        
        titulo = QLabel(f"📝 Primeros {min(20, len(comentarios))} comentarios")
        titulo.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(titulo)
        
        self.text_area = QTextBrowser()
        self.text_area.setStyleSheet("""
            QTextBrowser {
                background: #1e1e1e;
                color: #d4d4d4;
                font-family: monospace;
                font-size: 11px;
                border: 1px solid #555;
                border-radius: 5px;
            }
        """)
        
        texto = ""
        for i, c in enumerate(comentarios[:20], 1):
            texto += f"\n{'='*70}\n"
            texto += f"[{i}] 👤 {c.get('user', 'anónimo')}\n"
            texto += f"📅 {c.get('date', '?')} {c.get('time', '?')}\n"
            texto += f"💬 {c.get('body', '')[:300]}"
            if len(c.get('body', '')) > 300:
                texto += "..."
            texto += "\n"
        
        self.text_area.setText(texto)
        layout.addWidget(self.text_area)
        
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.accept)
        layout.addWidget(btn_cerrar)
        
        self.setStyleSheet("""
            QDialog { background-color: #2b2b2b; }
            QLabel { color: white; }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)


# ========================
# HILO DE EXTRACCIÓN (CON LOGS EN TIEMPO REAL)
# ========================
class ExtractionThread(QThread):
    log_signal = pyqtSignal(str)           # Para logs en tiempo real
    progress_signal = pyqtSignal(int, int) # Para la barra de progreso
    finished_signal = pyqtSignal(dict, int, list, str)  # comentarios, total, errores, noticia_id
    error_signal = pyqtSignal(str)
    
    def __init__(self, url: str, directorio: Path):
        super().__init__()
        self.url = url
        self.directorio = directorio
    
    def log(self, mensaje: str):
        """Emite un mensaje de log."""
        self.log_signal.emit(mensaje)
    
    def run(self):
        try:
            self.log("🔍 Iniciando extracción...")
            
            # Extraer ID
            noticia_id = self._extraer_id()
            if not noticia_id:
                self.error_signal.emit("No se pudo obtener el ID de la noticia")
                return
            
            self.log(f"✅ ID detectado: {noticia_id}")
            
            # Crear subcarpeta
            subdir = self.directorio / f"noticia_{noticia_id}"
            subdir.mkdir(parents=True, exist_ok=True)
            self.log(f"📁 Carpeta de destino: {subdir}")
            
            # Descargar comentarios
            comentarios, total, errores = self._descargar_comentarios(noticia_id)
            
            # Exportar
            self.log("💾 Guardando archivos...")
            self._exportar(comentarios, noticia_id, subdir, self.url)
            self._generar_estadisticas(comentarios, noticia_id, self.url, total, subdir, errores)
            
            self.log(f"✅ Proceso completado: {len(comentarios)}/{total} comentarios")
            self.finished_signal.emit(comentarios, total, errores, noticia_id)
            
        except Exception as e:
            self.error_signal.emit(str(e))
    
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
            self.log(f"📄 Descargando página {page_num}...")
            data = self._peticion_segura(noticia_id, ultimo_order)
            
            if not data:
                errores.append(f"Fallo al descargar página {page_num}")
                break
            
            if total_esperado is None:
                total_esperado = data.get("total", 0)
                self.log(f"📊 Total de comentarios esperados: {total_esperado}")
                self.progress_signal.emit(0, total_esperado)
            
            items = data.get("items", [])
            if not items:
                self.log(f"⚠️ No hay comentarios en página {page_num}")
                break
            
            nuevos = 0
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
                    nuevos += 1
            
            self.log(f"  ✅ Página {page_num}: +{nuevos} comentarios (Total: {len(comentarios)}/{total_esperado})")
            self.progress_signal.emit(len(comentarios), total_esperado)
            
            if data.get("lastPage"):
                self.log("🏁 Última página alcanzada")
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
        self.log(f"💾 Guardado: {archivo_completo.name}")
        
        archivo_simplificado = directorio / f"comentarios_{noticia_id}_simplificado.json"
        comentarios_simples = [
            {"order": c["order"], "usuario": c["user"], 
             "comentario": c["body"], "fecha": f"{c['date']} {c['time']}"}
            for c in comentarios_lista
        ]
        with open(archivo_simplificado, "w", encoding="utf-8") as f:
            json.dump(comentarios_simples, f, ensure_ascii=False, indent=2)
        self.log(f"💾 Guardado: {archivo_simplificado.name}")
    
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
        
        self.log(f"📊 Estadísticas guardadas en: {archivo.name}")


# ========================
# HILO DE EXTRACCIÓN POR LOTES
# ========================
class BatchExtractionThread(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, int)
    item_completed = pyqtSignal(int, int, str)  # índice, total, url
    finished_signal = pyqtSignal(list)  # lista de resultados
    error_signal = pyqtSignal(str)
    
    def __init__(self, urls: List[str], directorio: Path):
        super().__init__()
        self.urls = urls
        self.directorio = directorio
        self._is_cancelled = False
    
    def cancel(self):
        self._is_cancelled = True
    
    def log(self, mensaje: str):
        self.log_signal.emit(mensaje)
    
    def run(self):
        resultados = []
        total = len(self.urls)
        
        for i, url in enumerate(self.urls, 1):
            if self._is_cancelled:
                self.log("⚠️ Extracción por lotes cancelada")
                break
            
            self.log(f"\n{'='*60}")
            self.log(f"📌 Procesando {i}/{total}: {url[:80]}...")
            
            try:
                # Extraer ID
                noticia_id = self._extraer_id(url)
                if not noticia_id:
                    self.log(f"❌ No se pudo obtener ID para: {url}")
                    resultados.append({"url": url, "exito": False, "error": "ID no encontrado"})
                    self.item_completed.emit(i, total, "❌ Fallo")
                    continue
                
                self.log(f"✅ ID detectado: {noticia_id}")
                
                subdir = self.directorio / f"noticia_{noticia_id}"
                subdir.mkdir(parents=True, exist_ok=True)
                
                comentarios, total_esp, errores = self._descargar_comentarios(noticia_id, url)
                
                self._exportar(comentarios, noticia_id, subdir, url)
                self._generar_estadisticas(comentarios, noticia_id, url, total_esp, subdir, errores)
                
                self.log(f"✅ Completado: {len(comentarios)}/{total_esp} comentarios")
                resultados.append({"url": url, "exito": True, "comentarios": len(comentarios), "id": noticia_id})
                self.item_completed.emit(i, total, f"✅ {len(comentarios)}/{total_esp}")
                
            except Exception as e:
                self.log(f"❌ Error: {e}")
                resultados.append({"url": url, "exito": False, "error": str(e)})
                self.item_completed.emit(i, total, "❌ Error")
            
            self.progress_signal.emit(i, total)
        
        self.finished_signal.emit(resultados)
    
    def _extraer_id(self, url: str) -> Optional[str]:
        if url.isdigit():
            return url
        
        patrones_url = [
            r'/noticia[/-](\d+)',
            r'/comentarios[/-](\d+)',
            r'noticia=(\d+)',
            r'/(\d{6,})/'
        ]
        
        for patron in patrones_url:
            match = re.search(patron, url)
            if match:
                return match.group(1)
        
        try:
            response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
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
        url_api = "https://www.marca.com/servicios/noticias/comentarios/comunidad/listar.html"
        params = {"noticia": noticia_id, "version": "v2"}
        if pagina:
            params["pagina"] = pagina
        
        for intento in range(MAX_REINTENTOS):
            try:
                response = requests.get(url_api, params=params, headers=HEADERS, timeout=TIMEOUT)
                if response.status_code == 200:
                    return response.json()
            except:
                time.sleep(DELAY_ENTRE_PAGINAS)
        
        return None
    
    def _descargar_comentarios(self, noticia_id: str, url: str):
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


# ========================
# VENTANA PRINCIPAL (CON PESTAÑAS: SIMPLE + LOTES)
# ========================
class ComentiaWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.directorio = None
        self.extraction_thread = None
        self.batch_thread = None
        self.config = Configuracion()
        self.init_ui()
        self.setup_drag_drop()
        self.cargar_configuracion_guardada()
    
    def setup_drag_drop(self):
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.status_label.setText("🎯 Suelta la URL aquí")
            self.status_label.setStyleSheet("color: #FF9800; padding: 5px; font-weight: bold;")
    
    def dragLeaveEvent(self, event):
        self.status_label.setText("✅ Listo")
        self.status_label.setStyleSheet("color: #4CAF50; padding: 5px; font-weight: bold;")
    
    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            url = urls[0].toString()
            # Verificar qué pestaña está activa
            if self.tab_widget.currentIndex() == 0:
                self.url_input.setText(url)
            else:
                self.batch_url_input.setText(url)
            self.status_label.setText("✅ URL cargada desde arrastre")
            self.status_label.setStyleSheet("color: #4CAF50; padding: 5px; font-weight: bold;")
    
    def cargar_configuracion_guardada(self):
        # Cargar último directorio
        ultimo_dir = self.config.obtener_ultimo_directorio()
        if ultimo_dir and Path(ultimo_dir).exists():
            self.directorio = Path(ultimo_dir)
            self.dir_label.setText(str(self.directorio))
            self.batch_dir_label.setText(str(self.directorio))
            self.btn_extract.setEnabled(True)
            self.batch_btn_extract.setEnabled(True)
        
        # Cargar últimas URLs
        ultimas_urls = self.config.obtener_ultimas_urls()
        if ultimas_urls:
            completer = QCompleter(ultimas_urls)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            self.url_input.setCompleter(completer)
    
    def init_ui(self):
        self.setWindowTitle("📝 Comentia - Extractor de comentarios de Marca.com")
        self.setMinimumSize(800, 700)
        self.resize(900, 750)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Título general
        title = QLabel("📝 Comentia")
        title_font = QFont("Arial", 28, QFont.Bold)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        subtitle = QLabel("Extractor de comentarios de Marca.com")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #aaaaaa; font-size: 12px;")
        main_layout.addWidget(subtitle)
        
        main_layout.addSpacing(10)
        
        # Directorio (común para ambas pestañas)
        dir_group = QGroupBox("📁 Directorio de destino")
        dir_layout = QHBoxLayout(dir_group)
        
        self.dir_label = QLabel("Ninguna carpeta seleccionada")
        self.dir_label.setStyleSheet("padding: 10px; background: #3c3c3c; border-radius: 5px; color: #ffffff;")
        self.dir_label.setWordWrap(True)
        dir_layout.addWidget(self.dir_label, 2)
        
        self.btn_select_dir = QPushButton("📂 Seleccionar")
        self.btn_select_dir.setFixedWidth(120)
        self.btn_select_dir.clicked.connect(self.seleccionar_directorio)
        dir_layout.addWidget(self.btn_select_dir)
        
        main_layout.addWidget(dir_group)
        
        # Pestañas
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #555; background: #2b2b2b; border-radius: 5px; }
            QTabBar::tab { background: #3c3c3c; color: white; padding: 8px 20px; margin: 2px; border-radius: 5px; }
            QTabBar::tab:selected { background: #4CAF50; }
        """)
        
        # Pestaña 1: Extracción simple
        tab_simple = self._crear_tab_simple()
        self.tab_widget.addTab(tab_simple, "🚀 Extracción simple")
        
        # Pestaña 2: Extracción por lotes
        tab_batch = self._crear_tab_batch()
        self.tab_widget.addTab(tab_batch, "📚 Extracción por lotes")
        
        main_layout.addWidget(self.tab_widget)
        
        # Estado
        self.status_label = QLabel("✅ Listo")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #4CAF50; padding: 5px; font-weight: bold;")
        main_layout.addWidget(self.status_label)
        
        self.apply_dark_theme()
    
    def _crear_tab_simple(self):
        """Crea la pestaña de extracción simple (una URL)."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # URL
        url_group = QGroupBox("🔗 URL de la noticia")
        url_layout = QVBoxLayout(url_group)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.marca.com/... o ID de la noticia\n💡 Puedes arrastrar una URL desde el navegador")
        self.url_input.setMinimumHeight(50)
        url_layout.addWidget(self.url_input)
        
        # Botones de URL
        url_buttons = QHBoxLayout()
        self.btn_limpiar_url = QPushButton("🗑️ Limpiar")
        self.btn_limpiar_url.clicked.connect(lambda: self.url_input.clear())
        self.btn_limpiar_url.setFixedWidth(100)
        url_buttons.addWidget(self.btn_limpiar_url)
        
        self.btn_pegar = QPushButton("📋 Pegar")
        self.btn_pegar.clicked.connect(self.pegar_url)
        self.btn_pegar.setFixedWidth(100)
        url_buttons.addWidget(self.btn_pegar)
        
        url_layout.addLayout(url_buttons)
        layout.addWidget(url_group)
        
        # Botón extraer
        self.btn_extract = QPushButton("🚀 Extraer comentarios")
        self.btn_extract.setEnabled(False)
        self.btn_extract.clicked.connect(self.iniciar_extraccion)
        self.btn_extract.setMinimumHeight(45)
        layout.addWidget(self.btn_extract)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(25)
        layout.addWidget(self.progress_bar)
        
        # Área de log
        log_group = QGroupBox("📄 Progreso")
        log_layout = QVBoxLayout(log_group)
        
        log_buttons = QHBoxLayout()
        self.btn_limpiar_log = QPushButton("🧹 Limpiar")
        self.btn_limpiar_log.clicked.connect(lambda: self.log_area.clear())
        self.btn_limpiar_log.setFixedWidth(100)
        log_buttons.addWidget(self.btn_limpiar_log)
        
        self.btn_guardar_log = QPushButton("💾 Guardar log")
        self.btn_guardar_log.clicked.connect(self.guardar_log)
        self.btn_guardar_log.setFixedWidth(100)
        log_buttons.addWidget(self.btn_guardar_log)
        
        log_layout.addLayout(log_buttons)
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMinimumHeight(200)
        self.log_area.setStyleSheet("""
            QTextEdit {
                background: #1e1e1e;
                color: #d4d4d4;
                font-family: monospace;
                font-size: 11px;
                border: 1px solid #555;
                border-radius: 5px;
            }
        """)
        log_layout.addWidget(self.log_area)
        
        layout.addWidget(log_group)
        
        return widget
    
    def _crear_tab_batch(self):
        """Crea la pestaña de extracción por lotes (archivo TXT)."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Información
        info_label = QLabel("📄 Crea un archivo de texto (.txt) con una URL por línea")
        info_label.setStyleSheet("color: #aaaaaa; padding: 5px;")
        layout.addWidget(info_label)
        
        # Selección de archivo
        file_group = QGroupBox("📁 Archivo con URLs")
        file_layout = QHBoxLayout(file_group)
        
        self.batch_file_label = QLabel("Ningún archivo seleccionado")
        self.batch_file_label.setStyleSheet("padding: 10px; background: #3c3c3c; border-radius: 5px; color: #ffffff;")
        self.batch_file_label.setWordWrap(True)
        file_layout.addWidget(self.batch_file_label, 2)
        
        self.btn_select_file = QPushButton("📂 Seleccionar archivo")
        self.btn_select_file.clicked.connect(self.seleccionar_archivo_lotes)
        self.btn_select_file.setFixedWidth(150)
        file_layout.addWidget(self.btn_select_file)
        
        layout.addWidget(file_group)
        
        # Vista previa de URLs
        preview_group = QGroupBox("🔍 Vista previa de URLs")
        preview_layout = QVBoxLayout(preview_group)
        
        self.batch_url_list = QListWidget()
        self.batch_url_list.setStyleSheet("""
            QListWidget {
                background: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #555;
                border-radius: 5px;
                font-family: monospace;
                font-size: 11px;
            }
        """)
        preview_layout.addWidget(self.batch_url_list)
        
        layout.addWidget(preview_group)
        
        # Botón extraer
        self.batch_btn_extract = QPushButton("📚 Extraer todas las URLs")
        self.batch_btn_extract.setEnabled(False)
        self.batch_btn_extract.clicked.connect(self.iniciar_extraccion_lotes)
        self.batch_btn_extract.setMinimumHeight(45)
        layout.addWidget(self.batch_btn_extract)
        
        # Barra de progreso
        self.batch_progress_bar = QProgressBar()
        self.batch_progress_bar.setVisible(False)
        self.batch_progress_bar.setMinimumHeight(25)
        layout.addWidget(self.batch_progress_bar)
        
        # Área de log para lotes
        batch_log_group = QGroupBox("📄 Progreso (Lotes)")
        batch_log_layout = QVBoxLayout(batch_log_group)
        
        self.batch_log_area = QTextEdit()
        self.batch_log_area.setReadOnly(True)
        self.batch_log_area.setMinimumHeight(200)
        self.batch_log_area.setStyleSheet("""
            QTextEdit {
                background: #1e1e1e;
                color: #d4d4d4;
                font-family: monospace;
                font-size: 11px;
                border: 1px solid #555;
                border-radius: 5px;
            }
        """)
        batch_log_layout.addWidget(self.batch_log_area)
        
        layout.addWidget(batch_log_group)
        
        return widget
    
    def apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #2b2b2b; }
            QGroupBox { color: #ffffff; font-weight: bold; border: 2px solid #555;
                        border-radius: 8px; margin-top: 10px; padding-top: 10px;
                        background-color: #2b2b2b; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px;
                               color: #ffffff; }
            QLabel { color: #ffffff; }
            QLineEdit { background: #3c3c3c; color: white; border: 2px solid #555;
                        border-radius: 5px; padding: 8px; font-size: 13px; }
            QLineEdit:focus { border-color: #4CAF50; }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #666; }
            QProgressBar { border: 2px solid #555; border-radius: 5px; text-align: center;
                           color: white; background: #3c3c3c; }
            QProgressBar::chunk { background-color: #4CAF50; border-radius: 3px; }
            QTextEdit { background: #1e1e1e; color: #d4d4d4; border: 1px solid #555; border-radius: 5px; }
        """)
    
    def seleccionar_directorio(self):
        directorio = QFileDialog.getExistingDirectory(
            self, "Seleccionar carpeta de destino", str(Path.home())
        )
        if directorio:
            self.directorio = Path(directorio)
            self.dir_label.setText(str(self.directorio))
            self.batch_dir_label.setText(str(self.directorio))
            self.config.guardar_ultimo_directorio(str(self.directorio))
            self.btn_extract.setEnabled(True)
            self.batch_btn_extract.setEnabled(True if self.batch_url_list.count() > 0 else False)
            self.status_label.setText("✅ Carpeta seleccionada")
            self.log_area.append(f"✅ Carpeta seleccionada: {self.directorio}")
    
    def pegar_url(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if text:
            self.url_input.setText(text)
            self.status_label.setText("✅ URL pegada")
    
    def seleccionar_archivo_lotes(self):
        archivo, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo con URLs", str(Path.home()),
            "Archivos de texto (*.txt);;Todos los archivos (*)"
        )
        if archivo:
            self.batch_file = Path(archivo)
            self.batch_file_label.setText(str(self.batch_file))
            self.config.guardar_archivo_lotes(str(self.batch_file))
            
            # Cargar URLs
            self.batch_url_list.clear()
            with open(archivo, "r", encoding="utf-8") as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            for url in urls:
                item = QListWidgetItem(url)
                self.batch_url_list.addItem(item)
            
            self.batch_btn_extract.setEnabled(True if self.directorio else False)
            self.status_label.setText(f"✅ Cargadas {len(urls)} URLs")
            self.batch_log_area.append(f"✅ Cargado archivo con {len(urls)} URLs")
    
    def iniciar_extraccion(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Introduce la URL de la noticia")
            return
        
        if not self.directorio:
            QMessageBox.warning(self, "Error", "Selecciona una carpeta de destino")
            return
        
        # Configurar UI
        self.btn_extract.setEnabled(False)
        self.btn_select_dir.setEnabled(False)
        self.url_input.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.log_area.clear()
        self.status_label.setText("⏳ Extrayendo comentarios...")
        self.status_label.setStyleSheet("color: #FF9800; padding: 5px; font-weight: bold;")
        
        # Guardar URL
        self.config.guardar_ultimas_urls(url)
        
        # Iniciar hilo
        self.extraction_thread = ExtractionThread(url, self.directorio)
        self.extraction_thread.log_signal.connect(self.agregar_log)
        self.extraction_thread.progress_signal.connect(self.actualizar_progreso)
        self.extraction_thread.finished_signal.connect(self.extraccion_finalizada)
        self.extraction_thread.error_signal.connect(self.extraccion_error)
        self.extraction_thread.start()
    
    def iniciar_extraccion_lotes(self):
        if not self.batch_url_list.count():
            QMessageBox.warning(self, "Error", "Carga un archivo con URLs primero")
            return
        
        if not self.directorio:
            QMessageBox.warning(self, "Error", "Selecciona una carpeta de destino")
            return
        
        # Obtener todas las URLs
        urls = []
        for i in range(self.batch_url_list.count()):
            urls.append(self.batch_url_list.item(i).text())
        
        # Configurar UI
        self.batch_btn_extract.setEnabled(False)
        self.btn_select_file.setEnabled(False)
        self.batch_progress_bar.setVisible(True)
        self.batch_progress_bar.setMaximum(len(urls))
        self.batch_progress_bar.setValue(0)
        self.batch_log_area.clear()
        self.status_label.setText("⏳ Extrayendo lotes...")
        self.status_label.setStyleSheet("color: #FF9800; padding: 5px; font-weight: bold;")
        
        # Iniciar hilo
        self.batch_thread = BatchExtractionThread(urls, self.directorio)
        self.batch_thread.log_signal.connect(lambda msg: self.batch_log_area.append(msg))
        self.batch_thread.progress_signal.connect(self.actualizar_progreso_lotes)
        self.batch_thread.item_completed.connect(self.actualizar_item_lote)
        self.batch_thread.finished_signal.connect(self.extraccion_lotes_finalizada)
        self.batch_thread.error_signal.connect(self.extraccion_error)
        self.batch_thread.start()
    
    def agregar_log(self, mensaje: str):
        self.log_area.append(mensaje)
        scroll = self.log_area.verticalScrollBar()
        scroll.setValue(scroll.maximum())
    
    def actualizar_progreso(self, actual: int, total: int):
        if total > 0:
            porcentaje = int((actual / total) * 100)
            self.progress_bar.setValue(porcentaje)
            self.progress_bar.setFormat(f"{actual}/{total} comentarios ({porcentaje}%)")
    
    def actualizar_progreso_lotes(self, actual: int, total: int):
        self.batch_progress_bar.setValue(actual)
        self.batch_progress_bar.setFormat(f"Procesando {actual}/{total}")
    
    def actualizar_item_lote(self, indice: int, total: int, estado: str):
        item = self.batch_url_list.item(indice - 1)
        if estado.startswith("✅"):
            item.setForeground(Qt.green)
        elif estado.startswith("❌"):
            item.setForeground(Qt.red)
        else:
            item.setForeground(Qt.yellow)
        item.setText(f"[{indice}/{total}] {estado} - {item.text()[:60]}...")
    
    def extraccion_finalizada(self, comentarios: dict, total: int, errores: list, noticia_id: str):
        obtenidos = len(comentarios)
        exito = obtenidos >= total * 0.95 if total > 0 else obtenidos > 0
        
        self.btn_extract.setEnabled(True)
        self.btn_select_dir.setEnabled(True)
        self.url_input.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if exito:
            self.status_label.setText(f"✅ ¡Éxito! {obtenidos}/{total} comentarios guardados")
            self.status_label.setStyleSheet("color: #4CAF50; padding: 5px; font-weight: bold;")
            
            # Preguntar si quiere ver vista previa
            if comentarios and len(comentarios) > 0:
                reply = QMessageBox.question(
                    self, "Vista previa",
                    f"¿Quieres ver una vista previa de los {min(20, len(comentarios))} primeros comentarios?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    comentarios_lista = sorted(comentarios.values(), key=lambda x: x["order"])
                    vista = VistaPreviaDialog(comentarios_lista, self)
                    vista.exec_()
            
            QMessageBox.information(
                self, "Operación completada",
                f"✅ Extracción finalizada con éxito\n\n"
                f"📊 Comentarios obtenidos: {obtenidos}/{total}\n"
                f"📁 Ubicación: {self.directorio / f'noticia_{noticia_id}'}"
            )
        else:
            self.status_label.setText(f"⚠️ {obtenidos}/{total} comentarios - Con errores")
            self.status_label.setStyleSheet("color: #f44336; padding: 5px; font-weight: bold;")
            msg = f"⚠️ Operación con errores\n\n{obtenidos}/{total} comentarios obtenidos"
            if errores:
                msg += f"\n\nErrores:\n" + "\n".join(errores[:5])
            QMessageBox.warning(self, "Operación con errores", msg)
    
    def extraccion_lotes_finalizada(self, resultados: list):
        exitosos = sum(1 for r in resultados if r.get("exito"))
        fallidos = len(resultados) - exitosos
        
        self.batch_btn_extract.setEnabled(True)
        self.btn_select_file.setEnabled(True)
        self.batch_progress_bar.setVisible(False)
        
        self.status_label.setText(f"✅ Lotes completados: {exitosos} éxitos, {fallidos} fallos")
        self.status_label.setStyleSheet("color: #4CAF50; padding: 5px; font-weight: bold;")
        
        QMessageBox.information(
            self, "Extracción por lotes completada",
            f"📊 Resumen:\n\n✅ Exitosos: {exitosos}\n❌ Fallidos: {fallidos}\n📁 Ubicación: {self.directorio}"
        )
    
    def extraccion_error(self, error: str):
        self.btn_extract.setEnabled(True)
        self.btn_select_dir.setEnabled(True)
        self.url_input.setEnabled(True)
        self.batch_btn_extract.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.batch_progress_bar.setVisible(False)
        self.status_label.setText("❌ Error en la extracción")
        self.status_label.setStyleSheet("color: #f44336; padding: 5px; font-weight: bold;")
        QMessageBox.critical(self, "Error", f"Error durante la extracción:\n\n{error}")
    
    def guardar_log(self):
        if not self.log_area.toPlainText():
            QMessageBox.information(self, "Guardar log", "No hay contenido para guardar")
            return
        
        archivo, _ = QFileDialog.getSaveFileName(
            self, "Guardar log", str(Path.home() / "comentia_log.txt"),
            "Archivos de texto (*.txt)"
        )
        if archivo:
            with open(archivo, "w", encoding="utf-8") as f:
                f.write(self.log_area.toPlainText())
            QMessageBox.information(self, "Guardado", f"Log guardado en:\n{archivo}")


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Comentia")
    
    window = ComentiaWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()