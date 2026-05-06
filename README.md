# 📝 Comentia

<div align="center">

![Versión](https://img.shields.io/badge/versión-3.0.0-blue)
![Python](https://img.shields.io/badge/python-3.9+-green)
![Licencia](https://img.shields.io/badge/licencia-MIT-orange)

**Extrae todos los comentarios de cualquier noticia de Marca.com de forma sencilla y rápida**

</div>

---

## 📌 Tabla de contenidos
  * 📖 [¿Qué es Comentia?](#-qué-es-comentia)
  * ✨ [Características principales](#-características-principales)
  * 📋 [Requisitos previos](#-requisitos-previos)
  * 🚀 [Instalación](#-instalación)
  * 🧑‍💻 [Guía de Uso](#-guía-de-uso)
  * 📂 [Salida y archivos generados](#-salida-y-archivos-generados)
  * 📊 [Estadísticas](#-estadísticas)
  * 🛠️ [Estructura JSON](#-estructura-json)
  * ❓ [Preguntas Frecuentes (FAQ)](#-preguntas-frecuentes-faq)
  * 🐛 [Solución de problemas](#-solución-de-problemas)
  * 🤝 [Contribuir](#-contribuir)
  * 📄 [Licencia](#-licencia)
  * ⭐ [Soporte y Créditos](#-soporte-y-créditos)

---
<a name="qué-es-comentia"></a>
### 📖 ¿Qué es Comentia?

**Comentia** es una herramienta diseñada para fácil de usar que te permite **extraer, guardar y analizar comentarios** de cualquier noticia de **Marca.com** en tu ordenador y de forma automatizada. Solo necesitas **pegar la URL de la noticia** y Comentia se encarga del resto.

Ideal para:

* 📊 análisis de datos
* 🧠 estudios de comportamiento
* 💾 archivado de debates

---
<a name="características-principales"></a>
### ✨ Características principales

| Característica               | Descripción                                                                 |
| ---------------------------- | --------------------------------------------------------------------------- |
| 🚀 **Sencillo**              | Solo necesitas la URL de la noticia                                         |
| 💾 **Extracción completa**   | Descarga **todos** los comentarios, incluso los que están en varias páginas |
| 📁 **Organización**          | Selección de carpeta mediante una interfaz gráfica                          |
| 📊 **Estadísticas**          | Genera un informe automático con datos y metricas interesantes              |
| 🔄 **Sin duplicados**        | Detecta y evita comentarios repetidos automáticamente                       |
| 🛡️ **Robusto**               | Sistema de reintentos automático ante errores de conexión                   |
| 🎨 **Interfaz moderna**      | GUI con Qt5 + versión clásica (tkinter)                                     |
| ⚡ **Modo CLI**              | Uso desde terminal para automatización                                      |
| 📦 **Multiplataforma**       | Conpatible con Windows, macOS y Linux                                       |

---
<a name="requisitos-previos"></a>
### 📋 Requisitos previos

* **Python 3.9 o superior** ([Descargar Python](https://www.python.org/downloads/)) *(solo para versión desde código fuente)*
* Conexión a internet
* Espacio en disco: ~10 MB

---
<a name="instalación"></a>
### 🚀 Instalación

#### 🔧 Desde el código fuente

```bash
# Clonar el repositorio
git clone https://github.com/H0nt3/Comentia.git
cd Comentia

# Instalar dependencias
pip install -r requirements.txt
```
#### ▶️ Ejecutar

``` bash
# Ejecutar (GUI moderna - recomendado)
python qt_app/main.py

# GUI clásica
python -m comentia

# Modo consola
python -m comentia --cli
```

#### 📦 Ejecutable independiente

Descarga el ejecutable según tu S.O. desde **Releases**:

| Sistema Operativo | Archivo      | Ejecución    |
| ----------------- | ------------ | ------------ |
| Windows           | Comentia.exe | Doble click  |
| macOS             | Comentia.app | Doble click  |
| Linux             | Comentia     | `./Comentia` |


#### ⚡ App Electron

Ejecuta el archivo **.AppImage** o el instalador correspondiente a tu S.O., como cualquier otra aplicación.

---
<a name="guía-de-uso"></a>
### 🧑‍💻 Guía de Uso

  **1.** Busca la noticia en Marca.com que quieres analizar y copia la URL.

  **2.** Ejecuta Comentia.

  **3.** Selecciona la carpeta dónde deseas guardar los archivos que se van a generar.

  **4.** Pega la URL de la noticia.

  **5.** Espera a que termine y cierra Comentia si no lo necesitas más.

  Ejemplo de URL de Marca.com
  ```
  https://www.marca.com/futbol/real-madrid/2026/02/09/noticia-ejemplo.html

  ```
<a name="salida-y-archivos-generados"></a>
### 📂 Salida y archivos generados
```
noticia_ID/
├── comentarios_ID_completo.json
├── comentarios_ID_simplificado.json
└── comentarios_ID_estadisticas.txt
```

---
<a name="estadísticas"></a>
### 📊 Estadísticas

Incluye automáticamente:

  * 📈 Total de comentarios
  * 👥 Usuarios más activosç
  * 📝 Longitud media
  * 🔤 Palabras más frecuentes
  * ✅ Ratio de éxito de extracción

---
<a name="estructura-json"></a>
### 🛠️ Estructura JSON

#### Completo

```json
{
  "metadata": {
    "noticia_id": "ID",
    "url_noticia": "https://...",
    "total_comentarios": 838,
    "fecha_exportacion": "YYYY-MM-DD"
  },
  "comentarios": []
}
```

#### Simplificado

```json
[
  {
    "usuario": "X",
    "comentario": "...",
    "fecha": "..."
  }
]
```

---
<a name="preguntas-frecuentes-faq"></a>
### ❓ Preguntas Frecuentes (FAQ)
<details> <summary><b>¿Puedo extraer comentarios de cualquier noticia?</b></summary> 
  Sí, cualquier noticia de Marca.com que tenga sección de comentarios activa funciona perfectamente.</details>

<details> <summary><b>¿Cuánto tiempo tarda el proceso?</b></summary>
  Depende del número de comentarios. Para 1000 comentarios, aproximadamente 30-60 segundos.
</details>

<details> <summary><b>¿Es legal extraer estos comentarios?</b></summary>
  Sí, estás extrayendo datos públicos que ya están disponibles en la web. Recomendamos usarlo de forma ética y respetuosa, sin sobrecargar los servidores.
</details>

<details> <summary><b>¿Puedo usar los comentarios para análisis de datos?</b></summary>
  ¡Claro! Los archivos JSON son perfectos para análisis con Python, Pandas, Excel o cualquier herramienta de datos.
</details>

<details><summary><b>¿Qué hago si el programa no arranca en Linux?</b></summary>
  Asegúrate de tener instalado `python3-tk` y `python3-pyqt5`: 

```bash
  sudo apt install python3-tk python3-pyqt5
``` 
</details>

---
<a name="solución-de-problemas"></a>
### 🐛 Solución de problemas

| Problema                                         | Solución                      |
| ------------------------------------------------ | ------------------------------------------------------|
| `ModuleNotFoundError: No module named requests`  | Ejecuta en la terminal `pip install requests`         |
| `ModuleNotFoundError: No module named PyQt5`     | Ejecuta en la terminal `pip install PyQt5`            |
| La ventana de tkinter no se abre en Linux        | Ejecuta en la terminal `sudo apt install python3-tk`  |
| Error de conexión                                | Revisar internet                                      |
| Permission denied en Linux                       | Ejecuta en la terminal `chmod +x Comentia_Linux` antes de ejecutar     |


---
<a name="contribuir"></a>
### 🤝 Contribuir

Sientete libre de contribuir y mejorar **Comentia** de la manera que consideres oportuno.

---
<a name="licencia"></a>
### 📄 Licencia

MIT License© 2026

---
<a name="soporte-y-créditos"></a>
### ⭐ Soporte y Créditos

Si este proyecto te resulta útil:

<div align="center">

⭐ Dale una estrella en GitHub
🐛 Reporta bugs
💡 Propón mejoras

Desarrollado por Grupo 40 - Equipo EVO Madrid con ❤️

</div>