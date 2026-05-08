#!/usr/bin/env python3
"""
Comentia - Extractor de comentarios de Marca.com
Versión PyQt5 - Definitiva: estadísticas COMPLETAS, visor funcional, tema solo interruptor
"""

import sys
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
    QFileDialog, QMessageBox, QGroupBox, QDialog, QTextBrowser,
    QTabWidget, QListWidget, QListWidgetItem, QCompleter,
    QMenuBar, QMenu, QAction
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QDragEnterEvent, QDropEvent

# Importar configuración
from config import Configuracion

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

# Iconos compatibles (sin emojis dependientes del sistema)
ICONOS = {
    "app": "📝",
    "extraer": "▶",
    "carpeta": "📂",
    "url": "🌐",
    "ok": "✓",
    "error": "✗",
    "pagina": "📄",
    "guardar": "💾",
    "limpiar": "🗑",
    "pegar": "📋",
    "tema": "🎨",
    "lotes": "📚",
    "buscar": "🔍"
}


# ========================
# VISOR DE COMENTARIOS COMPLETO CON BÚSQUEDA
# ========================
class VisorComentariosDialog(QDialog):
    def __init__(self, comentarios, titulo_noticia="", parent=None):
        super().__init__(parent)
        self.comentarios_originales = comentarios
        self.comentarios_filtrados = comentarios[:] if comentarios else []
        self.setWindowTitle(f"Visor de comentarios - Total: {len(comentarios) if comentarios else 0}")
        self.setModal(False)
        self.resize(1000, 750)
        
        layout = QVBoxLayout(self)
        
        if titulo_noticia:
            lbl_titulo = QLabel(f"📰 {titulo_noticia}")
            lbl_titulo.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
            layout.addWidget(lbl_titulo)
        
        # Barra de búsqueda
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("🔍 Buscar:"))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por usuario, palabra o fecha (DD/MM/AAAA)...")
        self.search_input.textChanged.connect(self.filtrar_comentarios)
        search_layout.addWidget(self.search_input, 2)
        
        self.btn_limpiar_filtro = QPushButton("Mostrar todos")
        self.btn_limpiar_filtro.clicked.connect(self.limpiar_filtro)
        search_layout.addWidget(self.btn_limpiar_filtro)
        
        self.btn_exportar_filtro = QPushButton("💾 Exportar filtrados")
        self.btn_exportar_filtro.clicked.connect(self.exportar_filtrados)
        search_layout.addWidget(self.btn_exportar_filtro)
        
        layout.addLayout(search_layout)
        
        # Área de texto
        self.text_area = QTextBrowser()
        self.text_area.setStyleSheet("""
            QTextBrowser {
                background: #1e1e1e;
                color: #d4d4d4;
                font-family: monospace;
                font-size: 12px;
                border: 1px solid #555;
                border-radius: 5px;
            }
        """)
        self.actualizar_texto()
        layout.addWidget(self.text_area)
        
        # Estadísticas del filtro
        self.stats_label = QLabel(f"📊 Mostrando {len(self.comentarios_filtrados)} de {len(self.comentarios_originales) if self.comentarios_originales else 0} comentarios")
        layout.addWidget(self.stats_label)
        
        # Botón cerrar
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.accept)
        layout.addWidget(btn_cerrar)
        
        self.setStyleSheet("""
            QDialog { background-color: #2b2b2b; }
            QLabel { color: white; }
            QLineEdit { background: #3c3c3c; color: white; border: 1px solid #555; border-radius: 5px; padding: 8px; }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
    
    def filtrar_comentarios(self):
        if not self.comentarios_originales:
            return
        texto = self.search_input.text().lower()
        if not texto:
            self.comentarios_filtrados = self.comentarios_originales[:]
        else:
            self.comentarios_filtrados = []
            for c in self.comentarios_originales:
                if (texto in c.get('user', '').lower() or
                    texto in c.get('body', '').lower() or
                    texto in c.get('date', '').lower()):
                    self.comentarios_filtrados.append(c)
        self.actualizar_texto()
        self.stats_label.setText(f"📊 Mostrando {len(self.comentarios_filtrados)} de {len(self.comentarios_originales)} comentarios")
    
    def limpiar_filtro(self):
        self.search_input.clear()
    
    def exportar_filtrados(self):
        if not self.comentarios_filtrados:
            QMessageBox.warning(self, "Exportar", "No hay comentarios para exportar")
            return
        archivo, _ = QFileDialog.getSaveFileName(
            self, "Guardar comentarios filtrados", 
            str(Path.home() / "comentarios_filtrados.json"),
            "Archivos JSON (*.json)"
        )
        if archivo:
            with open(archivo, "w", encoding="utf-8") as f:
                json.dump(self.comentarios_filtrados, f, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "Exportar", f"Exportados {len(self.comentarios_filtrados)} comentarios")
    
    def actualizar_texto(self):
        if not self.comentarios_filtrados:
            self.text_area.setText("No hay comentarios para mostrar.")
            return
        texto = ""
        for i, c in enumerate(self.comentarios_filtrados, 1):
            texto += f"\n{'='*75}\n"
            texto += f"[{i:4d}] 👤 {c.get('user', 'anónimo')}\n"
            texto += f"📅 {c.get('date', '?')} {c.get('time', '?')}\n"
            texto += f"💬 {c.get('body', '')}\n"
            if c.get('references'):
                texto += f"🔗 Referencias: {len(c.get('references', []))}\n"
        if not texto:
            texto = "No se encontraron comentarios que coincidan con la búsqueda."
        self.text_area.setText(texto)


# ========================
# HILO DE EXTRACCIÓN (SIMPLE)
# ========================
class ExtractionThread(QThread):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, int)
    finished_signal = pyqtSignal(dict, int, list, str)
    error_signal = pyqtSignal(str)
    
    def __init__(self, url: str, directorio: Path):
        super().__init__()
        self.url = url
        self.directorio = directorio
        self.log_buffer = []
        self._tiempo_inicio = time.time()
    
    def log(self, mensaje: str):
        self.log_buffer.append(mensaje)
        self.log_signal.emit(mensaje)
    
    def run(self):
        try:
            self.log(f"{ICONOS['app']} Iniciando extracción...")
            
            noticia_id = self._extraer_id()
            if not noticia_id:
                self.error_signal.emit(f"{ICONOS['error']} No se pudo obtener el ID")
                return
            
            self.log(f"{ICONOS['ok']} ID detectado: {noticia_id}")
            subdir = self.directorio / f"noticia_{noticia_id}"
            subdir.mkdir(parents=True, exist_ok=True)
            self.log(f"{ICONOS['carpeta']} Carpeta: {subdir}")
            
            comentarios, total, errores = self._descargar_comentarios(noticia_id)
            
            self.log(f"{ICONOS['guardar']} Guardando archivos...")
            self._exportar(comentarios, noticia_id, subdir, self.url)
            self._generar_estadisticas_completas(comentarios, noticia_id, self.url, total, subdir, errores)
            
            # Guardar log de sesión (siempre)
            if self.log_buffer:
                log_file = subdir / f"logs_{noticia_id}_sesion.txt"
                with open(log_file, "w", encoding="utf-8") as f:
                    f.write(f"{'='*80}\n")
                    f.write(f"LOGS DE EXTRACCIÓN - NOTICIA {noticia_id}\n")
                    f.write(f"{'='*80}\n\n")
                    f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"URL: {self.url}\n\n")
                    f.write("\n".join(self.log_buffer))
                self.log(f"{ICONOS['guardar']} Log guardado: {log_file.name}")
            
            self.log(f"{ICONOS['ok']} Completado: {len(comentarios)}/{total}")
            self.finished_signal.emit(comentarios, total, errores, noticia_id)
        except Exception as e:
            self.error_signal.emit(str(e))
    
    def _extraer_id(self) -> Optional[str]:
        entrada = self.url
        if entrada.isdigit():
            return entrada
        patrones_url = [r'/noticia[/-](\d+)', r'/comentarios[/-](\d+)', r'noticia=(\d+)', r'/(\d{6,})/']
        for patron in patrones_url:
            match = re.search(patron, entrada)
            if match:
                return match.group(1)
        try:
            response = requests.get(entrada, headers=HEADERS, timeout=TIMEOUT)
            html = response.text
            patrones_html = [r'"commentId"\s*:\s*"(\d+)"', r'commentId["\']?\s*[:=]\s*["\']?(\d+)', r'data-noticia=["\'](\d+)']
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
    
    def _descargar_comentarios(self, noticia_id: str):
        comentarios = {}
        ultimo_order = None
        total_esperado = None
        page_num = 1
        errores = []
        while True:
            self.log(f"{ICONOS['pagina']} Descargando página {page_num}...")
            data = self._peticion_segura(noticia_id, ultimo_order)
            if not data:
                errores.append(f"Fallo página {page_num}")
                break
            if total_esperado is None:
                total_esperado = data.get("total", 0)
                self.log(f"📊 Total esperado: {total_esperado}")
                self.progress_signal.emit(0, total_esperado)
            items = data.get("items", [])
            if not items:
                break
            nuevos = 0
            for item in items:
                order = item.get("order")
                if order and order not in comentarios:
                    comentarios[order] = {
                        "id": item.get("id"), "order": order, "user": item.get("user"),
                        "body": item.get("body"), "date": item.get("date"), "time": item.get("time"),
                        "references": item.get("references", [])
                    }
                    nuevos += 1
            self.log(f"  {ICONOS['ok']} Página {page_num}: +{nuevos} (Total: {len(comentarios)}/{total_esperado})")
            self.progress_signal.emit(len(comentarios), total_esperado)
            if data.get("lastPage"):
                self.log("🏁 Última página")
                break
            if items:
                ultimo_order = items[-1]["order"]
            page_num += 1
            time.sleep(DELAY_ENTRE_PAGINAS)
        return comentarios, total_esperado or 0, errores
    
    def _exportar(self, comentarios_dict: Dict[int, dict], noticia_id: str, directorio: Path, url_noticia: str = ""):
        comentarios_lista = sorted(comentarios_dict.values(), key=lambda x: x["order"])
        datos_exportar = {
            "metadata": {
                "noticia_id": noticia_id, "url_noticia": url_noticia,
                "total_comentarios": len(comentarios_lista),
                "fecha_exportacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "fuente": "Marca.com"
            },
            "comentarios": comentarios_lista
        }
        archivo_completo = directorio / f"comentarios_{noticia_id}_completo.json"
        with open(archivo_completo, "w", encoding="utf-8") as f:
            json.dump(datos_exportar, f, ensure_ascii=False, indent=2)
        self.log(f"{ICONOS['guardar']} Guardado: {archivo_completo.name}")
        archivo_simplificado = directorio / f"comentarios_{noticia_id}_simplificado.json"
        comentarios_simples = [
            {"order": c["order"], "usuario": c["user"], "comentario": c["body"], "fecha": f"{c['date']} {c['time']}"}
            for c in comentarios_lista
        ]
        with open(archivo_simplificado, "w", encoding="utf-8") as f:
            json.dump(comentarios_simples, f, ensure_ascii=False, indent=2)
        self.log(f"{ICONOS['guardar']} Guardado: {archivo_simplificado.name}")
    
    def _generar_estadisticas_completas(self, comentarios_dict: Dict[int, dict], noticia_id: str,
                                        url_noticia: str, total_esperado: int, directorio: Path,
                                        errores: List[str]):
        """Genera estadísticas COMPLETAS con todas las métricas"""
        comentarios_reales = list(comentarios_dict.values())
        total_obtenidos = len(comentarios_reales)
        
        # ========== 1. ESTADÍSTICAS DE USUARIOS ==========
        usuarios = {}
        for c in comentarios_reales:
            user = c.get("user", "anónimo")
            usuarios[user] = usuarios.get(user, 0) + 1
        top_usuarios = sorted(usuarios.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # ========== 2. ACTIVIDAD POR FECHA ==========
        fechas = {}
        for c in comentarios_reales:
            fecha = c.get("date", "desconocida")
            fechas[fecha] = fechas.get(fecha, 0) + 1
        
        # ========== 3. ACTIVIDAD POR HORA ==========
        horas = []
        for c in comentarios_reales:
            hora_match = re.search(r'(\d{1,2}):', c.get("time", "00:00"))
            if hora_match:
                horas.append(int(hora_match.group(1)))
        
        hora_pico = "No disponible"
        distribucion_horas = {}
        if horas:
            hora_pico_valor = max(set(horas), key=horas.count)
            hora_pico = f"{hora_pico_valor:02d}:00 - {horas.count(hora_pico_valor)}"
            for h in horas:
                distribucion_horas[h] = distribucion_horas.get(h, 0) + 1
        
        # ========== 4. PALABRAS MÁS UTILIZADAS ==========
        palabras_comunes = {}
        stopwords = {'como', 'cuando', 'donde', 'este', 'esta', 'esto', 'para', 'porque', 
                     'pero', 'sino', 'sobre', 'entre', 'sin', 'que', 'con', 'por', 'de',
                     'en', 'a', 'es', 'son', 'fue', 'han', 'he', 'has', 'ha', 'hemos', 'han',
                     'ser', 'estar', 'tener', 'hacer', 'poder', 'decir', 'ir', 'ver', 'dar',
                     'muy', 'más', 'menos', 'tan', 'adonde', 'una', 'unas', 'uno', 'unos',
                     'la', 'las', 'el', 'los', 'y', 'o', 'porque', 'asi', 'esa', 'ese'}
        for c in comentarios_reales:
            texto = c.get("body", "").lower()
            texto = re.sub(r'http\S+', '', texto)
            texto = re.sub(r'@\w+', '', texto)
            palabras = re.findall(r'\b[a-záéíóúüñ]{4,}\b', texto)
            for palabra in palabras:
                if palabra not in stopwords and len(palabra) > 3:
                    palabras_comunes[palabra] = palabras_comunes.get(palabra, 0) + 1
        top_palabras = sorted(palabras_comunes.items(), key=lambda x: x[1], reverse=True)[:15]
        
        # ========== 5. MÉTRICAS DE CONTENIDO ==========
        longitudes = [len(c.get("body", "")) for c in comentarios_reales]
        if longitudes:
            longitud_promedio = sum(longitudes) / len(longitudes)
            longitud_min = min(longitudes)
            longitud_max = max(longitudes)
        else:
            longitud_promedio = longitud_min = longitud_max = 0
        
        comentarios_con_referencias = sum(1 for c in comentarios_reales if c.get("references"))
        total_referencias = sum(len(c.get("references", [])) for c in comentarios_reales)
        
        # ========== 6. USUARIOS MÁS REFERENCIADOS ==========
        referencias_recibidas = {}
        for c in comentarios_reales:
            for ref in c.get("references", []):
                if "order" in ref:
                    try:
                        orden_ref = int(ref["order"]) if isinstance(ref["order"], str) else ref["order"]
                        for c2 in comentarios_reales:
                            if c2.get("order") == orden_ref:
                                usuario_ref = c2.get("user", "desconocido")
                                referencias_recibidas[usuario_ref] = referencias_recibidas.get(usuario_ref, 0) + 1
                                break
                    except:
                        pass
        top_referenciados = sorted(referencias_recibidas.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # ========== 7. USUARIOS CONSTANTES ==========
        fechas_unicas = len(fechas)
        usuarios_constantes = 0
        if fechas_unicas > 1 and comentarios_reales:
            for user in usuarios:
                fechas_user = set()
                for c in comentarios_reales:
                    if c.get("user") == user:
                        fechas_user.add(c.get("date"))
                if len(fechas_user) > 1:
                    usuarios_constantes += 1
        
        # ========== 8. PORCENTAJE DE ÉXITO ==========
        porcentaje_exito = (total_obtenidos / total_esperado * 100) if total_esperado > 0 else 0
        
        # ========== 9. HUECOS ==========
        if comentarios_reales:
            orders = set(comentarios_dict.keys())
            max_order = max(orders)
            min_order = min(orders)
            huecos = sorted(set(range(min_order, max_order + 1)) - orders)
        else:
            max_order = min_order = 0
            huecos = []
        
        # ========== 10. COMENTARIOS ÚNICOS VS DUPLICADOS ==========
        cuerpos = [c.get("body", "").strip() for c in comentarios_reales]
        comentarios_unicos = len(set(cuerpos))
        comentarios_duplicados = total_obtenidos - comentarios_unicos
        
        # ========== 11. GENERAR ARCHIVO ==========
        archivo = directorio / f"comentarios_{noticia_id}_estadisticas.txt"
        with open(archivo, "w", encoding="utf-8") as f:
            f.write("=" * 90 + "\n")
            f.write("📊 COMENTIA - ESTADÍSTICAS COMPLETAS DE COMENTARIOS\n")
            f.write("=" * 90 + "\n\n")
            
            f.write("📰 INFORMACIÓN DE LA NOTICIA\n")
            f.write("-" * 50 + "\n")
            f.write(f"  ID de la noticia:              {noticia_id}\n")
            f.write(f"  URL:                           {url_noticia if url_noticia else 'No disponible'}\n")
            f.write(f"  Fecha de extracción:           {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"  Tiempo de ejecución:           {time.time() - self._tiempo_inicio:.2f} segundos\n\n")
            
            f.write("📊 RESUMEN DE EXTRACCIÓN\n")
            f.write("-" * 50 + "\n")
            f.write(f"  Total esperado según API:      {total_esperado} comentarios\n")
            f.write(f"  Total obtenido:                {total_obtenidos} comentarios\n")
            f.write(f"  Porcentaje de éxito:           {porcentaje_exito:.2f}%\n")
            f.write(f"  Comentarios perdidos:          {total_esperado - total_obtenidos}\n")
            f.write(f"  Rango de órdenes:              {min_order} - {max_order}\n")
            f.write(f"  Huecos detectados:             {len(huecos)}\n")
            if huecos:
                f.write(f"  Primeros 25 huecos:            {', '.join(map(str, huecos[:25]))}\n")
            f.write("\n")
            
            f.write("👥 ESTADÍSTICAS DE USUARIOS\n")
            f.write("-" * 50 + "\n")
            f.write(f"  Total de usuarios únicos:      {len(usuarios)}\n")
            f.write(f"  Promedio comentarios/usuario:  {total_obtenidos / len(usuarios):.2f}\n")
            f.write(f"  Usuarios constantes:           {usuarios_constantes}\n\n")
            f.write("  TOP 10 USUARIOS MÁS ACTIVOS:\n")
            for i, (user, count) in enumerate(top_usuarios, 1):
                f.write(f"    {i:2}. {user:<30} - {count:4} comentarios ({count/total_obtenidos*100:.1f}%)\n")
            f.write("\n")
            
            f.write("⏰ ACTIVIDAD TEMPORAL\n")
            f.write("-" * 50 + "\n")
            f.write(f"  Hora con más comentarios:      {hora_pico}\n")
            if distribucion_horas:
                f.write("  Distribución por horas:\n")
                for h in sorted(distribucion_horas.keys()):
                    f.write(f"    {h:02d}:00 - {distribucion_horas[h]} comentarios\n")
            f.write("\n")
            
            f.write("📅 ACTIVIDAD POR FECHA\n")
            f.write("-" * 50 + "\n")
            for fecha, count in sorted(fechas.items(), reverse=True):
                f.write(f"  {fecha}: {count} comentarios\n")
            f.write("\n")
            
            f.write("📝 MÉTRICAS DE CONTENIDO\n")
            f.write("-" * 50 + "\n")
            f.write(f"  Longitud promedio:             {longitud_promedio:.0f} caracteres\n")
            f.write(f"  Comentario más corto:          {longitud_min} caracteres\n")
            f.write(f"  Comentario más largo:          {longitud_max} caracteres\n")
            f.write(f"  Comentarios con referencias:   {comentarios_con_referencias}\n")
            f.write(f"  Total de referencias:          {total_referencias}\n")
            f.write(f"  Comentarios únicos:            {comentarios_unicos}\n")
            f.write(f"  Comentarios duplicados:        {comentarios_duplicados}\n\n")
            
            if top_referenciados:
                f.write("🏆 USUARIOS QUE MÁS REFERENCIAS RECIBEN\n")
                f.write("-" * 50 + "\n")
                for i, (user, count) in enumerate(top_referenciados, 1):
                    f.write(f"  {i}. {user:<30} - {count} referencias\n")
                f.write("\n")
            
            f.write("🔤 PALABRAS MÁS UTILIZADAS EN COMENTARIOS\n")
            f.write("-" * 50 + "\n")
            for i, (palabra, count) in enumerate(top_palabras, 1):
                f.write(f"  {i:2}. {palabra:<20} - {count:4} veces\n")
            f.write("\n")
            
            f.write("📁 ARCHIVOS GENERADOS\n")
            f.write("-" * 50 + "\n")
            f.write(f"  • comentarios_{noticia_id}_completo.json\n")
            f.write(f"  • comentarios_{noticia_id}_simplificado.json\n")
            f.write(f"  • comentarios_{noticia_id}_estadisticas.txt\n")
            f.write(f"  • logs_{noticia_id}_sesion.txt\n\n")
            
            if errores:
                f.write("⚠️ ERRORES DETECTADOS DURANTE LA EXTRACCIÓN\n")
                f.write("-" * 50 + "\n")
                for error in errores[:10]:
                    f.write(f"  • {error}\n")
                if len(errores) > 10:
                    f.write(f"  • ... y {len(errores) - 10} errores más\n")
                f.write("\n")
            
            f.write("=" * 90 + "\n")
            f.write("  Comentia - Extractor de comentarios de Marca.com\n")
            f.write("  https://github.com/H0nt3/Comentia\n")
            f.write("=" * 90 + "\n")
        
        self.log(f"📊 Estadísticas completas guardadas en: {archivo.name}")


# ========================
# HILO DE EXTRACCIÓN POR LOTES
# ========================
class BatchExtractionThread(QThread):
    log_signal = pyqtSignal(str)
    batch_progress_signal = pyqtSignal(int, int, str)
    item_completed = pyqtSignal(int, int, str)
    finished_signal = pyqtSignal(list)
    error_signal = pyqtSignal(str)
    
    def __init__(self, urls: List[str], directorio: Path):
        super().__init__()
        self.urls = urls
        self.directorio = directorio
        self._is_cancelled = False
        self.log_buffer = []
    
    def cancel(self):
        self._is_cancelled = True
        self.log_signal.emit(f"{ICONOS['error']} Cancelando...")
    
    def log(self, mensaje: str):
        self.log_buffer.append(mensaje)
        self.log_signal.emit(mensaje)
    
    def run(self):
        resultados = []
        total = len(self.urls)
        self.log(f"{ICONOS['app']} INICIANDO LOTES - {total} URLs")
        
        for i, url in enumerate(self.urls, 1):
            if self._is_cancelled:
                break
            
            self.log(f"\n📌 Procesando {i}/{total}: {url[:80]}...")
            self.batch_progress_signal.emit(i, total, url)
            
            exito, noticia_id, comentarios, total_esp, errores = self._extraer_comentario_individual(url)
            
            if exito and noticia_id:
                self.log(f"{ICONOS['ok']} Éxito: {len(comentarios)}/{total_esp}")
                resultados.append({"url": url, "exito": True, "comentarios": len(comentarios), "id": noticia_id})
                self.item_completed.emit(i, total, f"{ICONOS['ok']} {len(comentarios)}/{total_esp}")
            else:
                self.log(f"{ICONOS['error']} Fallo: {errores}")
                resultados.append({"url": url, "exito": False, "error": str(errores)})
                self.item_completed.emit(i, total, f"{ICONOS['error']} Fallo")
            
            self.batch_progress_signal.emit(i, total, url)
        
        exitosos = sum(1 for r in resultados if r.get("exito"))
        self.log(f"\n📊 RESUMEN: {exitosos}/{total} exitosos")
        self.finished_signal.emit(resultados)
    
    def _extraer_comentario_individual(self, url: str):
        try:
            noticia_id = self._extraer_id(url)
            if not noticia_id:
                return False, None, None, 0, "ID no encontrado"
            
            subdir = self.directorio / f"noticia_{noticia_id}"
            subdir.mkdir(parents=True, exist_ok=True)
            
            comentarios, total_esp, errores = self._descargar_comentarios(noticia_id, url)
            self._exportar(comentarios, noticia_id, subdir, url)
            self._generar_estadisticas_batch(comentarios, noticia_id, url, total_esp, subdir, errores)
            
            if self.log_buffer:
                log_file = subdir / f"logs_{noticia_id}_sesion.txt"
                try:
                    with open(log_file, "w", encoding="utf-8") as f:
                        f.write(f"LOGS NOTICIA {noticia_id}\n{datetime.now()}\nURL: {url}\n\n")
                        f.write("\n".join(self.log_buffer[-50:]))
                except:
                    pass
            
            return True, noticia_id, comentarios, total_esp, errores
        except Exception as e:
            return False, None, None, 0, str(e)
    
    def _extraer_id(self, url: str) -> Optional[str]:
        if url.isdigit():
            return url
        patrones_url = [r'/noticia[/-](\d+)', r'/comentarios[/-](\d+)', r'noticia=(\d+)', r'/(\d{6,})/']
        for patron in patrones_url:
            match = re.search(patron, url)
            if match:
                return match.group(1)
        try:
            response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            html = response.text
            patrones_html = [r'"commentId"\s*:\s*"(\d+)"', r'commentId["\']?\s*[:=]\s*["\']?(\d+)', r'data-noticia=["\'](\d+)']
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
            if self._is_cancelled:
                return None
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
            if self._is_cancelled:
                break
            data = self._peticion_segura(noticia_id, ultimo_order)
            if not data:
                errores.append(f"Fallo página {page_num}")
                break
            if total_esperado is None:
                total_esperado = data.get("total", 0)
                self.log(f"📊 Total esperado: {total_esperado}")
            items = data.get("items", [])
            if not items:
                break
            for item in items:
                order = item.get("order")
                if order and order not in comentarios:
                    comentarios[order] = {
                        "id": item.get("id"), "order": order, "user": item.get("user"),
                        "body": item.get("body"), "date": item.get("date"), "time": item.get("time"),
                        "references": item.get("references", [])
                    }
            self.log(f"{ICONOS['pagina']} Página {page_num}: +{len(items)} (Total: {len(comentarios)}/{total_esperado})")
            if data.get("lastPage"):
                break
            if items:
                ultimo_order = items[-1]["order"]
            page_num += 1
            time.sleep(DELAY_ENTRE_PAGINAS)
        return comentarios, total_esperado or 0, errores
    
    def _exportar(self, comentarios_dict: Dict[int, dict], noticia_id: str, directorio: Path, url_noticia: str = ""):
        comentarios_lista = sorted(comentarios_dict.values(), key=lambda x: x["order"])
        datos_exportar = {
            "metadata": {
                "noticia_id": noticia_id, "url_noticia": url_noticia,
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
        with open(archivo_simplificado, "w", encoding="utf-8") as f:
            json.dump([{"order": c["order"], "usuario": c["user"], "comentario": c["body"], "fecha": f"{c['date']} {c['time']}"} for c in comentarios_lista], f, ensure_ascii=False, indent=2)
    
    def _generar_estadisticas_batch(self, comentarios_dict: Dict[int, dict], noticia_id: str, url_noticia: str, total_esperado: int, directorio: Path, errores: List[str]):
        comentarios_reales = list(comentarios_dict.values())
        total_obtenidos = len(comentarios_reales)
        usuarios = {}
        for c in comentarios_reales:
            usuarios[c.get("user", "anónimo")] = usuarios.get(c.get("user", "anónimo"), 0) + 1
        top_usuarios = sorted(usuarios.items(), key=lambda x: x[1], reverse=True)[:10]
        longitudes = [len(c.get("body", "")) for c in comentarios_reales]
        porcentaje_exito = (total_obtenidos / total_esperado * 100) if total_esperado > 0 else 0
        archivo = directorio / f"comentarios_{noticia_id}_estadisticas.txt"
        with open(archivo, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write("📊 COMENTIA - ESTADÍSTICAS\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"ID: {noticia_id}\nURL: {url_noticia}\n")
            f.write(f"Extracción: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Esperados: {total_esperado} | Obtenidos: {total_obtenidos} | Éxito: {porcentaje_exito:.2f}%\n\n")
            f.write("TOP 10 USUARIOS:\n")
            for i, (user, count) in enumerate(top_usuarios, 1):
                f.write(f"{i:2}. {user:<30} - {count}\n")
            if longitudes:
                f.write(f"\nLongitud promedio: {sum(longitudes)/len(longitudes):.0f} caracteres\n")
            f.write(f"\nArchivos: comentarios_{noticia_id}_completo.json, simplificado.json, logs_{noticia_id}_sesion.txt\n")
        self.log(f"📊 Estadísticas: {archivo.name}")


# ========================
# VENTANA PRINCIPAL
# ========================
class ComentiaWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.directorio = None
        self.extraction_thread = None
        self.batch_thread = None
        self.config = Configuracion()
        self.tema_oscuro = True
        self.ultimos_comentarios = None
        self.ultimo_id = None
        self.init_ui()
        self.setup_drag_drop()
        self.cargar_configuracion_guardada()
        self.aplicar_tema()
    
    def setup_drag_drop(self):
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.status_label.setText("🎯 Suelta la URL aquí")
    
    def dragLeaveEvent(self, event):
        self.status_label.setText(f"{ICONOS['ok']} Listo")
    
    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            url = urls[0].toString()
            self.url_input.setText(url)
            self.status_label.setText(f"{ICONOS['ok']} URL cargada")
    
    def cargar_configuracion_guardada(self):
        ultimo_dir = self.config.obtener_ultimo_directorio()
        if ultimo_dir and Path(ultimo_dir).exists():
            self.directorio = Path(ultimo_dir)
            self.dir_label.setText(str(self.directorio))
            self.btn_extract.setEnabled(True)
        tema = self.config.cargar_configuracion().get("tema", "oscuro")
        self.tema_oscuro = (tema == "oscuro")
        self.btn_tema.setText("☀️ Claro" if self.tema_oscuro else "🌙 Oscuro")
    
    def init_ui(self):
        self.setWindowTitle("Comentia - Extractor de comentarios")
        self.setMinimumSize(800, 650)
        self.resize(950, 750)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Cabecera con interruptor de tema
        cabecera = QHBoxLayout()
        titulo = QLabel("📝 Comentia")
        titulo.setFont(QFont("Arial", 24, QFont.Bold))
        cabecera.addWidget(titulo, 3)
        self.btn_tema = QPushButton("☀️ Claro")
        self.btn_tema.setFixedSize(100, 40)
        self.btn_tema.clicked.connect(self.toggle_tema)
        cabecera.addWidget(self.btn_tema, 1)
        layout.addLayout(cabecera)
        
        subtitulo = QLabel("Extractor de comentarios de Marca.com")
        subtitulo.setAlignment(Qt.AlignCenter)
        subtitulo.setStyleSheet("color: #aaaaaa; font-size: 12px;")
        layout.addWidget(subtitulo)
        layout.addSpacing(10)
        
        # Menú (solo Visor y Ayuda, sin Tema)
        menubar = self.menuBar()
        menu_ver = menubar.addMenu("👁️ Ver")
        accion_visor = QAction("🔍 Visor de comentarios", self)
        accion_visor.triggered.connect(self.abrir_visor)
        menu_ver.addAction(accion_visor)
        menu_ayuda = menubar.addMenu("❓ Ayuda")
        accion_about = QAction("ℹ️ Acerca de", self)
        accion_about.triggered.connect(self.mostrar_acerca_de)
        menu_ayuda.addAction(accion_about)
        
        # Directorio común
        dir_group = QGroupBox(f"{ICONOS['carpeta']} Directorio de destino")
        dir_layout = QHBoxLayout(dir_group)
        self.dir_label = QLabel("Ninguna carpeta seleccionada")
        self.dir_label.setStyleSheet("padding: 10px; background: #3c3c3c; border-radius: 5px; color: #ffffff;")
        self.dir_label.setWordWrap(True)
        dir_layout.addWidget(self.dir_label, 2)
        self.btn_select_dir = QPushButton(f"{ICONOS['carpeta']} Seleccionar")
        self.btn_select_dir.setFixedWidth(120)
        self.btn_select_dir.clicked.connect(self.seleccionar_directorio)
        dir_layout.addWidget(self.btn_select_dir)
        layout.addWidget(dir_group)
        
        # Pestañas
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("QTabWidget::pane { border: 1px solid #555; border-radius: 5px; } QTabBar::tab { padding: 8px 25px; margin: 2px; border-radius: 5px; font-weight: bold; }")
        layout.addWidget(self.tab_widget)
        
        # Pestaña simple
        tab_simple = QWidget()
        simple_layout = QVBoxLayout(tab_simple)
        simple_layout.setSpacing(15)
        url_group = QGroupBox(f"{ICONOS['url']} URL de la noticia")
        url_layout = QVBoxLayout(url_group)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.marca.com/... o ID de la noticia\n💡 Puedes arrastrar una URL")
        self.url_input.setMinimumHeight(60)
        url_layout.addWidget(self.url_input)
        url_buttons = QHBoxLayout()
        self.btn_limpiar_url = QPushButton(f"{ICONOS['limpiar']} Limpiar")
        self.btn_limpiar_url.clicked.connect(lambda: self.url_input.clear())
        self.btn_limpiar_url.setFixedWidth(100)
        url_buttons.addWidget(self.btn_limpiar_url)
        self.btn_pegar = QPushButton(f"{ICONOS['pegar']} Pegar")
        self.btn_pegar.clicked.connect(self.pegar_url)
        self.btn_pegar.setFixedWidth(100)
        url_buttons.addWidget(self.btn_pegar)
        url_layout.addLayout(url_buttons)
        simple_layout.addWidget(url_group)
        self.btn_extract = QPushButton(f"{ICONOS['extraer']} Extraer comentarios")
        self.btn_extract.setEnabled(False)
        self.btn_extract.clicked.connect(self.iniciar_extraccion)
        self.btn_extract.setMinimumHeight(50)
        simple_layout.addWidget(self.btn_extract)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(25)
        simple_layout.addWidget(self.progress_bar)
        log_group = QGroupBox(f"{ICONOS['pagina']} Progreso")
        log_layout = QVBoxLayout(log_group)
        log_buttons = QHBoxLayout()
        self.btn_limpiar_log = QPushButton(f"{ICONOS['limpiar']} Limpiar")
        self.btn_limpiar_log.clicked.connect(lambda: self.log_area.clear())
        self.btn_limpiar_log.setFixedWidth(100)
        log_buttons.addWidget(self.btn_limpiar_log)
        self.btn_guardar_log = QPushButton(f"{ICONOS['guardar']} Guardar log")
        self.btn_guardar_log.clicked.connect(self.guardar_log)
        self.btn_guardar_log.setFixedWidth(100)
        log_buttons.addWidget(self.btn_guardar_log)
        log_layout.addLayout(log_buttons)
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMinimumHeight(200)
        log_layout.addWidget(self.log_area)
        simple_layout.addWidget(log_group)
        self.tab_widget.addTab(tab_simple, f"{ICONOS['extraer']} Extracción simple")
        
        # Pestaña lotes
        tab_batch = QWidget()
        batch_layout = QVBoxLayout(tab_batch)
        batch_layout.setSpacing(15)
        batch_layout.addWidget(QLabel("📄 Crea un archivo de texto (.txt) con una URL por línea"))
        file_group = QGroupBox(f"{ICONOS['carpeta']} Archivo con URLs")
        file_hlayout = QHBoxLayout(file_group)
        self.batch_file_label = QLabel("Ningún archivo seleccionado")
        self.batch_file_label.setStyleSheet("padding: 10px; background: #3c3c3c; border-radius: 5px;")
        self.batch_file_label.setWordWrap(True)
        file_hlayout.addWidget(self.batch_file_label, 2)
        self.btn_select_file = QPushButton(f"{ICONOS['carpeta']} Seleccionar archivo")
        self.btn_select_file.setFixedWidth(150)
        self.btn_select_file.clicked.connect(self.seleccionar_archivo_lotes)
        file_hlayout.addWidget(self.btn_select_file)
        batch_layout.addWidget(file_group)
        self.batch_url_list = QListWidget()
        self.batch_url_list.setMinimumHeight(120)
        batch_layout.addWidget(self.batch_url_list)
        self.batch_progress_bar = QProgressBar()
        self.batch_progress_bar.setVisible(False)
        self.batch_progress_bar.setMinimumHeight(25)
        batch_layout.addWidget(self.batch_progress_bar)
        self.batch_btn_extract = QPushButton(f"{ICONOS['lotes']} Extraer todas las URLs")
        self.batch_btn_extract.setEnabled(False)
        self.batch_btn_extract.clicked.connect(self.iniciar_extraccion_lotes)
        self.batch_btn_extract.setMinimumHeight(50)
        batch_layout.addWidget(self.batch_btn_extract)
        self.batch_log_area = QTextEdit()
        self.batch_log_area.setReadOnly(True)
        self.batch_log_area.setMinimumHeight(200)
        batch_layout.addWidget(self.batch_log_area)
        self.tab_widget.addTab(tab_batch, f"{ICONOS['lotes']} Extracción por lotes")
        
        self.status_label = QLabel(f"{ICONOS['ok']} Listo")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #4CAF50; padding: 5px; font-weight: bold;")
        layout.addWidget(self.status_label)
        self.aplicar_tema()
    
    def aplicar_tema(self):
        if self.tema_oscuro:
            self.setStyleSheet("""
                QMainWindow, QWidget { background-color: #2b2b2b; }
                QGroupBox { color: #ffffff; border: 2px solid #555; border-radius: 8px; margin-top: 10px; padding-top: 10px; background-color: #2b2b2b; }
                QGroupBox::title { color: #ffffff; }
                QLabel { color: #ffffff; }
                QLineEdit, QListWidget { background: #3c3c3c; color: white; border: 2px solid #555; border-radius: 5px; padding: 8px; }
                QPushButton { background-color: #4CAF50; color: white; border: none; border-radius: 5px; padding: 10px; font-weight: bold; }
                QPushButton:hover { background-color: #45a049; }
                QPushButton:disabled { background-color: #666; }
                QProgressBar { border: 2px solid #555; border-radius: 5px; color: white; background: #3c3c3c; text-align: center; }
                QProgressBar::chunk { background-color: #4CAF50; }
                QTextEdit, QTextBrowser { background: #1e1e1e; color: #d4d4d4; border: 1px solid #555; border-radius: 5px; }
                QTabWidget::pane { background: #2b2b2b; }
                QTabBar::tab { background: #3c3c3c; color: white; padding: 8px 20px; }
                QTabBar::tab:selected { background: #4CAF50; }
                QMenuBar { background-color: #3c3c3c; color: white; }
                QMenuBar::item { color: white; }
                QMenu { background-color: #3c3c3c; color: white; }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow, QWidget { background-color: #f0f0f0; }
                QGroupBox { color: #333333; border: 2px solid #ccc; border-radius: 8px; margin-top: 10px; padding-top: 10px; background-color: #f0f0f0; }
                QGroupBox::title { color: #333333; }
                QLabel { color: #333333; }
                QLineEdit, QListWidget { background: white; color: #333333; border: 2px solid #ccc; border-radius: 5px; padding: 8px; }
                QPushButton { background-color: #4CAF50; color: white; border: none; border-radius: 5px; padding: 10px; font-weight: bold; }
                QPushButton:hover { background-color: #45a049; }
                QProgressBar { border: 2px solid #ccc; border-radius: 5px; color: #333333; background: white; text-align: center; }
                QProgressBar::chunk { background-color: #4CAF50; }
                QTextEdit, QTextBrowser { background: white; color: #333333; border: 1px solid #ccc; border-radius: 5px; }
                QTabWidget::pane { background: #f0f0f0; }
                QTabBar::tab { background: #e0e0e0; color: #333333; padding: 8px 20px; }
                QTabBar::tab:selected { background: #4CAF50; color: white; }
                QMenuBar { background-color: #e0e0e0; color: #333333; }
                QMenuBar::item { color: #333333; }
                QMenu { background-color: #e0e0e0; color: #333333; }
            """)
    
    def toggle_tema(self):
        self.tema_oscuro = not self.tema_oscuro
        self.btn_tema.setText("🌙 Oscuro" if self.tema_oscuro else "☀️ Claro")
        self.aplicar_tema()
        cfg = self.config.cargar_configuracion()
        cfg["tema"] = "oscuro" if self.tema_oscuro else "claro"
        self.config._guardar_configuracion(cfg)
    
    def abrir_visor(self):
        if self.ultimos_comentarios and len(self.ultimos_comentarios) > 0:
            visor = VisorComentariosDialog(self.ultimos_comentarios, f"Noticia {self.ultimo_id}", self)
            visor.exec_()
        else:
            QMessageBox.information(self, "Visor", "No hay comentarios cargados. Extrae una noticia primero.")
    
    def mostrar_acerca_de(self):
        QMessageBox.about(self, "Acerca de Comentia",
            "📝 Comentia - Extractor de comentarios de Marca.com\n\n"
            "Versión: 3.0\n\n"
            "Desarrollado por H0nt3\n"
            "https://github.com/H0nt3/Comentia\n\n"
            "Licencia MIT\n\n"
            "Permite extraer y analizar comentarios de Marca.com")
    
    def seleccionar_directorio(self):
        d = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta", str(Path.home()))
        if d:
            self.directorio = Path(d)
            self.dir_label.setText(str(self.directorio))
            self.config.guardar_ultimo_directorio(str(self.directorio))
            self.btn_extract.setEnabled(True)
            self.log_area.append(f"{ICONOS['ok']} Carpeta: {self.directorio}")
    
    def pegar_url(self):
        self.url_input.setText(QApplication.clipboard().text())
        self.status_label.setText(f"{ICONOS['ok']} URL pegada")
    
    def seleccionar_archivo_lotes(self):
        archivo, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo", str(Path.home()), "Archivos de texto (*.txt);;Todos los archivos (*)")
        if archivo:
            self.batch_file_label.setText(archivo)
            self.batch_url_list.clear()
            urls = []
            with open(archivo, "r", encoding="utf-8-sig") as f:
                for line in f:
                    url = line.strip()
                    if url and not url.startswith('#'):
                        self.batch_url_list.addItem(QListWidgetItem(url))
                        urls.append(url)
            self.batch_urls = urls
            self.batch_btn_extract.setEnabled(bool(self.directorio and urls))
            self.batch_log_area.append(f"{ICONOS['ok']} Cargadas {len(urls)} URLs")
    
    def iniciar_extraccion(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Introduce la URL de la noticia")
            return
        if not self.directorio:
            QMessageBox.warning(self, "Error", "Selecciona una carpeta de destino")
            return
        self.btn_extract.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.log_area.clear()
        self.status_label.setText("⏳ Extrayendo comentarios...")
        self.config.guardar_ultimas_urls(url)
        self.extraction_thread = ExtractionThread(url, self.directorio)
        self.extraction_thread.log_signal.connect(self.agregar_log)
        self.extraction_thread.progress_signal.connect(self.actualizar_progreso)
        self.extraction_thread.finished_signal.connect(self.extraccion_finalizada)
        self.extraction_thread.error_signal.connect(self.extraccion_error)
        self.extraction_thread.start()
    
    def iniciar_extraccion_lotes(self):
        if not hasattr(self, 'batch_urls') or not self.batch_urls:
            QMessageBox.warning(self, "Error", "Carga un archivo con URLs primero")
            return
        if not self.directorio:
            QMessageBox.warning(self, "Error", "Selecciona una carpeta de destino")
            return
        self.batch_btn_extract.setEnabled(False)
        self.batch_progress_bar.setVisible(True)
        self.batch_progress_bar.setMaximum(len(self.batch_urls))
        self.batch_progress_bar.setValue(0)
        self.batch_log_area.clear()
        self.status_label.setText("⏳ Extrayendo lotes...")
        self.batch_thread = BatchExtractionThread(self.batch_urls, self.directorio)
        self.batch_thread.log_signal.connect(lambda m: self.batch_log_area.append(m))
        self.batch_thread.batch_progress_signal.connect(lambda a, t, u: self.batch_progress_bar.setValue(a))
        self.batch_thread.finished_signal.connect(self.extraccion_lotes_finalizada)
        self.batch_thread.error_signal.connect(self.extraccion_error)
        self.batch_thread.start()
    
    def agregar_log(self, mensaje: str):
        self.log_area.append(mensaje)
        self.log_area.verticalScrollBar().setValue(self.log_area.verticalScrollBar().maximum())
    
    def actualizar_progreso(self, actual: int, total: int):
        if total > 0:
            porcentaje = int((actual / total) * 100)
            self.progress_bar.setValue(porcentaje)
            self.progress_bar.setFormat(f"{actual}/{total} comentarios ({porcentaje}%)")
    
    def extraccion_finalizada(self, comentarios: dict, total: int, errores: list, noticia_id: str):
        self.btn_extract.setEnabled(True)
        self.progress_bar.setVisible(False)
        obtenidos = len(comentarios)
        
        # Guardar comentarios para el visor
        self.ultimos_comentarios = sorted(comentarios.values(), key=lambda x: x["order"])
        self.ultimo_id = noticia_id
        
        exito = obtenidos >= total * 0.95 if total > 0 else obtenidos > 0
        
        if exito:
            self.status_label.setText(f"{ICONOS['ok']} ¡Éxito! {obtenidos}/{total} comentarios")
            self.status_label.setStyleSheet("color: #4CAF50; padding: 5px; font-weight: bold;")
            
            # Preguntar si quiere ver el visor
            reply = QMessageBox.question(
                self, "Visor de comentarios",
                f"¿Quieres abrir el visor de los {obtenidos} comentarios?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                visor = VisorComentariosDialog(self.ultimos_comentarios, f"Noticia {noticia_id}", self)
                visor.exec_()
            
            QMessageBox.information(
                self, "Operación completada",
                f"{ICONOS['ok']} Extracción finalizada\n\n"
                f"Comentarios: {obtenidos}/{total}\n"
                f"Ubicación: {self.directorio / f'noticia_{noticia_id}'}"
            )
        else:
            self.status_label.setText(f"{ICONOS['error']} {obtenidos}/{total} comentarios - Con errores")
            self.status_label.setStyleSheet("color: #f44336; padding: 5px; font-weight: bold;")
            msg = f"{ICONOS['error']} Operación con errores\n\n{obtenidos}/{total} comentarios"
            if errores:
                msg += "\n\n" + "\n".join(errores[:5])
            QMessageBox.warning(self, "Operación con errores", msg)
    
    def extraccion_lotes_finalizada(self, resultados: list):
        self.batch_btn_extract.setEnabled(True)
        self.batch_progress_bar.setVisible(False)
        exitosos = sum(1 for r in resultados if r.get("exito"))
        fallidos = len(resultados) - exitosos
        
        self.status_label.setText(f"{ICONOS['ok']} Lotes: {exitosos} éxitos, {fallidos} fallos")
        self.status_label.setStyleSheet("color: #4CAF50; padding: 5px; font-weight: bold;")
        
        QMessageBox.information(
            self, "Extracción por lotes",
            f"📊 Resumen\n\n{ICONOS['ok']} Exitosos: {exitosos}\n{ICONOS['error']} Fallidos: {fallidos}\n📁 {self.directorio}"
        )
    
    def extraccion_error(self, error: str):
        self.btn_extract.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"{ICONOS['error']} Error")
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