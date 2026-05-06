#!/usr/bin/env python3
"""Configuración persistente para Comentia Qt5."""

import json
from pathlib import Path

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