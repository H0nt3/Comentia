#!/usr/bin/env python3
"""Núcleo de la lógica de extracción de comentarios."""

import requests
import json
import re
import time
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import Counter

# Configuración
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-ES,es;q=0.9",
    "Referer": "https://www.marca.com/"
}
DELAY_ENTRE_PAGINAS = 0.3
MAX_REINTENTOS = 3
TIMEOUT = 15


def extraer_id_noticia(entrada: str) -> Optional[str]:
    """Extrae el ID de la noticia desde URL o devuelve el ID si ya lo es."""
    if entrada.isdigit():
        return entrada

    # Patrones comunes en URL
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
    except Exception:
        pass

    return None


def peticion_segura(noticia_id: str, pagina: Optional[int] = None) -> Optional[dict]:
    """Realiza petición a la API con reintentos automáticos."""
    url = "https://www.marca.com/servicios/noticias/comentarios/comunidad/listar.html"
    params = {"noticia": noticia_id, "version": "v2"}
    if pagina:
        params["pagina"] = pagina

    for intento in range(MAX_REINTENTOS):
        try:
            response = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
            if response.status_code == 200:
                return response.json()
        except Exception:
            time.sleep(DELAY_ENTRE_PAGINAS)

    return None


def descargar_comentarios(noticia_id: str) -> Tuple[Dict[int, dict], int, List[str]]:
    """Descarga todos los comentarios usando paginación secuencial."""
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


def exportar_comentarios(comentarios_dict: Dict[int, dict], noticia_id: str,
                        directorio: Path, url_noticia: str = "") -> Tuple[Path, Path]:
    """Exporta los comentarios a JSON (completo y simplificado)."""
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

    return archivo_completo, archivo_simplificado


def generar_estadisticas_txt(noticia_id: str, url_noticia: str, comentarios_dict: Dict[int, dict],
                             total_esperado: int, tiempo_ejecucion: float,
                             directorio: Path, errores: List[str] = None) -> Path:
    """Genera archivo de texto con estadísticas detalladas."""
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

        palabras = re.findall(r'\b\w{4,}\b', c.get("body", "").lower())
        for palabra in palabras:
            if palabra not in ['como', 'cuando', 'donde', 'este', 'esta', 'esto', 'para']:
                palabras_comunes[palabra] = palabras_comunes.get(palabra, 0) + 1

    top_usuarios = sorted(usuarios.items(), key=lambda x: x[1], reverse=True)[:10]
    top_palabras = sorted(palabras_comunes.items(), key=lambda x: x[1], reverse=True)[:15]
    longitudes = [len(c.get("body", "")) for c in comentarios_reales]
    longitud_promedio = sum(longitudes) / len(longitudes) if longitudes else 0
    porcentaje_exito = (total_obtenidos / total_esperado * 100) if total_esperado > 0 else 0

    # Detectar huecos
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
        f.write(f"Fecha de extracción: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Tiempo de ejecución: {tiempo_ejecucion:.2f} segundos\n\n")

        f.write("📊 RESUMEN DE EXTRACCIÓN\n")
        f.write("-" * 40 + "\n")
        f.write(f"Total esperado según API: {total_esperado} comentarios\n")
        f.write(f"Total obtenido: {total_obtenidos} comentarios\n")
        f.write(f"Porcentaje de éxito: {porcentaje_exito:.2f}%\n")
        f.write(f"Comentarios perdidos: {total_esperado - total_obtenidos}\n")
        f.write(f"Huecos detectados: {len(huecos)}\n\n")

        f.write("👥 ESTADÍSTICAS DE USUARIOS\n")
        f.write("-" * 40 + "\n")
        f.write(f"Total de usuarios únicos: {len(usuarios)}\n")
        if len(usuarios) > 0:
            f.write(f"Promedio de comentarios por usuario: {total_obtenidos / len(usuarios):.2f}\n\n")
        f.write("TOP 10 USUARIOS MÁS ACTIVOS:\n")
        for i, (user, count) in enumerate(top_usuarios, 1):
            f.write(f"  {i:2}. {user:<20} - {count:3} comentarios ({count/total_obtenidos*100:.1f}%)\n")
        f.write("\n")

        f.write("📅 ACTIVIDAD POR FECHA\n")
        f.write("-" * 40 + "\n")
        for fecha, count in sorted(fechas.items(), key=lambda x: x[0], reverse=True)[:10]:
            f.write(f"  {fecha}: {count} comentarios\n")
        f.write("\n")

        f.write("📝 MÉTRICAS DE CONTENIDO\n")
        f.write("-" * 40 + "\n")
        f.write(f"Longitud promedio de comentarios: {longitud_promedio:.0f} caracteres\n")
        if longitudes:
            f.write(f"Comentario más corto: {min(longitudes)} caracteres\n")
            f.write(f"Comentario más largo: {max(longitudes)} caracteres\n")
        f.write(f"Comentarios con referencias: {comentarios_con_referencias}\n")
        f.write(f"Total de referencias: {sum(len(c.get('references', [])) for c in comentarios_reales)}\n\n")

        f.write("🔤 PALABRAS MÁS UTILIZADAS\n")
        f.write("-" * 40 + "\n")
        for i, (palabra, count) in enumerate(top_palabras[:10], 1):
            f.write(f"  {i:2}. {palabra:<15} - {count:3} veces\n")
        f.write("\n")

        f.write("📁 ARCHIVOS GENERADOS\n")
        f.write("-" * 40 + "\n")
        f.write(f"• comentarios_{noticia_id}_completo.json\n")
        f.write(f"• comentarios_{noticia_id}_simplificado.json\n")
        f.write(f"• comentarios_{noticia_id}_estadisticas.txt\n\n")

        if errores:
            f.write("⚠️ ERRORES DETECTADOS\n")
            f.write("-" * 40 + "\n")
            for error in errores[:5]:
                f.write(f"  • {error}\n")
            if len(errores) > 5:
                f.write(f"  • ... y {len(errores) - 5} más\n")
            f.write("\n")

        f.write("=" * 80 + "\n")
        f.write("Estadísticas generadas automáticamente por Comentia\n")
        f.write("https://github.com/H0nt3/Comentia\n")
        f.write("=" * 80 + "\n")

    return archivo


def extraer_comentarios_cli(url_opcional: str = None):
    """Versión CLI (consola) de la extracción."""
    print("=" * 60)
    print("📝 COMENTIA - Modo consola")
    print("=" * 60)

    if url_opcional:
        entrada = url_opcional
    else:
        entrada = input("\n📝 URL o ID de la noticia: ").strip()

    if not entrada:
        print("❌ No se introdujo ningún valor")
        return

    url_original = entrada if not entrada.isdigit() else ""
    noticia_id = extraer_id_noticia(entrada)

    if not noticia_id:
        print("❌ No se pudo obtener el ID de la noticia")
        return

    print(f"\n✅ ID: {noticia_id}")

    # Crear subcarpeta
    subdir = Path.cwd() / f"noticia_{noticia_id}"
    subdir.mkdir(exist_ok=True)

    # Descargar
    tiempo_inicio = time.time()
    comentarios_dict, total_esperado, errores = descargar_comentarios(noticia_id)
    tiempo_ejecucion = time.time() - tiempo_inicio

    # Exportar
    exportar_comentarios(comentarios_dict, noticia_id, subdir, url_original)
    generar_estadisticas_txt(noticia_id, url_original, comentarios_dict,
                            total_esperado, tiempo_ejecucion, subdir, errores)

    print(f"\n✅ Proceso completado!")
    print(f"📁 Ubicación: {subdir.absolute()}")