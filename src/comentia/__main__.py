#!/usr/bin/env python3
"""Punto de entrada principal de Comentia."""

import sys
import argparse
from .core import extraer_comentarios_cli
from .gui_tkinter import main_gui

def main():
    """Función principal que decide entre CLI y GUI."""
    parser = argparse.ArgumentParser(
        prog="comentia",
        description="Comentia - Extractor de comentarios de Marca.com"
    )
    parser.add_argument(
        "--cli", "-c",
        action="store_true",
        help="Usar modo consola (sin interfaz gráfica)"
    )
    parser.add_argument(
        "url",
        nargs="?",
        help="URL de la noticia (opcional, se pedirá si no se proporciona)"
    )

    args = parser.parse_args()

    if args.cli:
        extraer_comentarios_cli(args.url)
    else:
        main_gui()

if __name__ == "__main__":
    main()