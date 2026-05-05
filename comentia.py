#!/usr/bin/env python3
"""
Comentia - Extractor de comentarios de Marca.com
Versión: 3.0 (Optimizada)
"""

import requests
import json
import re
import time
import os
import sys
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
from collections import Counter

# Intentar importar tkinter
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
    TKINTER_DISPONIBLE = True
except ImportError:
    TKINTER_DISPONIBLE = False

# ========================
# CONFIGURACIÓN
# ========================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-ES,es;q=0.9",
    "Referer": "https://www.marca.com/"
}

DELAY_ENTRE_PAGINAS = 0.3
MAX_REINTENTOS = 3
TIMEOUT = 15


# ========================
# SELECTOR GRÁFICO DE DIRECTORIO
# ========================
class SelectorDirectorio:
    def __init__(self):
        self.ruta_seleccionada = None
        self.root = None
    
    def mostrar(self) -> Path:
        """Muestra ventana de selección de directorio"""
        if not TKINTER_DISPONIBLE:
            return self._selector_consola()
        
        self.root = tk.Tk()
        self.root.title("Comentia - Seleccionar directorio")
        self.root.geometry("500x360")
        self.root.resizable(False, False)
        self.root.configure(bg='#2b2b2b')
        self.root.eval('tk::PlaceWindow . center')
        
        # Configurar grid
        self.root.grid_rowconfigure(0, weight=0)
        self.root.grid_rowconfigure(1, weight=0)
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_rowconfigure(3, weight=0)
        self.root.grid_rowconfigure(4, weight=0)
        self.root.grid_rowconfigure(5, weight=0)
        self.root.grid_rowconfigure(6, weight=0)
        self.root.grid_rowconfigure(7, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Título
        titulo = tk.Label(self.root, text="📝 Comentia", 
                         font=('Arial', 18, 'bold'), bg='#2b2b2b', fg='white')
        titulo.grid(row=0, column=0, pady=(20, 5))
        
        # Subtítulo
        subtitulo = tk.Label(self.root, text="Extractor de comentarios de Marca.com",
                            font=('Arial', 10), bg='#2b2b2b', fg='#888')
        subtitulo.grid(row=1, column=0, pady=(0, 20))
        
        # Botones
        btn_frame = tk.Frame(self.root, bg='#2b2b2b')
        btn_frame.grid(row=3, column=0, pady=8)
        btn_seleccionar = tk.Button(btn_frame, text="📁 Seleccionar carpeta", 
                                   command=self._seleccionar, width=30, height=2,
                                   bg='#4CAF50', fg='white', font=('Arial', 10, 'bold'))
        btn_seleccionar.pack()
        
        btn_frame2 = tk.Frame(self.root, bg='#2b2b2b')
        btn_frame2.grid(row=4, column=0, pady=8)
        btn_actual = tk.Button(btn_frame2, text="💾 Carpeta actual", 
                              command=self._usar_actual, width=30, height=2,
                              bg='#2196F3', fg='white', font=('Arial', 10))
        btn_actual.pack()
        
        btn_frame3 = tk.Frame(self.root, bg='#2b2b2b')
        btn_frame3.grid(row=5, column=0, pady=8)
        btn_escritorio = tk.Button(btn_frame3, text="🖥️ Escritorio (carpeta Comentia)", 
                                  command=self._usar_escritorio, width=30, height=2,
                                  bg='#FF9800', fg='white', font=('Arial', 10))
        btn_escritorio.pack()
        
        btn_frame4 = tk.Frame(self.root, bg='#2b2b2b')
        btn_frame4.grid(row=6, column=0, pady=8)
        btn_cancelar = tk.Button(btn_frame4, text="❌ Cancelar", 
                                command=self._cancelar, width=30, height=2,
                                bg='#f44336', fg='white', font=('Arial', 10))
        btn_cancelar.pack()
        
        self.root.mainloop()
        
        if self.ruta_seleccionada is None:
            print("❌ No se seleccionó ningún directorio. Saliendo...")
            sys.exit(0)
        
        self.ruta_seleccionada.mkdir(parents=True, exist_ok=True)
        return self.ruta_seleccionada
    
    def _seleccionar(self):
        directorio = filedialog.askdirectory(title="Selecciona dónde guardar los comentarios")
        if directorio:
            self.ruta_seleccionada = Path(directorio)
            self.root.quit()
            self.root.destroy()
    
    def _usar_actual(self):
        self.ruta_seleccionada = Path.cwd()
        self.root.quit()
        self.root.destroy()
    
    def _usar_escritorio(self):
        if os.name == 'nt':
            escritorio = Path.home() / "Desktop"
        else:
            escritorio = Path.home() / "Desktop"
            if not escritorio.exists():
                escritorio = Path.home() / "Escritorio"
        self.ruta_seleccionada = escritorio / "Comentia_comentarios"
        self.root.quit()
        self.root.destroy()
    
    def _cancelar(self):
        self.ruta_seleccionada = None
        self.root.quit()
        self.root.destroy()
    
    def _selector_consola(self) -> Path:
        print("\n" + "=" * 60)
        print("📁 SELECCIÓN DE DIRECTORIO")
        print("=" * 60)
        print("\nOpciones:")
        print("  1. Directorio actual")
        print("  2. Directorio específico")
        print("  3. Crear carpeta 'Comentia_comentarios'")
        print("  4. Escritorio")
        print("  5. Salir")
        
        while True:
            opcion = input("\nOpción (1-5): ").strip()
            if opcion == "1":
                return Path.cwd()
            elif opcion == "2":
                ruta = input("Ruta completa: ").strip()
                directorio = Path(ruta)
                directorio.mkdir(parents=True, exist_ok=True)
                return directorio
            elif opcion == "3":
                directorio = Path.cwd() / "Comentia_comentarios"
                directorio.mkdir(exist_ok=True)
                return directorio
            elif opcion == "4":
                escritorio = Path.home() / "Desktop" / "Comentia_comentarios"
                if not escritorio.exists():
                    escritorio = Path.home() / "Escritorio" / "Comentia_comentarios"
                escritorio.mkdir(parents=True, exist_ok=True)
                return escritorio
            elif opcion == "5":
                sys.exit(0)


# ========================
# EXTRACCIÓN DEL ID
# ========================
def extraer_id_noticia(entrada: str) -> Optional[str]:
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


# ========================
# PETICIÓN SEGURA
# ========================
def peticion_segura(noticia_id: str, pagina: Optional[int] = None) -> Optional[dict]:
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


# ========================
# DESCARGA PRINCIPAL
# ========================
def descargar_comentarios(noticia_id: str) -> Tuple[Dict[int, dict], int, List[str]]:
    comentarios = {}
    ultimo_order = None
    total_esperado = None
    page_num = 1
    errores = []
    
    print("\n⬇️ Descargando comentarios...")
    print("-" * 50)
    
    while True:
        print(f"📄 Página {page_num}...", end=" ")
        data = peticion_segura(noticia_id, ultimo_order)
        
        if not data:
            errores.append(f"Fallo al descargar página {page_num}")
            break
        
        if total_esperado is None:
            total_esperado = data.get("total", 0)
            print(f"(Total: {total_esperado})")
        
        items = data.get("items", [])
        if not items:
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
        
        print(f"+{nuevos} | Total: {len(comentarios)}/{total_esperado}")
        
        if data.get("lastPage"):
            break
        
        if items:
            ultimo_order = items[-1]["order"]
        
        page_num += 1
        time.sleep(DELAY_ENTRE_PAGINAS)
    
    return comentarios, total_esperado or 0, errores


# ========================
# EXPORTACIÓN A JSON
# ========================
def exportar_comentarios(comentarios_dict: Dict[int, dict], noticia_id: str, 
                        directorio: Path, url_noticia: str = "") -> Tuple[Path, Path]:
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
    
    # Archivo completo
    archivo_completo = directorio / f"comentarios_{noticia_id}_completo.json"
    with open(archivo_completo, "w", encoding="utf-8") as f:
        json.dump(datos_exportar, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Archivo completo guardado: {archivo_completo.name}")
    
    # Archivo simplificado
    archivo_simplificado = directorio / f"comentarios_{noticia_id}_simplificado.json"
    comentarios_simples = [
        {"order": c["order"], "usuario": c["user"], 
         "comentario": c["body"], "fecha": f"{c['date']} {c['time']}"}
        for c in comentarios_lista
    ]
    with open(archivo_simplificado, "w", encoding="utf-8") as f:
        json.dump(comentarios_simples, f, ensure_ascii=False, indent=2)
    print(f"💾 Archivo simplificado guardado: {archivo_simplificado.name}")
    
    return archivo_completo, archivo_simplificado


# ========================
# GENERAR ESTADÍSTICAS EN TXT
# ========================
def generar_estadisticas_txt(noticia_id: str, url_noticia: str, comentarios_dict: Dict[int, dict], 
                             total_esperado: int, huecos: List[int], tiempo_ejecucion: float,
                             directorio: Path, errores: List[str] = None) -> Path:
    """
    Genera un archivo de texto con estadísticas detalladas de la extracción.
    """
    comentarios_reales = list(comentarios_dict.values())
    total_obtenidos = len(comentarios_reales)
    
    # Calcular estadísticas
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
        
        # Contar palabras comunes
        palabras = re.findall(r'\b\w{4,}\b', c.get("body", "").lower())
        for palabra in palabras:
            if palabra not in ['como', 'cuando', 'donde', 'este', 'esta', 'esto', 'para']:
                palabras_comunes[palabra] = palabras_comunes.get(palabra, 0) + 1
    
    top_usuarios = sorted(usuarios.items(), key=lambda x: x[1], reverse=True)[:10]
    top_palabras = sorted(palabras_comunes.items(), key=lambda x: x[1], reverse=True)[:15]
    longitudes = [len(c.get("body", "")) for c in comentarios_reales]
    longitud_promedio = sum(longitudes) / len(longitudes) if longitudes else 0
    porcentaje_exito = (total_obtenidos / total_esperado * 100) if total_esperado > 0 else 0
    
    # Calcular hora pico
    horas = []
    for c in comentarios_reales:
        hora_match = re.search(r'(\d{1,2}):', c.get("time", "00:00"))
        if hora_match:
            horas.append(int(hora_match.group(1)))
    if horas:
        hora_pico = max(set(horas), key=horas.count)
    else:
        hora_pico = "No disponible"
    
    archivo_estadisticas = directorio / f"comentarios_{noticia_id}_estadisticas.txt"
    
    with open(archivo_estadisticas, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("📊 COMENTIA - ESTADÍSTICAS DE COMENTARIOS\n")
        f.write("=" * 80 + "\n\n")
        
        # Información básica de la noticia
        f.write("📰 INFORMACIÓN BÁSICA\n")
        f.write("-" * 40 + "\n")
        f.write(f"ID de la noticia: {noticia_id}\n")
        f.write(f"URL: {url_noticia if url_noticia else 'No disponible'}\n")
        f.write(f"Fecha de extracción: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Tiempo de ejecución: {tiempo_ejecucion:.2f} segundos\n\n")
        
        # Resumen de extracción
        f.write("📊 RESUMEN DE EXTRACCIÓN\n")
        f.write("-" * 40 + "\n")
        f.write(f"Total esperado según API: {total_esperado} comentarios\n")
        f.write(f"Total obtenido: {total_obtenidos} comentarios\n")
        f.write(f"Porcentaje de éxito: {porcentaje_exito:.2f}%\n")
        f.write(f"Comentarios perdidos: {total_esperado - total_obtenidos}\n")
        f.write(f"Huecos detectados: {len(huecos)}\n")
        
        if huecos:
            huecos_mostrar = huecos[:20]
            f.write(f"Huecos (primeros 20): {', '.join(map(str, huecos_mostrar))}\n")
            if len(huecos) > 20:
                f.write(f"... y {len(huecos) - 20} huecos más\n")
        f.write("\n")
        
        # Estadísticas de usuarios
        f.write("👥 ESTADÍSTICAS DE USUARIOS\n")
        f.write("-" * 40 + "\n")
        f.write(f"Total de usuarios únicos: {len(usuarios)}\n")
        if len(usuarios) > 0:
            f.write(f"Promedio de comentarios por usuario: {total_obtenidos / len(usuarios):.2f}\n\n")
        f.write("TOP 10 USUARIOS MÁS ACTIVOS:\n")
        for i, (user, count) in enumerate(top_usuarios, 1):
            f.write(f"  {i:2}. {user:<20} - {count:3} comentarios ({count/total_obtenidos*100:.1f}%)\n")
        f.write("\n")
        
        # Actividad temporal
        f.write("⏰ ACTIVIDAD TEMPORAL\n")
        f.write("-" * 40 + "\n")
        f.write(f"Hora con más comentarios: {hora_pico}:00\n\n")
        
        f.write("📅 ACTIVIDAD POR FECHA\n")
        f.write("-" * 40 + "\n")
        fechas_ordenadas = sorted(fechas.items(), key=lambda x: x[0], reverse=True)[:10]
        for fecha, count in fechas_ordenadas:
            f.write(f"  {fecha}: {count} comentarios\n")
        f.write("\n")
        
        # Métricas de contenido
        f.write("📝 MÉTRICAS DE CONTENIDO\n")
        f.write("-" * 40 + "\n")
        f.write(f"Longitud promedio de comentarios: {longitud_promedio:.0f} caracteres\n")
        if longitudes:
            f.write(f"Comentario más corto: {min(longitudes)} caracteres\n")
            f.write(f"Comentario más largo: {max(longitudes)} caracteres\n")
        f.write(f"Comentarios con referencias: {comentarios_con_referencias}\n")
        f.write(f"Total de referencias: {sum(len(c.get('references', [])) for c in comentarios_reales)}\n\n")
        
        # Palabras más utilizadas
        f.write("🔤 PALABRAS MÁS UTILIZADAS\n")
        f.write("-" * 40 + "\n")
        for i, (palabra, count) in enumerate(top_palabras[:10], 1):
            f.write(f"  {i:2}. {palabra:<15} - {count:3} veces\n")
        f.write("\n")
        
        # Archivos generados
        f.write("📁 ARCHIVOS GENERADOS\n")
        f.write("-" * 40 + "\n")
        f.write(f"• comentarios_{noticia_id}_completo.json\n")
        f.write(f"• comentarios_{noticia_id}_simplificado.json\n")
        f.write(f"• comentarios_{noticia_id}_estadisticas.txt\n\n")
        
        # Errores detectados
        if errores:
            f.write("⚠️ ERRORES DETECTADOS\n")
            f.write("-" * 40 + "\n")
            for error in errores[:5]:
                f.write(f"  • {error}\n")
            if len(errores) > 5:
                f.write(f"  • ... y {len(errores) - 5} más\n")
            f.write("\n")
        
        # Información técnica
        f.write("⚙️ INFORMACIÓN TÉCNICA\n")
        f.write("-" * 40 + "\n")
        f.write(f"Versión del extractor: 3.0\n")
        f.write(f"Delay entre peticiones: {DELAY_ENTRE_PAGINAS}s\n")
        f.write(f"Timeout: {TIMEOUT}s\n")
        f.write(f"Máximo reintentos: {MAX_REINTENTOS}\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("Estadísticas generadas automáticamente por Comentia\n")
        f.write("https://github.com/H0nt3/comentia\n")
        f.write("=" * 80 + "\n")
    
    return archivo_estadisticas


# ========================
# NOTIFICACIÓN FINAL
# ========================
class NotificacionFinal:
    @staticmethod
    def mostrar(exito: bool, mensaje: str = "", errores: List[str] = None):
        if not TKINTER_DISPONIBLE:
            if exito:
                print(f"\n✅ {mensaje}")
            else:
                print(f"\n❌ {mensaje}")
                if errores:
                    for error in errores[:3]:
                        print(f"  • {error}")
            return
        
        root = tk.Tk()
        root.title("Comentia - Resultado")
        root.geometry("400x250")
        root.resizable(False, False)
        root.configure(bg='#2b2b2b')
        root.eval('tk::PlaceWindow . center')
        
        root.grid_rowconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=0)
        root.grid_rowconfigure(2, weight=0)
        root.grid_rowconfigure(3, weight=1)
        root.grid_columnconfigure(0, weight=1)
        
        if exito:
            icono = "✅"
            color = "#4CAF50"
            titulo = "OPERACIÓN COMPLETADA"
        else:
            icono = "❌"
            color = "#f44336"
            titulo = "OPERACIÓN CON ERRORES"
        
        lbl_icono = tk.Label(root, text=icono, font=('Arial', 48), bg='#2b2b2b', fg=color)
        lbl_icono.grid(row=0, column=0, pady=(20, 0))
        
        lbl_titulo = tk.Label(root, text=titulo, font=('Arial', 14, 'bold'), bg='#2b2b2b', fg=color)
        lbl_titulo.grid(row=1, column=0, pady=(10, 5))
        
        if mensaje:
            lbl_mensaje = tk.Label(root, text=mensaje, font=('Arial', 10), 
                                   bg='#2b2b2b', fg='white', wraplength=350)
            lbl_mensaje.grid(row=2, column=0, pady=(5, 10))
        
        btn_cerrar = tk.Button(root, text="Cerrar", command=root.destroy,
                              bg=color, fg='white', font=('Arial', 10, 'bold'),
                              width=15, height=1)
        btn_cerrar.grid(row=3 if not errores else 4, column=0, pady=20)
        
        root.mainloop()


# ========================
# FUNCIÓN PRINCIPAL
# ========================
def main():
    print("=" * 60)
    print("📝 COMENTIA - Extractor de comentarios de Marca.com")
    print("=" * 60)
    
    # Seleccionar directorio
    selector = SelectorDirectorio()
    directorio_base = selector.mostrar()
    
    # Solicitar URL o ID
    entrada = input("\n📝 URL o ID de la noticia: ").strip()
    if not entrada:
        NotificacionFinal.mostrar(False, "No se introdujo ningún valor")
        return
    
    url_original = entrada if not entrada.isdigit() else ""
    noticia_id = extraer_id_noticia(entrada)
    
    if not noticia_id:
        NotificacionFinal.mostrar(False, "No se pudo obtener el ID de la noticia")
        return
    
    print(f"\n✅ ID: {noticia_id}")
    
    # Crear subcarpeta
    subdir = directorio_base / f"noticia_{noticia_id}"
    subdir.mkdir(exist_ok=True)
    
    # Descargar
    tiempo_inicio = time.time()
    comentarios_dict, total_esperado, errores_descarga = descargar_comentarios(noticia_id)
    tiempo_ejecucion = time.time() - tiempo_inicio
    
    # Detectar huecos
    if comentarios_dict:
        orders_existentes = set(comentarios_dict.keys())
        if orders_existentes:
            max_order = max(orders_existentes)
            min_order = min(orders_existentes)
            orders_esperados = set(range(min_order, max_order + 1))
            huecos = sorted(orders_esperados - orders_existentes)
        else:
            huecos = []
    else:
        huecos = []
    
    # Exportar
    exportar_comentarios(comentarios_dict, noticia_id, subdir, url_original)
    
    # Generar estadísticas (solo en archivo)
    generar_estadisticas_txt(noticia_id, url_original, comentarios_dict, 
                            total_esperado, huecos, tiempo_ejecucion, subdir, 
                            errores_descarga)
    
    print(f"\n✅ Proceso completado!")
    print(f"📁 Ubicación: {subdir}")
    
    # Verificar éxito
    exito = len(comentarios_dict) >= total_esperado * 0.95 if total_esperado > 0 else len(comentarios_dict) > 0
    mensaje = f"{len(comentarios_dict)} comentarios guardados"
    
    NotificacionFinal.mostrar(exito, mensaje, errores_descarga if not exito else None)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Proceso cancelado")
        NotificacionFinal.mostrar(False, "Proceso cancelado por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        NotificacionFinal.mostrar(False, f"Error inesperado", [str(e)])