#!/usr/bin/env python3
"""Script CLI para Electron que llama al núcleo de Comentia."""

import sys
import json
from pathlib import Path

# Añadir el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from comentia.core import (extraer_id_noticia, descargar_comentarios,
                           exportar_comentarios, generar_estadisticas_txt)
import time

def main():
    if len(sys.argv) < 3:
        print("Uso: extractor.py <url> <directorio>")
        sys.exit(1)

    url = sys.argv[1]
    directorio = Path(sys.argv[2])

    noticia_id = extraer_id_noticia(url)
    if not noticia_id:
        print("❌ No se pudo obtener el ID")
        sys.exit(1)

    print(f"✅ ID: {noticia_id}")

    subdir = directorio / f"noticia_{noticia_id}"
    subdir.mkdir(parents=True, exist_ok=True)

    tiempo_inicio = time.time()
    comentarios, total_esperado, errores = descargar_comentarios(noticia_id)
    tiempo_ejecucion = time.time() - tiempo_inicio

    exportar_comentarios(comentarios, noticia_id, subdir, url)
    generar_estadisticas_txt(noticia_id, url, comentarios, total_esperado,
                            tiempo_ejecucion, subdir, errores)

    print(f"✅ {len(comentarios)}/{total_esperado} comentarios guardados")

if __name__ == "__main__":
    main()