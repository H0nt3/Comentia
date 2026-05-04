#!/usr/bin/env python3
"""
Extractor de comentarios de Marca.com
Versión: 2.0 (Robusta y optimizada)
Características:
- Extracción automática del ID desde URL
- Paginación inteligente con detección de huecos
- Sistema de reintentos para comentarios perdidos
- Progreso visual y logs detallados
- Manejo de errores robusto
- Sin duplicados
- Genera archivo de estadísticas en texto plano
"""

import requests
import json
import re
import time
from typing import Dict, List, Optional, Set, Tuple
from collections import OrderedDict
from datetime import datetime

# ========================
# CONFIGURACIÓN
# ========================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-ES,es;q=0.9",
    "Referer": "https://www.marca.com/"
}

DELAY_ENTRE_PAGINAS = 0.3  # Segundos entre peticiones
MAX_REINTENTOS = 3  # Reintentos por página fallida
TIMEOUT = 15  # Timeout por petición


# ========================
# EXTRACCIÓN DEL ID
# ========================
def extraer_id_noticia(entrada: str) -> Optional[str]:
    """
    Extrae el ID de la noticia desde URL o devuelve el ID si ya lo es.
    """
    # Si ya es un ID numérico
    if entrada.isdigit():
        return entrada
    
    # Intentar extraer de URL
    print("🔎 Extrayendo ID desde la URL...")
    
    try:
        # Método 1: Patrones comunes en URL
        patrones_url = [
            r'/noticia[/-](\d+)',
            r'/comentarios[/-](\d+)',
            r'noticia=(\d+)',
            r'/(\d{6,})/'
        ]
        
        for patron in patrones_url:
            match = re.search(patron, entrada)
            if match:
                print(f"✅ ID encontrado en URL: {match.group(1)}")
                return match.group(1)
        
        # Método 2: Descargar HTML y buscar en metadatos
        print("🌐 Descargando página para buscar el ID...")
        response = requests.get(entrada, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        html = response.text
        
        # Buscar commentId en JSON embebido
        patrones_html = [
            r'"commentId"\s*:\s*"(\d+)"',
            r'commentId["\']?\s*[:=]\s*["\']?(\d+)',
            r'data-noticia=["\'](\d+)',
            r'/comentarios/(\d+)'
        ]
        
        for patron in patrones_html:
            match = re.search(patron, html)
            if match:
                print(f"✅ ID encontrado en HTML: {match.group(1)}")
                return match.group(1)
        
        # Método 3: Buscar cualquier número de 6+ dígitos (último recurso)
        numeros = re.findall(r'\b(\d{6,})\b', html)
        if numeros:
            # Tomar el número más frecuente o el primero
            from collections import Counter
            id_candidato = Counter(numeros).most_common(1)[0][0]
            print(f"⚠️ ID candidato (modo fallback): {id_candidato}")
            return id_candidato
        
        print("❌ No se pudo encontrar el ID de la noticia")
        return None
        
    except Exception as e:
        print(f"❌ Error al extraer ID: {e}")
        return None


# ========================
# PETICIÓN CON REINTENTOS
# ========================
def peticion_segura(noticia_id: str, pagina: Optional[int] = None) -> Optional[dict]:
    """
    Realiza petición a la API con reintentos automáticos.
    """
    url = "https://www.marca.com/servicios/noticias/comentarios/comunidad/listar.html"
    
    params = {
        "noticia": noticia_id,
        "version": "v2"
    }
    
    if pagina is not None:
        params["pagina"] = pagina
    
    for intento in range(MAX_REINTENTOS):
        try:
            response = requests.get(
                url, 
                params=params, 
                headers=HEADERS, 
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                print(f"  ⚠️ Página no encontrada: {pagina}")
                return None
            else:
                print(f"  ⚠️ Error HTTP {response.status_code} (intento {intento+1}/{MAX_REINTENTOS})")
                
        except requests.exceptions.Timeout:
            print(f"  ⚠️ Timeout (intento {intento+1}/{MAX_REINTENTOS})")
        except requests.exceptions.ConnectionError:
            print(f"  ⚠️ Error de conexión (intento {intento+1}/{MAX_REINTENTOS})")
        except Exception as e:
            print(f"  ⚠️ Error inesperado: {e} (intento {intento+1}/{MAX_REINTENTOS})")
        
        if intento < MAX_REINTENTOS - 1:
            time.sleep(DELAY_ENTRE_PAGINAS * 2)
    
    print(f"  ❌ Fallo definitivo para página: {pagina}")
    return None


# ========================
# DESCARGA PRINCIPAL
# ========================
def descargar_comentarios(noticia_id: str) -> Tuple[Dict[int, dict], int]:
    """
    Descarga todos los comentarios usando paginación secuencial.
    Retorna: (diccionario {order: comentario}, total_esperado)
    """
    comentarios = {}  # Usamos dict para evitar duplicados automáticamente
    ultimo_order = None
    total_esperado = None
    page_num = 1
    
    print("\n⬇️ Iniciando descarga principal...")
    print("-" * 50)
    
    while True:
        print(f"📄 Descargando página {page_num}...", end=" ")
        
        # Obtener página actual
        data = peticion_segura(noticia_id, ultimo_order)
        
        if not data:
            print("❌ Sin datos")
            break
        
        # Obtener total esperado (solo primera vez)
        if total_esperado is None:
            total_esperado = data.get("total", 0)
            print(f"(Total esperado: {total_esperado} comentarios)")
        
        items = data.get("items", [])
        
        if not items:
            print("⚠️ Página vacía")
            break
        
        # Procesar comentarios
        nuevos = 0
        for item in items:
            order = item.get("order")
            if order and order not in comentarios:
                comentarios[order] = {
                    "id": item.get("id"),
                    "order": order,
                    "user": item.get("user"),
                    "avatar": item.get("avatar", ""),
                    "body": item.get("body"),
                    "date": item.get("date"),
                    "time": item.get("time"),
                    "references": item.get("references", [])
                }
                nuevos += 1
        
        # Mostrar progreso visual
        porc = (len(comentarios) / total_esperado * 100) if total_esperado else 0
        barra = "█" * int(porc / 5) + "░" * (20 - int(porc / 5))
        print(f"+{nuevos} | Total: {len(comentarios)}/{total_esperado} | {barra} {porc:.1f}%")
        
        # Verificar si es la última página
        if data.get("lastPage", False):
            print("🏁 Última página alcanzada")
            break
        
        # Actualizar para siguiente página
        if items:
            ultimo_order = items[-1]["order"]
        
        page_num += 1
        time.sleep(DELAY_ENTRE_PAGINAS)
    
    print("-" * 50)
    return comentarios, total_esperado or 0


# ========================
# DETECCIÓN Y RELLENO DE HUECOS
# ========================
def detectar_huecos(comentarios: Dict[int, dict], total_esperado: int) -> List[int]:
    """
    Detecta números de order faltantes.
    """
    if not comentarios:
        return []
    
    orders_existentes = set(comentarios.keys())
    max_order = max(orders_existentes)
    min_order = min(orders_existentes)
    
    # Generar todos los órdenes esperados (del más bajo al más alto)
    orders_esperados = set(range(min_order, max_order + 1))
    huecos = sorted(orders_esperados - orders_existentes)
    
    if huecos:
        print(f"\n⚠️ Detectados {len(huecos)} huecos en la secuencia:")
        # Agrupar huecos consecutivos para mostrar
        rangos = []
        inicio = huecos[0]
        fin = huecos[0]
        for h in huecos[1:]:
            if h == fin + 1:
                fin = h
            else:
                rangos.append(f"{inicio}-{fin}" if inicio != fin else str(inicio))
                inicio = fin = h
        rangos.append(f"{inicio}-{fin}" if inicio != fin else str(inicio))
        print(f"  Rangos faltantes: {', '.join(rangos[:5])}{'...' if len(rangos) > 5 else ''}")
    
    return huecos


def rellenar_huecos(noticia_id: str, huecos: List[int], comentarios_actuales: Dict[int, dict]) -> Dict[int, dict]:
    """
    Intenta rellenar los huecos descargando páginas específicas.
    """
    if not huecos:
        return comentarios_actuales
    
    print("\n🔁 Intentando rellenar huecos...")
    print("-" * 50)
    
    comentarios = comentarios_actuales.copy()
    nuevos_encontrados = 0
    
    # Probar cada hueco individualmente
    for i, order_hueco in enumerate(huecos, 1):
        print(f"🔍 Intentando recuperar order {order_hueco} ({i}/{len(huecos)})...", end=" ")
        
        data = peticion_segura(noticia_id, order_hueco)
        
        if not data:
            print("❌ No disponible")
            continue
        
        items = data.get("items", [])
        
        if not items:
            print("❌ Sin comentarios")
            continue
        
        # Buscar el comentario específico
        encontrado = False
        for item in items:
            if item.get("order") == order_hueco:
                comentarios[order_hueco] = {
                    "id": item.get("id"),
                    "order": order_hueco,
                    "user": item.get("user"),
                    "avatar": item.get("avatar", ""),
                    "body": item.get("body"),
                    "date": item.get("date"),
                    "time": item.get("time"),
                    "references": item.get("references", [])
                }
                encontrado = True
                nuevos_encontrados += 1
                print(f"✅ Recuperado!")
                break
        
        if not encontrado:
            # Buscar cualquier comentario en esta página
            for item in items:
                order_item = item.get("order")
                if order_item and order_item not in comentarios:
                    comentarios[order_item] = {
                        "id": item.get("id"),
                        "order": order_item,
                        "user": item.get("user"),
                        "avatar": item.get("avatar", ""),
                        "body": item.get("body"),
                        "date": item.get("date"),
                        "time": item.get("time"),
                        "references": item.get("references", [])
                    }
                    nuevos_encontrados += 1
                    print(f"✅ Recuperado comentario alternativo (order {order_item})")
                    encontrado = True
                    break
        
        if not encontrado:
            print("❌ No encontrado")
        
        time.sleep(DELAY_ENTRE_PAGINAS)
    
    print("-" * 50)
    print(f"✨ Recuperados {nuevos_encontrados} comentarios adicionales")
    
    return comentarios


# ========================
# EXPORTACIÓN A JSON
# ========================
def exportar_comentarios(comentarios_dict: Dict[int, dict], noticia_id: str, url_noticia: str = "", incluir_huecos: bool = False):
    """
    Exporta los comentarios a JSON con múltiples formatos.
    """
    # Ordenar por order (ascendente = cronológico)
    comentarios_lista = sorted(comentarios_dict.values(), key=lambda x: x["order"])
    
    # Preparar datos
    datos_exportar = {
        "metadata": {
            "noticia_id": noticia_id,
            "url_noticia": url_noticia,
            "total_comentarios": len([c for c in comentarios_lista if "missing" not in c]),
            "fecha_exportacion": time.strftime("%Y-%m-%d %H:%M:%S"),
            "fuente": "Marca.com"
        },
        "comentarios": comentarios_lista
    }
    
    # Guardar archivo principal
    archivo_principal = f"comentarios_{noticia_id}.json"
    with open(archivo_principal, "w", encoding="utf-8") as f:
        json.dump(datos_exportar, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Comentarios guardados en: {archivo_principal}")
    
    # Guardar versión simplificada (solo texto)
    archivo_texto = f"comentarios_{noticia_id}_texto.json"
    comentarios_simples = [
        {
            "order": c["order"],
            "usuario": c["user"],
            "comentario": c["body"],
            "fecha": f"{c['date']} {c['time']}"
        }
        for c in comentarios_lista
    ]
    
    with open(archivo_texto, "w", encoding="utf-8") as f:
        json.dump(comentarios_simples, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Versión simplificada guardada en: {archivo_texto}")


# ========================
# GENERAR ESTADÍSTICAS EN TXT
# ========================
def generar_estadisticas_txt(noticia_id: str, url_noticia: str, comentarios_dict: Dict[int, dict], 
                             total_esperado: int, huecos: List[int], tiempo_ejecucion: float):
    """
    Genera un archivo de texto con estadísticas detalladas de la extracción.
    """
    comentarios_reales = [c for c in comentarios_dict.values() if "missing" not in c]
    total_obtenidos = len(comentarios_reales)
    
    # Calcular estadísticas adicionales
    usuarios = {}
    fechas = {}
    palabras_clave = {}
    comentarios_con_referencias = 0
    
    for c in comentarios_reales:
        # Contar por usuario
        user = c.get("user", "anónimo")
        usuarios[user] = usuarios.get(user, 0) + 1
        
        # Contar por fecha
        fecha = c.get("date", "desconocida")
        fechas[fecha] = fechas.get(fecha, 0) + 1
        
        # Contar referencias
        if c.get("references") and len(c.get("references", [])) > 0:
            comentarios_con_referencias += 1
    
    # Top usuarios
    top_usuarios = sorted(usuarios.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Longitud promedio de comentarios
    longitudes = [len(c.get("body", "")) for c in comentarios_reales]
    longitud_promedio = sum(longitudes) / len(longitudes) if longitudes else 0
    
    # Porcentaje de éxito
    porcentaje_exito = (total_obtenidos / total_esperado * 100) if total_esperado > 0 else 0
    
    # Nombre del archivo
    archivo_estadisticas = f"comentarios_{noticia_id}_estadisticas.txt"
    
    with open(archivo_estadisticas, "w", encoding="utf-8") as f:
        # Cabecera
        f.write("=" * 80 + "\n")
        f.write("ESTADÍSTICAS DE COMENTARIOS - MARCA.COM\n")
        f.write("=" * 80 + "\n\n")
        
        # Información de la noticia
        f.write("📰 INFORMACIÓN DE LA NOTICIA\n")
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
            # Mostrar primeros 20 huecos
            huecos_mostrar = huecos[:20]
            f.write(f"Huecos (primeros 20): {', '.join(map(str, huecos_mostrar))}\n")
            if len(huecos) > 20:
                f.write(f"... y {len(huecos) - 20} huecos más\n")
        f.write("\n")
        
        # Estadísticas de usuarios
        f.write("👥 ESTADÍSTICAS DE USUARIOS\n")
        f.write("-" * 40 + "\n")
        f.write(f"Total de usuarios únicos: {len(usuarios)}\n")
        f.write(f"Promedio de comentarios por usuario: {total_obtenidos / len(usuarios):.2f}\n\n")
        f.write("TOP 10 USUARIOS MÁS ACTIVOS:\n")
        for i, (user, count) in enumerate(top_usuarios, 1):
            f.write(f"  {i:2}. {user:<20} - {count:3} comentarios ({count/total_obtenidos*100:.1f}%)\n")
        f.write("\n")
        
        # Estadísticas de fechas
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
        f.write(f"Comentario más corto: {min(longitudes)} caracteres\n")
        f.write(f"Comentario más largo: {max(longitudes)} caracteres\n")
        f.write(f"Comentarios con referencias: {comentarios_con_referencias}\n")
        f.write(f"Total de referencias: {sum(len(c.get('references', [])) for c in comentarios_reales)}\n\n")
        
        # Información técnica
        f.write("⚙️ INFORMACIÓN TÉCNICA\n")
        f.write("-" * 40 + "\n")
        f.write(f"Archivos generados:\n")
        f.write(f"  • comentarios_{noticia_id}.json\n")
        f.write(f"  • comentarios_{noticia_id}_texto.json\n")
        f.write(f"  • {archivo_estadisticas}\n")
        f.write(f"Versión del extractor: 2.0\n")
        f.write(f"Delay entre peticiones: {DELAY_ENTRE_PAGINAS}s\n")
        f.write(f"Timeout: {TIMEOUT}s\n")
        f.write(f"Máximo reintentos: {MAX_REINTENTOS}\n")
        
        # Pie de página
        f.write("\n" + "=" * 80 + "\n")
        f.write("Estadísticas generadas automáticamente por el extractor de comentarios de Marca.com\n")
        f.write("=" * 80 + "\n")
    
    print(f"💾 Estadísticas guardadas en: {archivo_estadisticas}")
    return archivo_estadisticas


# ========================
# VERIFICACIÓN FINAL
# ========================
def verificacion_final(comentarios: Dict[int, dict], total_esperado: int) -> bool:
    """
    Verifica si se obtuvieron todos los comentarios esperados.
    """
    obtenidos = len([c for c in comentarios.values() if "missing" not in c])
    
    print("\n" + "=" * 50)
    print("📈 RESUMEN FINAL")
    print("=" * 50)
    print(f"✅ Comentarios obtenidos: {obtenidos}")
    print(f"📋 Total esperado según API: {total_esperado}")
    
    if obtenidos >= total_esperado:
        print("🎉 ¡Éxito! Se obtuvieron todos los comentarios")
        return True
    else:
        perdidos = total_esperado - obtenidos
        print(f"⚠️ Advertencia: Faltan {perdidos} comentarios ({perdidos/total_esperado*100:.1f}%)")
        print("💡 Posibles causas:")
        print("   • Comentarios eliminados por moderación")
        print("   • Usuarios bloqueados o baneados")
        print("   • API de Marca con paginación inconsistente")
        return False


# ========================
# FUNCIÓN PRINCIPAL
# ========================
def main():
    print("=" * 60)
    print("🚀 EXTRACTOR DE COMENTARIOS - MARCA.COM")
    print("=" * 60)
    
    # Solicitar entrada al usuario
    entrada = input("\n📝 Introduce URL o ID de la noticia: ").strip()
    
    if not entrada:
        print("❌ No se introdujo ningún valor")
        return
    
    # Guardar URL original (si es URL)
    url_original = entrada if not entrada.isdigit() else ""
    
    # Extraer ID
    noticia_id = extraer_id_noticia(entrada)
    
    if not noticia_id:
        print("❌ No se pudo obtener el ID de la noticia")
        print("💡 Asegúrate de que la URL sea correcta y la noticia exista")
        return
    
    print(f"\n✅ Noticia ID: {noticia_id}")
    
    # Iniciar temporizador
    tiempo_inicio = time.time()
    
    # Descargar comentarios
    comentarios_dict, total_esperado = descargar_comentarios(noticia_id)
    
    # Detectar y rellenar huecos
    huecos = detectar_huecos(comentarios_dict, total_esperado)
    
    if huecos:
        comentarios_dict = rellenar_huecos(noticia_id, huecos, comentarios_dict)
        # Volver a detectar huecos después del relleno
        huecos_restantes = detectar_huecos(comentarios_dict, total_esperado)
        if huecos_restantes:
            print(f"\n⚠️ Quedan {len(huecos_restantes)} huecos sin rellenar")
        huecos = huecos_restantes if huecos_restantes else []
    
    # Calcular tiempo de ejecución
    tiempo_ejecucion = time.time() - tiempo_inicio
    
    # Verificar resultado
    verificacion_final(comentarios_dict, total_esperado)
    
    # Exportar resultados
    exportar_comentarios(comentarios_dict, noticia_id, url_original)
    
    # Generar estadísticas en TXT
    generar_estadisticas_txt(noticia_id, url_original, comentarios_dict, 
                            total_esperado, huecos, tiempo_ejecucion)
    
    print("\n✨ Proceso completado con éxito ✨")


# ========================
# EJECUCIÓN
# ========================
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Proceso interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()